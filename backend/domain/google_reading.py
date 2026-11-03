"""Reading the user's own Google calendars: picker, cached events, event -> task.

User decisions (2026-11-02): the user picks which calendars BearPlans reads; their
events are shown beside each day, and any event can be turned into a task. BearPlans
never changes these calendars (read-only scopes; only GET is used here).

Implementation rules:
- The calendar BearPlans itself writes ("BearPlans") is not offered in the picker.
- Events from WINDOW_BEFORE days ago to WINDOW_AFTER days ahead are cached and replaced
  on each read; fetching happens outside any transaction, then one write stores it.
- "Add as task" creates a task in the default project named after the event, planned
  on the event's first day (when that week is open) without a start time, so it does
  not create a second calendar event. It is idempotent per event.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, timedelta
from typing import Any, Protocol

from pydantic import BaseModel

from backend.domain.calendar import ApplicationCalendar, application_today
from backend.domain.errors import InvalidInput
from backend.domain.planning import WeekConflict, _create_placement_tx
from backend.domain.projects import default_project_id
from backend.domain.tasks import TITLE_MAX_LENGTH, Task, _create_task_tx, _read_task
from backend.storage.db import Database, utc_now

WINDOW_BEFORE = 14
WINDOW_AFTER = 56
MAX_RANGE_DAYS = 62


class ReadingClient(Protocol):
    def calendar_list(self) -> list[dict[str, Any]]: ...
    def list_events(self, calendar_id: str, time_min: str, time_max: str) -> list[dict[str, Any]]: ...


class SourceCalendar(BaseModel):
    calendar_id: str
    summary: str
    color: str
    is_primary: bool
    followed: bool


class SourceEvent(BaseModel):
    calendar_id: str
    calendar_summary: str
    color: str
    event_id: str
    summary: str
    location: str
    html_link: str
    all_day: bool
    start_at: str | None
    end_at: str | None
    first_day: date
    last_day: date
    task_id: str | None


class AddedEvent(BaseModel):
    event: SourceEvent
    task: Task
    planned: bool


# --------------------------------------------------------------------------- refresh


def _own_calendar(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT calendar_id FROM google_calendar WHERE id = 1").fetchone()
    return row["calendar_id"] if row else None


def refresh_calendars(db: Database, client: ReadingClient) -> None:
    items = [item for item in client.calendar_list() if isinstance(item.get("id"), str)]
    now = utc_now()
    with db.write() as conn:
        own = _own_calendar(conn)
        seen = set()
        for item in items:
            if item["id"] == own:
                continue
            seen.add(item["id"])
            conn.execute(
                "INSERT INTO google_source_calendars (calendar_id, summary, color, is_primary, in_source, fetched_at) "
                "VALUES (?, ?, ?, ?, 1, ?) ON CONFLICT(calendar_id) DO UPDATE SET summary = excluded.summary, "
                "color = excluded.color, is_primary = excluded.is_primary, in_source = 1, fetched_at = excluded.fetched_at",
                (item["id"], str(item.get("summaryOverride") or item.get("summary") or "Calendar")[:200],
                 str(item.get("backgroundColor") or "")[:20], 1 if item.get("primary") else 0, now))
        for row in conn.execute("SELECT calendar_id FROM google_source_calendars").fetchall():
            if row["calendar_id"] not in seen:
                conn.execute("UPDATE google_source_calendars SET in_source = 0 WHERE calendar_id = ?", (row["calendar_id"],))
                conn.execute("DELETE FROM google_source_events WHERE calendar_id = ?", (row["calendar_id"],))


def _days(item: dict[str, Any], calendar: ApplicationCalendar) -> tuple[bool, str | None, str | None, str, str] | None:
    start, end = item.get("start") or {}, item.get("end") or {}
    try:
        if start.get("date"):
            first = date.fromisoformat(start["date"])
            last = date.fromisoformat(end.get("date") or start["date"]) - timedelta(days=1)
            return True, None, None, first.isoformat(), max(first, last).isoformat()
        begins = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
        finishes = datetime.fromisoformat((end.get("dateTime") or start["dateTime"]).replace("Z", "+00:00"))
    except (KeyError, ValueError, TypeError, AttributeError):
        return None
    first_day = calendar.localize(begins).date()
    last_day = calendar.localize(max(begins, finishes - timedelta(microseconds=1))).date()
    return False, begins.isoformat(), finishes.isoformat(), first_day.isoformat(), max(first_day, last_day).isoformat()


def refresh_events(db: Database, client: ReadingClient, *, now: datetime | None = None) -> None:
    instant = now or datetime.now(UTC)
    with db.read() as conn:
        followed = [row["calendar_id"] for row in conn.execute(
            "SELECT calendar_id FROM google_source_calendars WHERE followed = 1 AND in_source = 1")]
    calendar = ApplicationCalendar.from_environment()
    time_min = (instant - timedelta(days=WINDOW_BEFORE)).isoformat()
    time_max = (instant + timedelta(days=WINDOW_AFTER)).isoformat()
    fetched = {calendar_id: client.list_events(calendar_id, time_min, time_max) for calendar_id in followed}
    with db.write() as conn:
        conn.execute("DELETE FROM google_source_events WHERE calendar_id NOT IN "
                     "(SELECT calendar_id FROM google_source_calendars WHERE followed = 1 AND in_source = 1)")
        for calendar_id, items in fetched.items():
            conn.execute("DELETE FROM google_source_events WHERE calendar_id = ?", (calendar_id,))
            for item in items:
                if not isinstance(item.get("id"), str) or item.get("status") == "cancelled":
                    continue
                days = _days(item, calendar)
                if days is None:
                    continue
                link = str(item.get("htmlLink") or "")
                conn.execute(
                    "INSERT OR REPLACE INTO google_source_events (calendar_id, event_id, summary, location, html_link, "
                    "all_day, start_at, end_at, first_day, last_day) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (calendar_id, item["id"], str(item.get("summary") or "(No title)")[:500],
                     str(item.get("location") or "")[:500],
                     link if link.startswith("https://www.google.com/calendar/") else "",
                     1 if days[0] else 0, *days[1:]))


def read_calendars(db: Database, client: ReadingClient) -> None:
    refresh_calendars(db, client)
    refresh_events(db, client)


# --------------------------------------------------------------------------- reading and choices


def list_calendars(db: Database) -> list[SourceCalendar]:
    with db.read() as conn:
        rows = conn.execute("SELECT * FROM google_source_calendars WHERE in_source = 1 "
                            "ORDER BY is_primary DESC, summary COLLATE NOCASE").fetchall()
    return [SourceCalendar(calendar_id=r["calendar_id"], summary=r["summary"], color=r["color"],
                           is_primary=bool(r["is_primary"]), followed=bool(r["followed"])) for r in rows]


def set_followed(db: Database, calendar_ids: list[str]) -> None:
    with db.write() as conn:
        known = {row["calendar_id"] for row in conn.execute("SELECT calendar_id FROM google_source_calendars")}
        unknown = [calendar_id for calendar_id in calendar_ids if calendar_id not in known]
        if unknown:
            raise InvalidInput("calendar_ids", "One of those calendars is no longer available. Refresh and try again.")
        conn.execute("UPDATE google_source_calendars SET followed = 0")
        for calendar_id in calendar_ids:
            conn.execute("UPDATE google_source_calendars SET followed = 1 WHERE calendar_id = ?", (calendar_id,))
        conn.execute("DELETE FROM google_source_events WHERE calendar_id NOT IN "
                     "(SELECT calendar_id FROM google_source_calendars WHERE followed = 1)")


_EVENT_SELECT = (
    "SELECT e.*, c.summary AS calendar_summary, c.color, l.task_id FROM google_source_events e "
    "JOIN google_source_calendars c ON c.calendar_id = e.calendar_id "
    "LEFT JOIN google_event_tasks l ON l.calendar_id = e.calendar_id AND l.event_id = e.event_id ")


def _event(row: sqlite3.Row) -> SourceEvent:
    return SourceEvent(
        calendar_id=row["calendar_id"], calendar_summary=row["calendar_summary"], color=row["color"],
        event_id=row["event_id"], summary=row["summary"], location=row["location"], html_link=row["html_link"],
        all_day=bool(row["all_day"]), start_at=row["start_at"], end_at=row["end_at"],
        first_day=date.fromisoformat(row["first_day"]), last_day=date.fromisoformat(row["last_day"]),
        task_id=row["task_id"])


def list_events(db: Database, start: str, end: str) -> list[SourceEvent]:
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except (TypeError, ValueError):
        raise InvalidInput("start", "Dates must look like 2026-11-03.") from None
    if last < first or (last - first).days > MAX_RANGE_DAYS:
        raise InvalidInput("end", f"Choose a range of at most {MAX_RANGE_DAYS} days.")
    with db.read() as conn:
        rows = conn.execute(_EVENT_SELECT + "WHERE e.first_day <= ? AND e.last_day >= ? "
                            "ORDER BY e.first_day, e.all_day DESC, e.start_at", (last.isoformat(), first.isoformat())).fetchall()
    return [_event(row) for row in rows]


def _when(event: SourceEvent) -> str:
    if event.all_day:
        return event.first_day.strftime("%a %b %-d") + ("" if event.last_day == event.first_day else event.last_day.strftime(" – %a %b %-d")) + ", all day"
    calendar = ApplicationCalendar.from_environment()
    begins = calendar.localize(datetime.fromisoformat(event.start_at or ""))
    finishes = calendar.localize(datetime.fromisoformat(event.end_at or event.start_at or ""))
    return begins.strftime("%a %b %-d, %-I:%M %p") + finishes.strftime(" – %-I:%M %p")


def add_event_task(db: Database, calendar_id: str, event_id: str) -> AddedEvent:
    with db.write() as conn:
        row = conn.execute(_EVENT_SELECT + "WHERE e.calendar_id = ? AND e.event_id = ?", (calendar_id, event_id)).fetchone()
        if row is None:
            raise InvalidInput("event_id", "That event is no longer in your followed calendars. Refresh and try again.")
        event = _event(row)
        if event.task_id is not None:
            return AddedEvent(event=event, task=_read_task(conn, event.task_id), planned=False)
        notes = f"From Google Calendar ({event.calendar_summary}): {_when(event)}"
        if event.location:
            notes += f"\nWhere: {event.location}"
        if event.html_link:
            notes += f"\n{event.html_link}"
        minutes = None
        if not event.all_day and event.start_at and event.end_at:
            span = int((datetime.fromisoformat(event.end_at) - datetime.fromisoformat(event.start_at)).total_seconds() // 60)
            minutes = span if 1 <= span <= 10080 else None
        task = _create_task_tx(conn, event.summary[:TITLE_MAX_LENGTH].strip() or "(No title)",
                               project_id=default_project_id(conn), notes=notes[:2000], estimate_minutes=minutes)
        planned = False
        if event.first_day >= application_today()[0] - timedelta(days=WINDOW_BEFORE):
            try:
                _create_placement_tx(conn, task.id, event.first_day)
                planned = True
            except WeekConflict:
                pass  # that week is closed; the task is kept unscheduled
        conn.execute("INSERT INTO google_event_tasks (calendar_id, event_id, task_id, created_at) VALUES (?, ?, ?, ?)",
                     (calendar_id, event_id, task.id, utc_now()))
        return AddedEvent(event=event.model_copy(update={"task_id": task.id}), task=_read_task(conn, task.id), planned=planned)
