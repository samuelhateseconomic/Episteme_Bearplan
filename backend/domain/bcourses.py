"""bCourses (Berkeley's Canvas) source: followed courses, cached assignments, reviewed adds.

User decisions (2026-11-01): read-only direct API; the user picks which courses to
follow; assignments wait in a review list and become tasks only when the user
chooses Add (in a project named after the course, with the due date and a link);
assignments without a due date are listed and can still be added.

Fetching happens outside any transaction; one short write then stores the result.
Source fields are refreshed from bCourses, while the user's task (title, notes,
subtasks, plans, completion) is never changed by a refresh. A later due-date change
is shown for review; only "Use new due date" changes the task's deadline.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import date, datetime
from typing import Any, Protocol

from pydantic import BaseModel

from backend.domain.calendar import ApplicationCalendar
from backend.domain.errors import InvalidInput
from backend.domain.projects import NAME_MAX_LENGTH, _create_project_tx
from backend.domain.tasks import TITLE_MAX_LENGTH, Task, _create_task_tx, _read_task, _update_task_tx
from backend.storage.db import Database, utc_now

SOURCE = "bcourses"


class Client(Protocol):
    def courses(self) -> list[dict[str, Any]]: ...
    def assignments(self, course_id: str) -> list[dict[str, Any]]: ...


class Course(BaseModel):
    course_id: str
    name: str
    course_code: str
    term: str
    followed: bool
    in_source: bool
    project_id: str | None


class Assignment(BaseModel):
    assignment_id: str
    course_id: str
    course_name: str
    title: str
    due_at: str | None
    due_date: date | None
    html_url: str
    points_possible: float | None
    in_source: bool
    status: str  # new | added | dismissed
    task_id: str | None
    due_changed: bool
    accepted_due_date: date | None


class SyncStatus(BaseModel):
    last_attempt_at: str | None
    last_success_at: str | None
    last_error: str | None


class BCoursesState(BaseModel):
    configured: bool
    sync: SyncStatus
    courses: list[Course]
    assignments: list[Assignment]


class AddResult(BaseModel):
    assignment: Assignment
    task: Task
    project_created: bool


def _text(value: object, limit: int) -> str:
    return " ".join(str(value).split())[:limit] if value is not None else ""


def _instant(value: object) -> str | None:
    """bCourses timestamps are ISO-8601 UTC; keep valid ones, drop anything else."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return value if parsed.tzinfo is not None else None


def local_due_date(due_at: str | None) -> date | None:
    if due_at is None:
        return None
    instant = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
    return ApplicationCalendar.from_environment().localize(instant).date()


def _course_fields(raw: dict[str, Any]) -> dict[str, str] | None:
    course_id = str(raw.get("id") or "")
    if not course_id or len(course_id) > 40:
        return None
    code = _text(raw.get("course_code"), 100)
    term = raw.get("term") if isinstance(raw.get("term"), dict) else {}
    return {"course_id": course_id, "name": _text(raw.get("name"), 200) or code or f"Course {course_id}",
            "course_code": code, "term": _text(term.get("name"), 100)}


def _assignment_fields(raw: dict[str, Any]) -> dict[str, Any] | None:
    assignment_id = str(raw.get("id") or "")
    if not assignment_id or len(assignment_id) > 40:
        return None
    url = raw.get("html_url") if isinstance(raw.get("html_url"), str) else ""
    points = raw.get("points_possible")
    return {
        "assignment_id": assignment_id,
        "title": _text(raw.get("name"), 500) or "Untitled assignment",
        "due_at": _instant(raw.get("due_at")),
        # Only links back to bCourses itself are kept.
        "html_url": url if url.startswith("https://bcourses.berkeley.edu/") else "",
        "points_possible": float(points) if isinstance(points, (int, float)) and not isinstance(points, bool) else None,
        "source_updated_at": _instant(raw.get("updated_at")),
    }


