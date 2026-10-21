"""Run the local service: python -m backend [--port N] [--no-browser].

Normally started by launch.py, which prepares dependencies and the interface first.
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

from backend import __version__
from backend.app import create_app
from backend.domain.rewards import RewardConfig
from backend.platform.instance_lock import acquire_instance_lock, running_instance_url
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


def _open_browser_when_ready(server: uvicorn.Server, url: str) -> None:
    def wait_and_open() -> None:
        deadline = time.monotonic() + 30
        while not server.started and not server.should_exit and time.monotonic() < deadline:
            time.sleep(0.1)
        if server.started:
            webbrowser.open(url)

    threading.Thread(target=wait_and_open, daemon=True).start()


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

    lock = acquire_instance_lock(data_dir)
    if lock is None:
        existing = running_instance_url(data_dir)
        print(f"BearPlans is already running for {data_dir}" + (f" at {existing}" if existing else "") + ".")
        if existing and not args.no_browser:
            webbrowser.open(existing)
        return 0

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

        url = f"http://{HOST}:{args.port}/"
        print(f"BearPlans {__version__}")
        print(f"  data:   {data_dir}")
        print(f"  schema: version {current_version(db)}")
        print(f"  open:   {url}  (Ctrl+C to stop)")
        if not (FRONTEND_DIST / "index.html").is_file():
            print("  note:   interface not built; run `python3 launch.py` or `npm run build` in frontend/")

        server = uvicorn.Server(
            uvicorn.Config(create_app(db, FRONTEND_DIST, reward_config=reward_config), host=HOST, port=args.port, workers=1, log_level="warning")
        )
        lock.record(url)
        if not args.no_browser:
            _open_browser_when_ready(server, url)
        try:
            server.run(sockets=[sock])
        except KeyboardInterrupt:
            pass
        if not server.started:
            return 1
        print("BearPlans stopped.")
        return 0
    finally:
        lock.release()


if __name__ == "__main__":
    sys.exit(main())
