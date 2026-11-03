"""Google Calendar events for planned tasks with a start time.

User decisions (2026-11-02): a planned task with a start time becomes an event in a
calendar BearPlans creates ("BearPlans"), lasting the task's estimate, with a popup
reminder 30 minutes before so Google notifies the user. BearPlans writes only to
that calendar and overwrites edits made to its events in Google.

Implementation rules:
- Only open (not completed) tasks get events; the calendar is created on first need.
- Moving the placement or changing its time updates the event; finishing the task,
  clearing the time or removing the placement deletes the event if it hasn't
  started yet. Past events are never deleted (closing a week keeps them).
- A placement whose time has already ended does not get a new event.
- Network calls happen outside any transaction; each created event is recorded in its
  own short write so a retry never duplicates it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from backend.domain.calendar import ApplicationCalendar
from backend.domain.tasks import _list_tasks
from backend.storage.db import Database, utc_now

CALENDAR_NAME = "BearPlans"
REMINDER_MINUTES = 30
DEFAULT_MINUTES = 30
DESCRIPTION_LIMIT = 6000


class CalendarClient(Protocol):
    def calendar_exists(self, calendar_id: str) -> bool: ...
    def insert_calendar(self, summary: str) -> dict[str, Any]: ...
    def events(self, calendar_id: str) -> list[dict[str, Any]]: ...
    def insert_event(self, calendar_id: str, body: dict[str, Any]) -> dict[str, Any]: ...
    def patch_event(self, calendar_id: str, event_id: str, body: dict[str, Any]) -> dict[str, Any]: ...
    def delete_event(self, calendar_id: str, event_id: str) -> None: ...


def start_instant(day: str, start_time: str) -> datetime:
    """The planned day and time in BearPlans' calendar, as an aware instant."""
    naive = datetime.fromisoformat(f"{day}T{start_time}:00")
    zone = ApplicationCalendar.from_environment().zone
    return naive.replace(tzinfo=zone) if zone is not None else naive.astimezone()


def _parse(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None
    except ValueError:
        return None


def _desired(db: Database) -> dict[str, tuple[datetime, dict[str, Any]]]:
    with db.read() as conn:
        projects = {row["id"]: row["name"] for row in conn.execute("SELECT id, name FROM projects")}
        tasks = {task.id: task for task in _list_tasks(conn)}
        rows = conn.execute("SELECT p.id, p.task_id, p.planned_date, t.start_time FROM planned_items p "
                            "JOIN placement_times t ON t.placement_id = p.id").fetchall()
    wanted: dict[str, tuple[datetime, dict[str, Any]]] = {}
    for row in rows:
        task = tasks.get(row["task_id"])
        if task is None or task.completed:
            continue
        start = start_instant(row["planned_date"], row["start_time"])
        end = start + timedelta(minutes=task.estimate_minutes or DEFAULT_MINUTES)
        parent = tasks.get(task.parent_id) if task.parent_id else None
        where = projects.get(task.project_id, "") + (f" › {parent.title}" if parent else "")
        description = where + (f"\n\n{task.notes}" if task.notes else "") + "\n\nPlanned in BearPlans."
        wanted[row["id"]] = (start, {
            "summary": task.title,
            "description": description[:DESCRIPTION_LIMIT],
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
            "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": REMINDER_MINUTES}]},
            "extendedProperties": {"private": {"bearplansPlacement": row["id"]}},
        })
    return wanted


def _differs(remote: dict[str, Any], body: dict[str, Any]) -> bool:
    reminders = remote.get("reminders") or {}
    overrides = sorted((o.get("method"), o.get("minutes")) for o in reminders.get("overrides") or [])
    return (remote.get("summary", "") != body["summary"]
            or (remote.get("description") or "") != body["description"]
            or _parse((remote.get("start") or {}).get("dateTime")) != _parse(body["start"]["dateTime"])
            or _parse((remote.get("end") or {}).get("dateTime")) != _parse(body["end"]["dateTime"])
            or bool(reminders.get("useDefault")) or overrides != [("popup", REMINDER_MINUTES)])


def _write(db: Database, sql: str, params: tuple[Any, ...]) -> None:
    with db.write() as conn:
        conn.execute(sql, params)


def _save_event(db: Database, placement_id: str, event_id: str, start: datetime) -> None:
    _write(db, "INSERT INTO google_events (placement_id, event_id, start_at, updated_at) VALUES (?, ?, ?, ?) "
               "ON CONFLICT(placement_id) DO UPDATE SET event_id = excluded.event_id, start_at = excluded.start_at, "
               "updated_at = excluded.updated_at",
           (placement_id, event_id, start.astimezone(UTC).isoformat(), utc_now()))


def sync_calendar(db: Database, client: CalendarClient, *, now: datetime | None = None) -> None:
    instant = now or datetime.now(UTC)
    with db.read() as conn:
        row = conn.execute("SELECT calendar_id FROM google_calendar WHERE id = 1").fetchone()
        mapped = {r["placement_id"]: (r["event_id"], datetime.fromisoformat(r["start_at"]))
                  for r in conn.execute("SELECT * FROM google_events")}
    calendar_id = row["calendar_id"] if row else None
    if calendar_id is not None and not client.calendar_exists(calendar_id):
        # The user deleted the BearPlans calendar in Google; start a new one if needed.
        with db.write() as conn:
            conn.execute("DELETE FROM google_events")
            conn.execute("DELETE FROM google_calendar")
        calendar_id, mapped = None, {}

    wanted = _desired(db)
    if calendar_id is None:
        if not any(start + timedelta(minutes=1) > instant for start, _ in wanted.values()):
            return
        calendar_id = client.insert_calendar(CALENDAR_NAME)["id"]
        _write(db, "INSERT INTO google_calendar (id, calendar_id, created_at) VALUES (1, ?, ?)", (calendar_id, utc_now()))

    remote = {event["id"]: event for event in client.events(calendar_id) if isinstance(event.get("id"), str)}
    for placement_id, (start, body) in wanted.items():
        end = _parse(body["end"]["dateTime"])
        known = mapped.get(placement_id)
        event = remote.get(known[0]) if known else None
        if event is None or event.get("status") == "cancelled":
            if end is not None and end <= instant:
                if known:  # an ended event the user removed: let it go
                    _write(db, "DELETE FROM google_events WHERE placement_id = ?", (placement_id,))
                continue
            created = client.insert_event(calendar_id, body)
            _save_event(db, placement_id, created["id"], start)
        elif _differs(event, body):
            client.patch_event(calendar_id, known[0], body)
            _save_event(db, placement_id, known[0], start)

    for placement_id, (event_id, start) in mapped.items():
        if placement_id in wanted:
            continue
        if start > instant:
            client.delete_event(calendar_id, event_id)
        _write(db, "DELETE FROM google_events WHERE placement_id = ?", (placement_id,))
