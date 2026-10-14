import sqlite3
from pathlib import Path

import pytest

from backend.domain.tasks import create_task
from backend.storage.db import Database, StorageError, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate


def tables(db: Database) -> set[str]:
    with db.read() as conn:
        return {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_fresh_database_reaches_latest_version(tmp_path: Path) -> None:
    db = open_database(tmp_path / "fresh.sqlite3")
    assert current_version(db) == len(load_migrations())
    assert {"tasks", "projects", "schema_migrations"} <= tables(db)
    with db.read() as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        rows = conn.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version").fetchall()
    assert [(row["version"], row["name"]) for row in rows] == [(m.version, m.name) for m in load_migrations()]
    assert all(row["applied_at"].endswith("Z") for row in rows)


def test_reopening_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3"
    open_database(path)
    db = open_database(path)
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == len(load_migrations())


def test_failed_migration_rolls_back_and_keeps_prior_version(tmp_path: Path) -> None:
    db = open_database(tmp_path / "db.sqlite3")
    applied = load_migrations()
    next_version = len(applied) + 1
    broken = [
        *applied,
        Migration(next_version, "broken", "CREATE TABLE half_done (id INTEGER); INSERT INTO missing_table VALUES (1);"),
    ]
    with pytest.raises(MigrationError, match=f"{next_version:04d}_broken failed and was rolled back"):
        migrate(db, broken)
    assert current_version(db) == len(applied)
    assert "half_done" not in tables(db)


def test_refuses_database_newer_than_build(tmp_path: Path) -> None:
    db = open_database(tmp_path / "db.sqlite3")
    with db.write() as conn:
        conn.execute("INSERT INTO schema_migrations VALUES (99, 'future', '2030-01-01T00:00:00Z')")
    with pytest.raises(MigrationError, match="newer than this BearPlans build"):
        migrate(db)
    assert current_version(db) == 99


def test_refuses_mismatched_applied_migration(tmp_path: Path) -> None:
    db = open_database(tmp_path / "db.sqlite3")
    renamed = [Migration(m.version, "renamed" if m.version == 1 else m.name, m.sql) for m in load_migrations()]
    with pytest.raises(MigrationError, match="does not match"):
        migrate(db, renamed)


def test_rejects_non_contiguous_files(tmp_path: Path) -> None:
    (tmp_path / "0001_a.sql").write_text("SELECT 1;")
    (tmp_path / "0003_c.sql").write_text("SELECT 1;")
    with pytest.raises(MigrationError, match="contiguous"):
        load_migrations(tmp_path)


def test_unreadable_database_is_reported_not_reset(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.sqlite3"
    path.write_bytes(b"this is not a database" * 100)
    original = path.read_bytes()
    with pytest.raises(StorageError, match="was not changed"):
        open_database(path)
    assert path.read_bytes() == original


def test_damaged_pages_behind_a_valid_header_are_reported_not_reset(tmp_path: Path) -> None:
    path = tmp_path / "damaged.sqlite3"
    db = open_database(path)
    for i in range(200):
        create_task(db, f"Task {i} " + "x" * 150)
    with db.exclusive() as conn:
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    data = bytearray(path.read_bytes())
    page_size = int.from_bytes(data[16:18], "big")
    data[page_size : page_size * 3] = b"\xff" * (page_size * 2)
    path.write_bytes(bytes(data))
    with pytest.raises(StorageError, match="was not changed"):
        open_database(path)
    assert path.read_bytes() == bytes(data)


def test_schema_rejects_blank_titles_even_without_the_domain_layer(db: Database) -> None:
    with db.read() as conn:
        project_id = conn.execute("SELECT id FROM projects WHERE is_default = 1").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
        with db.write() as conn:
            conn.execute(
                "INSERT INTO tasks (id, project_id, title, created_at, updated_at) VALUES (?, ?, '   ', 'x', 'x')",
                ("00000000-0000-4000-8000-000000000000", project_id),
            )


def test_upgrade_from_0001_preserves_every_task(tmp_path: Path) -> None:
    """M1 acceptance: foundation tasks survive the move into projects, unchanged."""
    path = tmp_path / "old.sqlite3"
    db = Database(path)
    with db.exclusive() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
    first_only = [m for m in load_migrations() if m.version == 1]
    migrate(db, first_only)

    rows = [
        ("fd08250b-b48f-4622-b6ac-a9349700d018", "Read Math 55 notes", "2026-10-14T04:30:00.000000Z", 3),
        ("1104110f-3146-449b-8f91-147852faf11c", "Write PS7", "2026-10-14T04:31:00.000000Z", 1),
    ]
    with db.write() as conn:
        for task_id, title, at, revision in rows:
            conn.execute(
                "INSERT INTO tasks (id, title, created_at, updated_at, revision) VALUES (?, ?, ?, ?, ?)",
                (task_id, title, at, at, revision),
            )

    migrate(db)
    assert current_version(db) == len(load_migrations())

    with db.read() as conn:
        after = conn.execute(
            "SELECT id, title, created_at, revision, project_id, parent_id, notes,"
            " deadline, estimate_minutes, completed_at FROM tasks ORDER BY created_at"
        ).fetchall()
        default_id = conn.execute("SELECT id FROM projects WHERE is_default = 1").fetchone()[0]
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

    assert [(r["id"], r["title"], r["created_at"], r["revision"]) for r in after] == rows
    for row in after:
        assert row["project_id"] == default_id
        assert (row["parent_id"], row["notes"], row["deadline"]) == (None, "", None)
        assert (row["estimate_minutes"], row["completed_at"]) == (None, None)


def test_upgrade_creates_a_default_project_even_with_no_tasks(tmp_path: Path) -> None:
    db = open_database(tmp_path / "empty.sqlite3")
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM projects WHERE is_default = 1").fetchone()[0] == 1


def test_a_second_default_project_is_impossible(tmp_path: Path) -> None:
    db = open_database(tmp_path / "db.sqlite3")
    with pytest.raises(sqlite3.IntegrityError):
        with db.write() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, is_default, created_at, updated_at, revision)"
                " VALUES ('00000000-0000-4000-8000-000000000001', 'Second', 1, 'x', 'x', 1)"
            )


def test_failed_v1_table_rebuild_preserves_original_and_can_retry(tmp_path: Path) -> None:
    from backend.domain.tasks import list_tasks

    db = Database(tmp_path / "upgrade.sqlite3")
    migrations = load_migrations()
    migrate(db, migrations[:1])
    original = ("00000000-0000-4000-8000-000000000001", "Foundation", "2026-10-13T20:00:00Z", "2026-10-13T21:00:00Z", 7)
    with db.write() as conn:
        conn.execute("INSERT INTO tasks (id, title, created_at, updated_at, revision) VALUES (?, ?, ?, ?, ?)", original)
    failed = Migration(2, migrations[1].name, migrations[1].sql + "\nINSERT INTO nonexistent VALUES (1);")
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [migrations[0], failed])
    assert current_version(db) == 1
    with db.read() as conn:
        assert tuple(conn.execute("SELECT id, title, created_at, updated_at, revision FROM tasks").fetchone()) == original
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert "projects" not in tables(db) and "tasks_new" not in tables(db)
    migrate(db)
    # Reopening a schema-2 database is also safe: nothing is rebuilt again.
    after = list_tasks(db)
    assert list_tasks(open_database(db.path)) == after
    with db.read() as conn:
        assert tuple(conn.execute("SELECT id, title, created_at, updated_at, revision FROM tasks").fetchone()) == original
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
