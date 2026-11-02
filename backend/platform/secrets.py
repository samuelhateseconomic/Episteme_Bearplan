"""Read API tokens from the owner's private, git-ignored secrets file.

User decision (2026-11-01): tokens live in `.secrets/bearplans.secrets.env`
(KEY=value lines) rather than Mac Keychain. Values are never logged or returned
by the API. BEARPLANS_SECRETS_FILE points elsewhere (tests use a temporary file).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from backend.platform.paths import SOURCE_ROOT

SECRETS_ENV = "BEARPLANS_SECRETS_FILE"
DEFAULT_SECRETS_FILE = SOURCE_ROOT / ".secrets" / "bearplans.secrets.env"


def secrets_file() -> Path:
    raw = os.environ.get(SECRETS_ENV)
    return Path(raw).expanduser() if raw else DEFAULT_SECRETS_FILE


def read_secret(key: str) -> str | None:
    """The value for key, or None when the file or value is missing."""
    path = secrets_file()
    try:
        if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
            os.chmod(path, 0o600)  # Keep it readable by the owner only.
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() == key and not name.lstrip().startswith("#"):
            return value.strip() or None
    return None
