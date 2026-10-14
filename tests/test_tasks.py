import threading
from datetime import date, datetime
from pathlib import Path
from uuid import UUID

import pytest

from backend.domain.errors import InvalidInput
from backend.domain.projects import create_project
from backend.domain.tasks import (
    ESTIMATE_MAX_MINUTES,
    TITLE_MAX_LENGTH,
    create_task,
    get_task,
    list_tasks,
    set_task_completion,
    update_task,
)
from backend.storage.db import Database, open_database


def test_create_returns_stored_task(db: Database) -> None:
    task = create_task(db, "  Read chapter 4  ")
    assert task.title == "Read chapter 4"
    assert UUID(task.id).version == 4
    assert task.revision == 1
    assert task.created_at == task.updated_at
    assert task.created_at.utcoffset().total_seconds() == 0
    assert list_tasks(db) == [task]


def test_list_is_empty_initially(db: Database) -> None:
    assert list_tasks(db) == []


def test_list_keeps_creation_order(db: Database) -> None:
    titles = [f"Task {i}" for i in range(20)]
    for title in titles:
        create_task(db, title)
    assert [t.title for t in list_tasks(db)] == titles


@pytest.mark.parametrize("title", ["", "   ", "\n\t", "​", "﻿", " ​　  ", " "])
def test_rejects_blank_title(db: Database, title: str) -> None:
    with pytest.raises(InvalidInput) as excinfo:
        create_task(db, title)
    assert excinfo.value.field == "title"
    assert list_tasks(db) == []


def test_title_length_limit(db: Database) -> None:
    assert create_task(db, "x" * TITLE_MAX_LENGTH).title == "x" * TITLE_MAX_LENGTH
    with pytest.raises(InvalidInput):
        create_task(db, "x" * (TITLE_MAX_LENGTH + 1))
    assert len(list_tasks(db)) == 1


def test_trims_invisible_edges_but_keeps_inner_text(db: Database) -> None:
    assert create_task(db, "﻿​Essay​ draft​ ").title == "Essay​ draft"


def test_rejects_unencodable_lone_surrogate(db: Database) -> None:
    with pytest.raises(InvalidInput, match="cannot be saved"):
        create_task(db, "a\ud800b")
    assert list_tasks(db) == []


def test_rejects_non_text_title(db: Database) -> None:
    with pytest.raises(InvalidInput):
        create_task(db, 42)  # type: ignore[arg-type]


def test_unicode_and_sql_like_text_round_trip(db: Database) -> None:
    title = "Bài tập 📚 '); DROP TABLE tasks; --"
    create_task(db, title)
    assert [t.title for t in list_tasks(db)] == [title]


