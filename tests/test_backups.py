"""WAL-consistent full backups, safe publication, clean restore and recovery."""
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from uuid import uuid4

import pytest

from backend import backup as cli
from backend.domain import backups
from backend.domain.backups import BackupError, automatic_backups, create_backup, inspect_backup, restore_backup
from backend.domain.planning import create_placement
from backend.domain.rewards import RewardConfig, ShopService
from backend.domain.tasks import create_task
from backend.domain.timer import TimerService
from backend.domain.weeks import close_week, preview_close
from backend.platform.instance_lock import acquire_instance_lock
from backend.platform.paths import DATABASE_FILENAME, SOURCE_ROOT
from backend.storage.db import Database, StorageError, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate
from tests.conftest import ROOT, Service, free_port, http_json
from tests.test_corrections import correct, seeded
from tests.test_forest import all_rows
from tests.test_timer_recovery import RecoveryClock, _observe, _start


def rich_database(path):
    db = open_database(path)
    session, task = seeded(db)
    create_placement(db, task.id, "2026-10-23")
    close_week(db, "2026-10-19", preview_close(db, "2026-10-19").preview_token)
    ShopService(db, RewardConfig(birch_price=60)).purchase("birch", 60, str(uuid4()))
    correct(db, session, [1_800_000_000])
    return db


def test_live_wal_snapshot_preserves_every_record_and_is_independent(tmp_path):
    db = rich_database(tmp_path / "live.sqlite3")
    with db.read() as held_connection:
        held_connection.execute("PRAGMA wal_autocheckpoint = 0")
        create_task(db, "Committed only to WAL")
        assert Path(str(db.path) + "-wal").stat().st_size > 0
        expected = all_rows(db)
        destination = tmp_path / "saved.sqlite3"
        result = create_backup(db.path, destination)
        create_task(db, "Only after snapshot")
        assert result["schema_version"] == len(load_migrations())
        assert all_rows(Database(destination)) == expected
    restored = tmp_path / "clean"
    restore_backup(destination, restored)
    assert all_rows(open_database(restored / DATABASE_FILENAME)) == expected
    assert all_rows(Database(destination)) == expected  # Inspection/restore did not migrate the backup.
    assert not Path(str(destination) + "-wal").exists()
    if os.name != "nt":
        assert destination.stat().st_mode & 0o777 == 0o600
        assert (restored / DATABASE_FILENAME).stat().st_mode & 0o777 == 0o600


def test_backup_during_writes_is_a_consistent_committed_snapshot(db, tmp_path):
    first, second = create_task(db, "0"), create_task(db, "0")

    def write():
        for counter in range(35):
            with db.write() as conn:
                conn.execute("UPDATE tasks SET title = ? WHERE id IN (?, ?)", (str(counter), first.id, second.id))

    with ThreadPoolExecutor(max_workers=1) as pool:
        job = pool.submit(write)
        create_backup(db.path, tmp_path / "concurrent.sqlite3")
        job.result()
    with Database(tmp_path / "concurrent.sqlite3").read() as conn:
        assert len({row[0] for row in conn.execute("SELECT title FROM tasks")}) == 1


@pytest.mark.parametrize("existing", ["file", "source", "symlink"])
def test_backup_never_overwrites_existing_paths(db, tmp_path, existing):
    destination = tmp_path / "existing.sqlite3"
    if existing == "file":
        destination.write_bytes(b"keep this existing export")
    elif existing == "source":
        destination = db.path
    else:
        try:
            destination.symlink_to(tmp_path / "missing.sqlite3")
        except OSError:
            pytest.skip("Creating symlinks is unavailable on this host")
    original = destination.read_bytes() if destination.is_file() else None
    with pytest.raises(BackupError, match="already exists"):
        create_backup(db.path, destination)
    assert (destination.read_bytes() if destination.is_file() else None) == original


def test_source_missing_does_not_create_empty_database(tmp_path):
    source = tmp_path / "missing.sqlite3"
    with pytest.raises(BackupError, match="does not exist"):
        create_backup(source, tmp_path / "out.sqlite3")
    assert not source.exists() and not (tmp_path / "out.sqlite3").exists()
    assert not list(tmp_path.glob(".bearplans-backup-*"))


