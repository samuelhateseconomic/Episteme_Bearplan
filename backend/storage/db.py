"""SQLite access: one database file, short transactions, one serialized write path.

SQLite allows a single writer at a time; WAL lets readers proceed alongside it.
Every mutation goes through Database.write(), so UI routes and later AI tools or
sync jobs share the same transaction rules. Never hold write() open while waiting
on a model or a provider API.
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

BUSY_TIMEOUT_MS = 5000


class StorageError(RuntimeError):
    """The database cannot be opened or used safely."""


def utc_now() -> str:
    """Current instant as an ISO-8601 UTC string, e.g. 2026-10-14T16:05:00.123456Z."""
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._write_lock = threading.Lock()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, autocommit=True, timeout=BUSY_TIMEOUT_MS / 1000)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA synchronous = FULL")
        conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
        return conn

    @contextmanager
    def read(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        """One serialized transaction; commits on success, rolls back on any error."""
        with self._write_lock:
            conn = self.connect()
            try:
                conn.execute("BEGIN IMMEDIATE")
                yield conn
                conn.execute("COMMIT")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
            finally:
                conn.close()

    @contextmanager
    def exclusive(self) -> Iterator[sqlite3.Connection]:
        """Hold the write path with an autocommit connection, for migrations that manage their own transactions."""
        with self._write_lock:
            conn = self.connect()
            try:
                yield conn
            finally:
                conn.close()


def open_database(path: Path) -> Database:
    """Open (creating if needed) the database in WAL mode and apply pending migrations."""
    from backend.storage.migrations import migrate
    from backend.storage.schema import validate_schema

    created = not path.exists()
    db = Database(path)
    try:
        with db.exclusive() as conn:
            mode = conn.execute("PRAGMA journal_mode = WAL").fetchone()[0]
            if mode.lower() != "wal":
                raise StorageError(f"Could not enable WAL mode (got {mode!r}).")
            check = conn.execute("PRAGMA quick_check").fetchone()[0]
            if check != "ok":
                raise StorageError(f"Database {path} failed its integrity check ({check}). It was not changed.")
        if created:
            try:
                path.chmod(0o600)
            except OSError:
                pass
        migrate(db)
        validate_schema(db)
    except sqlite3.Error as exc:
        raise StorageError(f"Cannot open database {path}: {exc}. It was not changed.") from exc
    return db