def test_tasks_persist_across_database_reopen(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3"
    created = create_task(open_database(path), "Problem set 2")
    assert list_tasks(open_database(path)) == [created]


def test_concurrent_creates_are_all_saved_with_unique_ids(db: Database) -> None:
    errors: list[BaseException] = []

    def worker(n: int) -> None:
        try:
            for i in range(10):
                create_task(db, f"worker {n} task {i}")
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    tasks = list_tasks(db)
    assert len(tasks) == 80
    assert len({t.id for t in tasks}) == 80


# --------------------------------------------------------------------------- M1: subtasks


def test_subtask_takes_its_parents_project(db: Database) -> None:
    project = create_project(db, "Math 55")
    parent = create_task(db, "Write PS7", project_id=project.id)
    child = create_task(db, "read ch.4", parent_id=parent.id)

    assert child.parent_id == parent.id
    assert child.project_id == project.id


def test_subtasks_cannot_nest_further(db: Database) -> None:
    parent = create_task(db, "Write PS7")
    child = create_task(db, "read ch.4", parent_id=parent.id)

    with pytest.raises(InvalidInput) as excinfo:
        create_task(db, "too deep", parent_id=child.id)
    assert excinfo.value.field == "parent_id"
    # One level of nesting is what makes a parent cycle impossible to build.
    assert len(list_tasks(db)) == 2


def test_subtask_cannot_name_a_different_project(db: Database) -> None:
    math = create_project(db, "Math 55")
    cs = create_project(db, "CS 61A")
    parent = create_task(db, "Write PS7", project_id=math.id)

    with pytest.raises(InvalidInput):
        create_task(db, "wrong project", parent_id=parent.id, project_id=cs.id)
    assert len(list_tasks(db, cs.id)) == 0


def test_rejects_unknown_parent(db: Database) -> None:
    with pytest.raises(InvalidInput) as excinfo:
        create_task(db, "orphan", parent_id="00000000-0000-4000-8000-000000000000")
    assert excinfo.value.field == "parent_id"
    assert list_tasks(db) == []


def test_list_puts_each_parent_before_its_own_subtasks(db: Database) -> None:
    first = create_task(db, "Write PS7")
    second = create_task(db, "Read paper")
    create_task(db, "read ch.4", parent_id=first.id)
    create_task(db, "take notes", parent_id=second.id)

    assert [t.title for t in list_tasks(db)] == ["Write PS7", "read ch.4", "Read paper", "take notes"]


# --------------------------------------------------------------------------- M1: editing


def test_edit_changes_only_what_is_supplied(db: Database) -> None:
    task = create_task(db, "Write PS7", notes="first pass", estimate_minutes=30)
    edited = update_task(db, task.id, title="Write PS7 (final)")

    assert edited.title == "Write PS7 (final)"
    assert edited.notes == "first pass"
    assert edited.estimate_minutes == 30
    assert edited.revision == task.revision + 1


def test_edit_can_clear_optional_fields(db: Database) -> None:
    task = create_task(db, "Write PS7", notes="x", deadline="2026-10-20", estimate_minutes=30)
    cleared = update_task(db, task.id, notes=None, deadline=None, estimate_minutes=None)

    assert (cleared.notes, cleared.deadline, cleared.estimate_minutes) == ("", None, None)


def test_a_rejected_field_leaves_no_partial_change(db: Database) -> None:
    task = create_task(db, "Write PS7")
    with pytest.raises(InvalidInput):
        update_task(db, task.id, title="Changed", estimate_minutes=0)

    unchanged = get_task(db, task.id)
    assert unchanged.title == "Write PS7"
    assert unchanged.revision == task.revision


@pytest.mark.parametrize("deadline", ["2026-13-45", "2026-02-30", "20261020", "tomorrow", "2026-1-2"])
def test_rejects_impossible_deadline(db: Database, deadline: str) -> None:
    task = create_task(db, "Write PS7")
    with pytest.raises(InvalidInput) as excinfo:
        update_task(db, task.id, deadline=deadline)
    assert excinfo.value.field == "deadline"


@pytest.mark.parametrize("estimate", [0, -5, ESTIMATE_MAX_MINUTES + 1, True, 1.5, "30"])
def test_rejects_impossible_estimate(db: Database, estimate: object) -> None:
    task = create_task(db, "Write PS7")
    with pytest.raises(InvalidInput) as excinfo:
        update_task(db, task.id, estimate_minutes=estimate)
    assert excinfo.value.field == "estimate_minutes"


def test_deadline_is_stored_as_a_plain_date(db: Database) -> None:
    task = create_task(db, "Write PS7", deadline="2026-10-20")
    assert task.deadline == date(2026, 10, 20)
    with db.read() as conn:
        assert conn.execute("SELECT deadline FROM tasks WHERE id = ?", (task.id,)).fetchone()[0] == "2026-10-20"


# --------------------------------------------------------------------------- M1: completion


def test_a_task_without_subtasks_completes_and_reopens(db: Database) -> None:
    task = create_task(db, "Write PS7")
    assert task.completed is False

    done = set_task_completion(db, task.id, True)
    assert done.completed is True and done.completed_at is not None

    reopened = set_task_completion(db, task.id, False)
    assert reopened.completed is False and reopened.completed_at is None


def test_a_parent_cannot_be_completed_directly(db: Database) -> None:
    parent = create_task(db, "Write PS7")
    create_task(db, "read ch.4", parent_id=parent.id)

    with pytest.raises(InvalidInput) as excinfo:
        set_task_completion(db, parent.id, True)
    assert excinfo.value.field == "complete"
    assert get_task(db, parent.id).completed is False


def test_a_parent_is_complete_exactly_when_its_subtasks_are(db: Database) -> None:
    parent = create_task(db, "Write PS7")
    first = create_task(db, "read ch.4", parent_id=parent.id)
    second = create_task(db, "draft proof", parent_id=parent.id)

    set_task_completion(db, first.id, True)
    partial = get_task(db, parent.id)
    assert partial.completed is False
    assert (partial.completed_subtask_count, partial.subtask_count) == (1, 2)

    set_task_completion(db, second.id, True)
    whole = get_task(db, parent.id)
    assert whole.completed is True
    # The parent's completion time is when the last subtask was finished.
    assert whole.completed_at == get_task(db, second.id).completed_at

    set_task_completion(db, second.id, False)
    assert get_task(db, parent.id).completed is False


def test_a_completed_task_that_gains_a_subtask_becomes_derived(db: Database) -> None:
    task = create_task(db, "Write PS7")
    set_task_completion(db, task.id, True)

    create_task(db, "oh wait, one more step", parent_id=task.id)

    now_derived = get_task(db, task.id)
    assert now_derived.completed is False
    assert now_derived.completed_at is None
    with db.read() as conn:
        stored = conn.execute("SELECT completed_at FROM tasks WHERE id = ?", (task.id,)).fetchone()[0]
    # The stale stored value is cleared, not merely ignored on read.
    assert stored is None


def test_completion_must_be_a_boolean(db: Database) -> None:
    task = create_task(db, "Write PS7")
    with pytest.raises(InvalidInput):
        set_task_completion(db, task.id, "yes")  # type: ignore[arg-type]


def test_parent_completion_time_ignores_stored_timestamp_precision(db: Database) -> None:
    """Instants are compared as instants, not as strings.

    '...283Z' and '...283000Z' are the same moment, but the first sorts after the second
    because 'Z' > '0'. A future migration writing millisecond precision must not make a
    parent report the wrong completion time.
    """
    parent = create_task(db, "Write PS7")
    early = create_task(db, "read ch.4", parent_id=parent.id)
    late = create_task(db, "draft proof", parent_id=parent.id)
    set_task_completion(db, early.id, True)
    set_task_completion(db, late.id, True)

    with db.write() as conn:
        # The later subtask, written at millisecond precision as migration SQL would.
        conn.execute("UPDATE tasks SET completed_at = '2026-10-14T05:36:37.283Z' WHERE id = ?", (late.id,))
        conn.execute("UPDATE tasks SET completed_at = '2026-10-14T05:36:37.100000Z' WHERE id = ?", (early.id,))

    assert get_task(db, parent.id).completed_at == datetime.fromisoformat("2026-10-14T05:36:37.283Z")


def test_repeating_a_completion_does_not_move_the_recorded_instant(db: Database) -> None:
    """A retried request must not shift a parent's derived completion time."""
    parent = create_task(db, "Write PS7")
    child = create_task(db, "read ch.4", parent_id=parent.id)

    first = set_task_completion(db, child.id, True)
    again = set_task_completion(db, child.id, True)

    assert again.completed_at == first.completed_at
    assert again.revision == first.revision
    assert get_task(db, parent.id).completed_at == first.completed_at


def test_repeating_a_reopen_is_also_a_no_op(db: Database) -> None:
    task = create_task(db, "Write PS7")
    before = set_task_completion(db, task.id, False)
    assert before.revision == task.revision
    assert before.completed_at is None


@pytest.mark.parametrize("complete", [False, True])
def test_parent_controls_never_change_children(db: Database, complete: bool) -> None:
    parent = create_task(db, "Container")
    child = create_task(db, "Work", parent_id=parent.id)
    set_task_completion(db, child.id, True)
    before = list_tasks(db)
    with pytest.raises(InvalidInput):
        set_task_completion(db, parent.id, complete)
    assert list_tasks(db) == before


@pytest.mark.parametrize("child_complete", [False, True])
def test_removing_last_child_returns_incomplete_leaf(db: Database, child_complete: bool) -> None:
    from backend.domain.tasks import completion_progress, remove_subtask

    parent = create_task(db, "Container", notes="Keep this", deadline="2026-10-20", estimate_minutes=30)
    set_task_completion(db, parent.id, True)
    child = create_task(db, "Work", parent_id=parent.id)
    set_task_completion(db, child.id, child_complete)
    returned = remove_subtask(db, child.id)
    assert returned.id == parent.id
    assert returned.completed is False and returned.completed_at is None
    assert returned.subtask_count == 0
    assert (returned.notes, returned.deadline, returned.estimate_minutes) == ("Keep this", date(2026, 10, 20), 30)
    assert list_tasks(db) == [returned]
    assert completion_progress(list_tasks(db)).model_dump() == {"completed": 0, "total": 1}
    reopened_db = open_database(db.path)
    assert get_task(reopened_db, parent.id) == returned
    assert set_task_completion(reopened_db, parent.id, True).completed is True


def test_removing_unfinished_child_recomputes_remaining_completion(db: Database) -> None:
    from backend.domain.tasks import remove_subtask

    parent = create_task(db, "Container")
    done = create_task(db, "Done", parent_id=parent.id)
    unfinished = create_task(db, "Not needed", parent_id=parent.id)
    completed = set_task_completion(db, done.id, True)
    result = remove_subtask(db, unfinished.id)
    assert result.completed is True
    assert result.completed_at == completed.completed_at
    assert result.completed_subtask_count == result.subtask_count == 1


def test_removal_rejects_root_and_missing_task_without_changes(db: Database) -> None:
    from backend.domain.tasks import remove_subtask

    parent = create_task(db, "Keep")
    before = list_tasks(db)
    for task_id in [parent.id, "missing"]:
        with pytest.raises(InvalidInput):
            remove_subtask(db, task_id)
        assert list_tasks(db) == before


def test_leaf_counts_through_completion_addition_and_removal(db: Database) -> None:
    from backend.domain.tasks import completion_progress, remove_subtask

    standalone = create_task(db, "Standalone")
    parent = create_task(db, "Container")
    first = create_task(db, "First", parent_id=parent.id)
    second = create_task(db, "Second", parent_id=parent.id)
    set_task_completion(db, standalone.id, True)
    set_task_completion(db, first.id, True)
    assert completion_progress(list_tasks(db)).model_dump() == {"completed": 2, "total": 3}
    set_task_completion(db, second.id, True)
    assert completion_progress(list_tasks(db)).model_dump() == {"completed": 3, "total": 3}
    third = create_task(db, "Additional parent work", parent_id=parent.id)
    assert get_task(db, parent.id).completed is False
    assert completion_progress(list_tasks(db)).model_dump() == {"completed": 3, "total": 4}
    remove_subtask(db, third.id)
    set_task_completion(db, second.id, False)
    assert completion_progress(list_tasks(db)).model_dump() == {"completed": 2, "total": 3}
