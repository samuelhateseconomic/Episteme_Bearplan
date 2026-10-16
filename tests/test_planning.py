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


def test_moving_one_placement_preserves_task_identity_and_every_field(db: Database) -> None:
    project = create_project(db, "Course")
    task = create_task(
        db, "Write proof", project_id=project.id, notes="Keep the original notes",
        deadline="2026-10-23", estimate_minutes=45,
    )
    task = set_task_completion(db, task.id, True)
    monday = create_placement(db, task.id, "2026-10-12")

    moved = move_placement(db, monday.id, "2026-10-20")

    assert moved.id == monday.id
    assert moved.task_id == task.id
    assert moved.planned_date == date(2026, 10, 20)
    assert moved.created_at == monday.created_at
    assert moved.revision == monday.revision + 1
    assert list_placements(db) == [moved]
    assert get_task(db, task.id) == task
    assert list_tasks(db) == [task]
    assert list_placements(open_database(db.path)) == list_placements(db)


def test_moving_to_another_tasks_day_keeps_both_task_identities(db: Database) -> None:
    first_task = create_task(db, "Read")
    second_task = create_task(db, "Write")
    first = create_placement(db, first_task.id, "2026-10-12")
    second = create_placement(db, second_task.id, "2026-10-20")
    tasks_before = list_tasks(db)
    moved = move_placement(db, first.id, second.planned_date)
    assert moved.id == first.id and moved.task_id == first_task.id
    assert moved.planned_date == second.planned_date
    assert {p.id: p for p in list_placements(db)} == {moved.id: moved, second.id: second}
    assert list_tasks(db) == tasks_before


@pytest.mark.parametrize("is_subtask", [False, True])
@pytest.mark.parametrize("complete", [False, True])
def test_multiple_planned_days_reference_one_leaf_and_keep_each_placement(
    db: Database, is_subtask: bool, complete: bool,
) -> None:
    parent = create_task(db, "Container") if is_subtask else None
    task = create_task(db, "One work item", parent_id=parent.id if parent else None)
    if complete:
        set_task_completion(db, task.id, True)
    placed = create_placement(db, task.id, "2026-10-15")
    tasks_before = list_tasks(db)
    another = create_placement(db, task.id, "2026-10-16", source_placement_id=placed.id)
    future = create_placement(db, task.id, "2026-10-22", source_placement_id=placed.id)
    assert len({placed.id, another.id, future.id}) == 3
    assert {placed.task_id, another.task_id, future.task_id} == {task.id}
    assert list_placements(db) == [placed, another, future]
    assert list_tasks(db) == tasks_before
    assert list_placements(open_database(db.path)) == [placed, another, future]


def test_duplicate_destination_move_and_add_preserve_all_existing_placements(db: Database) -> None:
    task = create_task(db, "Keep both dates", deadline="2026-10-30", notes="Original")
    source = create_placement(db, task.id, "2026-10-15")
    destination = create_placement(db, task.id, "2026-10-16")
    before = list_placements(db)
    for action in (
        lambda: move_placement(db, source.id, "2026-10-16"),
        lambda: create_placement(db, task.id, "2026-10-16", source_placement_id=source.id),
    ):
        with pytest.raises(PlacementConflict, match="2026-10-16") as excinfo:
            action()
        assert "kept" in str(excinfo.value).lower()
        assert list_placements(db) == before
        assert get_task(db, task.id) == task
    assert move_placement(db, source.id, source.planned_date) == source
    assert list_placements(db) == [source, destination]


def test_moving_or_removing_one_of_multiple_placements_keeps_all_other_rows(db: Database) -> None:
    task = create_task(db, "Shared identity")
    source = create_placement(db, task.id, "2026-10-15")
    other = create_placement(db, task.id, "2026-10-16")
    moved = move_placement(db, source.id, "2026-10-22")
    assert moved.id == source.id and moved.created_at == source.created_at
    assert moved.revision == source.revision + 1
    assert list_placements(db) == [other, moved]
    remove_placement(db, moved.id)
    assert list_placements(db) == [other]
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

    def assign(day: str) -> object:
        try:
            return create_placement(db, task.id, day)
        except PlacementConflict as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(assign, ("2026-10-15", "2026-10-15")))
    assert sum(isinstance(result, PlacementConflict) for result in results) == 1
    assert len(list_placements(db)) == 1
    assert list_tasks(db) == [task]


