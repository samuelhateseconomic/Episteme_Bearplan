"""Single-instance guard: one running service per data directory.

The operating system releases the lock when the process exits, including a crash,
so a stale lock file never blocks the next launch.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Literal
from urllib.parse import urlsplit
import webbrowser

from backend.platform.build_info import BuildInfo, current_build

LOCK_FILENAME = "bearplans.lock"
INSTANCE_FILENAME = "instance.json"


class InstanceLock:
    def __init__(self, handle: IO[bytes], info_path: Path) -> None:
        self._handle = handle
        self._info_path = info_path

    def record(self, url: str) -> None:
        build = current_build()
        self._info_path.write_text(json.dumps({
            "pid": os.getpid(), "url": url,
            "build_fingerprint": build.build_fingerprint,
            "source_root": build.source_root,
            "supported_schema": build.supported_schema,
            "started_at": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        }), encoding="utf-8")

    def release(self) -> None:
        try:
            self._info_path.unlink(missing_ok=True)
        finally:
            self._handle.close()


def _try_lock(handle: IO[bytes]) -> bool:
    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def acquire_instance_lock(data_dir: Path) -> InstanceLock | None:
    """Return the lock, or None when another instance already holds it."""
    handle = open(data_dir / LOCK_FILENAME, "a+b")
    if not _try_lock(handle):
        handle.close()
        return None
    return InstanceLock(handle, data_dir / INSTANCE_FILENAME)


def running_instance_url(data_dir: Path) -> str | None:
    return _loopback_url(_read_instance(data_dir).get("url"))


def _read_instance(data_dir: Path) -> dict:
    try:
        value = json.loads((data_dir / INSTANCE_FILENAME).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _loopback_url(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        if (
            url.scheme == "http" and url.hostname in {"127.0.0.1", "localhost", "::1"}
            and url.port is not None and 1 <= url.port <= 65535
            and not url.username and not url.password and url.path in {"", "/"}
            and not url.query and not url.fragment
        ):
            return value
    except ValueError:
        pass
    return None


@dataclass(frozen=True)
class RunningInstance:
    identity: Literal["same", "different", "unknown"]
    url: str | None
    message: str


def describe_running_instance(data_dir: Path, build: BuildInfo | None = None) -> RunningInstance:
    """Describe a held instance lock without touching its process or database."""
    info = _read_instance(data_dir)
    url = _loopback_url(info.get("url"))
    identity: Literal["same", "different", "unknown"] = "unknown"
    try:
        build = current_build() if build is None else build
        if (
            isinstance(info.get("build_fingerprint"), str)
            and isinstance(info.get("source_root"), str)
            and isinstance(info.get("supported_schema"), int)
            and not isinstance(info.get("supported_schema"), bool)
        ):
            identity = "same" if (
                info["build_fingerprint"] == build.build_fingerprint
                and info["source_root"] == build.source_root
                and info["supported_schema"] == build.supported_schema
            ) else "different"
    except OSError:
        pass
    if identity == "same" and url:
        message = f"BearPlans is already running for {data_dir} at {url} with this build."
    else:
        reason = "a different build is running" if identity == "different" else "its build identity is unavailable"
        message = (
            f"BearPlans is already running or starting for {data_dir}; {reason}. "
            "This launch will not update the interface or open the existing app. "
            "If startup is still in progress, wait and retry. Otherwise, deliberately stop "
            "the existing BearPlans service, then run python3 launch.py again to use this build. "
            "No service was restarted."
        )
        if not url:
            identity = "unknown"
    return RunningInstance(identity, url, message)


def report_running_instance(instance: RunningInstance, *, open_browser: bool) -> int:
    print(instance.message)
    if instance.identity == "same" and instance.url:
        if open_browser:
            webbrowser.open(instance.url)
        return 0
    return 1


def probe_running_instance(data_dir: Path) -> RunningInstance | None:
    """Probe only existing directories; a free/stale lock follows normal startup."""
    if not data_dir.is_dir():
        return None
    try:
        lock = acquire_instance_lock(data_dir)
        if lock is None:
            return describe_running_instance(data_dir)
        lock.release()
    except OSError:
        # Let the normal backend path report an unusable data directory/lock.
        return None
    return None
