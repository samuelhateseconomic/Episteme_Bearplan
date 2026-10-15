"""Weekly planning changes references and dates, never the referenced task."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime

import pytest

from backend.domain.errors import InvalidInput
from backend.domain.planning import (
    PlacementConflict,
    application_today,
    create_placement,
    get_planning,
    list_placements,
    move_placement,
    remove_placement,
    week_bounds,
)
from backend.domain.projects import create_project
from backend.domain.tasks import (
    create_task,
    get_task,
    list_tasks,
    remove_subtask,
    set_task_completion,
    update_task,
)
from backend.storage.db import Database, open_database


def test_multiple_dates_and_moves_preserve_task_identity_and_every_field(db: Database) -> None:
    project = create_project(db, "Course")
    task = create_task(
        db, "Write proof", project_id=project.id, notes="Keep the original notes",
        deadline="2026-10-23", estimate_minutes=45,
    )
    task = set_task_completion(db, task.id, True)
    monday = create_placement(db, task.id, "2026-10-12")
    wednesday = create_placement(db, task.id, date(2026, 10, 14))

    moved = move_placement(db, monday.id, "2026-10-20")

    assert moved.id == monday.id
    assert moved.task_id == wednesday.task_id == task.id
    assert moved.planned_date == date(2026, 10, 20)
    assert moved.created_at == monday.created_at
    assert moved.revision == monday.revision + 1
    assert {p.id: p for p in list_placements(db)} == {moved.id: moved, wednesday.id: wednesday}
    assert get_task(db, task.id) == task
    assert list_tasks(db) == [task]
    assert list_placements(open_database(db.path)) == list_placements(db)


def test_conflicting_move_leaves_both_placements_and_tasks_unchanged(db: Database) -> None:
    task = create_task(db, "One shared task")
    first = create_placement(db, task.id, "2026-10-12")
    second = create_placement(db, task.id, "2026-10-20")
    before = list_placements(db)
    with pytest.raises(PlacementConflict) as excinfo:
        move_placement(db, first.id, second.planned_date)
    assert "already" in str(excinfo.value).lower()
    assert list_placements(db) == before
    assert get_task(db, task.id) == task


def test_duplicate_assignment_is_rejected_but_other_tasks_share_the_day(db: Database) -> None:
    first = create_task(db, "First")
    second = create_task(db, "Second")
    placed = create_placement(db, first.id, "2026-10-15")
    with pytest.raises(PlacementConflict):
        create_placement(db, first.id, "2026-10-15")
    other = create_placement(db, second.id, "2026-10-15")
    assert list_placements(db) == [placed, other]


def test_concurrent_assignment_saves_exactly_one_reference(db: Database) -> None:
    task = create_task(db, "One task, two simultaneous requests")

    def assign() -> object:
        try:
            return create_placement(db, task.id, "2026-10-15")
        except PlacementConflict as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda _: assign(), range(2)))
    assert sum(isinstance(result, PlacementConflict) for result in results) == 1
    assert len(list_placements(db)) == 1
    assert list_tasks(db) == [task]


def test_moving_to_same_day_is_a_timestamp_and_revision_no_op(db: Database) -> None:
    task = create_task(db, "Already in place")
    placement = create_placement(db, task.id, "2026-10-15")
    assert move_placement(db, placement.id, "2026-10-15") == placement
    assert list_placements(db) == [placement]


def test_removing_one_placement_keeps_task_and_other_dates(db: Database) -> None:
    task = create_task(db, "Keep this task", deadline="2026-10-30", notes="Keep notes")
    first = create_placement(db, task.id, "2026-10-15")
    other = create_placement(db, task.id, "2026-10-22")
    assert remove_placement(db, first.id) == first.id
    assert list_placements(db) == [other]
    assert list_tasks(db) == [task]
    remove_placement(db, other.id)
    assert list_placements(db) == []
    assert list_tasks(db) == [task]
    assert get_planning(db, "2026-10-15").tasks == [task]


def test_completion_and_edits_are_shared_across_every_placement(db: Database) -> None:
    parent = create_task(db, "Assignment")
    child = create_task(db, "Proof", parent_id=parent.id)
    first = create_placement(db, child.id, "2026-10-15")
    second = create_placement(db, child.id, "2026-10-22")
    before = list_placements(db)
    update_task(db, child.id, title="Revised proof", deadline="2026-10-31", notes="Shared edit")
    completed = set_task_completion(db, child.id, True)
    snapshot = get_planning(db, "2026-10-12")
    by_id = {task.id: task for task in snapshot.tasks}
    assert by_id[child.id] == completed
    assert by_id[parent.id].completed is True
    assert by_id[parent.id].completed_subtask_count == by_id[parent.id].subtask_count == 1
    assert {placement.task_id for placement in snapshot.placements} == {child.id}
    assert {placement.id for placement in snapshot.placements} == {first.id, second.id}
    assert snapshot.placements == before
    set_task_completion(db, child.id, False)
    reopened = get_planning(db, "2026-10-19")
    assert all(not task.completed for task in reopened.tasks)
    assert reopened.placements == before


def test_only_leaves_are_schedulable_and_parents_remain_context(db: Database) -> None:
    parent = create_task(db, "Container")
    child = create_task(db, "Work", parent_id=parent.id)
    before = list_tasks(db)
    with pytest.raises(InvalidInput) as excinfo:
        create_placement(db, parent.id, "2026-10-15")
    assert excinfo.value.field == "task_id"
    assert list_tasks(db) == before
    assert list_placements(db) == []
    placement = create_placement(db, child.id, "2026-10-15")
    snapshot = get_planning(db)
    assert {task.id for task in snapshot.tasks} == {parent.id, child.id}
    assert snapshot.placements == [placement]
    with pytest.raises(InvalidInput):
        set_task_completion(db, parent.id, True)
    assert list_tasks(db) == before


def test_scheduled_leaf_must_be_unscheduled_before_gaining_children(db: Database) -> None:
    task = create_task(db, "Planned standalone task")
    placement = create_placement(db, task.id, "2026-10-15")
    with pytest.raises(InvalidInput) as excinfo:
        create_task(db, "Additional step", parent_id=task.id)
    assert "unschedul" in str(excinfo.value).lower() or "remove" in str(excinfo.value).lower()
    assert list_tasks(db) == [task]
    assert list_placements(db) == [placement]
    remove_placement(db, placement.id)
    child = create_task(db, "Additional step", parent_id=task.id)
    assert child.parent_id == task.id


def test_scheduled_subtask_must_be_unscheduled_before_removal(db: Database) -> None:
    parent = create_task(db, "Container")
    child = create_task(db, "Work", parent_id=parent.id)
    placement = create_placement(db, child.id, "2026-10-15")
    before = list_tasks(db)
    with pytest.raises(InvalidInput):
        remove_subtask(db, child.id)
    assert list_tasks(db) == before
    assert list_placements(db) == [placement]
    remove_placement(db, placement.id)
    returned = remove_subtask(db, child.id)
    assert returned.id == parent.id and returned.subtask_count == 0
    assert returned.completed is False
    create_placement(db, parent.id, "2026-10-15")


def test_week_snapshot_retains_unscheduled_tasks_and_placements_in_other_weeks(db: Database) -> None:
    project = create_project(db, "Another project")
    unscheduled = create_task(db, "Backlog")
    elsewhere = create_task(db, "Already planned", project_id=project.id)
    placement = create_placement(db, elsewhere.id, "2027-01-05")
    result = get_planning(db, "2026-12-31", now=datetime(2026, 10, 15, 12, tzinfo=UTC))
    assert (result.week_start, result.week_end) == (date(2026, 12, 28), date(2027, 1, 3))
    assert {task.id for task in result.tasks} == {unscheduled.id, elsewhere.id}
    assert result.placements == [placement]


@pytest.mark.parametrize("value", [
    "", "20261015", "2026-W42-4", "2026-2-05", "2026-02-30", "2026-10-15T00:00:00Z",
    None, 20261015, True, datetime(2026, 10, 15, tzinfo=UTC),
])
def test_invalid_placement_dates_never_write(db: Database, value: object) -> None:
    task = create_task(db, "Keep")
    placement = create_placement(db, task.id, "2026-10-15")
    for operation in (
        lambda: create_placement(db, task.id, value),
        lambda: move_placement(db, placement.id, value),
    ):
        with pytest.raises(InvalidInput) as excinfo:
            operation()
        assert excinfo.value.field == "planned_date"
        assert list_placements(db) == [placement]
        assert get_task(db, task.id) == task


def test_unknown_references_are_rejected_without_changes(db: Database) -> None:
    task = create_task(db, "Keep")
    placement = create_placement(db, task.id, "2026-10-15")
    operations = (
        lambda: create_placement(db, "missing", "2026-10-15"),
        lambda: move_placement(db, "missing", "2026-10-16"),
        lambda: remove_placement(db, "missing"),
    )
    for operation in operations:
        with pytest.raises(InvalidInput):
            operation()
        assert list_placements(db) == [placement]
        assert list_tasks(db) == [task]


@pytest.mark.parametrize("value,monday,sunday", [
    ("2026-10-12", "2026-10-12", "2026-10-18"),
    ("2026-10-18", "2026-10-12", "2026-10-18"),
    ("2026-12-31", "2026-12-28", "2027-01-03"),
    ("2027-01-03", "2026-12-28", "2027-01-03"),
    ("2028-02-29", "2028-02-28", "2028-03-05"),
    (date(2026, 11, 1), "2026-10-26", "2026-11-01"),
])
def test_week_boundaries_are_monday_through_sunday(value, monday: str, sunday: str) -> None:
    assert week_bounds(value) == (date.fromisoformat(monday), date.fromisoformat(sunday))


@pytest.mark.parametrize("value", ["20261015", "2026-02-30", "9999-12-31", datetime(2026, 10, 15), None])
def test_invalid_or_unrepresentable_weeks_are_actionable(value: object) -> None:
    with pytest.raises(InvalidInput):
        week_bounds(value)


@pytest.mark.parametrize("instant,expected", [
    (datetime(2026, 1, 1, 7, 59, tzinfo=UTC), date(2025, 12, 31)),
    (datetime(2026, 1, 1, 8, 0, tzinfo=UTC), date(2026, 1, 1)),
    (datetime(2026, 3, 8, 9, 59, tzinfo=UTC), date(2026, 3, 8)),
    (datetime(2026, 3, 8, 10, 1, tzinfo=UTC), date(2026, 3, 8)),
    (datetime(2026, 11, 1, 8, 59, tzinfo=UTC), date(2026, 11, 1)),
    (datetime(2026, 11, 1, 9, 1, tzinfo=UTC), date(2026, 11, 1)),
])
def test_today_uses_application_timezone_at_midnight_and_dst(monkeypatch, instant, expected) -> None:
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    assert application_today(instant) == (expected, "America/Los_Angeles")


def test_unset_timezone_defaults_to_os_local_and_default_week_uses_that_today(monkeypatch, db: Database) -> None:
    monkeypatch.delenv("BEARPLANS_TIMEZONE", raising=False)
    instant = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)
    expected = instant.astimezone().date()
    today, label = application_today(instant)
    assert today == expected and label
    snapshot = get_planning(db, now=instant)
    assert snapshot.today == expected and snapshot.timezone == label
    assert (snapshot.week_start, snapshot.week_end) == week_bounds(expected)


def test_invalid_timezone_setting_gives_an_actionable_error(monkeypatch) -> None:
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "Not/A_Real_Zone")
    with pytest.raises(InvalidInput) as excinfo:
        application_today(datetime(2026, 10, 15, tzinfo=UTC))
    assert "timezone" in str(excinfo.value).lower() or "time zone" in str(excinfo.value).lower()


def test_first_and_last_representable_full_weeks() -> None:
    assert week_bounds(date.min) == (date(1, 1, 1), date(1, 1, 7))
    assert week_bounds("9999-12-26") == (date(9999, 12, 20), date(9999, 12, 26))
