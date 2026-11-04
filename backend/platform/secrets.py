"""Read API tokens from the owner's private secrets folder.

User decision (2026-11-01): tokens live in a KEY=value file rather than Mac Keychain.
User decision (2026-11-03): that folder is `secrets/` inside the BearPlans data folder
(on a Mac, ~/Library/Application Support/BearPlans/secrets/), not the code folder, so
credentials can later be set from inside the app. The old `.secrets/` folder in the
code folder is copied there once at startup and then left alone.

Values are never logged or returned by the API. Credentials are not in the database,
so database backups never contain them. BEARPLANS_SECRETS_FILE points elsewhere
(tests use a temporary file); its folder then holds the Google files too.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import threading
from pathlib import Path

from backend.platform.paths import SOURCE_ROOT, DataDirError, resolve_data_dir

SECRETS_ENV = "BEARPLANS_SECRETS_FILE"
SECRETS_FILENAME = "bearplans.secrets.env"
SECRETS_DIRNAME = "secrets"
LEGACY_SECRETS_DIR = SOURCE_ROOT / ".secrets"
# Every credential file BearPlans keeps; only these are copied from the old folder.
CREDENTIAL_FILES = (SECRETS_FILENAME, "google_oauth_client.json", "google_token.json")
# Written after the one-time copy, so a credential later removed in the app is not copied back.
MOVED_MARKER = ".copied-from-code-folder"


def secrets_file() -> Path:
    raw = os.environ.get(SECRETS_ENV)
    if raw:
        return Path(raw).expanduser()
    try:
        return resolve_data_dir() / SECRETS_DIRNAME / SECRETS_FILENAME
    except DataDirError:
        # The service refuses to start in this case; callers simply find no credentials.
        return LEGACY_SECRETS_DIR / SECRETS_FILENAME


def secrets_dir() -> Path:
    return secrets_file().parent


def move_legacy_secrets(legacy_dir: Path = LEGACY_SECRETS_DIR) -> list[str]:
    """Copy credentials from the code folder's `.secrets/` into the data folder once.

    Runs once (a marker file records it). A file already in the new folder is never
    overwritten, the old folder is left as it is, and nothing is copied when
    BEARPLANS_SECRETS_FILE is set. Returns the names
    copied (never contents), so the caller can report a count.
    """
    if os.environ.get(SECRETS_ENV) or not legacy_dir.is_dir():
        return []
    target = secrets_dir()
    if target.resolve() == legacy_dir.resolve() or (target / MOVED_MARKER).exists():
        return []
    target.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(target, 0o700)
    copied: list[str] = []
    for name in CREDENTIAL_FILES:
        source, destination = legacy_dir / name, target / name
        if not source.is_file() or destination.exists():
            continue
        temporary = destination.with_name(destination.name + ".tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "wb") as out, source.open("rb") as src:
            shutil.copyfileobj(src, out)
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
        copied.append(name)
    (target / MOVED_MARKER).write_text(
        "Credentials were copied here from the code folder's .secrets/ once; delete this file to copy again.\n",
        encoding="utf-8")
    return copied


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


# ---- writing (connection setup step 2, 2026-11-03)
#
# Values are written atomically and owner-only. Callers check a value before saving
# it; nothing here ever returns a stored value except read_secret().

STATUS_FILENAME = "status.json"  # Dates and check results only, never a credential.
_write_lock = threading.Lock()


def _ensure_dir() -> Path:
    folder = secrets_dir()
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(folder, 0o700)
    return folder


def write_private_file(path: Path, data: bytes) -> None:
    """Replace path with data, owner-only, so a crash leaves the old or the new file."""
    _ensure_dir()
    temporary = path.with_name(path.name + ".tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def remove_private_file(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


def _set_line(key: str, value: str | None) -> None:
    path = secrets_file()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        lines = []
    kept = [line for line in lines
            if line.lstrip().startswith("#") or line.partition("=")[0].strip() != key or "=" not in line]
    if value is not None:
        kept.append(f"{key}={value}")
    write_private_file(path, ("\n".join(kept) + "\n").encode("utf-8") if kept else b"")


def write_secret(key: str, value: str) -> None:
    """Save key=value in the secrets file, replacing any earlier value and keeping other lines."""
    if not value or any(ch.isspace() or not ch.isprintable() for ch in value):
        raise ValueError("A secret value must be one line without spaces.")
    with _write_lock:
        _set_line(key, value)


def remove_secret(key: str) -> bool:
    """Remove key from the secrets file; True when a value was there."""
    with _write_lock:
        had = read_secret(key) is not None
        if had:
            _set_line(key, None)
        return had


def read_status() -> dict[str, dict[str, object]]:
    try:
        data = json.loads((secrets_dir() / STATUS_FILENAME).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, dict)} if isinstance(data, dict) else {}


def update_status(name: str, entry: dict[str, object] | None) -> None:
    """Record (or with None, forget) when a credential was saved and last checked."""
    with _write_lock:
        status = read_status()
        if entry is None:
            status.pop(name, None)
        else:
            status[name] = {**status.get(name, {}), **entry}
        write_private_file(secrets_dir() / STATUS_FILENAME, json.dumps(status, indent=2).encode("utf-8"))
