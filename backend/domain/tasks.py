"""Task application functions, including subtasks.

The interface, and later the assistant and connection adapters, all call these
functions; none of them write task rows directly.

A subtask is a task with a parent, not a separate record. Nesting is one level
deep: a subtask may not have subtasks of its own, which also makes a parent cycle
impossible to construct.

Completion rule (authoritative M1 product decision):
a task with no subtasks is complete when it is marked complete. A task that has
subtasks has no completion of its own -- it is complete exactly when every one of
its subtasks is, and its completion time is when the last of them was completed.
Marking such a task complete directly is rejected rather than silently ignored.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from backend.domain.errors import InvalidInput
from backend.domain.projects import default_project_id, require_project
from backend.domain.text import clean_text
from backend.storage.db import Database, utc_now

TITLE_MAX_LENGTH = 200
NOTES_MAX_LENGTH = 2000
ESTIMATE_MIN_MINUTES = 1
ESTIMATE_MAX_MINUTES = 10080  # seven days; a planning estimate, not a timer limit

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class _Unset:
    """Marks an argument the caller did not supply, which is not the same as None."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "UNSET"


UNSET: Any = _Unset()


class Task(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    project_id: str
    parent_id: str | None
    title: str
    notes: str
    deadline: date | None
    estimate_minutes: int | None
    completed: bool
    completed_at: datetime | None
    subtask_count: int
    completed_subtask_count: int
    created_at: datetime
    updated_at: datetime
    revision: int

    @property
    def is_parent(self) -> bool:
        return self.subtask_count > 0


class TaskNotFound(InvalidInput):
    def __init__(self, task_id: str, field: str = "task_id") -> None:
        super().__init__(field, f"No task with id {task_id}.")


class CompletionProgress(BaseModel):
    completed: int
    total: int


def completion_progress(tasks: list[Task]) -> CompletionProgress:
    """Count leaf work once. Containers contribute neither numerator nor denominator."""
    leaves = [task for task in tasks if not task.is_parent]
    return CompletionProgress(completed=sum(task.completed for task in leaves), total=len(leaves))


# --------------------------------------------------------------------------- validation


def _clean_title(title: object) -> str:
    return clean_text(
        title,
        "title",
        max_length=TITLE_MAX_LENGTH,
        required=True,
        empty_message="Enter a task title.",
        long_message=f"Keep the title to {TITLE_MAX_LENGTH} characters or fewer.",
    )


def _clean_notes(notes: object) -> str:
    if notes is None:
        return ""
    return clean_text(
        notes,
        "notes",
        max_length=NOTES_MAX_LENGTH,
        required=False,
        empty_message="",
        long_message=f"Keep notes to {NOTES_MAX_LENGTH} characters or fewer.",
    )


def _clean_deadline(deadline: object) -> str | None:
    """A date, never an instant: a deadline of 'the 20th' does not move with a timezone."""
    if deadline is None:
        return None
    if isinstance(deadline, date) and not isinstance(deadline, datetime):
        return deadline.isoformat()
    if not isinstance(deadline, str):
        raise InvalidInput("deadline", "Use a date in YYYY-MM-DD form.")
    text = deadline.strip()
    if not text:
        return None
    # date.fromisoformat also accepts forms like '20261020'; require the one shape we store.
    if not _DATE_PATTERN.match(text):
        raise InvalidInput("deadline", "Use a date in YYYY-MM-DD form.")
    try:
        date.fromisoformat(text)
    except ValueError:
        raise InvalidInput("deadline", f"{text} is not a real date.") from None
    return text


def _clean_estimate(estimate: object) -> int | None:
    if estimate is None:
        return None
    # bool is a subclass of int; True must not become an estimate of one minute.
    if isinstance(estimate, bool) or not isinstance(estimate, int):
        raise InvalidInput("estimate_minutes", "Give the estimate as a whole number of minutes.")
    if not ESTIMATE_MIN_MINUTES <= estimate <= ESTIMATE_MAX_MINUTES:
        raise InvalidInput(
            "estimate_minutes",
            f"Estimates run from {ESTIMATE_MIN_MINUTES} to {ESTIMATE_MAX_MINUTES} minutes.",
        )
    return estimate


def _require_task(conn: sqlite3.Connection, task_id: object, field: str = "task_id") -> sqlite3.Row:
    if not isinstance(task_id, str):
        raise InvalidInput(field, "Task id must be text.")
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise TaskNotFound(task_id, field)
    return row


def _resolve_parent(conn: sqlite3.Connection, parent_id: object, task_id: str | None) -> sqlite3.Row:
    """Validate a proposed parent. One level of nesting, same project, never itself."""
    parent = _require_task(conn, parent_id, field="parent_id")
    if task_id is not None and parent["id"] == task_id:
        raise InvalidInput("parent_id", "A task cannot be its own subtask.")
    if parent["parent_id"] is not None:
        raise InvalidInput("parent_id", "Subtasks cannot have subtasks of their own.")
    return parent


# --------------------------------------------------------------------------- reading


def _hydrate(row: sqlite3.Row, children: list[sqlite3.Row]) -> Task:
    """Build a Task, deriving completion from subtasks when there are any."""
    if children:
        done = [c["completed_at"] for c in children if c["completed_at"] is not None]
        complete = len(done) == len(children)
        # Compare parsed instants, not the stored strings. Both '...283Z' (migration
        # strftime, milliseconds) and '...283000Z' (utc_now, microseconds) are valid
        # UTC ISO-8601, but '...283Z' sorts AFTER '...283000Z' because 'Z' > '0'.
        completed_at = max(done, key=datetime.fromisoformat) if complete else None
    else:
        completed_at = row["completed_at"]
        complete = completed_at is not None
    return Task(
        id=row["id"],
        project_id=row["project_id"],
        parent_id=row["parent_id"],
        title=row["title"],
        notes=row["notes"],
        deadline=date.fromisoformat(row["deadline"]) if row["deadline"] else None,
        estimate_minutes=row["estimate_minutes"],
        completed=complete,
        completed_at=datetime.fromisoformat(completed_at) if completed_at else None,
        subtask_count=len(children),
        completed_subtask_count=sum(1 for c in children if c["completed_at"] is not None),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        revision=row["revision"],
    )


def _children_of(conn: sqlite3.Connection, task_id: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM tasks WHERE parent_id = ? ORDER BY created_at, rowid", (task_id,)
    ).fetchall()


def _read_task(conn: sqlite3.Connection, task_id: str) -> Task:
    row = _require_task(conn, task_id)
    return _hydrate(row, _children_of(conn, task_id))


def get_task(db: Database, task_id: str) -> Task:
    with db.read() as conn:
        return _read_task(conn, task_id)


def list_tasks(db: Database, project_id: str | None = None) -> list[Task]:
    """Tasks oldest first, each parent immediately followed by its own subtasks."""
    with db.read() as conn:
        return _list_tasks(conn, project_id)


def _list_tasks(conn: sqlite3.Connection, project_id: str | None = None) -> list[Task]:
    """Read tasks using an existing transaction, including planning snapshots."""
    if project_id is None:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at, rowid").fetchall()
    else:
        require_project(conn, project_id)
        rows = conn.execute(
            "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at, rowid", (project_id,)
        ).fetchall()

    children: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        if row["parent_id"] is not None:
            children.setdefault(row["parent_id"], []).append(row)

    ordered: list[Task] = []
    for row in rows:
        if row["parent_id"] is not None:
            continue
        own = children.get(row["id"], [])
        ordered.append(_hydrate(row, own))
        ordered.extend(_hydrate(child, []) for child in own)
    return ordered


# --------------------------------------------------------------------------- writing


def _reject_tracked_structure_change(conn: sqlite3.Connection, task_id: str, field: str) -> None:
    # Upgrade tests also exercise genuine pre-timer schemas. Their tasks remain
    # usable before migration 6; current services always have this table.
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'timer_sessions'").fetchone()
    if exists and conn.execute(
        "SELECT 1 FROM timer_sessions WHERE task_id = ? AND state <> 'finished'", (task_id,)
    ).fetchone():
        raise InvalidInput(field, "This task has an unfinished countdown. Finish it in Track before changing its subtasks or removing it.")


def create_task(
    db: Database,
    title: str,
    *,
    project_id: str | None = None,
    parent_id: str | None = None,
    notes: str | None = None,
    deadline: str | date | None = None,
    estimate_minutes: int | None = None,
) -> Task:
    """Validate and save a new task or subtask; returns the stored record.

    Every value is validated before anything is written, so a rejected field
    leaves the database untouched.
    """
    cleaned_title = _clean_title(title)
    cleaned_notes = _clean_notes(notes)
    cleaned_deadline = _clean_deadline(deadline)
    cleaned_estimate = _clean_estimate(estimate_minutes)
    task_id = str(uuid4())
    now = utc_now()

    with db.write() as conn:
        if parent_id is not None:
            parent = _resolve_parent(conn, parent_id, task_id=None)
            _reject_tracked_structure_change(conn, parent_id, "parent_id")
            if conn.execute("SELECT 1 FROM planned_items WHERE task_id = ? LIMIT 1", (parent_id,)).fetchone():
                raise InvalidInput(
                    "parent_id",
                    "This task has planned dates. Remove its placements before adding subtasks, "
                    "then plan its subtasks instead.",
                )
            if project_id is not None and project_id != parent["project_id"]:
                raise InvalidInput("project_id", "A subtask belongs to the same project as its parent.")
            resolved_project = parent["project_id"]
        elif project_id is not None:
            resolved_project = require_project(conn, project_id)
        else:
            resolved_project = default_project_id(conn)

        conn.execute(
            "INSERT INTO tasks (id, project_id, parent_id, title, notes, deadline,"
            " estimate_minutes, completed_at, created_at, updated_at, revision)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, 1)",
            (
                task_id,
                resolved_project,
                parent_id,
                cleaned_title,
                cleaned_notes,
                cleaned_deadline,
                cleaned_estimate,
                now,
                now,
            ),
        )
        if parent_id is not None:
            # The parent's completion is derived from now on, so a stored one would be
            # stale. Clearing it here keeps the row honest about what it holds.
            conn.execute(
                "UPDATE tasks SET completed_at = NULL, updated_at = ?, revision = revision + 1"
                " WHERE id = ?",
                (now, parent_id),
            )
        return _read_task(conn, task_id)


def update_task(
    db: Database,
    task_id: str,
    *,
    title: Any = UNSET,
    notes: Any = UNSET,
    deadline: Any = UNSET,
    estimate_minutes: Any = UNSET,
) -> Task:
    """Edit a task's planning fields. Only supplied fields change.

    Passing None for notes, deadline or estimate_minutes clears that field; leaving
    an argument out leaves it alone. Every field is validated before any is written.
    """
    updates: dict[str, object] = {}
    if title is not UNSET:
        updates["title"] = _clean_title(title)
    if notes is not UNSET:
        updates["notes"] = _clean_notes(notes)
    if deadline is not UNSET:
        updates["deadline"] = _clean_deadline(deadline)
    if estimate_minutes is not UNSET:
        updates["estimate_minutes"] = _clean_estimate(estimate_minutes)

    with db.write() as conn:
        _require_task(conn, task_id)
        if not updates:
            return _read_task(conn, task_id)
        assignments = ", ".join(f"{column} = ?" for column in updates)
        conn.execute(
            f"UPDATE tasks SET {assignments}, updated_at = ?, revision = revision + 1 WHERE id = ?",
            (*updates.values(), utc_now(), task_id),
        )
        return _read_task(conn, task_id)


def set_task_completion(db: Database, task_id: str, complete: bool) -> Task:
    """Mark a task complete or incomplete.

    Rejected for a task that has subtasks: its completion is derived from theirs.
    """
    if not isinstance(complete, bool):
        raise InvalidInput("complete", "Completion must be true or false.")
    with db.write() as conn:
        row = _require_task(conn, task_id)
        if _children_of(conn, task_id):
            raise InvalidInput(
                "complete",
                "This task is complete when all of its subtasks are. Complete its subtasks instead.",
            )
        # Idempotent: repeating a completion must not move the recorded instant, or a
        # retried request would shift the derived completion time of its parent.
        if (row["completed_at"] is not None) == complete:
            return _read_task(conn, task_id)
        now = utc_now()
        conn.execute(
            "UPDATE tasks SET completed_at = ?, updated_at = ?, revision = revision + 1 WHERE id = ?",
            (now if complete else None, now, task_id),
        )
        if row["parent_id"] is not None:
            conn.execute(
                "UPDATE tasks SET updated_at = ?, revision = revision + 1 WHERE id = ?",
                (now, row["parent_id"]),
            )
        return _read_task(conn, task_id)


def remove_subtask(db: Database, task_id: str) -> Task:
    """Remove only a subtask and return its parent, in one transaction.

    Removing the last child leaves an incomplete standalone task. A former
    container never inherits a removed child's completion or restores an old one.
    General task/project deletion is outside this build.
    """
    with db.write() as conn:
        child = _require_task(conn, task_id)
        parent_id = child["parent_id"]
        if parent_id is None:
            raise InvalidInput("task_id", "Only subtasks can be removed in this build.")
        _reject_tracked_structure_change(conn, task_id, "task_id")
        if conn.execute("SELECT 1 FROM planned_items WHERE task_id = ? LIMIT 1", (task_id,)).fetchone():
            raise InvalidInput("task_id", "Remove this subtask's planned placements before deleting it.")
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.execute(
            "UPDATE tasks SET completed_at = NULL, updated_at = ?, revision = revision + 1 WHERE id = ?",
            (utc_now(), parent_id),
        )
        return _read_task(conn, parent_id)
