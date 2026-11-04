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

import os
import shutil
import stat
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
