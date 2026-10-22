"""Actual schema-8 identity collision and additive launch-repair compatibility.

The frozen legacy SQL is copied byte-for-byte from the preserved local recovery
branch: stash untracked commit eeee9a6378d08ac73ff7f9626486c26d13dd9193,
path backend/storage/migrations/0008_timer_recovery.sql, Git blob
3a61b238572131d9f860e5207bbfa74a65337cde. It deliberately has the same version/name
as the subsequently pulled migration while creating a different recovery table.
The fixture must not be replaced with current SQL or an artificial dropped table.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from uuid import uuid4

import pytest

from backend.app import create_app
from backend.domain.forest import list_forest
from backend.domain.planning import create_placement
from backend.domain.projects import create_project
from backend.domain.rewards import RewardConfig, ShopService
from backend.domain.streaks import get_streaks
from backend.domain.tasks import create_task, get_task, set_task_completion
from backend.domain.timer import TimerService
from backend.domain.weeks import close_week, preview_close
from backend.storage.db import Database, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate
from tests.test_timer_recovery import RecoveryClock, _observe

LEGACY8_FIXTURE = Path(__file__).parent / "fixtures" / "0008_legacy_timer_recovery.sql"
LEGACY8_SHA256 = "d7b41e9e962e0fcde2fb8e5c2160f2317c3e322d8225ec93ee018009e090d743"


def _clock():
    return RecoveryClock(datetime(2026, 10, 22, 20, tzinfo=UTC))


def _snapshot(db: Database):
    """Capture row order and every original column, including recovery evidence."""
    with db.read() as conn:
        names = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
        )]
        return {name: {
            "columns": [row[1] for row in conn.execute(f'PRAGMA table_info("{name}")')],
            "rows": [dict(row) for row in conn.execute(f'SELECT * FROM "{name}" ORDER BY rowid')],
        } for name in names}


def _assert_preserved(db: Database, before):
    with db.read() as conn:
        for table, entry in before.items():
            columns = ", ".join(f'"{name}"' for name in entry["columns"])
            rows = [dict(row) for row in conn.execute(f'SELECT {columns} FROM "{table}" ORDER BY rowid')]
            if table == "schema_migrations":
                original_versions = {row["version"] for row in entry["rows"]}
                rows = [row for row in rows if row["version"] in original_versions]
            assert rows == entry["rows"], table


def _assert_integrity(db: Database):
    with db.read() as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def _schema_objects(db: Database):
    with db.read() as conn:
        return [tuple(row) for row in conn.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name")]


def _legacy_ten(path: Path, state: str):
    """Apply the actual legacy 8, then the current 9/10 without rerunning 8."""
    migrations = load_migrations()
    db = Database(path)
    migrate(db, migrations[:7])
    project = create_project(db, "Preserved legacy project")
    parent = create_task(db, "Preserved parent", project_id=project.id, notes="Original parent notes", deadline="2026-11-02")
    work = create_task(db, "Preserved subtask", parent_id=parent.id, project_id=project.id, notes="Original child notes", estimate_minutes=17)
    other = create_task(db, "Completed sibling", parent_id=parent.id, project_id=project.id)
    set_task_completion(db, other.id, True)
    create_placement(db, work.id, "2026-10-12")
    close_week(db, "2026-10-12", preview_close(db, "2026-10-12").preview_token)
    create_placement(db, work.id, "2026-10-19")
    legacy8 = Migration(8, migrations[7].name, LEGACY8_FIXTURE.read_text())
    migrate(db, [*migrations[:7], legacy8])
    finished_id, active_id = str(uuid4()), str(uuid4())
    with db.write() as conn:
        for session_id, row_state, checkpoint, active_us in (
            (finished_id, "finished", "2026-10-18T20:00:04.250000Z", 4_250_000),
            (active_id, state, "2026-10-18T20:10:07.250000Z", 7_250_000),
        ):
            start = "2026-10-18T20:00:00.000000Z" if row_state == "finished" else "2026-10-18T20:10:00.000000Z"
            operation = str(uuid4())
            conn.execute(
                "INSERT INTO timer_sessions (id, start_operation_id, task_id, task_title, project_id, project_name, parent_title, "
                "duration_minutes, state, active_microseconds, started_at, checkpoint_at, finished_at, outcome, review_reason, revision, pause_reason) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 25, ?, ?, ?, ?, ?, ?, ?, 7, ?)",
                (session_id, operation, work.id, "Historical child context", project.id, "Historical project context", "Historical parent context",
                 row_state, active_us, start, checkpoint,
                 "2026-10-18T20:02:00.000000Z" if row_state == "finished" else None,
                 "interrupted" if row_state == "finished" else None,
                 "Original uncertain gap" if row_state == "needs_review" else None,
                 "sleep" if row_state == "paused" else None),
            )
            conn.execute(
                "INSERT INTO timer_intervals (id, session_id, started_at, checkpoint_at, ended_at, active_microseconds) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid4()), session_id, start, checkpoint, None if row_state == "running" else checkpoint, active_us),
            )
            conn.execute("INSERT INTO timer_operations VALUES (?, ?, 'start', ?)", (operation, session_id, '{"legacy":"preserve exact fingerprint"}'))
        conn.execute(
            "INSERT INTO timer_recovery_gaps VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'finish')",
            (str(uuid4()), finished_id, "Original resolved history", "2026-10-18T20:00:04.250000Z",
             "2026-10-18T20:01:00.000000Z", 55_750_000, "2026-10-18T20:02:00.000000Z"),
        )
        if state == "needs_review":
            conn.execute(
                "INSERT INTO timer_recovery_gaps VALUES (?, ?, ?, ?, ?, ?, 0, NULL, NULL)",
                (str(uuid4()), active_id, "Original uncertain gap", "2026-10-18T20:10:07.250000Z",
                 "2026-10-18T20:11:00.000000Z", 52_750_000),
            )
    before_later_migrations = _snapshot(db)
    # Same migration identity, different SQL: this is the original failure path.
    assert legacy8.name == migrations[7].name == "timer_recovery"
    assert legacy8.sql != migrations[7].sql
    migrate(db, migrations[:10])
    _assert_preserved(db, before_later_migrations)
    with db.read() as conn:
        assert tuple(conn.execute("SELECT version, name FROM schema_migrations WHERE version = 8").fetchone()) == (8, "timer_recovery")
        assert conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'timer_interruptions'").fetchone() is None
    return db, work, finished_id, active_id


def test_frozen_legacy_schema8_fixture_matches_preserved_branch_bytes():
    assert hashlib.sha256(LEGACY8_FIXTURE.read_bytes()).hexdigest() == LEGACY8_SHA256


@pytest.mark.parametrize("state", ["running", "needs_review", "paused"])
def test_exact_legacy8_to_current10_launch_failure_is_repaired_additively_by11(tmp_path: Path, state):
    db, task, _, active_id = _legacy_ten(tmp_path / f"legacy-{state}.sqlite3", state)
    before = _snapshot(db)
    assert current_version(db) == 10
    # This fixture has never contained the current recovery table; no DROP is used.
    with pytest.raises(sqlite3.OperationalError, match="no such table: timer_interruptions"):
        create_app(db, timer_clock=_clock()).state.timer.get()
    _assert_preserved(db, before)
    repaired = open_database(db.path)
    assert current_version(repaired) >= 11
    _assert_preserved(repaired, before)
    with repaired.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timer_interruptions").fetchone()[0] == 0
    timer = create_app(repaired, timer_clock=_clock()).state.timer
    current = timer.get().active_session
    assert current.id == active_id and current.active_seconds == 7.25
    assert current.state == ("paused" if state == "paused" else "needs_review")
    if state != "paused":
        assert current.recovery.kind == ("service_restart" if state == "running" else "checkpoint_gap")
        assert current.recovery.confirmed_active_seconds == 7.25
        assert current.recovery.measured_sleep_seconds is None
    else:
        assert current.recovery is None
    expected = before
    if state == "running":
        expected = {table: {"columns": entry["columns"], "rows": [dict(row) for row in entry["rows"]]} for table, entry in before.items()}
        session = next(row for row in expected["timer_sessions"]["rows"] if row["id"] == active_id)
        session.update(state="needs_review", review_reason=current.review_reason, revision=session["revision"] + 1)
        interval = next(row for row in expected["timer_intervals"]["rows"] if row["session_id"] == active_id)
        interval["ended_at"] = interval["checkpoint_at"]
    _assert_preserved(repaired, expected)
    assert get_task(repaired, task.id) == task
    with repaired.read() as conn:
        # Earlier sessions remain ineligible for all M3 backfills.
        for table in ("trees", "coin_enrollments", "coin_ledger", "owned_species", "shop_operations"):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    after_startup = _snapshot(repaired)
    for _ in range(2):
        reopened = open_database(db.path)
        again = create_app(reopened, timer_clock=_clock()).state.timer.get().active_session
        assert again == current
        _assert_preserved(reopened, after_startup)
    _assert_integrity(repaired)


@pytest.mark.parametrize("resolution", ["resume", "finish"])
def test_preserved_unresolved_legacy_evidence_never_overrides_current_explicit_decision(tmp_path: Path, resolution):
    db, _, _, active_id = _legacy_ten(tmp_path / f"decision-{resolution}.sqlite3", "needs_review")
    repaired = open_database(db.path)
    clock = _clock()
    timer = create_app(repaired, timer_clock=clock).state.timer
    review = timer.get().active_session
    key = str(uuid4())
    arguments = dict(expected_revision=review.revision, operation_id=key, discard_uncertain=True)
    result = timer.recover(active_id, resolution, **arguments)
    chosen = result.active_session if resolution == "resume" else result.last_session
    before_schema_reopen = _snapshot(repaired)
    _assert_preserved(open_database(db.path), before_schema_reopen)
    if resolution == "resume":
        assert chosen.state == "running"
        # Database reopening alone cannot reblock the current running session.
        assert timer.get().active_session.state == "running"
        chosen = timer.control(active_id, "pause", expected_revision=chosen.revision).active_session
    before_restart = _snapshot(repaired)
    for _ in range(2):
        clock.advance(60)
        reopened = open_database(db.path)
        fresh = create_app(reopened, timer_clock=clock).state.timer
        replay = fresh.recover(active_id, resolution, **arguments)
        actual = replay.active_session if resolution == "resume" else replay.last_session
        assert actual == chosen
        assert actual.state == ("paused" if resolution == "resume" else "finished")
        _assert_preserved(reopened, before_restart)
    with repaired.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timer_recovery_gaps WHERE resolved_at IS NULL").fetchone()[0] == 1
        canonical = conn.execute("SELECT * FROM timer_interruptions WHERE session_id = ?", (active_id,)).fetchall()
        assert len(canonical) == 1 and canonical[0]["resolution"] == resolution and canonical[0]["resolved_at"] is not None
        assert conn.execute("SELECT COUNT(*) FROM timer_interruptions WHERE resolved_at IS NULL").fetchone()[0] == 0
    _assert_integrity(repaired)


def test_valid_current_interruptions_forest_coins_and_purchases_survive_repair_and_repeated_launch(tmp_path: Path):
    migrations = load_migrations()
    db = Database(tmp_path / "healthy-current10.sqlite3")
    migrate(db, migrations[:10])
    config = RewardConfig(coins_per_minute=2, birch_price=1)
    clock = _clock()
    timer = TimerService(db, clock, reward_config=config)
    task = create_task(db, "Current enrolled work", notes="Retain all user fields", deadline="2026-11-02", estimate_minutes=23)
    first = timer.start(task.id, 2, str(uuid4())).active_session
    _observe(timer, clock, 65)
    clock.advance(20)
    review = timer.get().active_session
    timer.recover(first.id, "finish", expected_revision=review.revision, operation_id=str(uuid4()), discard_uncertain=True)
    shop = ShopService(db, config)
    purchase_key = str(uuid4())
    purchase = shop.purchase("birch", 1, purchase_key)
    second = timer.start(task.id, 1, str(uuid4()), species="birch").active_session
    complete = _observe(timer, clock, 60).last_session
    assert complete.id == second.id and complete.tree.outcome == "mature"
    forest, balance = list_forest(db), shop.get()
    streaks = get_streaks(db, now=clock.wall)
    assert len(forest) == 2 and len(balance.recent_entries) == 3 and balance.balance == 3
    before = _snapshot(db)
    assert before["timer_interruptions"]["rows"]
    assert before["coin_enrollments"]["rows"] and before["trees"]["rows"]
    for _ in range(3):
        reopened = open_database(db.path)
        fresh = create_app(reopened, timer_clock=clock, reward_config=config).state.timer
        assert fresh.get().last_session == complete
        assert list_forest(reopened) == forest
        assert ShopService(reopened, config).get() == balance
        assert ShopService(reopened, config).purchase("birch", 1, purchase_key) == purchase
        assert get_streaks(reopened, now=clock.wall) == streaks
        assert get_task(reopened, task.id) == task
        _assert_preserved(reopened, before)
    _assert_integrity(reopened)


def test_failed11_on_exact_legacy_variant_rolls_back_every_schema_and_row_change_then_retries(tmp_path: Path):
    db, _, _, _ = _legacy_ten(tmp_path / "legacy-failed-repair.sqlite3", "needs_review")
    before, schema_before = _snapshot(db), _schema_objects(db)
    migrations = load_migrations()
    repair = migrations[10]
    assert repair.version == 11 and repair.name == "repair_timer_interruptions"
    broken = Migration(11, repair.name, repair.sql + "\nINSERT INTO missing_repair_probe VALUES (1);")
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations[:10], broken])
    assert current_version(db) == 10
    assert _snapshot(db) == before and _schema_objects(db) == schema_before
    assert migrate(db) >= 11
    _assert_preserved(db, before)
    first_repair = _snapshot(db)
    assert migrate(db) >= 11
    _assert_preserved(db, first_repair)
    repaired = open_database(db.path)
    assert create_app(repaired, timer_clock=_clock()).state.timer.get().active_session.active_seconds == 7.25
    _assert_integrity(repaired)
