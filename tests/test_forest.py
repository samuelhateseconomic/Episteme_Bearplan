"""Forest outcomes follow confirmed session credit, using disposable clocks/data.

Recovery observations here are simulated and do not certify Mac power behavior.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import threading
from uuid import uuid4

import pytest

from backend.domain.forest import list_forest
from backend.domain.planning import create_placement, move_placement
from backend.domain.projects import create_project, rename_project
from backend.domain.tasks import create_task, get_task, remove_subtask, set_task_completion, update_task
from backend.domain.timer import TimerService
from backend.storage.db import Database, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate
from tests.test_timer import FakeClock, observed
from tests.test_timer_recovery import _schema_seven_with_history


def setup_tree(db):
    clock = FakeClock()
    timer = TimerService(db, clock)
    task = create_task(db, "Forest work", deadline="2026-11-04", notes="Keep these fields")
    session = timer.start(task.id, 1, str(uuid4())).active_session
    return timer, clock, task, session


def all_rows(db):
    with db.read() as conn:
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        return {name: [tuple(r) for r in conn.execute(f"SELECT * FROM {name} ORDER BY rowid")] for name in names}


def test_growth_uses_confirmed_time_and_matures_only_at_finalized_full_duration(db):
    timer, clock, task, session = setup_tree(db)
    tree = session.tree
    assert tree.species == "pine" and tree.stage == "seedling"
    assert tree.progress == 0 and tree.outcome is None
    assert list_forest(db) == []
    before_half = observed(timer, clock, 29.999999).active_session
    assert before_half.tree.id == tree.id and before_half.tree.stage == "seedling"
    half = observed(timer, clock, 0.000001).active_session
    assert half.tree.stage == "sapling" and half.tree.progress == 0.5
    almost = observed(timer, clock, 29.999999).active_session
    assert almost.tree.stage == "sapling" and almost.tree.outcome is None
    assert almost.tree.progress < 1 and list_forest(db) == []
    saved = observed(timer, clock, 0.000001).last_session
    assert saved.tree.id == tree.id and saved.tree.stage == "mature"
    assert saved.tree.progress == 1 and saved.tree.outcome == "mature"
    assert saved.state == "finished" and saved.outcome == "completed" and saved.active_seconds == 60
    forest = list_forest(db)
    assert len(forest) == 1 and forest[0].id == tree.id and forest[0].session_id == session.id
    assert forest[0].task_title == task.title and forest[0].active_seconds == 60
    assert forest[0].started_at == session.started_at and forest[0].finished_at == saved.finished_at
    assert forest[0].duration_minutes == 1
    assert get_task(db, task.id) == task


def test_pause_and_paused_restart_preserve_growth_then_resume_same_tree(db):
    timer, clock, _, session = setup_tree(db)
    observed(timer, clock, 32)
    paused = timer.control(session.id, "pause", expected_revision=session.revision).active_session
    assert paused.tree.stage == "sapling" and paused.tree.progress == 32 / 60
    clock.advance(500)
    assert timer.get().active_session.tree == paused.tree
    reopened = TimerService(open_database(db.path), clock)
    current = reopened.get().active_session
    assert current.tree == paused.tree and current.state == "paused"
    resumed = reopened.control(session.id, "resume", expected_revision=current.revision).active_session
    assert resumed.tree == paused.tree
    saved = observed(reopened, clock, 28).last_session
    assert saved.tree.id == session.tree.id and saved.tree.outcome == "mature"
    assert len(list_forest(db)) == 1


@pytest.mark.parametrize("seconds,stage", [(0, "seedling"), (12.5, "seedling"), (59.999, "sapling")])
def test_early_finish_keeps_time_and_one_unfinished_tree(db, seconds, stage):
    timer, clock, task, session = setup_tree(db)
    current = observed(timer, clock, seconds).active_session
    saved = timer.control(session.id, "finish", expected_revision=current.revision).last_session
    assert saved.active_seconds == seconds and saved.outcome == "finished_early"
    assert saved.tree.id == session.tree.id and saved.tree.outcome == "unfinished"
    assert saved.tree.stage == stage and saved.tree.progress == seconds / 60
    forest = list_forest(db)
    assert len(forest) == 1 and forest[0].outcome == "unfinished"
    assert get_task(db, task.id) == task
    clock.advance(600)
    assert timer.get().last_session == saved
    assert list_forest(open_database(db.path)) == forest


@pytest.mark.parametrize("resolution", ["resume", "finish"])
def test_review_freezes_tree_and_recovery_preserves_identity_excluding_gap(db, resolution):
    timer, clock, task, session = setup_tree(db)
    confirmed = observed(timer, clock, 35).active_session
    clock.advance(1000)
    review = timer.get().active_session
    assert review.state == "needs_review" and review.tree == confirmed.tree
    assert review.active_seconds == 35 and review.tree.outcome is None
    clock.advance(1000)
    assert timer.get().active_session.tree == confirmed.tree and list_forest(db) == []
    key = str(uuid4())
    result = timer.recover(session.id, resolution, expected_revision=review.revision,
                           operation_id=key, discard_uncertain=True)
    current = result.active_session if resolution == "resume" else result.last_session
    assert current.tree.id == session.tree.id and current.active_seconds == 35
    assert current.tree.progress == 35 / 60
    if resolution == "resume":
        assert current.tree.outcome is None
        current = observed(timer, clock, 25).last_session
        assert current.tree.outcome == "mature" and current.active_seconds == 60
    else:
        assert current.tree.outcome == "unfinished" and current.outcome == "interrupted"
    before = all_rows(db)
    timer.recover(session.id, resolution, expected_revision=review.revision,
                  operation_id=key, discard_uncertain=True)
    assert all_rows(db) == before
    assert get_task(db, task.id) == task and len(list_forest(db)) == 1


def test_running_restart_cannot_mature_tree_or_credit_missing_time(db):
    timer, clock, _, session = setup_tree(db)
    current = observed(timer, clock, 58).active_session
    clock.advance(100)
    reopened = TimerService(open_database(db.path), FakeClock(clock.wall))
    review = reopened.get().active_session
    assert review.state == "needs_review" and review.tree == current.tree
    saved = reopened.recover(session.id, "finish", expected_revision=review.revision,
                             operation_id=str(uuid4()), discard_uncertain=True).last_session
    assert saved.tree.outcome == "unfinished" and saved.active_seconds == 58
    assert list_forest(db)[0].stage == "sapling"


def test_measured_sleep_freezes_growth_across_maintenance_wakes(db):
    timer, clock, _, session = setup_tree(db)
    confirmed = observed(timer, clock, 15).active_session
    clock.advance(1, wall=301, continuous=301)
    paused = timer.get().active_session
    assert paused.state == "paused" and paused.tree == confirmed.tree
    for _ in range(3):
        clock.advance(1, wall=61, continuous=61)
        assert timer.get().active_session.tree == paused.tree
    resumed = timer.control(session.id, "resume", expected_revision=paused.revision).active_session
    assert resumed.tree == paused.tree
    assert observed(timer, clock, 45).last_session.tree.outcome == "mature"


def test_concurrent_and_repeated_finalization_have_one_storage_enforced_outcome(db):
    timer, clock, _, session = setup_tree(db)
    observed(timer, clock, 10)
    barrier = threading.Barrier(6)

    def finish(_):
        barrier.wait()
        return timer.control(session.id, "finish", operation_id=str(uuid4())).last_session

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(finish, range(6)))
    assert all(result.tree.id == session.tree.id and result.tree.outcome == "unfinished" for result in results)
    forest = list_forest(db)
    assert len(forest) == 1
    before = all_rows(db)
    assert timer.control(session.id, "finish").last_session.tree.id == session.tree.id
    assert all_rows(db) == before
    with pytest.raises(sqlite3.IntegrityError):
        with db.write() as conn:
            conn.execute("INSERT INTO trees (id, session_id, species, created_at) VALUES (?, ?, 'pine', ?)",
                         (str(uuid4()), session.id, session.started_at))
    assert list_forest(db) == forest


@pytest.mark.parametrize("automatic", [False, True])
def test_tree_save_failure_rolls_back_finalization_and_can_retry(db, automatic):
    timer, clock, task, session = setup_tree(db)
    confirmed = observed(timer, clock, 58).active_session
    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_tree BEFORE UPDATE OF outcome ON trees "
                     "BEGIN SELECT RAISE(ABORT, 'injected tree write failure'); END")
    if automatic:
        clock.advance(2)
    before = all_rows(db)
    key = str(uuid4())
    with pytest.raises(sqlite3.Error, match="injected tree write"):
        if automatic:
            timer.get()
        else:
            timer.control(session.id, "finish", expected_revision=confirmed.revision, operation_id=key)
    assert all_rows(db) == before and list_forest(db) == []
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_tree")
    saved = (timer.get() if automatic else timer.control(
        session.id, "finish", expected_revision=confirmed.revision, operation_id=key,
    )).last_session
    assert saved.tree.id == session.tree.id
    assert saved.active_seconds == (60 if automatic else 58)
    assert saved.tree.outcome == ("mature" if automatic else "unfinished")
    assert get_task(db, task.id) == task and len(list_forest(db)) == 1


def test_tree_enrollment_failure_rolls_back_new_session_interval_and_receipt(db):
    clock = FakeClock()
    timer = TimerService(db, clock)
    task = create_task(db, "Retry tree enrollment")
    key = str(uuid4())
    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_enrollment BEFORE INSERT ON trees "
                     "BEGIN SELECT RAISE(ABORT, 'injected enrollment failure'); END")
    before = all_rows(db)
    with pytest.raises(sqlite3.Error, match="injected enrollment"):
        timer.start(task.id, 1, key)
    assert all_rows(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_enrollment")
    session = timer.start(task.id, 1, key).active_session
    assert session.tree is not None
    assert timer.start(task.id, 1, key).active_session.tree == session.tree
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM trees").fetchone()[0] == 1


def test_task_edits_completion_scheduling_and_removal_preserve_historical_tree(db):
    clock = FakeClock()
    timer = TimerService(db, clock)
    project = create_project(db, "Original course")
    parent = create_task(db, "Original assignment", project_id=project.id)
    child = create_task(db, "Original proof", parent_id=parent.id)
    session = timer.start(child.id, 1, str(uuid4())).active_session
    observed(timer, clock, 12)
    timer.control(session.id, "finish")
    forest = list_forest(db)
    assert forest[0].project_name == "Original course"
    assert forest[0].task_title == "Original proof" and forest[0].parent_title == "Original assignment"
    rename_project(db, project.id, "Renamed course")
    update_task(db, parent.id, title="Renamed assignment")
    update_task(db, child.id, title="Renamed proof", deadline="2026-12-01")
    set_task_completion(db, child.id, True)
    placement = create_placement(db, child.id, "2026-11-02")
    move_placement(db, placement.id, "2026-11-03")
    assert list_forest(db) == forest
    from backend.domain.planning import remove_placement
    remove_placement(db, placement.id)
    remove_subtask(db, child.id)
    assert list_forest(db) == forest
    assert list_forest(open_database(db.path)) == forest


def test_schema_eight_upgrade_is_atomic_preserves_all_rows_and_never_backfills(tmp_path: Path):
    db = _schema_seven_with_history(tmp_path / "before-trees.sqlite3")
    migrations = load_migrations()
    migrate(db, migrations[:8])
    before = all_rows(db)
    tree_migration = migrations[8]
    assert tree_migration.version == 9
    broken = Migration(9, tree_migration.name, tree_migration.sql + "\nINSERT INTO absent_tree_table VALUES (1);")
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations[:8], broken])
    assert current_version(db) == 8 and all_rows(db) == before
    migrate(db)
    assert current_version(db) == len(migrations)
    after = all_rows(db)
    for name, rows in before.items():
        assert (after[name][:8] if name == "schema_migrations" else after[name]) == rows
    assert after["trees"] == []
    assert all_rows(open_database(db.path)) == after
    clock = FakeClock()
    timer = TimerService(db, clock)
    review = timer.get().active_session
    assert review.tree is None and timer.get().last_session.tree is None
    saved = timer.recover(review.id, "finish", expected_revision=review.revision,
                          operation_id=str(uuid4()), discard_uncertain=True).last_session
    assert saved.tree is None and list_forest(db) == []
    fresh = timer.start(review.task_id, 1, str(uuid4())).active_session
    assert fresh.tree is not None
    with db.read() as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


@pytest.mark.parametrize("interruption", ["review", "sleep"])
def test_interrupted_finish_tree_failure_rolls_back_resolution_and_retries(db, interruption):
    timer, clock, task, session = setup_tree(db)
    observed(timer, clock, 59)
    if interruption == "review":
        clock.advance(300)
    else:
        clock.advance(1, wall=301, continuous=301)
    current = timer.get().active_session
    assert current.state == ("needs_review" if interruption == "review" else "paused")
    assert current.tree.stage == "sapling" and current.tree.progress == 59 / 60
    key = str(uuid4())

    def finish():
        if interruption == "review":
            return timer.recover(session.id, "finish", expected_revision=current.revision,
                                 operation_id=key, discard_uncertain=True)
        return timer.control(session.id, "finish", expected_revision=current.revision, operation_id=key)

    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_interrupted_tree BEFORE UPDATE OF outcome ON trees "
                     "BEGIN SELECT RAISE(ABORT, 'injected interrupted tree failure'); END")
    before = all_rows(db)
    with pytest.raises(sqlite3.Error, match="injected interrupted tree"):
        finish()
    assert all_rows(db) == before and list_forest(db) == []
    assert timer.get().active_session.recovery.resolved_at is None
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_interrupted_tree")
    saved = finish().last_session
    assert saved.tree.outcome == "unfinished" and saved.tree.stage == "sapling"
    assert saved.outcome == "interrupted" and saved.active_seconds == 59
    assert saved.recovery.resolution == "finish"
    assert get_task(db, task.id) == task and len(list_forest(db)) == 1
    after = all_rows(db)
    assert finish().last_session == saved and all_rows(db) == after


def test_domain_finalization_rejects_active_session_and_never_matures_unresolved_time(db):
    from backend.domain.forest import finalize_tree

    timer, clock, _, session = setup_tree(db)
    with db.write() as conn:
        with pytest.raises(ValueError, match="finalized countdown"):
            finalize_tree(conn, session.id)
    clock.advance(20)
    review = timer.get().active_session
    assert review.state == "needs_review" and review.recovery.resolved_at is None
    # Defense in depth: even an inconsistent full-duration session row cannot
    # mature a tree while an interruption still requires a decision.
    with db.write() as conn:
        conn.execute("UPDATE timer_sessions SET state = 'finished', outcome = 'completed', "
                     "active_microseconds = 60000000, finished_at = checkpoint_at WHERE id = ?", (session.id,))
        finalize_tree(conn, session.id)
    assert list_forest(db)[0].outcome == "unfinished"
    assert list_forest(db)[0].stage == "sapling"


def test_legacy_start_receipt_replay_does_not_enroll_existing_session(tmp_path):
    from backend.domain.timer import _fingerprint

    db = _schema_seven_with_history(tmp_path / "legacy-replay.sqlite3")
    migrate(db, load_migrations()[:8])
    with db.write() as conn:
        row = conn.execute("SELECT * FROM timer_sessions WHERE state = 'running'").fetchone()
        conn.execute("UPDATE timer_operations SET fingerprint = ? WHERE operation_id = ?", (
            _fingerprint("start", task_id=row["task_id"], duration_minutes=row["duration_minutes"]),
            row["start_operation_id"],
        ))
    migrate(db)
    timer = TimerService(db, FakeClock())
    review = timer.get().active_session
    assert review.tree is None
    replayed = timer.start(row["task_id"], row["duration_minutes"], row["start_operation_id"])
    assert replayed.active_session == review
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM trees").fetchone()[0] == 0
