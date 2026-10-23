"""All-time reports from one saved snapshot; never persist derived counters.

Completion/estimates describe current leaves. Time describes historical sessions,
including work whose task was removed or became a container. Project attribution
is the project at session start. Closed-week snapshots are never reinterpreted.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict

from backend.domain.calendar import ApplicationCalendar
from backend.domain.streaks import allocate_confirmed_time
from backend.domain.tasks import _list_tasks
from backend.storage.db import Database


class Completion(BaseModel):
    completed: int = 0
    total: int = 0
    percent: float = 0


class DailyStatistics(BaseModel):
    date: date
    active_microseconds: int
    completed: int


class TaskStatistics(BaseModel):
    task_id: str
    project_id: str
    title: str
    parent_title: str | None
    current_leaf: bool
    completed: bool | None
    estimate_minutes: int | None
    active_microseconds: int = 0
    session_count: int = 0


class ProjectStatistics(BaseModel):
    project_id: str
    name: str
    completion: Completion
    active_microseconds: int = 0


class StatisticsView(BaseModel):
    model_config = ConfigDict(frozen=True)

    today: date
    timezone: str
    completion: Completion
    active_microseconds: int
    session_count: int
    days: list[DailyStatistics]
    projects: list[ProjectStatistics]
    tasks: list[TaskStatistics]


def _completion(tasks) -> Completion:
    total = len(tasks)
    completed = sum(task.completed for task in tasks)
    return Completion(completed=completed, total=total, percent=round(100 * completed / total, 2) if total else 0)


def get_statistics(db: Database, *, now: datetime | None = None) -> StatisticsView:
    instant = datetime.now(UTC) if now is None else now
    calendar = ApplicationCalendar.from_environment()
    today = calendar.localize(instant).date()
    with db.read() as conn:
        conn.execute("BEGIN")
        current = _list_tasks(conn)
        projects = conn.execute("SELECT id, name FROM projects ORDER BY created_at, rowid").fetchall()
        intervals = conn.execute(
            "SELECT s.id AS session_id, s.task_id, s.project_id, s.task_title, s.project_name, s.parent_title, "
            "i.started_at, i.ended_at, i.active_microseconds "
            "FROM timer_sessions s JOIN timer_intervals i ON i.session_id = s.id "
            "WHERE s.state = 'finished' AND i.ended_at IS NOT NULL "
            "AND NOT EXISTS (SELECT 1 FROM timer_interruptions x "
            "WHERE x.session_id = s.id AND x.resolved_at IS NULL) ORDER BY s.rowid, i.rowid"
        ).fetchall()

    leaves = [task for task in current if not task.is_parent]
    by_id = {task.id: task for task in current}
    project_rows = {row["id"]: ProjectStatistics(
        project_id=row["id"], name=row["name"],
        completion=_completion([task for task in leaves if task.project_id == row["id"]]),
    ) for row in projects}
    task_rows = {(task.project_id, task.id): TaskStatistics(
        task_id=task.id, project_id=task.project_id, title=task.title,
        parent_title=by_id[task.parent_id].title if task.parent_id in by_id else None,
        current_leaf=True, completed=task.completed, estimate_minutes=task.estimate_minutes,
    ) for task in leaves}
    daily_time: dict[date, int] = defaultdict(int)
    daily_completed: dict[date, int] = defaultdict(int)
    for task in leaves:
        if task.completed_at is not None:
            daily_completed[calendar.localize(task.completed_at).date()] += 1
    sessions: set[str] = set()
    task_sessions: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in intervals:
        # The exact same integer allocation as streaks, including DST and drift.
        allocate_confirmed_time(daily_time, calendar, row["started_at"], row["ended_at"], row["active_microseconds"])
        key = row["project_id"], row["task_id"]
        if row["project_id"] not in project_rows:
            project_rows[row["project_id"]] = ProjectStatistics(
                project_id=row["project_id"], name=row["project_name"], completion=Completion(),
            )
        if key not in task_rows:
            task_rows[key] = TaskStatistics(
                task_id=row["task_id"], project_id=row["project_id"], title=row["task_title"],
                parent_title=row["parent_title"], current_leaf=False, completed=None, estimate_minutes=None,
            )
        task_rows[key].active_microseconds += row["active_microseconds"]
        project_rows[row["project_id"]].active_microseconds += row["active_microseconds"]
        sessions.add(row["session_id"])
        task_sessions[key].add(row["session_id"])
    for key, row in task_rows.items():
        row.session_count = len(task_sessions[key])
    days = sorted(daily_time.keys() | daily_completed.keys(), reverse=True)
    return StatisticsView(
        today=today, timezone=calendar.label(instant), completion=_completion(leaves),
        active_microseconds=sum(daily_time.values()), session_count=len(sessions),
        days=[DailyStatistics(date=day, active_microseconds=daily_time.get(day, 0), completed=daily_completed.get(day, 0)) for day in days],
        projects=list(project_rows.values()), tasks=list(task_rows.values()),
    )
