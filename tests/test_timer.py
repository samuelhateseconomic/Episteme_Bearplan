"""Countdown invariants with an injectable clock; no three-hour wall-time wait."""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from backend.domain.errors import InvalidInput
from backend.domain.planning import create_placement, move_placement
from backend.domain.projects import rename_project
from backend.domain.tasks import create_task, get_task, list_tasks, remove_subtask, update_task
from backend.domain.timer import ClockSample, TimerConflict, TimerService
from backend.storage.db import Database, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate


class FakeClock:
    def __init__(self, at: datetime | None = None) -> None:
        self.wall = at or datetime(2026, 10, 16, 20, 0, tzinfo=UTC)
        self.monotonic_ns = 0
        self.continuous_ns = 0

    def sample(self) -> ClockSample:
        return ClockSample(self.wall, self.monotonic_ns, self.continuous_ns)

    def advance(self, seconds: float, *, wall: float | None = None, continuous: float | None = None) -> None:
        self.wall += timedelta(seconds=seconds if wall is None else wall)
        self.monotonic_ns += round(seconds * 1_000_000_000)
        self.continuous_ns += round((seconds if continuous is None else continuous) * 1_000_000_000)


@pytest.fixture
def timer(db: Database) -> tuple[TimerService, FakeClock]:
    clock = FakeClock()
    return TimerService(db, clock), clock


def start(timer: TimerService, db: Database, minutes: int = 1):
    task = create_task(db, "Unscheduled work", deadline="2026-10-30", notes="Keep")
    session = timer.start(task.id, minutes, str(uuid4())).active_session
    assert session is not None
    return task, session


def observed(timer: TimerService, clock: FakeClock, seconds: float):
    """Advance a continuously observed awake service, never an uncertain gap."""
    remaining = seconds
    result = timer.get()
    while remaining > 0:
        step = min(4, remaining)
        clock.advance(step)
        result = timer.get()
        remaining -= step
    return result


def stored(db: Database):
    with db.read() as conn:
        return {
            table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            for table in ("timer_sessions", "timer_intervals", "timer_operations")
        }


@pytest.mark.parametrize("minutes", [1, 180])
def test_duration_endpoints_and_unscheduled_leaf(timer, db: Database, minutes: int):
    service, _ = timer
    task, session = start(service, db, minutes)
    assert session.state == "running" and session.active_seconds == 0
    assert session.requested_seconds == session.remaining_seconds == minutes * 60
    assert session.task_id == task.id
    assert get_task(db, task.id) == task
    assert session.deadline_at.endswith(".000000Z")


@pytest.mark.parametrize("minutes", [0, 181, -1, 1.5, True, "5", None])
def test_invalid_duration_never_writes(timer, db: Database, minutes):
    service, _ = timer
    task = create_task(db, "Work")
    before = stored(db)
    with pytest.raises(InvalidInput, match="1 to 180"):
        service.start(task.id, minutes, str(uuid4()))
    assert stored(db) == before


def test_missing_task_container_and_bad_operation_rejected(timer, db: Database):
    service, _ = timer
    parent = create_task(db, "Parent")
    child = create_task(db, "Leaf", parent_id=parent.id)
    for task_id in ("missing", parent.id):
        with pytest.raises(InvalidInput):
            service.start(task_id, 1, str(uuid4()))
    with pytest.raises(InvalidInput, match="UUID"):
        service.start(child.id, 1, "bad")
    assert not stored(db)["timer_sessions"]


