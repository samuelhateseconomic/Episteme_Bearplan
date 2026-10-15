"""Immutable week history and reviewed, retry-safe carryover.

Closing transfers placements into historical storage, retaining their identities.
The current task rows are never changed. Both preview validation and the mutation
run against a consistent transaction; a failed write cannot leave a partial week.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4

from pydantic import BaseModel

from backend.domain.errors import InvalidInput
from backend.domain.planning import (
    ClosedWeek, ClosedWeekSummary, HistoricalTask, Placement, WeekConflict,
    _list_placements, _planned_date, _require_open_week, application_today, week_bounds,
)
from backend.domain.tasks import Task, _list_tasks
from backend.storage.db import Database, utc_now


class ClosePreview(BaseModel):
    preview_token: str
    snapshot: ClosedWeek


class CarryoverCandidate(BaseModel):
    task_id: str
    snapshot_task: HistoricalTask
    task: Task | None
    eligible: bool
    reason: str | None
    existing_planned_date: date | None


class CarryoverOptions(BaseModel):
    week_start: date
    destination_start: date
    destination_end: date
    candidates: list[CarryoverCandidate]


class CarryoverItem(BaseModel):
    task_id: str
    planned_date: date
    task: Task
    project_name: str
    parent_title: str | None


class CarryoverPreview(BaseModel):
    preview_token: str
    week_start: date
    destination_start: date
    destination_end: date
    items: list[CarryoverItem]


class CarryoverResult(BaseModel):
    operation_id: str
    week_start: date
    placements: list[Placement]


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: object) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _closed_week(conn: sqlite3.Connection, monday: str) -> ClosedWeek | None:
    row = conn.execute("SELECT snapshot_json FROM closed_weeks WHERE week_start = ?", (monday,)).fetchone()
    return ClosedWeek.model_validate_json(row["snapshot_json"]) if row else None


def _closed_week_summaries(conn: sqlite3.Connection) -> list[ClosedWeekSummary]:
    summaries = []
    for row in conn.execute("SELECT snapshot_json FROM closed_weeks ORDER BY week_start DESC"):
        snapshot = ClosedWeek.model_validate_json(row["snapshot_json"])
        summaries.append(ClosedWeekSummary(
            week_start=snapshot.week_start, week_end=snapshot.week_end,
            closed_at=snapshot.closed_at, completed=snapshot.completed, total=snapshot.total,
        ))
    return summaries


def _snapshot(conn: sqlite3.Connection, week: str | date) -> ClosedWeek:
    monday, sunday = week_bounds(week)
    placements = [p for p in _list_placements(conn) if monday <= p.planned_date <= sunday]
    tasks = _list_tasks(conn)
    by_id = {task.id: task for task in tasks}
    project_names = dict(conn.execute("SELECT id, name FROM projects"))
    placed_ids = {p.task_id for p in placements}
    displayed_ids = placed_ids | {by_id[task_id].parent_id for task_id in placed_ids}
    displayed = [HistoricalTask(
        **task.model_dump(), project_name=project_names[task.project_id],
        parent_title=by_id[task.parent_id].title if task.parent_id else None,
    ) for task in tasks if task.id in displayed_ids]
    leaves = [task for task in tasks if task.id in placed_ids and not task.is_parent]
    _, timezone = application_today()
    return ClosedWeek(
        week_start=monday, week_end=sunday, timezone=timezone, tasks=displayed,
        placements=placements, completed=sum(task.completed for task in leaves), total=len(leaves),
    )


def preview_close(db: Database, week: str | date) -> ClosePreview:
    monday, _ = week_bounds(week)
    with db.read() as conn:
        conn.execute("BEGIN")
        snapshot = _closed_week(conn, monday.isoformat()) or _snapshot(conn, monday)
        return ClosePreview(preview_token=_digest(snapshot.model_dump(mode="json")), snapshot=snapshot)


def close_week(db: Database, week: str | date, preview_token: str) -> ClosedWeek:
    monday, _ = week_bounds(week)
    with db.write() as conn:
        existing = _closed_week(conn, monday.isoformat())
        if existing:
            return existing  # Lost-response retries return the original closure.
        snapshot = _snapshot(conn, monday)
        if preview_token != _digest(snapshot.model_dump(mode="json")):
            raise WeekConflict("preview_token", "The week's plan or task details changed. Preview End Week again before closing. Nothing was changed.")
        snapshot = snapshot.model_copy(update={"closed_at": datetime.fromisoformat(utc_now())})
        conn.execute(
            "INSERT INTO closed_weeks (week_start, week_end, closed_at, timezone, snapshot_json) VALUES (?, ?, ?, ?, ?)",
            (monday.isoformat(), snapshot.week_end.isoformat(), snapshot.closed_at.isoformat(timespec="microseconds").replace("+00:00", "Z"),
             snapshot.timezone, snapshot.model_dump_json()),
        )
        conn.execute(
            "INSERT INTO closed_placements (id, task_id, planned_date, created_at, updated_at, revision, week_start) "
            "SELECT id, task_id, planned_date, created_at, updated_at, revision, ? FROM planned_items "
            "WHERE planned_date BETWEEN ? AND ?",
            (monday.isoformat(), monday.isoformat(), snapshot.week_end.isoformat()),
        )
        conn.execute("DELETE FROM planned_items WHERE planned_date BETWEEN ? AND ?", (monday.isoformat(), snapshot.week_end.isoformat()))
        return snapshot


def _require_closed(conn: sqlite3.Connection, week: str | date) -> ClosedWeek:
    monday, _ = week_bounds(week)
    snapshot = _closed_week(conn, monday.isoformat())
    if snapshot is None:
        raise WeekConflict("week", "Close the source week with End Week before carrying work over.")
    return snapshot


def _following_week(source: ClosedWeek) -> tuple[date, date]:
    try:
        monday = source.week_start + timedelta(days=7)
    except OverflowError:
        raise InvalidInput("week", "The following week is outside the supported calendar range.") from None
    return week_bounds(monday)


def _carryover_options(conn: sqlite3.Connection, week: str | date) -> CarryoverOptions:
    snapshot = _require_closed(conn, week)
    start, end = _following_week(snapshot)
    current = {task.id: task for task in _list_tasks(conn)}
    planned = {p.task_id: p for p in _list_placements(conn)}
    destination_closed = _closed_week(conn, start.isoformat()) is not None
    placed = {p.task_id for p in snapshot.placements}
    candidates = []
    for frozen in snapshot.tasks:
        if frozen.id not in placed or frozen.is_parent or frozen.completed:
            continue
        task = current.get(frozen.id)
        existing = planned.get(frozen.id)
        reason = None
        if task is None:
            reason = "This task no longer exists. Its closed-week history is preserved."
        elif task.completed:
            reason = "Currently complete; excluded from carryover."
        elif task.is_parent:
            reason = "This task now has subtasks. Plan its unfinished subtasks instead."
        elif destination_closed:
            reason = "The following week is closed. Historical scheduling is read-only."
        elif existing:
            reason = f"Already planned for {existing.planned_date.isoformat()}. Move or remove that active plan first; carryover will not add another day."
        candidates.append(CarryoverCandidate(
            task_id=frozen.id, snapshot_task=frozen, task=task, eligible=reason is None,
            reason=reason, existing_planned_date=existing.planned_date if existing else None,
        ))
    return CarryoverOptions(week_start=snapshot.week_start, destination_start=start, destination_end=end, candidates=candidates)


def get_carryover(db: Database, week: str | date) -> CarryoverOptions:
    with db.read() as conn:
        conn.execute("BEGIN")
        return _carryover_options(conn, week)


def _selections(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise InvalidInput("selections", "Select at least one unfinished task and its destination date.")
    normalized = []
    seen = set()
    for item in value:
        if not isinstance(item, dict) or set(item) != {"task_id", "planned_date"} or not isinstance(item["task_id"], str):
            raise InvalidInput("selections", "Each selection needs a task ID and a planned date.")
        if item["task_id"] in seen:
            raise InvalidInput("selections", "Select each task only once. Split multi-day work into subtasks.")
        seen.add(item["task_id"])
        normalized.append({"task_id": item["task_id"], "planned_date": _planned_date(item["planned_date"])})
    return sorted(normalized, key=lambda item: item["task_id"])


def _carryover_preview(conn: sqlite3.Connection, week: str | date, selections: list[dict[str, str]]) -> CarryoverPreview:
    options = _carryover_options(conn, week)
    by_id = {candidate.task_id: candidate for candidate in options.candidates}
    project_names = dict(conn.execute("SELECT id, name FROM projects"))
    current = {task.id: task for task in _list_tasks(conn)}
    items = []
    for selection in selections:
        candidate = by_id.get(selection["task_id"])
        if candidate is None:
            raise InvalidInput("selections", "Select only work that was unfinished when this source week closed.")
        day = date.fromisoformat(selection["planned_date"])
        if not options.destination_start <= day <= options.destination_end:
            raise InvalidInput("planned_date", f"Choose a date in the following week: {options.destination_start} through {options.destination_end}.")
        if not candidate.eligible:
            raise WeekConflict("selections", f"{candidate.snapshot_task.title}: {candidate.reason} Nothing was changed. Refresh and review carryover again.")
        _require_open_week(conn, day.isoformat())
        task = candidate.task
        items.append(CarryoverItem(
            task_id=task.id, planned_date=day, task=task, project_name=project_names[task.project_id],
            parent_title=current[task.parent_id].title if task.parent_id else None,
        ))
    payload = {"week_start": options.week_start.isoformat(), "destination_start": options.destination_start.isoformat(),
               "destination_end": options.destination_end.isoformat(), "items": [item.model_dump(mode="json") for item in items]}
    return CarryoverPreview(**payload, preview_token=_digest(payload))


def preview_carryover(db: Database, week: str | date, selections: object) -> CarryoverPreview:
    normalized = _selections(selections)
    with db.read() as conn:
        conn.execute("BEGIN")
        return _carryover_preview(conn, week, normalized)


def apply_carryover(db: Database, week: str | date, selections: object, preview_token: str, operation_id: str) -> CarryoverResult:
    monday, _ = week_bounds(week)
    normalized = _selections(selections)
    try:
        if not isinstance(operation_id, str) or str(UUID(operation_id)) != operation_id:
            raise ValueError
    except (ValueError, AttributeError):
        raise InvalidInput("operation_id", "Use a valid unique operation ID for this carryover; keep it when retrying.") from None
    request_hash = _digest({"week_start": monday.isoformat(), "selections": normalized})
    with db.write() as conn:
        prior = conn.execute("SELECT request_hash, result_json FROM carryover_operations WHERE operation_id = ?", (operation_id,)).fetchone()
        if prior:
            if prior["request_hash"] != request_hash:
                raise WeekConflict("operation_id", "This carryover operation ID was used for different work or dates. Review again with a new operation ID. Nothing was changed.")
            return CarryoverResult.model_validate_json(prior["result_json"])
        preview = _carryover_preview(conn, monday, normalized)
        if preview_token != preview.preview_token:
            raise WeekConflict("preview_token", "Task details or the destination plan changed. Review carryover again before applying. Nothing was changed.")
        now = utc_now()
        placements = []
        for item in preview.items:
            placement = Placement(id=str(uuid4()), task_id=item.task_id, planned_date=item.planned_date,
                                  created_at=now, updated_at=now, revision=1)
            conn.execute(
                "INSERT INTO planned_items (id, task_id, planned_date, created_at, updated_at, revision) VALUES (?, ?, ?, ?, ?, ?)",
                (placement.id, placement.task_id, placement.planned_date.isoformat(), now, now, 1),
            )
            placements.append(placement)
        result = CarryoverResult(operation_id=operation_id, week_start=monday, placements=placements)
        conn.execute("INSERT INTO carryover_operations (operation_id, week_start, request_hash, result_json) VALUES (?, ?, ?, ?)",
                     (operation_id, monday.isoformat(), request_hash, result.model_dump_json()))
        return result
