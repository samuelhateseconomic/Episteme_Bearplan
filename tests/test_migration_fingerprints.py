"""New migration identities must never silently change or partially commit."""
import hashlib
from pathlib import Path

import pytest

from backend.storage.db import Database, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate


def snapshot(db):
    with db.read() as conn:
        return {name: [tuple(row) for row in conn.execute(f'SELECT * FROM "{name}" ORDER BY rowid')]
                for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_hash_receipts_start_with_12_without_claiming_old_sql_identity(tmp_path: Path):
    db = Database(tmp_path / "upgrade.sqlite3")
    migrations = load_migrations()
    migrate(db, migrations[:11])
    before = snapshot(db)
    migrate(db)
    after = snapshot(db)
    assert {key: after[key] for key in before if key != "schema_migrations"} == {key: value for key, value in before.items() if key != "schema_migrations"}
    assert after["schema_migrations"][:11] == before["schema_migrations"]
    assert after["migration_fingerprints"] == [(item.version, hashlib.sha256(item.sql.encode()).hexdigest()) for item in migrations if item.version >= 12]


def test_changed_sql_with_same_version_and_name_refuses_without_replay(db):
    before = snapshot(db)
    migrations = load_migrations()
    changed = [Migration(item.version, item.name, item.sql + "\n-- accidental applied-file edit\n") if item.version == 12 else item for item in migrations]
    with pytest.raises(MigrationError, match="0012_.*fingerprint"):
        migrate(db, changed)
    assert snapshot(db) == before


@pytest.mark.parametrize("damage", ["missing_receipt", "wrong_hash", "missing_table", "wrong_table"])
def test_damaged_fingerprints_fail_actionably_and_preserve_all_saved_records(db, damage):
    with db.write() as conn:
        if damage == "missing_receipt":
            conn.execute("DELETE FROM migration_fingerprints WHERE version = 12")
        elif damage == "wrong_hash":
            conn.execute("UPDATE migration_fingerprints SET sha256 = ?", ("0" * 64,))
        else:
            conn.execute("DROP TABLE migration_fingerprints")
            if damage == "wrong_table":
                conn.execute("CREATE TABLE migration_fingerprints (version INTEGER PRIMARY KEY)")
    before = snapshot(db)
    with pytest.raises(MigrationError, match="[Kk]eep.*backup"):
        open_database(db.path)
    assert snapshot(db) == before


def test_failed_new_upgrade_rolls_back_ddl_and_fingerprint_then_retries(db):
    migrations = load_migrations()
    version = len(migrations) + 1
    upgrade = Migration(version, "future_test", "CREATE TABLE future_test (id INTEGER PRIMARY KEY);")
    failed = Migration(version, upgrade.name, upgrade.sql + "INSERT INTO missing_table VALUES (1);")
    before = snapshot(db)
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations, failed])
    assert snapshot(db) == before
    migrate(db, [*migrations, upgrade])
    assert current_version(db) == version
    with db.read() as conn:
        assert conn.execute("SELECT sha256 FROM migration_fingerprints WHERE version = ?", (version,)).fetchone()[0] == hashlib.sha256(upgrade.sql.encode()).hexdigest()
    after = snapshot(db)
    migrate(db, [*migrations, upgrade])
    assert snapshot(db) == after


def test_failed_first_fingerprint_migration_leaves_schema11_exactly_retryable(tmp_path: Path):
    db = Database(tmp_path / "schema11.sqlite3")
    migrations = load_migrations()
    migrate(db, migrations[:11])
    before = snapshot(db)
    failed = Migration(12, migrations[11].name, migrations[11].sql + "INSERT INTO missing_table VALUES (1);")
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations[:11], failed])
    assert snapshot(db) == before and current_version(db) == 11
    migrate(db)
    assert current_version(db) == len(migrations)
