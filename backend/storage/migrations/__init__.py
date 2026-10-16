"""Versioned SQL migrations.

Files are named NNNN_description.sql and applied in order, normally each in its own
transaction together with its schema_migrations row. The legacy multi-day upgrade
groups the superseded 4–7 chain atomically. Applied migrations are never edited;
schema changes add a new file. Migration SQL must not contain BEGIN/COMMIT.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from backend.storage.db import Database, StorageError, utc_now

MIGRATIONS_DIR = Path(__file__).parent
_FILENAME = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")


class MigrationError(StorageError):
    """Migrations cannot be applied; the database is left at its last good version."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


def load_migrations(directory: Path = MIGRATIONS_DIR) -> list[Migration]:
    migrations = []
    for path in sorted(directory.glob("*.sql")):
        match = _FILENAME.match(path.name)
        if not match:
            raise MigrationError(f"Unexpected migration filename: {path.name}")
        migrations.append(
            Migration(int(match.group(1)), match.group(2), path.read_text(encoding="utf-8"))
        )
    expected = list(range(1, len(migrations) + 1))
    if [m.version for m in migrations] != expected:
        raise MigrationError("Migration versions must be contiguous and start at 0001.")
    return migrations


def current_version(db: Database) -> int:
    with db.read() as conn:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        if not exists:
            return 0
        return conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]


def _upgrade_legacy_multiple_dates(
    conn: sqlite3.Connection, migrations: list[Migration], applied: dict[int, str],
) -> set[int]:
    """Preserve schema-3 multi-day plans through the superseded one-day upgrade.

    Only the exact shipped 4–7 chain qualifies. Its transient unique-task index
    would fail on valid legacy dates and is removed by 7 anyway. Skip that index
    while applying and recording the entire chain atomically, so no committed
    intermediate version claims a constraint it lacks. Applied SQL stays intact;
    custom migration lists and builds ending before 7 retain their usual behavior.
    """
    if set(applied) != {1, 2, 3}:
        return set()
    chain = load_migrations()[3:7]
    if [(item.version, item.name) for item in chain] != [
        (4, "single_planned_day"), (5, "closed_weeks"),
        (6, "countdown"), (7, "multiple_planned_days"),
    ]:
        return set()
    supplied = {item.version: item for item in migrations}
    if any(supplied.get(item.version) != item for item in chain):
        return set()
    if not conn.execute("SELECT 1 FROM planned_items GROUP BY task_id HAVING COUNT(*) > 1 LIMIT 1").fetchone():
        return set()
    try:
        conn.execute("BEGIN IMMEDIATE")
        for item in chain:
            if item.version != 4:
                conn.executescript(item.sql)
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (item.version, item.name, utc_now()),
            )
        conn.execute("COMMIT")
    except sqlite3.Error as exc:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise MigrationError(
            f"The legacy multiple-planned-date upgrade failed and was rolled back: {exc}. "
            "All saved plans were kept. Correct the failure and retry this update.",
        ) from exc
    return {item.version for item in chain}


def migrate(db: Database, migrations: list[Migration] | None = None) -> int:
    """Apply pending migrations and return the resulting schema version."""
    migrations = load_migrations() if migrations is None else migrations
    with db.exclusive() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " version INTEGER PRIMARY KEY,"
            " name TEXT NOT NULL,"
            " applied_at TEXT NOT NULL)"
        )
        applied = dict(conn.execute("SELECT version, name FROM schema_migrations").fetchall())
        known = {m.version: m.name for m in migrations}
        newest_applied = max(applied, default=0)
        if newest_applied > max(known, default=0):
            raise MigrationError(
                f"Database schema version {newest_applied} is newer than this BearPlans build "
                f"supports ({max(known, default=0)}). Update BearPlans; the database was not changed."
            )
        for version, name in applied.items():
            if known.get(version) != name:
                raise MigrationError(
                    f"Applied migration {version:04d}_{name} does not match this build's migrations."
                )
        upgraded = _upgrade_legacy_multiple_dates(conn, migrations, applied)
        for migration in migrations:
            if migration.version in applied or migration.version in upgraded:
                continue
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.executescript(migration.sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                    (migration.version, migration.name, utc_now()),
                )
                conn.execute("COMMIT")
            except sqlite3.Error as exc:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                if migration.name == "single_planned_day" and isinstance(exc, sqlite3.IntegrityError):
                    raise MigrationError(
                        "The one-planned-day upgrade could not be applied because some tasks have "
                        "multiple planned dates. No plans or tasks were removed; the upgrade was "
                        "rolled back. Open the previous BearPlans build, remove extra planned dates "
                        "so each task has only one, then retry this update. Split multi-day work "
                        "into subtasks."
                    ) from exc
                raise MigrationError(
                    f"Migration {migration.version:04d}_{migration.name} failed and was rolled back: {exc}"
                ) from exc
        return conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()[0]
