"""Google Tasks sync: BearPlans -> Google, plus completion ticked in Google.

Each sync also updates Google Calendar events (see google_calendar.py).

User decisions (2026-11-02):
- Every project, task and subtask syncs. Project -> task list named like the project,
  task -> task, subtask -> subtask (both sides allow one level only).
- BearPlans is the source of truth. Titles, notes, dates, nesting and completion are
  sent to Google; an edit made in Google to those is overwritten on the next sync.
  The exception: ticking (or unticking) a task in Google changes its completion in
  BearPlans, unless BearPlans also changed that completion since the last sync.
- Google's date is the deadline if set, else the next planned day (or the latest
  past one), else none. Google Tasks only keeps a date.
- BearPlans touches only the lists and tasks it created (remembered in google_* tables).
  Tasks the user adds in Google, and their own lists, are left alone.

Network calls happen outside any transaction; each Google item created is recorded
in its own short write, so an interrupted sync never creates duplicates on retry.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel

from backend.domain.calendar import application_today
from backend.domain.google_calendar import CalendarClient, sync_calendar
from backend.domain.google_reading import read_calendars
from backend.domain.tasks import Task, _list_tasks, _set_completion_tx
from backend.storage.db import Database, utc_now

_LOG = logging.getLogger("bearplans.google")
PERIOD_SECONDS = 120
NUDGE_DELAY_SECONDS = 4
NOTES_LIMIT = 8000


class TasksClient(Protocol):
    def lists(self) -> list[dict[str, Any]]: ...
    def insert_list(self, title: str) -> dict[str, Any]: ...
    def rename_list(self, list_id: str, title: str) -> dict[str, Any]: ...
    def tasks(self, list_id: str) -> list[dict[str, Any]]: ...
    def insert_task(self, list_id: str, body: dict[str, Any], parent: str | None) -> dict[str, Any]: ...
    def patch_task(self, list_id: str, task_id: str, body: dict[str, Any]) -> dict[str, Any]: ...
    def move_task(self, list_id: str, task_id: str, parent: str | None) -> dict[str, Any]: ...
    def delete_task(self, list_id: str, task_id: str) -> None: ...


class SyncStatus(BaseModel):
    last_attempt_at: str | None
    last_success_at: str | None
    last_error: str | None
    synced_lists: int
    synced_tasks: int
    synced_events: int


@dataclass(frozen=True)
class _Mapping:
    task_id: str
    list_id: str
    google_id: str
    pushed_status: str


# --------------------------------------------------------------------------- reading


def get_status(db: Database) -> SyncStatus:
    with db.read() as conn:
        row = conn.execute("SELECT * FROM google_sync WHERE id = 1").fetchone()
        lists = conn.execute("SELECT count(*) FROM google_task_lists").fetchone()[0]
        tasks = conn.execute("SELECT count(*) FROM google_tasks").fetchone()[0]
        events = conn.execute("SELECT count(*) FROM google_events").fetchone()[0]
    return SyncStatus(
        last_attempt_at=row["last_attempt_at"] if row else None,
        last_success_at=row["last_success_at"] if row else None,
        last_error=row["last_error"] if row else None,
        synced_lists=lists, synced_tasks=tasks, synced_events=events)


def _snapshot(conn: sqlite3.Connection) -> tuple[dict[str, str], list[Task], dict[str, list[str]], dict[str, str], dict[str, _Mapping]]:
    projects = {row["id"]: row["name"] for row in conn.execute("SELECT id, name FROM projects ORDER BY created_at, rowid")}
    tasks = _list_tasks(conn)
    plans: dict[str, list[str]] = {}
    for row in conn.execute("SELECT task_id, planned_date FROM planned_items ORDER BY planned_date"):
        plans.setdefault(row["task_id"], []).append(row["planned_date"])
    lists = {row["project_id"]: row["list_id"] for row in conn.execute("SELECT project_id, list_id FROM google_task_lists")}
    mapped = {row["task_id"]: _Mapping(row["task_id"], row["list_id"], row["google_id"], row["pushed_status"])
              for row in conn.execute("SELECT * FROM google_tasks")}
    return projects, tasks, plans, lists, mapped


def _google_date(task: Task, plans: dict[str, list[str]], children: list[Task], today: str) -> str | None:
    """Deadline, else the next planned day (or latest past one), else none."""
    if task.deadline is not None:
        return task.deadline.isoformat()
    days = list(plans.get(task.id, []))
    for child in children:
        days += plans.get(child.id, [])
    if not days:
        return None
    upcoming = sorted(day for day in days if day >= today)
    return upcoming[0] if upcoming else max(days)


def _desired(task: Task, due: str | None) -> dict[str, Any]:
    return {
        "title": task.title,
        "notes": task.notes[:NOTES_LIMIT],
        "due": f"{due}T00:00:00.000Z" if due else None,
        "status": "completed" if task.completed else "needsAction",
    }


def _differs(remote: dict[str, Any], desired: dict[str, Any]) -> bool:
    return (remote.get("title", "") != desired["title"]
            or (remote.get("notes") or "") != desired["notes"]
            or (remote.get("due") or "")[:10] != (desired["due"] or "")[:10]
            or remote.get("status") != desired["status"])


# --------------------------------------------------------------------------- writing


def _record(db: Database, sql: str, params: tuple[Any, ...]) -> None:
    with db.write() as conn:
        conn.execute(sql, params)


def _save_mapping(db: Database, task_id: str, list_id: str, google_id: str, status: str) -> None:
    _record(db, "INSERT INTO google_tasks (task_id, list_id, google_id, pushed_status, updated_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(task_id) DO UPDATE SET list_id = excluded.list_id, google_id = excluded.google_id, "
                "pushed_status = excluded.pushed_status, updated_at = excluded.updated_at",
            (task_id, list_id, google_id, status, utc_now()))


def _set_sync(db: Database, *, success: bool, error: str | None) -> None:
    now = utc_now()
    with db.write() as conn:
        conn.execute("INSERT INTO google_sync (id) VALUES (1) ON CONFLICT(id) DO NOTHING")
        if success:
            conn.execute("UPDATE google_sync SET last_attempt_at = ?, last_success_at = ?, last_error = NULL WHERE id = 1", (now, now))
        else:
            conn.execute("UPDATE google_sync SET last_attempt_at = ?, last_error = ? WHERE id = 1", (now, error))


def _apply_ticks(db: Database, ticks: dict[str, str]) -> int:
    """Bring completion ticked in Google into BearPlans; returns how many tasks changed.

    Applied only where BearPlans still has the completion it last sent, so a change
    made in BearPlans since then wins. Ticking a parent completes its open subtasks;
    unticking a parent is not applied (its completion comes from its subtasks).
    """
    changed = 0
    with db.write() as conn:
        tasks = {task.id: task for task in _list_tasks(conn)}
        mapped = {row["task_id"]: row["pushed_status"] for row in conn.execute("SELECT task_id, pushed_status FROM google_tasks")}
        for task_id, status in ticks.items():
            task = tasks.get(task_id)
            pushed = mapped.get(task_id)
            if task is None or pushed is None or ("completed" if task.completed else "needsAction") != pushed:
                continue
            complete = status == "completed"
            if task.is_parent:
                if not complete:
                    continue
                for child in tasks.values():
                    if child.parent_id == task_id and not child.completed:
                        _set_completion_tx(conn, child.id, True)
                        changed += 1
            else:
                _set_completion_tx(conn, task_id, complete)
                changed += 1
            conn.execute("UPDATE google_tasks SET pushed_status = ?, updated_at = ? WHERE task_id = ?", (status, utc_now(), task_id))
    return changed


# --------------------------------------------------------------------------- sync


def sync(db: Database, client: TasksClient, unavailable: type[Exception],
         calendar: CalendarClient | None = None) -> SyncStatus:
    """One full sync (Tasks, BearPlans calendar, then reading followed calendars). Raises `unavailable` (after recording it) when Google fails."""
    try:
        _sync(db, client)
        if calendar is not None:
            sync_calendar(db, calendar)
            read_calendars(db, calendar)  # type: ignore[arg-type]
    except unavailable as error:
        _set_sync(db, success=False, error=getattr(error, "message", str(error)))
        raise
    _set_sync(db, success=True, error=None)
    return get_status(db)


def _sync(db: Database, client: TasksClient) -> None:
    with db.read() as conn:
        _, _, _, lists, mapped = _snapshot(conn)

    # 1. Read what Google has in BearPlans' lists; forget lists the user deleted there.
    present = {item["id"] for item in client.lists() if isinstance(item.get("id"), str)}
    for project_id, list_id in list(lists.items()):
        if list_id not in present:
            _record(db, "DELETE FROM google_tasks WHERE list_id = ?", (list_id,))
            _record(db, "DELETE FROM google_task_lists WHERE project_id = ?", (project_id,))
            del lists[project_id]
    remote: dict[str, dict[str, Any]] = {}
    for list_id in lists.values():
        for item in client.tasks(list_id):
            if isinstance(item.get("id"), str):
                remote[item["id"]] = item

    # 2. Bring back completion ticked in Google.
    ticks = {m.task_id: item["status"] for m in mapped.values()
             if (item := remote.get(m.google_id)) and not item.get("deleted")
             and item.get("status") in ("completed", "needsAction") and item["status"] != m.pushed_status}
    if ticks:
        _apply_ticks(db, ticks)

    # 3. Send BearPlans to Google.
    with db.read() as conn:
        projects, tasks, plans, lists, mapped = _snapshot(conn)
    today = application_today()[0].isoformat()
    children: dict[str, list[Task]] = {}
    for task in tasks:
        if task.parent_id:
            children.setdefault(task.parent_id, []).append(task)
    titles = {item["id"]: item.get("title") for item in client.lists() if isinstance(item.get("id"), str)}

    for project_id, name in projects.items():
        list_id = lists.get(project_id)
        if list_id is None:
            created = client.insert_list(name)
            lists[project_id] = created["id"]
            _record(db, "INSERT INTO google_task_lists (project_id, list_id, created_at) VALUES (?, ?, ?)",
                    (project_id, created["id"], utc_now()))
        elif titles.get(list_id) != name:
            client.rename_list(list_id, name)

    google_ids: dict[str, str] = {}
    local_ids = {task.id for task in tasks}
    for task in tasks:  # parents come before their subtasks
        list_id = lists[task.project_id]
        parent_google = google_ids.get(task.parent_id) if task.parent_id else None
        desired = _desired(task, _google_date(task, plans, children.get(task.id, []), today))
        current = mapped.get(task.id)
        item = remote.get(current.google_id) if current else None
        if current and (item is None or item.get("deleted") or current.list_id != list_id):
            if item is not None and not item.get("deleted"):
                client.delete_task(current.list_id, current.google_id)  # moved to another project
            current, item = None, None
        if current is None:
            created = client.insert_task(list_id, {k: v for k, v in desired.items() if v is not None}, parent_google)
            _save_mapping(db, task.id, list_id, created["id"], desired["status"])
            google_ids[task.id] = created["id"]
            continue
        google_ids[task.id] = current.google_id
        if (item.get("parent") or None) != parent_google:
            client.move_task(list_id, current.google_id, parent_google)
        if _differs(item, desired):
            body = dict(desired)
            if desired["status"] == "needsAction":
                body["completed"] = None
            client.patch_task(list_id, current.google_id, body)
        if current.pushed_status != desired["status"]:
            _save_mapping(db, task.id, list_id, current.google_id, desired["status"])

    # 4. Remove from Google what was removed in BearPlans (subtasks first).
    gone = [m for m in mapped.values() if m.task_id not in local_ids]
    gone.sort(key=lambda m: 0 if (remote.get(m.google_id) or {}).get("parent") else 1)
    for mapping in gone:
        client.delete_task(mapping.list_id, mapping.google_id)
        _record(db, "DELETE FROM google_tasks WHERE task_id = ?", (mapping.task_id,))


# --------------------------------------------------------------------------- background


class GoogleSyncService:
    """Runs sync in the background: every PERIOD_SECONDS, and shortly after a change."""

    def __init__(self, db: Database, client_factory: Any, unavailable: type[Exception], connected: Any,
                 calendar_factory: Any = None) -> None:
        self._db = db
        self._client_factory = client_factory
        self._calendar_factory = calendar_factory
        self._unavailable = unavailable
        self._connected = connected
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._version = 0

    @property
    def version(self) -> int:
        """Goes up whenever a sync changes something the open page shows (a tick from
        Google, followed-calendar events), so the page knows to refresh."""
        return self._version

    def _fingerprint(self) -> int:
        with self._db.read() as conn:
            return hash((
                tuple(tuple(row) for row in conn.execute("SELECT id, revision, completed_at FROM tasks ORDER BY id")),
                tuple(tuple(row) for row in conn.execute("SELECT * FROM google_source_events ORDER BY calendar_id, event_id")),
                tuple(tuple(row) for row in conn.execute("SELECT calendar_id, summary, followed, in_source FROM google_source_calendars ORDER BY calendar_id")),
            ))

    def sync_now(self) -> SyncStatus:
        with self._lock:  # one sync at a time
            calendar = self._calendar_factory() if self._calendar_factory else None
            before = self._fingerprint()
            try:
                return sync(self._db, self._client_factory(), self._unavailable, calendar)
            finally:
                if self._fingerprint() != before:
                    self._version += 1

    def nudge(self) -> None:
        self._wake.set()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()

        def run() -> None:
            while not self._stop.is_set():
                woken = self._wake.wait(PERIOD_SECONDS)
                if self._stop.is_set():
                    break
                if woken:
                    self._stop.wait(NUDGE_DELAY_SECONDS)  # gather a burst of edits
                    self._wake.clear()
                if not self._connected():
                    continue
                try:
                    self.sync_now()
                except self._unavailable:
                    pass  # recorded in google_sync and shown in the app
                except (sqlite3.Error, OSError):
                    _LOG.warning("Google Tasks sync could not save its progress; it will retry.")

        self._thread = threading.Thread(target=run, daemon=True, name="bearplans-google-sync")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

