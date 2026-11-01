"""Full-database snapshots and restore into a clean, separately locked data folder.

SQLite's backup API includes committed WAL records. Files are staged, checked and
published without replacing an existing path. No personal content is logged and
no directory other than the selected database is included in a backup.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time
from uuid import uuid4

from backend.platform.instance_lock import INSTANCE_FILENAME, LOCK_FILENAME, acquire_instance_lock
from backend.platform.paths import DATABASE_FILENAME, SOURCE_ROOT, DataDirError, _is_within, ensure_data_dir
from backend.storage.db import StorageError, open_database
from backend.storage.migrations import current_version, load_migrations


class BackupError(StorageError):
    """A backup/restore could not safely finish; existing data is retained."""


def _outside_source(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if _is_within(resolved, SOURCE_ROOT.resolve()):
        raise BackupError("Choose a backup or data location outside the BearPlans source folder.")
    return resolved


@contextmanager
def _stage(directory: Path):
    descriptor, name = tempfile.mkstemp(prefix=".bearplans-backup-", suffix=".sqlite3", dir=directory)
    os.close(descriptor)  # mkstemp creates a private (0600) file.
    path = Path(name)
    try:
        yield path
    finally:
        for suffix in ("", "-wal", "-shm", "-journal"):
            Path(str(path) + suffix).unlink(missing_ok=True)


def _snapshot(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise BackupError("The selected database does not exist or is not a regular file.")
    deadline = time.monotonic() + 30

    def progress(status: int, remaining: int, total: int) -> None:
        if time.monotonic() > deadline:
            raise BackupError("The snapshot did not finish within 30 seconds. Retry after current writes finish.")

    with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, autocommit=True)) as original:
        with closing(sqlite3.connect(destination, autocommit=True)) as target:
            original.backup(target, pages=256, progress=progress, sleep=0.05)
            # Keep the published snapshot self-contained, without WAL sidecars.
            target.execute("PRAGMA journal_mode = DELETE")


def _check(path: Path) -> dict:
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, autocommit=True)) as conn:
        conn.execute("BEGIN")
        if [r[0] for r in conn.execute("PRAGMA integrity_check")] != ["ok"]:
            raise BackupError("The database failed its integrity check. Keep the original and choose a verified backup.")
        if conn.execute("PRAGMA foreign_key_check").fetchone():
            raise BackupError("The database has broken record relationships. No restore was published.")
        try:
            version = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
        except sqlite3.Error as exc:
            raise BackupError("This is not a recognized BearPlans database.") from exc
        if not isinstance(version, int) or not 1 <= version <= len(load_migrations()):
            raise BackupError("This backup uses an unsupported schema. Use the matching or a newer BearPlans build.")
        counts = {}
        for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            quoted = '"' + name.replace('"', '""') + '"'
            counts[name] = conn.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
        return {"schema_version": version, "record_counts": counts}


def _validate_upgrade(path: Path) -> dict:
    """Validate/upgrade only the disposable stage; never open the source for writes."""
    before = _check(path)
    db = open_database(path)
    with db.exclusive() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA journal_mode = DELETE")
    _check(path)
    return {**before, "restored_schema_version": current_version(db)}


def _publish(stage: Path, destination: Path) -> None:
    with stage.open("rb") as handle:
        os.fsync(handle.fileno())
    # A hard link is an atomic no-replace publication on the same filesystem.
    # Unlike replace()/POSIX rename(), this cannot overwrite a concurrent save.
    os.link(stage, destination)
    if os.name != "nt":
        descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def inspect_backup(source: Path) -> dict:
    """Check a consistent copy and prove it can reach this build's schema."""
    source = _outside_source(source)
    try:
        with tempfile.TemporaryDirectory(prefix="bearplans-backup-check-") as directory:
            with _stage(Path(directory)) as stage:
                _snapshot(source, stage)
                return _validate_upgrade(stage)
    except (OSError, sqlite3.Error, StorageError, DataDirError) as exc:
        if isinstance(exc, BackupError):
            raise
        raise BackupError(f"Cannot inspect this backup: {exc}. The source was not replaced.") from exc


