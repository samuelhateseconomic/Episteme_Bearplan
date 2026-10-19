"""Recovery contracts with disposable databases and independently controlled clocks.

These deterministic scenarios verify interval accounting. They do not stand in
for the target Mac's physical sleep/wake or long-session acceptance evidence.
"""

from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from backend.domain.errors import InvalidInput
from backend.domain.planning import create_placement
from backend.domain.tasks import create_task, get_task
from backend.domain.timer import ClockSample, TimerConflict, TimerService
from backend.domain.weeks import close_week, preview_close
from backend.storage.db import Database, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate


class RecoveryClock:
    def __init__(self, at: datetime | None = None) -> None:
        self.wall = at or datetime(2026, 10, 18, 20, 0, tzinfo=UTC)
        self.monotonic_ns = 0
        self.continuous_ns = 0

    def sample(self) -> ClockSample:
        return ClockSample(self.wall, self.monotonic_ns, self.continuous_ns)

    def advance(self, seconds: float, *, wall: float | None = None, continuous: float | None = None) -> None:
        self.wall += timedelta(seconds=seconds if wall is None else wall)
        self.monotonic_ns += round(seconds * 1_000_000_000)
        self.continuous_ns += round((seconds if continuous is None else continuous) * 1_000_000_000)


def _at(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _start(db: Database, *, at: datetime | None = None, minutes: int = 2):
    clock = RecoveryClock(at)
    timer = TimerService(db, clock)
    task = create_task(db, "Recovery work", notes="Preserve this task", deadline="2026-11-02")
    session = timer.start(task.id, minutes, str(uuid4())).active_session
    assert session is not None
    return timer, clock, task, session


def _observe(timer: TimerService, clock: RecoveryClock, seconds: float):
    remaining = seconds
    result = timer.get()
    while remaining > 0:
        step = min(4.0, remaining)
        clock.advance(step)
        result = timer.get()
        remaining -= step
    return result


def _rows(db: Database, *tables: str) -> dict[str, list[tuple]]:
    with db.read() as conn:
        return {
            table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY rowid")]
            for table in tables
        }


def _timer_rows(db: Database) -> dict[str, list[tuple]]:
    return _rows(db, "timer_sessions", "timer_intervals", "timer_operations", "timer_interruptions")


def _review_after_restart(db: Database):
    original, clock, task, session = _start(db)
    _observe(original, clock, 7.25)
    checkpoint = original.get().active_session.checkpoint_at
    clock.advance(3600)
    restarted_clock = RecoveryClock(clock.wall)
    restarted = TimerService(open_database(db.path), restarted_clock)
    review = restarted.get().active_session
    assert review is not None and review.state == "needs_review"
    return restarted, restarted_clock, task, session, review, checkpoint


def test_running_restart_preserves_confirmed_checkpoint_and_one_durable_review(db: Database):
    timer, clock, task, session, review, checkpoint = _review_after_restart(db)
    event = review.recovery
    assert review.id == session.id and review.active_seconds == 7.25
    assert review.remaining_seconds == 112.75 and review.deadline_at is None
    assert review.checkpoint_at == checkpoint
    assert event is not None and event.kind == "service_restart"
    assert event.reason and event.id and event.checkpoint_at == checkpoint
    assert event.detected_at == _at(clock.wall)
    assert event.confirmed_active_seconds == 7.25
    assert event.measured_sleep_seconds is None
    assert event.resolved_at is None and event.resolution is None
    assert get_task(db, task.id) == task
    before = _timer_rows(db)
    clock.advance(60)
    reopened = TimerService(open_database(db.path), RecoveryClock(clock.wall))
    assert reopened.get().active_session == review
    assert _timer_rows(db) == before
    with db.read() as conn:
        interval = conn.execute("SELECT * FROM timer_intervals").fetchone()
        assert interval["ended_at"] == interval["checkpoint_at"] == checkpoint
        assert interval["active_microseconds"] == 7_250_000


def test_review_resume_uses_same_session_new_interval_and_excludes_all_offline_time(db: Database):
    timer, clock, task, session, review, checkpoint = _review_after_restart(db)
    clock.advance(90)
    resumed_at = _at(clock.wall)
    resumed = timer.recover(
        session.id, "resume", expected_revision=review.revision,
        operation_id=str(uuid4()), discard_uncertain=True,
    ).active_session
    assert resumed is not None and resumed.id == session.id and resumed.state == "running"
    assert resumed.revision == review.revision + 1
    assert resumed.active_seconds == 7.25 and resumed.remaining_seconds == 112.75
    assert resumed.checkpoint_at == resumed_at
    assert resumed.recovery.id == review.recovery.id
    assert resumed.recovery.resolved_at == resumed_at and resumed.recovery.resolution == "resume"
    assert resumed.recovery.confirmed_active_seconds == 7.25
    _observe(timer, clock, 5.5)
    saved = timer.control(session.id, "finish").last_session
    assert saved is not None and saved.active_seconds == 12.75
    assert get_task(db, task.id) == task
    with db.read() as conn:
        intervals = conn.execute("SELECT * FROM timer_intervals ORDER BY rowid").fetchall()
        assert len(intervals) == 2
        assert intervals[0]["ended_at"] == checkpoint
        assert intervals[1]["started_at"] == resumed_at
        assert [row["active_microseconds"] for row in intervals] == [7_250_000, 5_500_000]


def test_review_finish_saves_interrupted_once_and_persists_after_reopening(db: Database):
    timer, clock, task, session, review, _ = _review_after_restart(db)
    key = str(uuid4())
    saved = timer.recover(
        session.id, "finish", expected_revision=review.revision,
        operation_id=key, discard_uncertain=True,
    ).last_session
    assert saved is not None and saved.id == session.id and saved.state == "finished"
    assert saved.outcome == "interrupted" and saved.active_seconds == 7.25
    assert saved.remaining_seconds == 112.75 and saved.recovery.resolution == "finish"
    before = _timer_rows(db)
    clock.advance(500)
    reopened = TimerService(open_database(db.path), clock)
    retry = reopened.recover(
        session.id, "finish", expected_revision=review.revision,
        operation_id=key, discard_uncertain=True,
    )
    assert retry.active_session is None and retry.last_session == saved
    assert _timer_rows(db) == before
    assert get_task(db, task.id) == task


@pytest.mark.parametrize("resolution", ["resume", "finish"])
@pytest.mark.parametrize("ack", [False, None, 1, "true"])
def test_review_requires_explicit_boolean_acknowledgment(db: Database, resolution, ack):
    timer, _, _, session, review, _ = _review_after_restart(db)
    before = _timer_rows(db)
    with pytest.raises(InvalidInput):
        timer.recover(
            session.id, resolution, expected_revision=review.revision,
            operation_id=str(uuid4()), discard_uncertain=ack,
        )
    assert _timer_rows(db) == before


@pytest.mark.parametrize("revision", [None, True, 0, -1, 1.5, "2"])
def test_recovery_requires_valid_revision_without_partial_writes(db: Database, revision):
    timer, _, _, session, _, _ = _review_after_restart(db)
    before = _timer_rows(db)
    with pytest.raises(InvalidInput):
        timer.recover(
            session.id, "resume", expected_revision=revision,
            operation_id=str(uuid4()), discard_uncertain=True,
        )
    assert _timer_rows(db) == before


@pytest.mark.parametrize("key", [None, "bad", 42])
def test_recovery_requires_persistent_request_uuid(db: Database, key):
    timer, _, _, session, review, _ = _review_after_restart(db)
    before = _timer_rows(db)
    with pytest.raises(InvalidInput):
        timer.recover(
            session.id, "resume", expected_revision=review.revision,
            operation_id=key, discard_uncertain=True,
        )
    assert _timer_rows(db) == before


def test_recovery_rejects_stale_revision_and_reused_key_for_different_resolution(db: Database):
    timer, _, _, session, review, _ = _review_after_restart(db)
    before = _timer_rows(db)
    with pytest.raises(TimerConflict):
        timer.recover(
            session.id, "resume", expected_revision=review.revision - 1,
            operation_id=str(uuid4()), discard_uncertain=True,
        )
    assert _timer_rows(db) == before
    key = str(uuid4())
    timer.recover(
        session.id, "resume", expected_revision=review.revision,
        operation_id=key, discard_uncertain=True,
    )
    before = _timer_rows(db)
    with pytest.raises(TimerConflict, match="different work"):
        timer.recover(
            session.id, "finish", expected_revision=review.revision,
            operation_id=key, discard_uncertain=True,
        )
    assert _timer_rows(db) == before


@pytest.mark.parametrize("later_kind", ["checkpoint_gap", "clock_change"])
def test_replayed_recovery_cannot_resume_a_newer_pause_or_resolve_a_later_interruption(db: Database, later_kind):
    timer, clock, _, session, review, _ = _review_after_restart(db)
    key = str(uuid4())

    def retry():
        return timer.recover(
            session.id, "resume", expected_revision=review.revision,
            operation_id=key, discard_uncertain=True,
        )

    resumed = retry().active_session
    _observe(timer, clock, 2)
    paused = timer.control(session.id, "pause", expected_revision=resumed.revision).active_session
    before = _timer_rows(db)
    assert retry().active_session == paused
    assert _timer_rows(db) == before
    running = timer.control(session.id, "resume", expected_revision=paused.revision).active_session
    if later_kind == "checkpoint_gap":
        clock.advance(20)
    else:
        clock.advance(1, wall=-3599)
    later = timer.get().active_session
    assert later.state == "needs_review" and later.recovery.id != review.recovery.id
    assert later.recovery.kind == later_kind
    assert later.revision > running.revision
    before = _timer_rows(db)
    assert retry().active_session == later
    assert _timer_rows(db) == before
    assert later.recovery.resolved_at is None


def test_conflicting_tabs_cannot_both_resolve_the_same_interruption(db: Database):
    timer, _, _, session, review, _ = _review_after_restart(db)
    barrier = threading.Barrier(2)

    def recover(resolution):
        barrier.wait()
        try:
            result = timer.recover(
                session.id, resolution, expected_revision=review.revision,
                operation_id=str(uuid4()), discard_uncertain=True,
            )
            return resolution, result
        except TimerConflict:
            return resolution, None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(recover, ("resume", "finish")))
    accepted = [(resolution, result) for resolution, result in results if result is not None]
    assert len(accepted) == 1
    resolution, result = accepted[0]
    current = result.active_session if resolution == "resume" else result.last_session
    assert current.active_seconds == 7.25 and current.revision == review.revision + 1
    assert current.recovery.resolution == resolution
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timer_operations").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM timer_interruptions").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM timer_intervals").fetchone()[0] == (2 if resolution == "resume" else 1)