@pytest.mark.parametrize("name", ["test.sqlite3-wal", "test.sqlite3-shm", "test.sqlite3-journal", "bearplans.lock", "instance.json", "INSTANCE.JSON", "TEST.SQLITE3-WAL"])
def test_backup_cannot_occupy_database_auxiliary_or_instance_paths(db, name):
    destination = db.path.parent / name
    before = all_rows(db)
    with pytest.raises(BackupError):
        create_backup(db.path, destination)
    assert all_rows(db) == before
    assert not destination.exists()


def test_source_tree_destinations_are_rejected_without_creation(db):
    with pytest.raises(BackupError, match="outside"):
        create_backup(db.path, SOURCE_ROOT / "never-created-backup.sqlite3")
    with pytest.raises(BackupError, match="outside"):
        restore_backup(db.path, SOURCE_ROOT / "never-created-data")
    assert not (SOURCE_ROOT / "never-created-data").exists()


@pytest.mark.parametrize("damage", ["corrupt", "unrelated", "future", "fingerprint", "foreign_key", "schema"])
def test_invalid_backup_is_rejected_and_original_remains_retryable(tmp_path, damage):
    source = tmp_path / "invalid.sqlite3"
    if damage == "corrupt":
        source.write_bytes(b"not sqlite" * 100)
    elif damage == "unrelated":
        with sqlite3.connect(source) as conn:
            conn.execute("CREATE TABLE other (id INTEGER)")
    else:
        db = open_database(source)
        if damage == "foreign_key":
            create_task(db, "Broken relationship")
            with db.read() as conn:
                conn.execute("PRAGMA foreign_keys = OFF")
                conn.execute("UPDATE tasks SET project_id='missing'")
        else:
            with db.write() as conn:
                if damage == "future":
                    conn.execute("INSERT INTO schema_migrations VALUES (99, 'future', '2030-01-01T00:00:00Z')")
                elif damage == "fingerprint":
                    conn.execute("UPDATE migration_fingerprints SET sha256=? WHERE version=13", ("f" * 64,))
                else:
                    conn.execute("DROP TABLE session_corrections")
    before = source.read_bytes()
    with pytest.raises(BackupError):
        inspect_backup(source)
    target = tmp_path / "clean"
    with pytest.raises(BackupError):
        restore_backup(source, target)
    assert not (target / DATABASE_FILENAME).exists()
    assert source.read_bytes() == before
    assert not list(target.glob(".bearplans-backup-*"))


def test_restore_refuses_occupied_or_running_destination(db, tmp_path):
    folder = tmp_path / "occupied"
    folder.mkdir()
    original = folder / DATABASE_FILENAME
    original.write_bytes(b"keep my current database")
    with pytest.raises(BackupError, match="empty"):
        restore_backup(db.path, folder)
    assert original.read_bytes() == b"keep my current database"
    clean = tmp_path / "running"
    clean.mkdir()
    lock = acquire_instance_lock(clean)
    try:
        with pytest.raises(BackupError, match="using"):
            restore_backup(db.path, clean)
    finally:
        lock.release()


def test_failed_publication_leaves_no_partial_database_and_retry_works(db, tmp_path, monkeypatch):
    publish = backups._publish

    def fail(*args):
        raise OSError("synthetic disk failure")

    monkeypatch.setattr(backups, "_publish", fail)
    target = tmp_path / "restore"
    with pytest.raises(BackupError, match="disk failure"):
        restore_backup(db.path, target)
    assert not (target / DATABASE_FILENAME).exists()
    assert not list(target.glob(".bearplans-backup-*"))
    monkeypatch.setattr(backups, "_publish", publish)
    restore_backup(db.path, target)
    assert all_rows(Database(target / DATABASE_FILENAME)) == all_rows(db)


