"""Independent totals for the all-time report; only disposable saved records."""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.domain.projects import create_project, rename_project
from backend.domain.planning import create_placement
from backend.domain.statistics import get_statistics
from backend.domain.streaks import StreakDataError, get_streaks
from backend.domain.tasks import create_task, remove_subtask, set_task_completion, update_task
from backend.storage.db import open_database
from tests.test_forest import all_rows
from tests.test_streaks import HOUR, NOW, iso, saved_interval


@pytest.fixture(autouse=True)
def utc_calendar(monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")


def test_empty_current_and_saved_totals_are_zero_and_reads_change_no_records(db):
    before = all_rows(db)
    view = get_statistics(db, now=NOW)
    assert view.completion.model_dump() == {"completed": 0, "total": 0, "percent": 0}
    assert view.active_microseconds == view.session_count == 0
    assert view.days == view.tasks == []
    assert len(view.projects) == 1 and view.projects[0].name == "Inbox"
    assert all_rows(db) == before


def test_known_totals_leaf_denominator_estimates_multiple_dates_and_intervals(db):
    project = create_project(db, "Math")
    parent = create_task(db, "Container", project_id=project.id, estimate_minutes=999)
    child = create_task(db, "Exercises", project_id=project.id, parent_id=parent.id, estimate_minutes=60)
    other = create_task(db, "Essay", estimate_minutes=30)
    create_task(db, "No estimate")
    set_task_completion(db, child.id, True)
    create_placement(db, child.id, "2026-10-20")
    create_placement(db, child.id, "2026-10-21")
    saved = saved_interval(db, NOW - timedelta(hours=2), NOW - timedelta(hours=1, minutes=30), HOUR // 2, task=child)
    with db.write() as conn:
        conn.execute("UPDATE tasks SET completed_at = ? WHERE id = ?", (iso(NOW), child.id))
        conn.execute("INSERT INTO timer_intervals (id, session_id, started_at, checkpoint_at, ended_at, active_microseconds) "
                     "VALUES (?, ?, ?, ?, ?, ?)",
                     (str(uuid4()), saved, iso(NOW - timedelta(minutes=20)), iso(NOW - timedelta(minutes=10)),
                      iso(NOW - timedelta(minutes=10)), 600_000_000))
        conn.execute("UPDATE timer_sessions SET active_microseconds = ? WHERE id = ?", (2_400_000_000, saved))
    saved_interval(db, NOW - timedelta(hours=1), NOW - timedelta(minutes=40), 1_200_000_000, task=other, outcome="finished_early")
    before = all_rows(db)
    view = get_statistics(db, now=NOW)
    assert view.completion.model_dump() == {"completed": 1, "total": 3, "percent": 33.33}
    assert view.session_count == 2 and view.active_microseconds == HOUR
    assert [(day.active_microseconds, day.completed) for day in view.days] == [(HOUR, 1)]
    rows = {task.task_id: task for task in view.tasks}
    assert parent.id not in rows
    assert rows[child.id].active_microseconds == 2_400_000_000 and rows[child.id].session_count == 1
    assert rows[child.id].estimate_minutes == 60 and rows[child.id].parent_title == "Container"
    assert sum(task.estimate_minutes or 0 for task in rows.values()) == 90
    assert sum(project.active_microseconds for project in view.projects) == HOUR
    assert sum(task.active_microseconds for task in view.tasks) == HOUR
    assert all_rows(db) == before
    assert get_statistics(open_database(db.path), now=NOW) == view


@pytest.mark.parametrize("state", ["paused", "running", "needs_review"])
def test_unfinished_intervals_never_become_saved_time(db, state):
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR, state=state)
    assert get_statistics(db, now=NOW).active_microseconds == 0


def test_no_fallback_to_session_total_open_interval_or_unresolved_work(db):
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR, interval=False)
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR, closed=False)
    unresolved = saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR)
    with db.write() as conn:
        conn.execute("INSERT INTO timer_interruptions (id, session_id, kind, reason, checkpoint_at, detected_at, confirmed_active_microseconds) "
                     "VALUES (?, ?, 'service_restart', 'Fixture', ?, ?, ?)", (str(uuid4()), unresolved, iso(NOW), iso(NOW), HOUR))
    view = get_statistics(db, now=NOW)
    assert view.active_microseconds == view.session_count == 0 and not view.days


