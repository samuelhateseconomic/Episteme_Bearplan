"""Single-instance guard: one running service per data directory.

The operating system releases the lock when the process exits, including a crash,
so a stale lock file never blocks the next launch.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import IO

LOCK_FILENAME = "bearplans.lock"
INSTANCE_FILENAME = "instance.json"


class InstanceLock:
    def __init__(self, handle: IO[bytes], info_path: Path) -> None:
        self._handle = handle
        self._info_path = info_path

    def record(self, url: str) -> None:
        self._info_path.write_text(json.dumps({"pid": os.getpid(), "url": url}), encoding="utf-8")

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
    try:
        return json.loads((data_dir / INSTANCE_FILENAME).read_text(encoding="utf-8")).get("url")
    except (OSError, ValueError, AttributeError):
        return None