def test_destination_created_during_backup_cannot_be_overwritten(db, tmp_path, monkeypatch):
    publish = backups._publish
    destination = tmp_path / "race.sqlite3"

    def concurrent_save(stage, target):
        target.write_bytes(b"concurrent save must survive")
        publish(stage, target)

    monkeypatch.setattr(backups, "_publish", concurrent_save)
    with pytest.raises(BackupError):
        create_backup(db.path, destination)
    assert destination.read_bytes() == b"concurrent save must survive"
    assert not list(tmp_path.glob(".bearplans-backup-*"))


def test_backup_directory_failure_is_actionable_and_preserves_source(db, tmp_path, monkeypatch):
    from backend.platform.paths import DataDirError

    def denied(path):
        raise DataDirError("synthetic folder permission denied")

    before = all_rows(db)
    monkeypatch.setattr(backups, "ensure_data_dir", denied)
    with pytest.raises(BackupError, match="permission denied"):
        create_backup(db.path, tmp_path / "export.sqlite3")
    assert all_rows(db) == before


def test_preupgrade_safety_copy_survives_failed_migration_and_retry(tmp_path):
    folder = tmp_path / "legacy"
    folder.mkdir()
    db = Database(folder / DATABASE_FILENAME)
    shipped = load_migrations()
    migrate(db, shipped[:3])
    create_task(db, "Keep old data")
    before = all_rows(db)
    safety, = automatic_backups(folder, before_open=True)
    broken = Migration(4, shipped[3].name, shipped[3].sql + "\nINSERT INTO missing_table VALUES (1);")
    with pytest.raises(MigrationError):
        migrate(db, [*shipped[:3], broken])
    assert all_rows(db) == before and all_rows(Database(safety)) == before
    open_database(db.path)
    assert current_version(db) == len(shipped)
    assert all_rows(Database(safety)) == before


def test_failed_upgrade_only_changes_stage_then_retry_succeeds(tmp_path, monkeypatch):
    source = tmp_path / "legacy.sqlite3"
    old = Database(source)
    migrate(old, load_migrations()[:3])
    task = create_task(old, "Preserve legacy identity", notes="Original")
    before = all_rows(old)
    opener = backups.open_database

    def fail(stage):
        with Database(stage).write() as conn:
            conn.execute("UPDATE tasks SET title='stage changed'")
        raise StorageError("synthetic migration failure")

    monkeypatch.setattr(backups, "open_database", fail)
    with pytest.raises(BackupError, match="migration failure"):
        restore_backup(source, tmp_path / "restored")
    assert all_rows(old) == before
    assert not (tmp_path / "restored" / DATABASE_FILENAME).exists()
    monkeypatch.setattr(backups, "open_database", opener)
    result = restore_backup(source, tmp_path / "restored")
    assert result["schema_version"] == 3 and result["restored_schema_version"] == len(load_migrations())
    assert all_rows(old) == before
    with Database(Path(result["path"])).read() as conn:
        assert conn.execute("SELECT title,notes,revision FROM tasks WHERE id=?", (task.id,)).fetchone()[:] == (task.title, "Original", 1)


@pytest.mark.parametrize("state", ["running", "paused"])
def test_restore_does_not_credit_absence_or_duplicate_tree_and_reward(db, tmp_path, state):
    timer, clock, task, session = _start(db)
    _observe(timer, clock, 7.25)
    if state == "paused":
        timer.control(session.id, "pause", expected_revision=session.revision)
    expected = all_rows(db)
    create_backup(db.path, tmp_path / "saved.sqlite3")
    result = restore_backup(tmp_path / "saved.sqlite3", tmp_path / "restored")
    restored = open_database(Path(result["path"]))
    assert all_rows(restored) == expected
    later = RecoveryClock(clock.wall + timedelta(days=2))
    reopened = TimerService(restored, later)
    actual = reopened.get().active_session
    assert actual.id == session.id and actual.active_seconds == 7.25
    assert actual.state == ("needs_review" if state == "running" else "paused")
    assert actual.tree.id == session.tree.id
    assert all_rows(restored)["coin_ledger"] == []
    before_wait = all_rows(restored)
    later.advance(300)
    assert reopened.get().active_session.active_seconds == 7.25
    assert all_rows(restored) == before_wait


