"""Run the local service: python -m backend [--port N] [--no-browser].

Normally started by launch.py, which prepares dependencies and the interface first.
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import sqlite3
import sys
import threading
from collections.abc import Callable
import webbrowser

import uvicorn

from backend import __version__
from backend.app import create_app
from backend.domain.rewards import RewardConfig
from backend.platform.instance_lock import acquire_instance_lock, describe_running_instance, report_running_instance
from backend.platform.paths import (
    DATABASE_FILENAME,
    FRONTEND_DIST,
    DataDirError,
    ensure_data_dir,
    resolve_data_dir,
)
from backend.storage.db import StorageError, open_database
from backend.storage.migrations import current_version

HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="bearplans", description="Run the BearPlans local service.")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("BEARPLANS_PORT", DEFAULT_PORT)),
        help=f"loopback port (default {DEFAULT_PORT}, or BEARPLANS_PORT)",
    )
    parser.add_argument("--no-browser", action="store_true", help="do not open the browser")
    return parser.parse_args(argv)


def _treat_stop_signals_as_interrupt() -> None:
    """End on SIGTERM or Ctrl+Break exactly as on Ctrl+C.

    uvicorn drains in-flight requests, then re-raises the signal it caught; mapping
    these to KeyboardInterrupt lets main() release the instance lock and exit 0.
    """
    for name in ("SIGTERM", "SIGBREAK"):
        sig = getattr(signal, name, None)
        if sig is not None:
            signal.signal(sig, signal.default_int_handler)


def _bind(port: int) -> socket.socket:
    """Claim the loopback port before announcing it, so a busy port fails with a clear message."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if sys.platform == "win32":
            # Windows SO_REUSEADDR would let us share a port another program is listening on.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, port))
        sock.listen(128)
    except OSError:
        sock.close()
        raise
    return sock


class _ReadyServer(uvicorn.Server):
    """Announce readiness only after app lifespan and listener startup succeed."""

    def __init__(self, config: uvicorn.Config, on_ready: Callable[[], None]) -> None:
        super().__init__(config)
        self._on_ready = on_ready

    async def startup(self, sockets: list[socket.socket] | None = None) -> None:
        await super().startup(sockets=sockets)
        if self.started and not self.should_exit:
            try:
                self._on_ready()
            except BaseException:
                # Metadata/readiness failure must also drain the app lifespan;
                # closing the socket alone would leave its timer monitor alive.
                await self.shutdown(sockets=sockets)
                raise


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    _treat_stop_signals_as_interrupt()
    try:
        reward_config = RewardConfig.from_environment()
    except ValueError as exc:
        print(f"BearPlans cannot start: {exc}", file=sys.stderr)
        return 1
    try:
        data_dir = ensure_data_dir(resolve_data_dir())
    except DataDirError as exc:
        print(f"BearPlans cannot start: {exc}", file=sys.stderr)
        return 1

    try:
        lock = acquire_instance_lock(data_dir)
    except OSError as exc:
        print(f"BearPlans cannot start: cannot access the data-directory lock ({exc}).", file=sys.stderr)
        return 1
    if lock is None:
        return report_running_instance(describe_running_instance(data_dir), open_browser=not args.no_browser)

    sock = None
    try:
        try:
            db = open_database(data_dir / DATABASE_FILENAME)
        except StorageError as exc:
            print(f"BearPlans cannot start: {exc}", file=sys.stderr)
            return 1

        try:
            sock = _bind(args.port)
        except OSError as exc:
            print(
                f"BearPlans cannot start: port {args.port} is unavailable ({exc.strerror or exc}). "
                "Another program may be using it; run with --port N or set BEARPLANS_PORT.",
                file=sys.stderr,
            )
            return 1

        try:
            # Binding precedes TimerService initialization: a busy port must not
            # turn a saved running countdown into a recovered session.
            app = create_app(db, FRONTEND_DIST, reward_config=reward_config)
            schema = current_version(db)
            url = f"http://{HOST}:{args.port}/"

            def announce_ready() -> None:
                lock.record(url)
                print(f"BearPlans {__version__}")
                print(f"  data:   {data_dir}")
                print(f"  schema: version {schema}")
                print(f"  open:   {url}  (Ctrl+C to stop)", flush=True)
                if not (FRONTEND_DIST / "index.html").is_file():
                    print("  note:   interface not built; run `python3 launch.py` or `npm run build` in frontend/")
                if not args.no_browser:
                    threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()

            server = _ReadyServer(
                uvicorn.Config(app, host=HOST, port=args.port, workers=1, log_level="warning"),
                announce_ready,
            )
            try:
                server.run(sockets=[sock])
            except KeyboardInterrupt:
                pass
        except (StorageError, sqlite3.Error, OSError) as exc:
            print(
                f"BearPlans cannot start: {exc}\n"
                "Saved data was not reset. Keep the data folder and check the database/update before retrying.",
                file=sys.stderr,
            )
            return 1
        if not server.started:
            print("BearPlans cannot start: the local service did not finish starting.", file=sys.stderr)
            return 1
        print("BearPlans stopped.")
        return 0
    finally:
        try:
            if sock is not None:
                sock.close()
        finally:
            lock.release()


if __name__ == "__main__":
    sys.exit(main())