def test_retrying_old_recovery_cannot_change_a_new_active_session(db: Database):
    timer, _, task, session, review, _ = _review_after_restart(db)
    key = str(uuid4())

    def retry():
        return timer.recover(
            session.id, "finish", expected_revision=review.revision,
            operation_id=key, discard_uncertain=True,
        )

    saved = retry().last_session
    newer = timer.start(task.id, 1, str(uuid4())).active_session
    assert newer.id != session.id
    before = _timer_rows(db)
    replayed = retry()
    assert replayed.active_session == newer and replayed.last_session == saved
    assert _timer_rows(db) == before


@pytest.mark.parametrize("resolution", ["resume", "finish"])
def test_receipt_failure_rolls_back_recovery_event_session_and_interval(db: Database, monkeypatch, resolution):
    timer, clock, _, session, review, _ = _review_after_restart(db)
    before = _timer_rows(db)
    key = str(uuid4())
    receipt = timer._receipt

    def fail_after_receipt(*args):
        receipt(*args)
        raise sqlite3.OperationalError("injected recovery receipt failure")

    with monkeypatch.context() as patch:
        patch.setattr(timer, "_receipt", fail_after_receipt)
        with pytest.raises(sqlite3.OperationalError, match="injected recovery"):
            timer.recover(
                session.id, resolution, expected_revision=review.revision,
                operation_id=key, discard_uncertain=True,
            )
    assert _timer_rows(db) == before
    assert timer.get().active_session == review
    clock.advance(10)
    result = timer.recover(
        session.id, resolution, expected_revision=review.revision,
        operation_id=key, discard_uncertain=True,
    )
    recovered = result.active_session if resolution == "resume" else result.last_session
    assert recovered is not None and recovered.active_seconds == 7.25
    assert recovered.recovery.resolution == resolution
    if resolution == "resume":
        assert _observe(timer, clock, 1.5).active_session.active_seconds == 8.75