def test_automatic_copies_are_due_once_and_retention_preserves_other_files(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    db = open_database(folder / DATABASE_FILENAME)
    first = datetime(2026, 1, 1, tzinfo=UTC)
    for weeks in range(6):
        automatic_backups(folder, before_open=False, now=first + timedelta(weeks=weeks))
    for day in range(10):
        automatic_backups(folder, before_open=False, now=first + timedelta(weeks=6, days=day))
    directory = folder / "backups"
    assert len(list(directory.glob("daily-*.sqlite3"))) == 7
    assert len(list(directory.glob("weekly-*.sqlite3"))) == 4
    manual = directory / "my-export.sqlite3"
    manual.write_bytes(b"manual file must stay")
    safety = directory / "pre-upgrade-v3-keep.sqlite3"
    safety.write_bytes(b"safety file must stay")
    last = first + timedelta(weeks=6, days=9)
    assert automatic_backups(folder, before_open=False, now=last) == []
    assert manual.read_bytes() == b"manual file must stay" and safety.read_bytes() == b"safety file must stay"
    assert len(list(directory.glob("daily-*.sqlite3"))) == 7
    assert all_rows(db) == all_rows(Database(sorted(directory.glob("daily-*.sqlite3"))[-1]))


def test_automatic_failure_does_not_prune_or_replace_due_copy(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    db = open_database(folder / DATABASE_FILENAME)
    now = datetime(2026, 10, 31, tzinfo=UTC)
    automatic_backups(folder, before_open=False, now=now)
    due = folder / "backups/daily-2026-10-31.sqlite3"
    due.write_bytes(b"damaged due copy")
    before = all_rows(db)
    with pytest.raises(BackupError):
        automatic_backups(folder, before_open=False, now=now)
    assert due.read_bytes() == b"damaged due copy" and all_rows(db) == before


def test_cli_create_inspect_restore_and_errors(tmp_path, monkeypatch, capsys):
    folder = tmp_path / "data"
    folder.mkdir()
    db = rich_database(folder / DATABASE_FILENAME)
    monkeypatch.setenv("BEARPLANS_DATA_DIR", str(folder))
    destination = tmp_path / "portable.sqlite3"
    assert cli.main(["create", str(destination)]) == 0
    assert cli.main(["inspect", str(destination)]) == 0
    restored = tmp_path / "clean"
    assert cli.main(["restore", str(destination), "--into", str(restored)]) == 0
    assert all_rows(Database(restored / DATABASE_FILENAME)) == all_rows(db)
    assert cli.main(["restore", str(destination), "--into", str(restored)]) == 1
    assert "empty data folder" in capsys.readouterr().err


def test_real_startup_saves_preupgrade_and_daily_then_restore_restarts_identically(tmp_path):
    folder = tmp_path / "legacy"
    folder.mkdir()
    db = Database(folder / DATABASE_FILENAME)
    migrate(db, load_migrations()[:3])
    task = create_task(db, "Persist through upgrade and restore")
    original = all_rows(db)
    service = Service(folder, free_port()).start()
    _, expected = http_json("GET", service.url + "/api/tasks")
    assert service.stop() == 0
    safety, = (folder / "backups").glob("pre-upgrade-*.sqlite3")
    assert all_rows(Database(safety)) == original
    assert list((folder / "backups").glob("daily-*.sqlite3"))
    snapshot = tmp_path / "manual.sqlite3"
    env = {**os.environ, "BEARPLANS_DATA_DIR": str(folder)}
    result = subprocess.run([sys.executable, "-m", "backend.backup", "create", str(snapshot)],
                            cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    restored = tmp_path / "restored"
    restore_backup(snapshot, restored)
    rows = all_rows(Database(restored / DATABASE_FILENAME))
    for _ in range(2):
        service = Service(restored, free_port()).start()
        assert http_json("GET", service.url + "/api/tasks")[1] == expected
        assert service.stop() == 0
        assert all_rows(Database(restored / DATABASE_FILENAME)) == rows
    assert expected["tasks"][0]["id"] == task.id