def create_backup(source: Path, destination: Path, *, safety_copy: bool = False) -> dict:
    """Publish one snapshot. Safety copies preserve pre-upgrade schema verbatim."""
    source = _outside_source(source)
    # Check the supplied path before resolving it, including dangling symlinks.
    if os.path.lexists(destination.expanduser()):
        raise BackupError("The backup destination already exists. Choose a new filename; existing backups are never overwritten.")
    destination = _outside_source(destination)
    same_folder = destination.parent == source.parent or (
        destination.parent.exists() and os.path.samefile(destination.parent, source.parent)
    )
    if same_folder and destination.name.casefold() in {
        *(source.name.casefold() + suffix for suffix in ("-wal", "-shm", "-journal")), LOCK_FILENAME, INSTANCE_FILENAME,
    }:
        raise BackupError("Choose a separate backup filename, outside SQLite auxiliary and BearPlans instance files.")
    try:
        ensure_data_dir(destination.parent)
        with _stage(destination.parent) as stage:
            _snapshot(source, stage)
            info = _check(stage)
            if not safety_copy:
                # Validation can migrate its own second copy, preserving the
                # snapshot's original records/schema at the chosen destination.
                inspect_backup(stage)
            _publish(stage, destination)
        return {"path": str(destination), **info}
    except (OSError, sqlite3.Error, StorageError, DataDirError) as exc:
        if isinstance(exc, BackupError):
            raise
        raise BackupError(f"Cannot save the backup: {exc}. Existing data/backups were not replaced.") from exc


def restore_backup(source: Path, data_dir: Path) -> dict:
    """Restore to a clean folder only. The previous app/data remain the rollback."""
    source, data_dir = _outside_source(source), _outside_source(data_dir)
    try:
        ensure_data_dir(data_dir)
        if any(p.name != LOCK_FILENAME for p in data_dir.iterdir()):
            raise BackupError("Restore needs an empty data folder. Choose a clean folder; your existing data stays in place.")
        lock = acquire_instance_lock(data_dir)
        if lock is None:
            raise BackupError("BearPlans is using the destination folder. Stop that instance or choose a clean folder.")
        try:
            # Recheck after locking so a concurrent launch/restore cannot win
            # between the initial empty-folder check and publication.
            if any(p.name != LOCK_FILENAME for p in data_dir.iterdir()):
                raise BackupError("The destination changed. Choose a clean folder and retry; no database was replaced.")
            with _stage(data_dir) as stage:
                _snapshot(source, stage)
                info = _validate_upgrade(stage)
                destination = data_dir / DATABASE_FILENAME
                _publish(stage, destination)
            return {"path": str(destination), **info}
        finally:
            lock.release()
    except (OSError, sqlite3.Error, StorageError, DataDirError) as exc:
        if isinstance(exc, BackupError):
            raise
        raise BackupError(f"Cannot restore the backup: {exc}. The backup and original data were not replaced.") from exc


_AUTOMATIC = re.compile(r"^(daily-\d{4}-\d{2}-\d{2}|weekly-\d{4}-W\d{2})\.sqlite3$")


def automatic_backups(data_dir: Path, *, before_open: bool, daily_keep: int = 7, weekly_keep: int = 4,
                      now: datetime | None = None) -> list[Path]:
    """Called while startup owns the instance lock; failures prevent unsafe launch.

    Before an upgrade keep a unique unpruned safety copy. After successful open,
    keep a daily and an ISO-week copy. Prune only owned names after new copies
    validate, never manual exports or pre-upgrade originals.
    """
    if daily_keep < 1 or weekly_keep < 1:
        raise BackupError("Backup retention must keep at least one daily and one weekly copy.")
    source = data_dir / DATABASE_FILENAME
    if not source.is_file():
        return []
    data_dir = _outside_source(data_dir)
    directory = data_dir / "backups"
    now = datetime.now().astimezone() if now is None else now
    created = []
    if before_open:
        # Read-only version inspection must precede open_database/migrations.
        try:
            with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
                version = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
        except sqlite3.Error as exc:
            raise BackupError(f"Cannot inspect the database before backup: {exc}. It was not changed.") from exc
        if 0 < version < len(load_migrations()):
            destination = directory / f"pre-upgrade-v{version}-{now.strftime('%Y%m%dT%H%M%S')}-{uuid4().hex}.sqlite3"
            create_backup(source, destination, safety_copy=True)
            created.append(destination)
        return created
    for prefix, label in (("daily", now.strftime("%Y-%m-%d")), ("weekly", now.strftime("%G-W%V"))):
        destination = directory / f"{prefix}-{label}.sqlite3"
        if destination.exists():
            inspect_backup(destination)  # A corrupt due copy must not suppress a new safe launch silently.
        else:
            create_backup(source, destination)
            created.append(destination)
    for prefix, keep in (("daily", daily_keep), ("weekly", weekly_keep)):
        candidates = sorted((p for p in directory.iterdir() if p.is_file() and not p.is_symlink()
                             and _AUTOMATIC.fullmatch(p.name) and p.name.startswith(prefix + "-")), reverse=True)
        for obsolete in candidates[keep:]:
            obsolete.unlink()
    return created