def test_concurrent_add_and_move_to_one_destination_preserve_the_losing_source(db: Database) -> None:
    task = create_task(db, "Shared task")
    source = create_placement(db, task.id, "2026-10-15")

    def request(add: bool) -> object:
        try:
            return (create_placement(db, task.id, "2026-10-16", source_placement_id=source.id)
                    if add else move_placement(db, source.id, "2026-10-16"))
        except PlacementConflict as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(request, (True, False)))
    assert sum(isinstance(result, PlacementConflict) for result in results) == 1
    placements = list_placements(db)
    assert len([item for item in placements if item.planned_date == date(2026, 10, 16)]) == 1
    assert any(item.id == source.id for item in placements)
    assert get_task(db, task.id) == task


def test_moving_to_same_day_is_a_timestamp_and_revision_no_op(db: Database) -> None:
    task = create_task(db, "Already in place")
    placement = create_placement(db, task.id, "2026-10-15")
    assert move_placement(db, placement.id, "2026-10-15") == placement
    assert list_placements(db) == [placement]


def test_unscheduling_keeps_tasks_and_allows_assignment_to_a_new_day(db: Database) -> None:
    task = create_task(db, "Keep this task", deadline="2026-10-30", notes="Keep notes")
    other_task = create_task(db, "Keep its plan")
    first = create_placement(db, task.id, "2026-10-15")
    other = create_placement(db, other_task.id, "2026-10-22")
    assert remove_placement(db, first.id) == first.id
    assert list_placements(db) == [other]
    assert list_tasks(db) == [task, other_task]
    assert get_planning(db, "2026-10-15").tasks == [task, other_task]
    reassigned = create_placement(db, task.id, "2026-10-23")
    assert reassigned.id != first.id and reassigned.task_id == task.id
    assert list_placements(db) == [other, reassigned]
    assert list_tasks(db) == [task, other_task]


def test_separate_subtasks_have_independent_completion_and_derive_parent_progress(db: Database) -> None:
    parent = create_task(db, "Assignment")
    child = create_task(db, "Proof", parent_id=parent.id)
    second_child = create_task(db, "Review proof", parent_id=parent.id)
    first = create_placement(db, child.id, "2026-10-15")
    second = create_placement(db, second_child.id, "2026-10-22")
    before = list_placements(db)
    update_task(db, child.id, title="Revised proof", deadline="2026-10-31", notes="Shared edit")
    completed = set_task_completion(db, child.id, True)
    snapshot = get_planning(db, "2026-10-12")
    by_id = {task.id: task for task in snapshot.tasks}
    assert by_id[child.id] == completed
    assert by_id[second_child.id] == second_child
    assert by_id[parent.id].completed is False
    assert (by_id[parent.id].completed_subtask_count, by_id[parent.id].subtask_count) == (1, 2)
    assert {placement.task_id for placement in snapshot.placements} == {child.id, second_child.id}
    assert {placement.id for placement in snapshot.placements} == {first.id, second.id}
    assert snapshot.placements == before
    set_task_completion(db, second_child.id, True)
    completed_snapshot = get_planning(db, "2026-10-19")
    assert all(task.completed for task in completed_snapshot.tasks)
    assert completed_snapshot.placements == before
    set_task_completion(db, child.id, False)
    reopened = get_planning(db, "2026-10-19")
    reopened_by_id = {task.id: task for task in reopened.tasks}
    assert reopened_by_id[child.id].completed is False
    assert reopened_by_id[parent.id].completed is False
    assert reopened_by_id[second_child.id].completed is True
    assert reopened_by_id[parent.id].completed_subtask_count == 1
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
