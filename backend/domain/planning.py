"""Weekly planning application functions shared by the UI and future adapters.

A placement is one task on one date. Tasks, their completion, and their deadlines
are never cloned or changed by scheduling. All task/placement reads in a planning
snapshot share a SQLite read transaction.
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict

from backend.domain.errors import InvalidInput
from backend.domain.tasks import Task, _children_of, _list_tasks, _require_task
from backend.storage.db import Database, utc_now

_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


class Placement(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    task_id: str
    planned_date: date
    created_at: datetime
    updated_at: datetime
    revision: int


class PlanningSnapshot(BaseModel):
    today: date
    timezone: str
    week_start: date
    week_end: date
    tasks: list[Task]
    placements: list[Placement]


class PlacementConflict(InvalidInput):
    def __init__(self, planned_date: str) -> None:
        super().__init__(
            "planned_date",
            f"This task is already planned for {planned_date}. Choose another date or remove "
            "that placement first. Nothing was changed.",
        )


def _date(value: object, field: str = "planned_date") -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        raise InvalidInput(field, "Use a real date in YYYY-MM-DD form.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise InvalidInput(field, "Use a real date in YYYY-MM-DD form.") from None


def week_bounds(value: str | date) -> tuple[date, date]:
    """Normalize any date to its Monday–Sunday calendar week, without time arithmetic."""
    day = _date(value, "week")
    try:
        monday = day - timedelta(days=day.weekday())
        return monday, monday + timedelta(days=6)
    except OverflowError:
        raise InvalidInput("week", "That week is outside the supported calendar range.") from None


def application_today(now: datetime | None = None) -> tuple[date, str]:
    """Use configured IANA timezone, otherwise the OS local timezone at this instant.

    No timezone settings record exists yet. The system-local default deliberately
    uses astimezone() for each instant, including local DST changes, not a fixed
    offset captured when the service starts. Tests may pass an aware UTC clock.
    """
    instant = datetime.now(UTC) if now is None else now
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("The planning clock must be timezone-aware.")
    configured = os.environ.get("BEARPLANS_TIMEZONE", "").strip()
    if configured:
        try:
            local = instant.astimezone(ZoneInfo(configured))
        except (ZoneInfoNotFoundError, ValueError):
            raise InvalidInput(
                "timezone",
                "BEARPLANS_TIMEZONE must name an installed IANA timezone, such as "
                "America/Los_Angeles. Correct it or unset it to use system local time.",
            ) from None
        return local.date(), configured
    local = instant.astimezone()
    return local.date(), f"System local ({local.tzname()})"


def _placement(row: sqlite3.Row) -> Placement:
    return Placement(**dict(row))


def _require_placement(conn: sqlite3.Connection, placement_id: object) -> sqlite3.Row:
    if not isinstance(placement_id, str):
        raise InvalidInput("placement_id", "Placement id must be text.")
    row = conn.execute("SELECT * FROM planned_items WHERE id = ?", (placement_id,)).fetchone()
    if row is None:
        raise InvalidInput("placement_id", "This planned placement no longer exists. Refresh the plan.")
    return row


def _list_placements(conn: sqlite3.Connection) -> list[Placement]:
    return [_placement(row) for row in conn.execute(
        "SELECT * FROM planned_items ORDER BY planned_date, created_at, rowid"
    ).fetchall()]


def list_placements(db: Database) -> list[Placement]:
    with db.read() as conn:
        return _list_placements(conn)


def get_planning(db: Database, week: str | date | None = None, *, now: datetime | None = None) -> PlanningSnapshot:
    today, timezone = application_today(now)
    monday, sunday = week_bounds(today if week is None else week)
    with db.read() as conn:
        conn.execute("BEGIN")
        return PlanningSnapshot(
            today=today, timezone=timezone, week_start=monday, week_end=sunday,
            tasks=_list_tasks(conn), placements=_list_placements(conn),
        )


def _planned_date(value: object) -> str:
    day = _date(value)
    week_bounds(day)  # Every saved placement must have a representable full week.
    return day.isoformat()


def _require_leaf(conn: sqlite3.Connection, task_id: object) -> None:
    _require_task(conn, task_id)
    if _children_of(conn, task_id):
        raise InvalidInput("task_id", "Plan this task's subtasks instead. Parent tasks are shown as context.")


def _check_duplicate(conn: sqlite3.Connection, task_id: str, day: str, *, except_id: str = "") -> None:
    if conn.execute(
        "SELECT 1 FROM planned_items WHERE task_id = ? AND planned_date = ? AND id <> ?",
        (task_id, day, except_id),
    ).fetchone():
        raise PlacementConflict(day)


def create_placement(db: Database, task_id: str, planned_date: str | date) -> Placement:
    day = _planned_date(planned_date)
    now = utc_now()
    placement_id = str(uuid4())
    with db.write() as conn:
        _require_leaf(conn, task_id)
        _check_duplicate(conn, task_id, day)
        conn.execute(
            "INSERT INTO planned_items (id, task_id, planned_date, created_at, updated_at, revision) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            (placement_id, task_id, day, now, now),
        )
        return _placement(_require_placement(conn, placement_id))


def move_placement(db: Database, placement_id: str, planned_date: str | date) -> Placement:
    day = _planned_date(planned_date)
    with db.write() as conn:
        row = _require_placement(conn, placement_id)
        _require_leaf(conn, row["task_id"])
        _check_duplicate(conn, row["task_id"], day, except_id=placement_id)
        if row["planned_date"] != day:
            conn.execute(
                "UPDATE planned_items SET planned_date = ?, updated_at = ?, revision = revision + 1 WHERE id = ?",
                (day, utc_now(), placement_id),
            )
        return _placement(_require_placement(conn, placement_id))


def remove_placement(db: Database, placement_id: str) -> str:
    with db.write() as conn:
        _require_placement(conn, placement_id)
        conn.execute("DELETE FROM planned_items WHERE id = ?", (placement_id,))
    return placement_id