def test_pause_resume_arithmetic_finish_and_completion_are_separate(timer, db: Database):
    service, clock = timer
    task, session = start(service, db)
    observed(service, clock, 12.125)
    paused = service.control(session.id, "pause", expected_revision=1).active_session
    assert paused.state == "paused" and paused.active_seconds == 12.125
    assert paused.remaining_seconds == 47.875 and paused.deadline_at is None
    clock.advance(400)
    assert service.get().active_session.active_seconds == 12.125
    running = service.control(session.id, "resume", expected_revision=paused.revision).active_session
    assert running.state == "running"
    observed(service, clock, 5.5)
    result = service.control(session.id, "finish", expected_revision=running.revision).last_session
    assert result.outcome == "finished_early" and result.active_seconds == 17.625
    assert result.remaining_seconds == 42.375 and result.finished_at is not None
    assert get_task(db, task.id) == task and not task.completed
    with db.read() as conn:
        intervals = conn.execute("SELECT * FROM timer_intervals ORDER BY rowid").fetchall()
        assert [row["active_microseconds"] for row in intervals] == [12_125_000, 5_500_000]
        assert all(row["ended_at"] == row["checkpoint_at"] for row in intervals)
        assert intervals[1]["started_at"] > intervals[0]["ended_at"]


@pytest.mark.parametrize("minutes", [1, 180])
def test_expiry_clips_duration_and_finishes_once_without_browser(timer, db: Database, minutes):
    service, clock = timer
    task, session = start(service, db, minutes)
    before_end = observed(service, clock, minutes * 60 - 0.25)
    assert before_end.active_session.remaining_seconds == 0.25
    clock.advance(3)
    finished = service.get()
    assert finished.active_session is None
    saved = finished.last_session
    assert saved.outcome == "completed" and saved.active_seconds == minutes * 60
    assert saved.remaining_seconds == 0
    expected_end = datetime(2026, 10, 16, 20, 0, tzinfo=UTC) + timedelta(minutes=minutes)
    assert saved.finished_at == expected_end.isoformat(timespec="microseconds").replace("+00:00", "Z")
    clock.advance(1000)
    assert service.get().last_session == saved
    assert service.control(session.id, "finish", expected_revision=1).last_session == saved
    assert get_task(db, task.id) == task
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timer_sessions").fetchone()[0] == 1
        assert conn.execute("SELECT SUM(active_microseconds) FROM timer_intervals").fetchone()[0] == minutes * 60_000_000


def test_operation_replays_and_stale_controls_do_not_affect_new_interval(timer, db: Database):
    service, clock = timer
    task = create_task(db, "Work")
    key = str(uuid4())
    session = service.start(task.id, 1, key).active_session
    assert service.start(task.id, 1, key).active_session.id == session.id
    with pytest.raises(TimerConflict, match="different work"):
        service.start(task.id, 2, key)
    pause_key = str(uuid4())
    paused = service.control(session.id, "pause", expected_revision=1, operation_id=pause_key).active_session
    assert service.control(session.id, "pause", expected_revision=1).active_session == paused
    resumed = service.control(session.id, "resume", expected_revision=paused.revision).active_session
    assert resumed.revision == 3
    # Retry of an acknowledged operation is a replay, never a second pause.
    assert service.control(session.id, "pause", expected_revision=1, operation_id=pause_key).active_session.state == "running"
    with pytest.raises(TimerConflict, match="another tab"):
        service.control(session.id, "pause", expected_revision=1)
    observed(service, clock, 1.25)
    assert service.get().active_session.revision == resumed.revision
    result = service.control(session.id, "finish").last_session
    assert service.start(task.id, 1, key).last_session == result
    # Same key cannot be reassigned even to a different control.
    with pytest.raises(TimerConflict, match="different work"):
        service.control(session.id, "finish", operation_id=pause_key)


def test_competing_starts_and_repeated_finishes_are_atomic(timer, db: Database):
    service, _ = timer
    task = create_task(db, "Work")
    barrier = threading.Barrier(2)

    def begin(_):
        barrier.wait()
        try:
            return service.start(task.id, 1, str(uuid4())).active_session
        except TimerConflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        starts = list(pool.map(begin, range(2)))
    assert sum(session is not None for session in starts) == 1
    session = next(session for session in starts if session)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: service.control(session.id, "finish").last_session, range(12)))
    assert all(result == results[0] for result in results)
    assert len(stored(db)["timer_sessions"]) == 1