def refresh(db: Database, client: Client, unavailable: type[Exception]) -> None:
    """Fetch courses, and assignments of followed courses, then store them in one short write.

    `unavailable` is the client's error type. On failure nothing in the cache
    changes except the recorded attempt and its message.
    """
    attempt = utc_now()
    try:
        courses = [fields for raw in client.courses() if (fields := _course_fields(raw))]
        with db.read() as conn:
            followed = {row["course_id"] for row in conn.execute("SELECT course_id FROM source_courses WHERE followed = 1")}
        fetched: dict[str, list[dict[str, Any]]] = {}
        for course in courses:
            if course["course_id"] in followed:
                fetched[course["course_id"]] = [
                    fields for raw in client.assignments(course["course_id"]) if (fields := _assignment_fields(raw))]
    except unavailable as error:
        message = getattr(error, "message", "bCourses could not be read.")
        with db.write() as conn:
            _record_sync(conn, attempt, success=False, error=message)
        raise
    with db.write() as conn:
        _store(conn, courses, fetched, attempt)
        _record_sync(conn, attempt, success=True, error=None)


def _record_sync(conn: sqlite3.Connection, attempt: str, *, success: bool, error: str | None) -> None:
    conn.execute(
        "INSERT INTO source_sync (source, last_attempt_at, last_success_at, last_error) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(source) DO UPDATE SET last_attempt_at = excluded.last_attempt_at,"
        " last_success_at = COALESCE(excluded.last_success_at, source_sync.last_success_at),"
        " last_error = excluded.last_error",
        (SOURCE, attempt, attempt if success else None, error))


def _store(conn: sqlite3.Connection, courses: list[dict[str, str]],
           fetched: dict[str, list[dict[str, Any]]], now: str) -> None:
    seen = [course["course_id"] for course in courses]
    for course in courses:
        conn.execute(
            "INSERT INTO source_courses (course_id, name, course_code, term, in_source, fetched_at)"
            " VALUES (:course_id, :name, :course_code, :term, 1, :now)"
            " ON CONFLICT(course_id) DO UPDATE SET name = excluded.name, course_code = excluded.course_code,"
            " term = excluded.term, in_source = 1, fetched_at = excluded.fetched_at",
            {**course, "now": now})
    conn.execute(f"UPDATE source_courses SET in_source = 0 WHERE course_id NOT IN ({','.join('?' * len(seen))})", seen)
    for course_id, assignments in fetched.items():
        ids = [item["assignment_id"] for item in assignments]
        for item in assignments:
            conn.execute(
                "INSERT INTO source_assignments (assignment_id, course_id, title, due_at, html_url, points_possible,"
                " source_updated_at, in_source, fetched_at)"
                " VALUES (:assignment_id, :course_id, :title, :due_at, :html_url, :points_possible,"
                " :source_updated_at, 1, :now)"
                " ON CONFLICT(assignment_id) DO UPDATE SET course_id = excluded.course_id, title = excluded.title,"
                " due_at = excluded.due_at, html_url = excluded.html_url, points_possible = excluded.points_possible,"
                " source_updated_at = excluded.source_updated_at, in_source = 1, fetched_at = excluded.fetched_at",
                {**item, "course_id": course_id, "now": now})
        conn.execute(
            f"UPDATE source_assignments SET in_source = 0 WHERE course_id = ? AND assignment_id NOT IN ({','.join('?' * len(ids))})",
            (course_id, *ids))


def set_followed(db: Database, course_ids: Iterable[str]) -> None:
    chosen = set(course_ids)
    with db.write() as conn:
        known = {row["course_id"] for row in conn.execute("SELECT course_id FROM source_courses")}
        unknown = chosen - known
        if unknown:
            raise InvalidInput("course_ids", "One of those courses is not in the bCourses list. Choose Refresh, then try again.")
        conn.execute("UPDATE source_courses SET followed = 0 WHERE followed = 1")
        conn.executemany("UPDATE source_courses SET followed = 1 WHERE course_id = ?", [(c,) for c in chosen])


def _effective_status(row: sqlite3.Row) -> str:
    # A task removed later (assistant Undo) leaves the assignment available again.
    return "new" if row["status"] == "added" and row["task_id"] is None else row["status"]


def _assignment(row: sqlite3.Row) -> Assignment:
    status = _effective_status(row)
    due, accepted = local_due_date(row["due_at"]), local_due_date(row["accepted_due_at"])
    return Assignment(
        assignment_id=row["assignment_id"], course_id=row["course_id"], course_name=row["course_name"],
        title=row["title"], due_at=row["due_at"], due_date=due, html_url=row["html_url"],
        points_possible=row["points_possible"], in_source=bool(row["in_source"]), status=status,
        task_id=row["task_id"] if status == "added" else None,
        due_changed=status == "added" and due != accepted, accepted_due_date=accepted if status == "added" else None)


_ASSIGNMENT_SQL = ("SELECT a.*, c.name AS course_name FROM source_assignments a"
                   " JOIN source_courses c ON c.course_id = a.course_id")


