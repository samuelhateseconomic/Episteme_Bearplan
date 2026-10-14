"""Locate the user's data directory, which must stay outside the source tree.

Updates replace code, not user data, so the database never lives in the repository.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

APP_NAME = "BearPlans"
DATA_DIR_ENV = "BEARPLANS_DATA_DIR"
DATABASE_FILENAME = "bearplans.sqlite3"

SOURCE_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = SOURCE_ROOT / "frontend" / "dist"


class DataDirError(RuntimeError):
    """The configured data directory is unusable."""


def default_data_dir(
    platform: str = sys.platform,
    environ: Mapping[str, str] = os.environ,
    home: Path | None = None,
) -> Path:
    home = home or Path.home()
    if platform == "darwin":
        return home / "Library" / "Application Support" / APP_NAME
    if platform == "win32":
        base = environ.get("LOCALAPPDATA") or str(home / "AppData" / "Local")
        return Path(base) / APP_NAME
    base = environ.get("XDG_DATA_HOME") or str(home / ".local" / "share")
    return Path(base) / "bearplans"


def _is_within(path: Path, root: Path) -> bool:
    """True if path is root or below it, tolerating case-insensitive filesystems and symlinks."""
    if path == root or root in path.parents:
        return True
    for candidate in (path, *path.parents):
        try:
            if candidate.exists() and os.path.samefile(candidate, root):
                return True
        except OSError:
            continue
    return False


def resolve_data_dir(
    environ: Mapping[str, str] = os.environ,
    source_root: Path = SOURCE_ROOT,
) -> Path:
    raw = environ.get(DATA_DIR_ENV)
    path = Path(raw).expanduser() if raw else default_data_dir(environ=environ)
    path = path.resolve()
    if _is_within(path, source_root.resolve()):
        raise DataDirError(
            f"Data directory {path} is inside the source tree {source_root}. "
            f"Choose a location outside the repository (unset {DATA_DIR_ENV} to use the default)."
        )
    return path


def ensure_data_dir(path: Path) -> Path:
    try:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
    except OSError as exc:
        raise DataDirError(f"Cannot create data directory {path}: {exc}") from exc
    if not path.is_dir():
        raise DataDirError(f"Data directory {path} is not a directory.")
    return path