def test_paused_and_review_sessions_occupy_one_active_allowance(timer, db: Database):
    service, clock = timer
    task, session = start(service, db)
    paused = service.control(session.id, "pause", expected_revision=1).active_session
    with pytest.raises(TimerConflict, match="already"):
        service.start(task.id, 1, str(uuid4()))
    service.control(session.id, "resume", expected_revision=paused.revision)
    clock.advance(10)
    with pytest.raises(TimerConflict, match="already"):
        service.start(task.id, 1, str(uuid4()))
    assert service.get().active_session.state == "needs_review"


@pytest.mark.parametrize("kind", ["gap", "sleep", "clock_forward", "clock_backward", "monotonic_backward"])
def test_uncertain_time_never_earns_credit(timer, db: Database, kind):
    service, clock = timer
    _, session = start(service, db)
    observed(service, clock, 3)
    if kind == "gap":
        clock.advance(20)
    elif kind == "sleep":
        clock.advance(1, wall=30, continuous=30)
    elif kind == "clock_forward":
        clock.advance(1, wall=301)
    elif kind == "clock_backward":
        clock.advance(1, wall=-299)
    else:
        clock.advance(-1)
    review = service.get().active_session
    assert review.state == "needs_review" and review.active_seconds == 3
    assert review.review_reason and review.deadline_at is None
    with pytest.raises(TimerConflict, match="explicitly"):
        service.control(session.id, "finish")
    result = service.control(session.id, "finish", discard_uncertain=True).last_session
    assert result.outcome == "interrupted" and result.active_seconds == 3
    assert result.review_reason == review.review_reason


@pytest.mark.parametrize("state", ["running", "paused"])
def test_restart_uses_checkpoint_and_requires_explicit_review(timer, db: Database, state):
    service, clock = timer
    _, session = start(service, db)
    observed(service, clock, 2.5)
    if state == "paused":
        service.control(session.id, "pause", expected_revision=1)
    clock.advance(3600)
    reopened = TimerService(open_database(db.path), FakeClock(clock.wall))
    review = reopened.get().active_session
    assert review.state == "needs_review" and review.active_seconds == 2.5
    assert review.checkpoint_at == "2026-10-16T20:00:02.500000Z"
    result = reopened.control(session.id, "finish", discard_uncertain=True).last_session
    assert result.active_seconds == 2.5 and result.outcome == "interrupted"
    assert TimerService(open_database(db.path), clock).get().last_session == result


def test_moving_editing_and_removed_subtasks_cannot_move_history(timer, db: Database):
    service, clock = timer
    parent = create_task(db, "Parent")
    child = create_task(db, "Original leaf", parent_id=parent.id, deadline="2026-10-30")
    placement = create_placement(db, child.id, "2026-10-16")
    session = service.start(child.id, 1, str(uuid4())).active_session
    observed(service, clock, 2)
    saved = service.control(session.id, "finish").last_session
    before = stored(db)
    move_placement(db, placement.id, "2026-11-06")
    update_task(db, child.id, title="Edited leaf", deadline="2027-01-01")
    rename_project(db, child.project_id, "Edited project")
    assert stored(db) == before and service.get().last_session == saved
    assert saved.task_id == child.id and saved.task_title == "Original leaf"
    from backend.domain.planning import remove_placement
    remove_placement(db, placement.id)
    remove_subtask(db, child.id)
    assert stored(db) == before and service.get().last_session == saved


def test_active_task_structure_is_guarded_but_normal_edits_continue(timer, db: Database):
    service, _ = timer
    task, session = start(service, db)
    with pytest.raises(InvalidInput, match="unfinished countdown"):
        create_task(db, "New child", parent_id=task.id)
    update_task(db, task.id, notes="Edit during tracking")
    assert service.get().active_session.id == session.id
    service.control(session.id, "finish")
    child = create_task(db, "Child", parent_id=task.id)
    current = service.start(child.id, 1, str(uuid4())).active_session
    with pytest.raises(InvalidInput, match="unfinished countdown"):
        remove_subtask(db, child.id)
    service.control(current.id, "finish")
    remove_subtask(db, child.id)