def test_removed_subtask_and_container_history_keep_time_without_estimates_or_completion(db):
    parent = create_task(db, "Original parent")
    child = create_task(db, "Removed child", parent_id=parent.id, estimate_minutes=10)
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR, task=child, outcome="interrupted")
    remove_subtask(db, child.id)
    saved_interval(db, NOW - timedelta(hours=2), NOW - timedelta(hours=1), HOUR, task=parent)
    create_task(db, "New child", parent_id=parent.id)
    before = all_rows(db)
    view = get_statistics(db, now=NOW)
    assert view.active_microseconds == 2 * HOUR
    assert view.completion.total == 1
    historical = [row for row in view.tasks if not row.current_leaf]
    assert {row.task_id for row in historical} == {parent.id, child.id}
    assert all(row.estimate_minutes is None and row.completed is None for row in historical)
    assert all_rows(db) == before


def test_renaming_and_reopening_change_current_details_not_saved_time(db):
    project = create_project(db, "Original project")
    task = create_task(db, "Original title", project_id=project.id, estimate_minutes=10)
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR, task=task)
    set_task_completion(db, task.id, True)
    assert get_statistics(db, now=NOW).completion.completed == 1
    rename_project(db, project.id, "New project")
    update_task(db, task.id, title="New title", estimate_minutes=20)
    set_task_completion(db, task.id, False)
    view = get_statistics(db, now=NOW)
    assert view.completion.completed == 0 and all(day.completed == 0 for day in view.days)
    assert view.tasks[0].title == "New title" and view.tasks[0].estimate_minutes == 20
    assert next(row for row in view.projects if row.project_id == project.id).name == "New project"
    assert view.active_microseconds == HOUR
    with db.read() as conn:
        assert conn.execute("SELECT task_title FROM timer_sessions").fetchone()[0] == "Original title"


@pytest.mark.parametrize("zone,start,end,credit,expected", [
    ("America/Los_Angeles", "2026-10-21T06:30:00Z", "2026-10-21T07:30:00Z", HOUR, {"2026-10-20": HOUR // 2, "2026-10-21": HOUR // 2}),
    ("America/Los_Angeles", "2026-11-01T08:30:00Z", "2026-11-01T10:30:00Z", 2 * HOUR, {"2026-11-01": 2 * HOUR}),
    ("UTC", "2026-10-20T23:59:59.999997Z", "2026-10-21T00:00:00.000003Z", 5, {"2026-10-20": 2, "2026-10-21": 3}),
    ("UTC", "2026-10-21T20:00:00Z", "2026-10-21T20:00:00Z", 1, {"2026-10-21": 1}),
])
def test_calendar_allocation_conserves_credit_and_agrees_with_streaks(db, monkeypatch, zone, start, end, credit, expected):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", zone)
    saved_interval(db, start, end, credit)
    now = datetime.fromisoformat(end.replace("Z", "+00:00"))
    view = get_statistics(db, now=now)
    assert {str(day.date): day.active_microseconds for day in view.days} == expected
    assert sum(expected.values()) == view.active_microseconds == credit
    assert {str(day.date): day.active_microseconds for day in get_streaks(db, now=now).days if day.active_microseconds} == expected


def test_bad_interval_fails_closed_without_writes(db):
    saved_interval(db, "invalid", iso(NOW), HOUR)
    before = all_rows(db)
    with pytest.raises(StreakDataError):
        get_statistics(db, now=NOW)
    assert all_rows(db) == before