@pytest.mark.parametrize("wall_shift", [-3600, 3600])
def test_paused_restart_and_wall_adjustment_remain_paused_without_credit(db: Database, wall_shift):
    timer, clock, _, session = _start(db)
    _observe(timer, clock, 3.75)
    paused = timer.control(session.id, "pause", expected_revision=session.revision).active_session
    clock.advance(100, wall=wall_shift)
    reopened = TimerService(open_database(db.path), RecoveryClock(clock.wall))
    current = reopened.get().active_session
    assert current == paused and current.active_seconds == 3.75
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timer_interruptions").fetchone()[0] == 0
    resumed = reopened.control(session.id, "resume", expected_revision=current.revision).active_session
    assert resumed.state == "running" and resumed.active_seconds == 3.75


@pytest.mark.parametrize("wall_shift", [-299, 301])
def test_running_wall_adjustment_requires_review_and_keeps_last_checkpoint(db: Database, wall_shift):
    timer, clock, _, session = _start(db)
    checkpoint = _observe(timer, clock, 4.5).active_session.checkpoint_at
    clock.advance(1, wall=wall_shift)
    review = timer.get().active_session
    assert review.state == "needs_review" and review.active_seconds == 4.5
    assert review.checkpoint_at == checkpoint
    assert review.recovery.kind == "clock_change"
    assert review.recovery.checkpoint_at == checkpoint
    assert review.recovery.measured_sleep_seconds is None
    assert timer.get().active_session == review
    recovered = timer.recover(
        session.id, "resume", expected_revision=review.revision,
        operation_id=str(uuid4()), discard_uncertain=True,
    ).active_session
    assert recovered.active_seconds == 4.5
    assert _observe(timer, clock, 2).active_session.active_seconds == 6.5
    with db.read() as conn:
        for row in conn.execute("SELECT started_at, checkpoint_at, ended_at FROM timer_intervals"):
            assert row["checkpoint_at"] >= row["started_at"]
            assert row["ended_at"] is None or row["ended_at"] >= row["started_at"]