def test_failed_start_and_finish_roll_back_and_retry(timer, db: Database, monkeypatch):
    service, clock = timer
    task = create_task(db, "Work")
    key = str(uuid4())
    receipt = service._receipt

    def fail_receipt(*args):
        receipt(*args)
        raise sqlite3.OperationalError("injected failure after receipt")

    with monkeypatch.context() as patch:
        patch.setattr(service, "_receipt", fail_receipt)
        with pytest.raises(sqlite3.OperationalError):
            service.start(task.id, 1, key)
    assert all(not rows for rows in stored(db).values())
    session = service.start(task.id, 1, key).active_session
    observed(service, clock, 2)
    before = stored(db)
    finish_key = str(uuid4())
    with monkeypatch.context() as patch:
        patch.setattr(service, "_receipt", fail_receipt)
        with pytest.raises(sqlite3.OperationalError):
            service.control(session.id, "finish", operation_id=finish_key)
    assert stored(db) == before
    clock.advance(1)
    result = service.control(session.id, "finish", operation_id=finish_key).last_session
    assert result.active_seconds == 3
    assert service.control(session.id, "finish", operation_id=finish_key).last_session == result


def test_sql_unique_constraint_is_final_active_barrier(timer, db: Database):
    service, _ = timer
    _, _ = start(service, db)
    with pytest.raises(sqlite3.IntegrityError):
        with db.write() as conn:
            conn.execute(
                "INSERT INTO timer_sessions SELECT ?, ?, task_id, task_title, project_id, project_name, parent_title,"
                " duration_minutes, state, active_microseconds, started_at, checkpoint_at, finished_at, outcome,"
                " review_reason, revision FROM timer_sessions LIMIT 1", (str(uuid4()), str(uuid4())),
            )


@pytest.mark.parametrize("case", ["small_backward", "clipped_expiry", "paused_backward"])
def test_wall_clock_cannot_reverse_interval_endpoints(timer, db: Database, case):
    service, clock = timer
    _, session = start(service, db)
    if case == "small_backward":
        clock.advance(0.5, wall=-0.5)
    elif case == "clipped_expiry":
        observed(service, clock, 59.75)
        clock.advance(1, wall=0.1)
    else:
        observed(service, clock, 2)
        service.control(session.id, "pause", expected_revision=1)
        clock.advance(1, wall=-0.5)
    before = stored(db)["timer_intervals"]
    review = service.get().active_session
    assert review.state == "needs_review"
    with db.read() as conn:
        for row in conn.execute("SELECT * FROM timer_intervals"):
            assert row["checkpoint_at"] >= row["started_at"]
    after = stored(db)["timer_intervals"]
    # Review may close the interval at its existing checkpoint; it cannot add time.
    assert [row[-1] for row in before] == [row[-1] for row in after]


def test_v5_upgrade_preserves_all_existing_rows_and_failed_upgrade_retries(tmp_path: Path):
    db = Database(tmp_path / "v5.sqlite3")
    migrations = load_migrations()
    migrate(db, migrations[:5])
    parent = create_task(db, "Parent", deadline="2026-10-30")
    child = create_task(db, "Child", parent_id=parent.id, notes="Preserve")
    create_placement(db, child.id, "2026-10-16")
    from backend.domain.weeks import close_week, preview_close
    close_week(db, "2026-10-12", preview_close(db, "2026-10-12").preview_token)

    def legacy():
        with db.read() as conn:
            names = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'") if row[0] != "schema_migrations"]
            return {name: [tuple(row) for row in conn.execute(f"SELECT * FROM {name}")] for name in names if not name.startswith("timer_")}

    before = legacy()
    broken = Migration(6, migrations[5].name, migrations[5].sql + "\nINSERT INTO missing_table VALUES (1);")
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations[:5], broken])
    assert current_version(db) == 5 and legacy() == before
    with db.read() as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'timer_sessions'").fetchone() is None
    migrate(db)
    assert current_version(db) == 6 and legacy() == before
    reopened = open_database(db.path)
    assert list_tasks(reopened) == list_tasks(db)
    with reopened.read() as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