def get_state(db: Database, configured: bool) -> BCoursesState:
    with db.read() as conn:
        sync = conn.execute("SELECT * FROM source_sync WHERE source = ?", (SOURCE,)).fetchone()
        courses = conn.execute("SELECT * FROM source_courses ORDER BY in_source DESC, name, course_id").fetchall()
        rows = conn.execute(_ASSIGNMENT_SQL + " WHERE c.followed = 1"
                            " ORDER BY a.due_at IS NULL, a.due_at, c.name, a.title").fetchall()
    return BCoursesState(
        configured=configured,
        sync=SyncStatus(last_attempt_at=sync["last_attempt_at"] if sync else None,
                        last_success_at=sync["last_success_at"] if sync else None,
                        last_error=sync["last_error"] if sync else None),
        courses=[Course(course_id=r["course_id"], name=r["name"], course_code=r["course_code"], term=r["term"],
                        followed=bool(r["followed"]), in_source=bool(r["in_source"]), project_id=r["project_id"])
                 for r in courses],
        assignments=[_assignment(row) for row in rows])


def _require_assignment(conn: sqlite3.Connection, assignment_id: object) -> sqlite3.Row:
    if not isinstance(assignment_id, str):
        raise InvalidInput("assignment_id", "Assignment id must be text.")
    row = conn.execute(_ASSIGNMENT_SQL + " WHERE a.assignment_id = ?", (assignment_id,)).fetchone()
    if row is None:
        raise InvalidInput("assignment_id", "That bCourses assignment is not in the list. Choose Refresh, then try again.")
    return row


def add_assignment(db: Database, assignment_id: str) -> AddResult:
    """Create the task for one reviewed assignment. Adding it twice returns the same task."""
    with db.write() as conn:
        row = _require_assignment(conn, assignment_id)
        if _effective_status(row) == "added":
            return AddResult(assignment=_assignment(row), task=_read_task(conn, row["task_id"]), project_created=False)
        course = conn.execute("SELECT * FROM source_courses WHERE course_id = ?", (row["course_id"],)).fetchone()
        project_id, created = course["project_id"], False
        if project_id is None or conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone() is None:
            project_id, created = _create_project_tx(conn, course["name"][:NAME_MAX_LENGTH]).id, True
            conn.execute("UPDATE source_courses SET project_id = ? WHERE course_id = ?", (project_id, course["course_id"]))
        notes = f"From bCourses: {row['html_url']}" if row["html_url"] else "From bCourses."
        task = _create_task_tx(conn, row["title"][:TITLE_MAX_LENGTH], project_id=project_id, notes=notes,
                               deadline=local_due_date(row["due_at"]))
        conn.execute(
            "UPDATE source_assignments SET status = 'added', task_id = ?, accepted_due_at = ?, decided_at = ?"
            " WHERE assignment_id = ?", (task.id, row["due_at"], utc_now(), assignment_id))
        stored = _require_assignment(conn, assignment_id)
    return AddResult(assignment=_assignment(stored), task=task, project_created=created)


def set_dismissed(db: Database, assignment_id: str, dismissed: bool) -> Assignment:
    with db.write() as conn:
        row = _require_assignment(conn, assignment_id)
        if _effective_status(row) == "added":
            raise InvalidInput("assignment_id", "This assignment is already a task. Nothing was changed.")
        conn.execute("UPDATE source_assignments SET status = ?, task_id = NULL, decided_at = ? WHERE assignment_id = ?",
                     ("dismissed" if dismissed else "new", utc_now(), assignment_id))
        return _assignment(_require_assignment(conn, assignment_id))


def resolve_due_change(db: Database, assignment_id: str, use_new: bool) -> Assignment:
    """Use bCourses' new due date as the task deadline, or keep the task's own; either way stop flagging it."""
    with db.write() as conn:
        row = _require_assignment(conn, assignment_id)
        if _effective_status(row) != "added":
            raise InvalidInput("assignment_id", "This assignment is not a task, so there is no due date to update.")
        if use_new:
            _update_task_tx(conn, row["task_id"], {"deadline": local_due_date(row["due_at"])})
        conn.execute("UPDATE source_assignments SET accepted_due_at = ?, decided_at = ? WHERE assignment_id = ?",
                     (row["due_at"], utc_now(), assignment_id))
        return _assignment(_require_assignment(conn, assignment_id))