def test_multiple_sleep_and_darkwake_gaps_remain_paused_until_explicit_resume(db: Database):
    timer, clock, _, session = _start(db)
    event_ids = []
    for cycle in range(3):
        before_sleep = _observe(timer, clock, 2).active_session
        clock.advance(1, wall=31, continuous=31)
        paused = timer.get().active_session
        assert paused.state == "paused" and paused.active_seconds == (cycle + 1) * 2
        assert paused.checkpoint_at == before_sleep.checkpoint_at
        event = paused.recovery
        assert event.kind == "sleep" and event.measured_sleep_seconds == 30
        assert event.confirmed_active_seconds == paused.active_seconds
        assert event.resolved_at is None and event.resolution is None
        event_ids.append(event.id)
        before = _timer_rows(db)
        # DarkWake/polling does not distinguish user intent or restart credit.
        for _ in range(3):
            clock.advance(1, wall=90, continuous=90)
            assert timer.get().active_session == paused
        assert _timer_rows(db) == before
        if cycle < 2:
            resumed = timer.control(session.id, "resume", expected_revision=paused.revision).active_session
            assert resumed.state == "running" and resumed.active_seconds == paused.active_seconds
            assert resumed.recovery.id == event.id and resumed.recovery.resolution == "resume"
        else:
            saved = timer.control(session.id, "finish", expected_revision=paused.revision).last_session
            assert saved.active_seconds == 6 and saved.recovery.resolution == "finish"
    assert len(set(event_ids)) == 3
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timer_interruptions").fetchone()[0] == 3
        assert conn.execute("SELECT SUM(active_microseconds) FROM timer_intervals").fetchone()[0] == 6_000_000


@pytest.mark.parametrize(
    ("start", "end_hour"),
    [
        (datetime(2026, 10, 18, 23, 59, 58, tzinfo=UTC), None),
        (datetime(2026, 10, 19, 6, 59, 58, tzinfo=UTC), None),
        (datetime(2026, 3, 8, 9, 59, 58, tzinfo=UTC), 3),
        (datetime(2026, 11, 1, 8, 59, 58, tzinfo=UTC), 1),
    ],
)
def test_midnight_and_dst_calendar_boundaries_preserve_monotonic_credit(db: Database, start, end_hour):
    timer, clock, task, session = _start(db, at=start)
    before_local = clock.wall.astimezone(ZoneInfo("America/Los_Angeles"))
    current = _observe(timer, clock, 4).active_session
    assert current.id == session.id and current.state == "running"
    assert current.active_seconds == 4 and current.remaining_seconds == 116
    assert current.recovery is None
    assert current.checkpoint_at == _at(start + timedelta(seconds=4))
    assert get_task(db, task.id) == task
    if end_hour is not None:
        after_local = clock.wall.astimezone(ZoneInfo("America/Los_Angeles"))
        assert after_local.hour == end_hour
        assert before_local.utcoffset() != after_local.utcoffset()
    else:
        assert start.date() != clock.wall.date() or before_local.date() != clock.wall.astimezone(
            ZoneInfo("America/Los_Angeles")
        ).date()


def test_ten_minute_synthetic_continuous_session_matches_independent_elapsed_and_expires_once(db: Database):
    timer, clock, _, session = _start(db, minutes=10)
    reference_start_ns = clock.monotonic_ns
    result = _observe(timer, clock, 599.75)
    assert result.active_session.remaining_seconds == 0.25
    clock.advance(0.25)
    saved = timer.get().last_session
    reference_seconds = (clock.monotonic_ns - reference_start_ns) / 1_000_000_000
    assert saved.id == session.id and saved.outcome == "completed"
    assert saved.active_seconds == reference_seconds == 600
    assert saved.recovery is None
    before = _timer_rows(db)
    clock.advance(20)
    assert timer.get().last_session == saved
    assert _timer_rows(db) == before


