"""Week closure freezes history; reviewed carryover only schedules existing work.

All migration and injected-failure cases use disposable SQLite databases.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.domain.errors import InvalidInput
from backend.domain.planning import (
    create_placement, get_planning, list_placements, move_placement, remove_placement,
)
from backend.domain.projects import create_project, rename_project
from backend.domain.tasks import (
    create_task, get_task, list_tasks, remove_subtask, set_task_completion, update_task,
)
from backend.domain.weeks import (
    WeekConflict, apply_carryover, close_week, get_carryover, preview_carryover, preview_close,
)
from backend.storage.db import Database, open_database
from backend.storage.migrations import Migration, MigrationError, current_version, load_migrations, migrate

SOURCE = "2026-10-12"
FOLLOWING = "2026-10-19"


def dumped(model) -> dict:
    return model.model_dump(mode="json")


def closed(db: Database, week: str = SOURCE):
    preview = preview_close(db, week)
    return close_week(db, week, preview.preview_token)


def selections(*items: tuple[str, str]) -> list[dict[str, str]]:
    return [{"task_id": task_id, "planned_date": day} for task_id, day in items]


def carried(db: Database, selected: list[dict[str, str]], *, week: str = SOURCE, operation_id: str | None = None):
    preview = preview_carryover(db, week, selected)
    return apply_carryover(db, week, selected, preview.preview_token, operation_id or str(uuid4()))


def rows(db: Database, table: str) -> list[tuple]:
    assert table in {"tasks", "projects", "planned_items", "closed_weeks", "closed_placements", "carryover_operations"}
    with db.read() as conn:
        return [tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY 1")]


def saved_content(db: Database) -> dict[str, list[tuple]]:
    return {table: rows(db, table) for table in (
        "tasks", "projects", "planned_items", "closed_weeks", "closed_placements", "carryover_operations",
    )}


def test_close_freezes_full_display_details_and_archives_placements_without_changing_tasks(db: Database) -> None:
    project = create_project(db, "Course at closure")
    parent = create_task(db, "Assignment context", project_id=project.id, notes="Parent notes")
    child = create_task(db, "Unfinished proof", parent_id=parent.id, notes="Keep proof notes",
                        deadline="2026-10-30", estimate_minutes=45)
    done = create_task(db, "Finished step", parent_id=parent.id)
    set_task_completion(db, done.id, True)
    first = create_placement(db, child.id, "2026-10-15")
    second = create_placement(db, done.id, "2026-10-16")
    future = create_task(db, "Next week's separate work")
    future_plan = create_placement(db, future.id, "2026-10-22")
    task_rows, project_rows = rows(db, "tasks"), rows(db, "projects")
    source_plan_rows = [row for row in rows(db, "planned_items") if row[0] in {first.id, second.id}]

    history = closed(db)
    frozen = dumped(history)
    assert frozen["week_start"] == SOURCE and frozen["week_end"] == "2026-10-18"
    assert frozen["timezone"] and frozen["closed_at"].endswith("Z")
    assert {item["id"] for item in frozen["placements"]} == {first.id, second.id}
    assert {item["id"] for item in frozen["tasks"]} == {parent.id, child.id, done.id}
    assert all(item["project_name"] == project.name for item in frozen["tasks"])
    assert next(item for item in frozen["tasks"] if item["id"] == child.id)["parent_title"] == parent.title
    assert (frozen["completed"], frozen["total"]) == (1, 2)
    assert rows(db, "tasks") == task_rows and rows(db, "projects") == project_rows
    assert list_placements(db) == [future_plan]
    with db.read() as conn:
        archived = [tuple(row) for row in conn.execute(
            "SELECT id, task_id, planned_date, created_at, updated_at, revision FROM closed_placements ORDER BY id"
        )]
        assert archived == source_plan_rows
    assert dumped(get_planning(db, SOURCE).closed_week) == frozen


def test_history_ignores_later_project_task_completion_scheduling_and_deletion_changes(db: Database) -> None:
    project = create_project(db, "Original project")
    parent = create_task(db, "Original parent", project_id=project.id)
    child = create_task(db, "Original child", parent_id=parent.id, notes="Original notes",
                        deadline="2026-10-30", estimate_minutes=30)
    create_placement(db, child.id, "2026-10-15")
    history = dumped(closed(db))
    stored_history = rows(db, "closed_weeks"), rows(db, "closed_placements")

    rename_project(db, project.id, "Renamed project")
    update_task(db, parent.id, title="Renamed parent")
    update_task(db, child.id, title="Renamed child", notes="New notes", deadline="2027-01-01", estimate_minutes=60)
    set_task_completion(db, child.id, True)
    assert dumped(get_planning(db, SOURCE).closed_week) == history
    active = create_placement(db, child.id, "2026-10-22")
    assert dumped(get_planning(db, SOURCE).closed_week) == history
    move_placement(db, active.id, "2026-10-23")
    remove_placement(db, active.id)
    remove_subtask(db, child.id)
    reopened = open_database(db.path)
    assert dumped(get_planning(reopened, SOURCE).closed_week) == history
    assert (rows(reopened, "closed_weeks"), rows(reopened, "closed_placements")) == stored_history
    assert all(task.id != child.id for task in list_tasks(reopened))


def test_empty_week_closes_with_zero_total_and_retry_returns_identical_snapshot(db: Database) -> None:
    first = closed(db)
    body = dumped(first)
    assert body["completed"] == body["total"] == 0
    assert body["tasks"] == body["placements"] == []
    assert close_week(db, SOURCE, "stale retry token") == first
    assert len(rows(db, "closed_weeks")) == 1
    assert rows(db, "closed_placements") == []
    assert get_planning(db, SOURCE).closed_week == first


def test_multiple_placements_count_each_leaf_once_and_exclude_parent_context(db: Database) -> None:
    """Defensive historical count: repeated references never change the denominator."""
    parent = create_task(db, "Parent")
    child = create_task(db, "Completed child", parent_id=parent.id)
    unfinished = create_task(db, "Unfinished child", parent_id=parent.id)
    set_task_completion(db, child.id, True)
    placement = create_placement(db, child.id, "2026-10-15")
    create_placement(db, unfinished.id, "2026-10-16")
    # Exercise snapshot deduplication without weakening production's one-active-plan rule.
    with db.write() as conn:
        conn.execute("DROP INDEX planned_items_one_per_task")
        conn.execute(
            "INSERT INTO planned_items (id, task_id, planned_date, created_at, updated_at, revision)"
            " SELECT ?, task_id, '2026-10-17', created_at, updated_at, revision FROM planned_items WHERE id = ?",
            (str(uuid4()), placement.id),
        )
    history = dumped(closed(db))
    assert len(history["placements"]) == 3
    assert (history["completed"], history["total"]) == (1, 2)
    assert len({task["id"] for task in history["tasks"]}) == 3


@pytest.mark.parametrize("operation", ["assign", "move_into", "move_archived", "same_day_archived", "remove_archived"])
def test_backend_rejects_all_closed_week_placement_mutations(db: Database, operation: str) -> None:
    task = create_task(db, "Historical work")
    placement = create_placement(db, task.id, "2026-10-15")
    closed(db)
    other = create_task(db, "Open work")
    active = create_placement(db, other.id, "2026-10-22")
    unplanned = create_task(db, "Backlog")
    before = saved_content(db)
    actions = {
        "assign": lambda: create_placement(db, unplanned.id, "2026-10-16"),
        "move_into": lambda: move_placement(db, active.id, "2026-10-17"),
        "move_archived": lambda: move_placement(db, placement.id, "2026-10-23"),
        "same_day_archived": lambda: move_placement(db, placement.id, "2026-10-15"),
        "remove_archived": lambda: remove_placement(db, placement.id),
    }
    with pytest.raises(WeekConflict) as excinfo:
        actions[operation]()
    assert "closed" in str(excinfo.value).lower()
    assert saved_content(db) == before


@pytest.mark.parametrize("table", ["closed_weeks", "closed_placements"])
@pytest.mark.parametrize("statement", ["UPDATE", "DELETE"])
def test_database_guards_reject_rewriting_or_deleting_history(db: Database, table: str, statement: str) -> None:
    task = create_task(db, "Historical work")
    create_placement(db, task.id, "2026-10-15")
    closed(db)
    before = saved_content(db)
    sql = f"DELETE FROM {table}" if statement == "DELETE" else (
        "UPDATE closed_weeks SET timezone = 'UTC'" if table == "closed_weeks" else
        "UPDATE closed_placements SET planned_date = '2026-10-16'"
    )
    with pytest.raises(sqlite3.IntegrityError):
        with db.write() as conn:
            conn.execute(sql)
    assert saved_content(db) == before


def test_close_requires_fresh_preview_and_failure_changes_nothing(db: Database) -> None:
    task = create_task(db, "Changed since preview")
    create_placement(db, task.id, "2026-10-15")
    preview = preview_close(db, SOURCE)
    update_task(db, task.id, notes="A later edit")
    before = saved_content(db)
    with pytest.raises(WeekConflict) as excinfo:
        close_week(db, SOURCE, preview.preview_token)
    assert "preview" in str(excinfo.value).lower()
    assert saved_content(db) == before
    assert closed(db)


def test_close_failure_after_snapshot_insert_rolls_back_archive_and_can_retry(db: Database) -> None:
    task = create_task(db, "Keep this plan")
    create_placement(db, task.id, "2026-10-15")
    preview = preview_close(db, SOURCE)
    before = saved_content(db)
    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_archive BEFORE INSERT ON closed_placements BEGIN SELECT RAISE(ABORT, 'injected archive failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="injected archive failure"):
        close_week(db, SOURCE, preview.preview_token)
    assert saved_content(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_archive")
    assert close_week(db, SOURCE, preview.preview_token)
    assert len(rows(db, "closed_weeks")) == len(rows(db, "closed_placements")) == 1
    assert rows(db, "planned_items") == []


def test_close_failure_after_archive_copy_restores_all_source_placements(db: Database) -> None:
    for title in ("First preserved placement", "Second preserved placement"):
        task = create_task(db, title)
        create_placement(db, task.id, "2026-10-15")
    preview = preview_close(db, SOURCE)
    before = saved_content(db)
    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_source_removal BEFORE DELETE ON planned_items BEGIN SELECT RAISE(ABORT, 'injected archive finalization failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="injected archive finalization failure"):
        close_week(db, SOURCE, preview.preview_token)
    assert saved_content(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_source_removal")
    close_week(db, SOURCE, preview.preview_token)
    assert len(rows(db, "closed_placements")) == 2 and rows(db, "planned_items") == []


def test_concurrent_close_requests_create_one_snapshot_with_original_placement_id(db: Database) -> None:
    task = create_task(db, "Concurrent close")
    placement = create_placement(db, task.id, "2026-10-15")
    preview = preview_close(db, SOURCE)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: close_week(db, SOURCE, preview.preview_token), range(2)))
    assert results[0] == results[1]
    assert len(rows(db, "closed_weeks")) == len(rows(db, "closed_placements")) == 1
    assert rows(db, "closed_placements")[0][0] == placement.id


def test_reviewed_carryover_references_original_tasks_and_preserves_source_and_every_task_field(db: Database) -> None:
    project = create_project(db, "Course")
    parent = create_task(db, "Assignment", project_id=project.id)
    first = create_task(db, "Proof", parent_id=parent.id, notes="Keep notes", deadline="2026-10-30", estimate_minutes=45)
    second = create_task(db, "Review", parent_id=parent.id, deadline="2026-11-01")
    source = create_placement(db, first.id, "2026-10-15")
    create_placement(db, second.id, "2026-10-16")
    frozen = dumped(closed(db))
    tasks_before, projects_before = rows(db, "tasks"), rows(db, "projects")
    archive_before = rows(db, "closed_placements")
    carried(db, selections((first.id, "2026-10-20")))
    plans = list_placements(db)
    assert len(plans) == 1 and plans[0].task_id == first.id
    assert plans[0].planned_date == date(2026, 10, 20) and plans[0].id != source.id
    assert rows(db, "tasks") == tasks_before and rows(db, "projects") == projects_before
    assert rows(db, "closed_placements") == archive_before
    assert dumped(get_planning(db, SOURCE).closed_week) == frozen
    assert get_task(db, first.id) == first
    assert {task.id for task in list_tasks(db)} == {parent.id, first.id, second.id}


def test_carryover_options_exclude_currently_complete_deleted_parent_and_previously_complete_work(db: Database) -> None:
    parent = create_task(db, "Container")
    completed_later = create_task(db, "Done now", parent_id=parent.id)
    removed = create_task(db, "Removed later", parent_id=parent.id)
    now_container = create_task(db, "New parent later")
    done_at_close = create_task(db, "Already done")
    eligible = create_task(db, "Still unfinished")
    set_task_completion(db, done_at_close.id, True)
    for task in (completed_later, removed, now_container, done_at_close, eligible):
        create_placement(db, task.id, "2026-10-15")
    closed(db)
    set_task_completion(db, completed_later.id, True)
    remove_subtask(db, removed.id)
    create_task(db, "New child", parent_id=now_container.id)
    set_task_completion(db, done_at_close.id, False)
    options = dumped(get_carryover(db, SOURCE))
    candidates = {item["task_id"]: item for item in options["candidates"]}
    assert candidates[eligible.id]["eligible"] is True
    for task in (completed_later, removed, now_container):
        assert candidates[task.id]["eligible"] is False and candidates[task.id]["reason"]
    assert done_at_close.id not in candidates
    for task in (completed_later, removed, now_container, done_at_close):
        before = saved_content(db)
        with pytest.raises((WeekConflict, InvalidInput)):
            preview_carryover(db, SOURCE, selections((task.id, "2026-10-20")))
        assert saved_content(db) == before


@pytest.mark.parametrize("destination", ["2026-10-18", "2026-10-26", "20261020", "2026-02-30", "2026-10-20T12:00:00Z", None])
def test_carryover_rejects_dates_outside_following_week_or_invalid_dates(db: Database, destination) -> None:
    task = create_task(db, "Unfinished")
    create_placement(db, task.id, "2026-10-15")
    closed(db)
    before = saved_content(db)
    with pytest.raises(InvalidInput):
        preview_carryover(db, SOURCE, [{"task_id": task.id, "planned_date": destination}])
    assert saved_content(db) == before


@pytest.mark.parametrize("selected", [None, {}, [], [{"task_id": "missing", "planned_date": "2026-10-20"}],
                                      [{"task_id": 3, "planned_date": "2026-10-20"}],
                                      [{"task_id": "{task}", "planned_date": "2026-10-20", "complete": True}]])
def test_carryover_rejects_invalid_selections_without_mutation(db: Database, selected) -> None:
    task = create_task(db, "Unfinished")
    create_placement(db, task.id, "2026-10-15")
    closed(db)
    if isinstance(selected, list):
        selected = [{key: task.id if value == "{task}" else value for key, value in item.items()} for item in selected]
    before = saved_content(db)
    with pytest.raises((InvalidInput, WeekConflict)):
        preview_carryover(db, SOURCE, selected)
    assert saved_content(db) == before


def test_carryover_rejects_duplicate_task_selections_even_on_different_days(db: Database) -> None:
    task = create_task(db, "One work item")
    create_placement(db, task.id, "2026-10-15")
    closed(db)
    before = saved_content(db)
    for second_day in ("2026-10-20", "2026-10-21"):
        with pytest.raises(InvalidInput):
            preview_carryover(db, SOURCE, selections((task.id, "2026-10-20"), (task.id, second_day)))
        assert saved_content(db) == before


@pytest.mark.parametrize("existing_date", ["2026-10-20", "2026-10-23", "2026-11-02"])
def test_carryover_explains_existing_destination_or_other_active_plan_and_leaves_it_unchanged(db: Database, existing_date: str) -> None:
    task = create_task(db, "Already scheduled again")
    create_placement(db, task.id, "2026-10-15")
    closed(db)
    existing = create_placement(db, task.id, existing_date)
    before = saved_content(db)
    with pytest.raises((WeekConflict, InvalidInput)) as excinfo:
        preview_carryover(db, SOURCE, selections((task.id, "2026-10-20")))
    assert existing_date in str(excinfo.value)
    assert saved_content(db) == before and list_placements(db) == [existing]


def test_carryover_requires_closed_source_and_open_following_destination(db: Database) -> None:
    task = create_task(db, "Work")
    create_placement(db, task.id, "2026-10-15")
    with pytest.raises((WeekConflict, InvalidInput)):
        get_carryover(db, SOURCE)
    closed(db)
    closed(db, FOLLOWING)
    before = saved_content(db)
    with pytest.raises(WeekConflict) as excinfo:
        preview_carryover(db, SOURCE, selections((task.id, "2026-10-20")))
    assert "closed" in str(excinfo.value).lower()
    assert saved_content(db) == before


@pytest.mark.parametrize("later_change", ["completion", "edit", "assignment", "close_destination"])
def test_carryover_preview_is_rechecked_against_live_state_before_apply(db: Database, later_change: str) -> None:
    task = create_task(db, "Changed after carryover preview")
    create_placement(db, task.id, "2026-10-15")
    closed(db)
    selected = selections((task.id, "2026-10-20"))
    preview = preview_carryover(db, SOURCE, selected)
    if later_change == "completion":
        set_task_completion(db, task.id, True)
    elif later_change == "edit":
        update_task(db, task.id, notes="Changed since review")
    elif later_change == "assignment":
        create_placement(db, task.id, "2026-10-21")
    else:
        closed(db, FOLLOWING)
    before = saved_content(db)
    with pytest.raises((WeekConflict, InvalidInput)):
        apply_carryover(db, SOURCE, selected, preview.preview_token, str(uuid4()))
    assert saved_content(db) == before


def test_carryover_retry_with_same_operation_returns_original_result_even_after_later_changes(db: Database) -> None:
    first = create_task(db, "First")
    second = create_task(db, "Second")
    for task in (first, second):
        create_placement(db, task.id, "2026-10-15")
    closed(db)
    selected = selections((first.id, "2026-10-20"), (second.id, "2026-10-21"))
    preview = preview_carryover(db, SOURCE, selected)
    operation_id = str(uuid4())
    initial = apply_carryover(db, SOURCE, selected, preview.preview_token, operation_id)
    set_task_completion(db, first.id, True)
    plans_before = list_placements(db)
    assert apply_carryover(db, SOURCE, list(reversed(selected)), "old retry token", operation_id) == initial
    assert list_placements(db) == plans_before and len(plans_before) == 2
    assert len(rows(db, "carryover_operations")) == 1
    before = saved_content(db)
    with pytest.raises(WeekConflict):
        apply_carryover(db, SOURCE, selections((first.id, "2026-10-22")), preview.preview_token, operation_id)
    assert saved_content(db) == before


def test_carryover_replay_still_returns_receipt_after_destination_week_closes(db: Database) -> None:
    task = create_task(db, "Carried then archived again")
    create_placement(db, task.id, "2026-10-15")
    source = dumped(closed(db))
    selected = selections((task.id, "2026-10-20"))
    preview = preview_carryover(db, SOURCE, selected)
    operation_id = str(uuid4())
    result = apply_carryover(db, SOURCE, selected, preview.preview_token, operation_id)
    destination = dumped(closed(db, FOLLOWING))
    before = saved_content(db)
    assert apply_carryover(db, SOURCE, selected, "lost response retry", operation_id) == result
    assert saved_content(db) == before
    assert dumped(get_planning(db, SOURCE).closed_week) == source
    assert dumped(get_planning(db, FOLLOWING).closed_week) == destination


@pytest.mark.parametrize("operation_id", ["", "not-a-uuid", "00000000000000000000000000000000", None, 3])
def test_carryover_rejects_invalid_operation_ids_without_placing_work(db: Database, operation_id) -> None:
    task = create_task(db, "Retry ID needed")
    create_placement(db, task.id, "2026-10-15")
    closed(db)
    selected = selections((task.id, "2026-10-20"))
    preview = preview_carryover(db, SOURCE, selected)
    before = saved_content(db)
    with pytest.raises(InvalidInput) as excinfo:
        apply_carryover(db, SOURCE, selected, preview.preview_token, operation_id)
    assert excinfo.value.field == "operation_id"
    assert saved_content(db) == before


def test_concurrent_same_carryover_operation_inserts_each_reference_once(db: Database) -> None:
    task = create_task(db, "Retry twice")
    create_placement(db, task.id, "2026-10-15")
    closed(db)
    selected = selections((task.id, "2026-10-20"))
    preview = preview_carryover(db, SOURCE, selected)
    operation_id = str(uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: apply_carryover(db, SOURCE, selected, preview.preview_token, operation_id), range(2)))
    assert results[0] == results[1]
    assert len(list_placements(db)) == len(rows(db, "carryover_operations")) == 1


def test_carryover_failure_after_first_insert_rolls_back_all_destinations_and_operation(db: Database) -> None:
    first, second = create_task(db, "First"), create_task(db, "Second")
    for task in (first, second):
        create_placement(db, task.id, "2026-10-15")
    closed(db)
    selected = selections((first.id, "2026-10-20"), (second.id, "2026-10-21"))
    preview = preview_carryover(db, SOURCE, selected)
    operation_id = str(uuid4())
    before = saved_content(db)
    with db.write() as conn:
        conn.execute(
            "CREATE TRIGGER fail_second_carryover BEFORE INSERT ON planned_items "
            "WHEN (SELECT COUNT(*) FROM planned_items) >= 1 "
            "BEGIN SELECT RAISE(ABORT, 'injected second carryover failure'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="injected second carryover failure"):
        apply_carryover(db, SOURCE, selected, preview.preview_token, operation_id)
    assert saved_content(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_second_carryover")
    apply_carryover(db, SOURCE, selected, preview.preview_token, operation_id)
    assert len(list_placements(db)) == 2 and len(rows(db, "carryover_operations")) == 1


def test_carryover_receipt_failure_rolls_back_all_saved_destinations(db: Database) -> None:
    first, second = create_task(db, "First"), create_task(db, "Second")
    for task in (first, second):
        create_placement(db, task.id, "2026-10-15")
    closed(db)
    selected = selections((first.id, "2026-10-20"), (second.id, "2026-10-21"))
    preview = preview_carryover(db, SOURCE, selected)
    operation_id = str(uuid4())
    before = saved_content(db)
    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON carryover_operations BEGIN SELECT RAISE(ABORT, 'injected receipt failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="injected receipt failure"):
        apply_carryover(db, SOURCE, selected, preview.preview_token, operation_id)
    assert saved_content(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_receipt")
    apply_carryover(db, SOURCE, selected, preview.preview_token, operation_id)
    assert len(list_placements(db)) == 2


def test_carryover_following_week_crosses_year_as_calendar_dates(db: Database) -> None:
    task = create_task(db, "Year boundary")
    create_placement(db, task.id, "2026-12-31")
    closed(db, "2026-12-28")
    carried(db, selections((task.id, "2027-01-10")), week="2026-12-28")
    assert list_placements(db)[0].planned_date == date(2027, 1, 10)


def test_last_representable_week_can_close_but_carryover_fails_actionably(db: Database) -> None:
    task = create_task(db, "End of date range")
    create_placement(db, task.id, "9999-12-26")
    assert closed(db, "9999-12-20")
    before = saved_content(db)
    with pytest.raises(InvalidInput):
        get_carryover(db, "9999-12-20")
    assert saved_content(db) == before


def test_schema_four_upgrade_preserves_all_task_project_and_placement_fields(tmp_path: Path) -> None:
    db = Database(tmp_path / "schema-four.sqlite3")
    migrate(db, load_migrations()[:4])
    project = create_project(db, "Keep project")
    parent = create_task(db, "Keep parent", project_id=project.id)
    child = create_task(db, "Keep child", parent_id=parent.id, deadline="2026-10-30", notes="Keep notes", estimate_minutes=25)
    set_task_completion(db, child.id, True)
    # Use SQL for the genuine previous schema; newer domain functions may read new tables.
    with db.write() as conn:
        conn.execute(
            "INSERT INTO planned_items (id, task_id, planned_date, created_at, updated_at, revision) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid4()), child.id, "2026-10-15", "2026-10-14T10:00:00.123456Z", "2026-10-14T11:00:00.123456Z", 7),
        )
    before = {table: rows(db, table) for table in ("tasks", "projects", "planned_items")}
    migrate(db)
    reopened = open_database(db.path)
    assert current_version(reopened) == len(load_migrations())
    assert {table: rows(reopened, table) for table in before} == before
    assert rows(reopened, "closed_weeks") == rows(reopened, "closed_placements") == rows(reopened, "carryover_operations") == []
    with reopened.read() as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_failed_history_migration_preserves_schema_four_records_and_can_retry(tmp_path: Path) -> None:
    db = Database(tmp_path / "schema-four-retry.sqlite3")
    migrations = load_migrations()
    migrate(db, migrations[:4])
    task = create_task(db, "Keep saved work", notes="Keep notes", deadline="2026-10-30")
    with db.write() as conn:
        conn.execute(
            "INSERT INTO planned_items (id, task_id, planned_date, created_at, updated_at, revision) VALUES (?, ?, '2026-10-15', '2026-10-14T10:00:00.000000Z', '2026-10-14T10:00:00.000000Z', 1)",
            (str(uuid4()), task.id),
        )
    before = {table: rows(db, table) for table in ("tasks", "projects", "planned_items")}
    migration = migrations[4]
    broken = Migration(migration.version, migration.name, migration.sql + "\nINSERT INTO nonexistent VALUES (1);")
    with pytest.raises(MigrationError, match="rolled back"):
        migrate(db, [*migrations[:4], broken])
    assert current_version(db) == 4
    assert {table: rows(db, table) for table in before} == before
    with db.read() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert not {"closed_weeks", "closed_placements", "carryover_operations"} & tables
    migrate(db)
    assert {table: rows(db, table) for table in before} == before
    assert dumped(closed(db))["total"] == 1


def api_close(client: TestClient, week: str = SOURCE) -> dict:
    response = client.get(f"/api/weeks/{week}/close-preview")
    assert response.status_code == 200
    response = client.post(f"/api/weeks/{week}/close", json={"preview_token": response.json()["preview_token"]})
    assert response.status_code == 200
    return response.json()


def test_http_close_and_carryover_expose_history_alongside_current_status(client: TestClient, db: Database) -> None:
    task = create_task(db, "Snapshot title", deadline="2026-10-30", notes="Snapshot notes")
    create_placement(db, task.id, "2026-10-15")
    history = api_close(client)
    assert history["completed"] == 0 and history["total"] == 1
    selected = selections((task.id, "2026-10-20"))
    options = client.get(f"/api/weeks/{SOURCE}/carryover")
    assert options.status_code == 200
    preview = client.post(f"/api/weeks/{SOURCE}/carryover-preview", json={"selections": selected})
    assert preview.status_code == 200
    payload = {"selections": selected, "preview_token": preview.json()["preview_token"], "operation_id": str(uuid4())}
    carried_response = client.post(f"/api/weeks/{SOURCE}/carryover", json=payload)
    assert carried_response.status_code == 200
    assert client.post(f"/api/weeks/{SOURCE}/carryover", json=payload).json() == carried_response.json()
    set_task_completion(db, task.id, True)
    update_task(db, task.id, title="Current title")
    planning = client.get("/api/planning", params={"week": SOURCE}).json()
    assert planning["closed_week"] == history
    assert planning["tasks"][0]["completed"] is True and planning["tasks"][0]["title"] == "Current title"
    assert planning["closed_week"]["tasks"][0]["completed"] is False
    assert planning["closed_week"]["tasks"][0]["title"] == "Snapshot title"
    assert any(item["week_start"] == SOURCE for item in planning["closed_weeks"])
    assert planning["placements"][0]["task_id"] == task.id
    assert planning["placements"][0]["planned_date"] == "2026-10-20"


@pytest.mark.parametrize("method,path,payload", [
    ("POST", "/api/placements", {"task_id": "{unplanned}", "planned_date": "2026-10-15"}),
    ("PATCH", "/api/placements/{archived}", {"planned_date": "2026-10-22"}),
    ("PATCH", "/api/placements/{archived}", {"planned_date": "2026-10-15"}),
    ("DELETE", "/api/placements/{archived}", None),
    ("PATCH", "/api/placements/{active}", {"planned_date": "2026-10-15"}),
])
def test_http_closed_scheduling_is_read_only_with_structured_conflict(client: TestClient, db: Database, method, path, payload) -> None:
    task = create_task(db, "Historical work")
    archived = create_placement(db, task.id, "2026-10-15")
    api_close(client)
    unplanned = create_task(db, "Backlog")
    active_task = create_task(db, "Future work")
    active = create_placement(db, active_task.id, "2026-10-22")
    path = path.format(archived=archived.id, active=active.id)
    if payload:
        payload = {key: unplanned.id if value == "{unplanned}" else value for key, value in payload.items()}
    before = saved_content(db)
    response = client.request(method, path, json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "week_conflict"
    assert "closed" in response.json()["error"]["message"].lower()
    assert saved_content(db) == before


@pytest.mark.parametrize("endpoint,payload", [
    ("close", {}), ("close", {"preview_token": None}), ("close", {"preview_token": "x", "reopen": True}),
    ("carryover-preview", {}), ("carryover-preview", {"selections": None}),
    ("carryover-preview", {"selections": [{"task_id": 1, "planned_date": "2026-10-20"}]}),
    ("carryover", {"selections": [], "preview_token": "x"}),
    ("carryover", {"selections": [], "preview_token": "x", "operation_id": None}),
])
def test_http_invalid_week_mutation_payloads_use_structured_errors(client: TestClient, db: Database, endpoint, payload) -> None:
    before = saved_content(db)
    response = client.post(f"/api/weeks/{SOURCE}/{endpoint}", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert response.json()["error"]["message"]
    assert saved_content(db) == before


@pytest.mark.parametrize("endpoint", ["close-preview", "carryover"])
@pytest.mark.parametrize("week", ["20261015", "2026-02-30", "9999-12-31"])
def test_http_invalid_week_dates_are_actionable(client: TestClient, endpoint, week) -> None:
    response = client.get(f"/api/weeks/{week}/{endpoint}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


@pytest.mark.parametrize("endpoint", ["close", "carryover-preview", "carryover"])
@pytest.mark.parametrize("headers,status", [({"Origin": "https://evil.example"}, 403), ({"Host": "evil.example"}, 400)])
def test_week_mutations_retain_loopback_and_same_origin_protection(client: TestClient, db: Database, endpoint, headers, status) -> None:
    before = saved_content(db)
    response = client.post(f"/api/weeks/{SOURCE}/{endpoint}", json={}, headers=headers)
    assert response.status_code == status
    assert saved_content(db) == before


@pytest.mark.parametrize("operation", ["close", "carryover"])
def test_locked_week_save_is_actionable_atomic_and_retryable(client: TestClient, db: Database, monkeypatch, operation) -> None:
    from backend.storage import db as storage

    task = create_task(db, "Keep saved data")
    create_placement(db, task.id, "2026-10-15")
    if operation == "close":
        preview = client.get(f"/api/weeks/{SOURCE}/close-preview").json()
        payload = {"preview_token": preview["preview_token"]}
    else:
        api_close(client)
        selected = selections((task.id, "2026-10-20"))
        preview = client.post(f"/api/weeks/{SOURCE}/carryover-preview", json={"selections": selected}).json()
        payload = {"selections": selected, "preview_token": preview["preview_token"], "operation_id": str(uuid4())}
    before = saved_content(db)
    monkeypatch.setattr(storage, "BUSY_TIMEOUT_MS", 10)
    with db.read() as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        response = client.post(f"/api/weeks/{SOURCE}/{operation}", json=payload)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "storage_unavailable"
        assert "try again" in response.json()["error"]["message"]
        assert saved_content(db) == before
        blocker.execute("ROLLBACK")
    assert client.post(f"/api/weeks/{SOURCE}/{operation}", json=payload).status_code == 200
