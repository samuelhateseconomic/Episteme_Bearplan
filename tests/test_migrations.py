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
    assert current_version(db) == len(load_migrations()) == 1
    assert {"tasks", "schema_migrations"} <= tables(db)
    with db.read() as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        row = conn.execute("SELECT version, name, applied_at FROM schema_migrations").fetchone()
    assert (row["version"], row["name"]) == (1, "initial")
    assert row["applied_at"].endswith("Z")


def test_reopening_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3"
    open_database(path)
    db = open_database(path)
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1


def test_failed_migration_rolls_back_and_keeps_prior_version(tmp_path: Path) -> None:
    db = open_database(tmp_path / "db.sqlite3")
    broken = [
        *load_migrations(),
        Migration(2, "broken", "CREATE TABLE half_done (id INTEGER); INSERT INTO missing_table VALUES (1);"),
    ]
    with pytest.raises(MigrationError, match="0002_broken failed and was rolled back"):
        migrate(db, broken)
    assert current_version(db) == 1
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
    with pytest.raises(MigrationError, match="does not match"):
        migrate(db, [Migration(1, "renamed", "SELECT 1;")])


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
    with pytest.raises(sqlite3.IntegrityError):
        with db.write() as conn:
            conn.execute(
                "INSERT INTO tasks (id, title, created_at, updated_at) VALUES (?, '   ', 'x', 'x')",
                ("00000000-0000-4000-8000-000000000000",),
            )