def _schema_seven_with_history(path: Path) -> Database:
    """Construct pre-recovery records without invoking newer timer functions."""
    db = Database(path)
    migrate(db, load_migrations()[:7])
    task = create_task(db, "Original task", notes="Keep every field", deadline="2026-11-02")
    create_placement(db, task.id, "2026-10-15")
    close_week(db, "2026-10-12", preview_close(db, "2026-10-12").preview_token)
    create_placement(db, task.id, "2026-10-22")
    at = "2026-10-18T20:00:00.000000Z"
    checkpoint = "2026-10-18T20:00:04.250000Z"
    with db.write() as conn:
        for state in ("finished", "running"):
            session_id, operation_id = str(uuid4()), str(uuid4())
            conn.execute(
                "INSERT INTO timer_sessions (id, start_operation_id, task_id, task_title, project_id, project_name,"
                " duration_minutes, state, active_microseconds, started_at, checkpoint_at, finished_at, outcome, revision)"
                " VALUES (?, ?, ?, ?, ?, 'Original project', 25, ?, 4250000, ?, ?, ?, ?, 7)",
                (session_id, operation_id, task.id, task.title, task.project_id, state, at, checkpoint,
                 checkpoint if state == "finished" else None, "finished_early" if state == "finished" else None),
            )
            conn.execute(
                "INSERT INTO timer_intervals (id, session_id, started_at, checkpoint_at, ended_at, active_microseconds)"
                " VALUES (?, ?, ?, ?, ?, 4250000)",
                (str(uuid4()), session_id, at, checkpoint, checkpoint if state == "finished" else None),
            )
            conn.execute("INSERT INTO timer_operations VALUES (?, ?, 'start', ?)",
                         (operation_id, session_id, '{"legacy":"unchanged"}'))
    return db


def _all_rows(db: Database) -> dict[str, list[tuple]]:
    with db.read() as conn:
        tables = [row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
    return _rows(db, *tables)


def test_schema_seven_upgrade_preserves_original_history_and_retries_after_atomic_failure(tmp_path: Path):
    db = _schema_seven_with_history(tmp_path / "recovery-upgrade.sqlite3")
    before = _all_rows(db)
    migrations = load_migrations()
    recovery = migrations[7]
    assert recovery.version == 8
    broken = Migration(recovery.version, recovery.name, recovery.sql + "\nINSERT INTO missing_recovery_table VALUES (1);")
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations[:7], broken])
    assert current_version(db) == 7 and _all_rows(db) == before
    migrate(db)
    assert current_version(db) == 8
    after = _all_rows(db)
    for table, rows in before.items():
        if table == "schema_migrations":
            assert after[table][:7] == rows
        else:
            assert after[table] == rows
    assert after["timer_interruptions"] == []
    reopened = open_database(db.path)
    assert _all_rows(reopened) == after
    with reopened.read() as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    timer = TimerService(reopened, RecoveryClock(datetime(2026, 10, 18, 21, 0, tzinfo=UTC)))
    review = timer.get().active_session
    assert review.state == "needs_review" and review.active_seconds == 4.25
    assert review.recovery.kind == "service_restart"


def test_legacy_needs_review_gains_one_event_and_remains_resumable_after_upgrade(tmp_path: Path):
    db = _schema_seven_with_history(tmp_path / "legacy-review.sqlite3")
    with db.write() as conn:
        conn.execute(
            "UPDATE timer_sessions SET state = 'needs_review', review_reason = 'Legacy uncertain checkpoint'"
            " WHERE state = 'running'"
        )
        conn.execute("UPDATE timer_intervals SET ended_at = checkpoint_at WHERE ended_at IS NULL")
    migrate(db)
    clock = RecoveryClock(datetime(2026, 10, 18, 21, 0, tzinfo=UTC))
    timer = TimerService(db, clock)
    review = timer.get().active_session
    assert review.state == "needs_review" and review.active_seconds == 4.25
    assert review.recovery.kind == "checkpoint_gap"
    assert review.recovery.reason == review.review_reason == "Legacy uncertain checkpoint"
    before = _timer_rows(db)
    reopened = TimerService(open_database(db.path), clock)
    assert reopened.get().active_session == review and _timer_rows(db) == before
    resumed = reopened.recover(
        review.id, "resume", expected_revision=review.revision,
        operation_id=str(uuid4()), discard_uncertain=True,
    ).active_session
    assert resumed.id == review.id and resumed.state == "running" and resumed.active_seconds == 4.25
