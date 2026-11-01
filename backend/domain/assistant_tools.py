"""Bounded read tools shared by assistant adapters. No write capability is exposed."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.calendar import application_today
from backend.domain.planning import _date, get_planning, week_bounds
from backend.domain.projects import list_projects
from backend.domain.statistics import get_statistics
from backend.domain.tasks import get_task, list_tasks
from backend.storage.db import Database


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class PlanArguments(Arguments):
    date: str | None = Field(default=None, max_length=10)


class SearchArguments(Arguments):
    query: str = Field(min_length=1, max_length=200)
    project_id: str | None = Field(default=None, max_length=100)
    offset: int = Field(default=0, ge=0, le=10000)
    limit: int = Field(default=10, ge=1, le=20)


class ListArguments(Arguments):
    status: Literal["incomplete", "complete", "any"] = "incomplete"
    level: Literal["subtasks", "top_level", "work_items", "any"] = "any"
    project_id: str | None = Field(default=None, max_length=100)
    offset: int = Field(default=0, ge=0, le=10000)
    limit: int = Field(default=20, ge=1, le=20)


class TaskArguments(Arguments):
    task_id: str = Field(min_length=1, max_length=100)


TOOL_MODELS: dict[str, tuple[type[Arguments], str]] = {
    "get_day_plan": (PlanArguments, "Read planned work on a date; omit date for service Today. Includes frozen history for a closed week."),
    "get_week_plan": (PlanArguments, "Read a Monday–Sunday plan containing date; omit date for this service week. Includes frozen history if closed."),
    "search_tasks": (SearchArguments, "Find current tasks by literal case-insensitive title or notes. Returns stable IDs and pagination; duplicate names are distinct."),
    "list_tasks": (ListArguments, "List current tasks by completion and level without a search word. level: subtasks (tasks with a parent), top_level, work_items (tasks without subtasks) or any. Omit project_id to cover all projects. Returns totals and pagination."),
    "get_task": (TaskArguments, "Read one current task by its exact stable ID, including notes, deadline and completion."),
    "get_time_summary": (Arguments, "Read exact all-time saved active microseconds, current leaf completion and the latest 31 dated totals. Running/uncertain time is excluded."),
}


def tool_schemas() -> list[dict]:
    return [{"type": "function", "function": {"name": name, "description": description,
             "parameters": model.model_json_schema()}} for name, (model, description) in TOOL_MODELS.items()]


def read_tool(db: Database, name: str, raw: dict, *, now: datetime | None = None) -> dict[str, Any]:
    """Validate before reading. Callers cannot select SQL, file paths or mutations."""
    if name not in TOOL_MODELS:
        raise ValueError("Only the documented read tools are available. No changes were made.")
    args = TOOL_MODELS[name][0].model_validate(raw).model_dump()
    instant = datetime.now(UTC) if now is None else now
    if name == "get_time_summary":
        report = get_statistics(db, now=instant)
        return {"scope": "all_time_saved", "today": str(report.today), "timezone": report.timezone,
                "active_microseconds": report.active_microseconds, "session_count": report.session_count,
                "completion": report.completion.model_dump(),
                "days": [day.model_dump(mode="json") for day in report.days[-31:]],
                "days_truncated": len(report.days) > 31}
    projects = {p.id: p.name for p in list_projects(db)}
    if name == "get_task":
        task = get_task(db, args["task_id"])
        return {"task": {**task.model_dump(mode="json"), "project_name": projects.get(task.project_id, "")}}
    if name == "list_tasks":
        everything = list_tasks(db, args["project_id"])
        by_id = {t.id: t for t in everything}
        level = {"subtasks": lambda t: t.parent_id is not None, "top_level": lambda t: t.parent_id is None,
                 "work_items": lambda t: not t.is_parent, "any": lambda t: True}[args["level"]]
        status = {"incomplete": lambda t: not t.completed, "complete": lambda t: t.completed, "any": lambda t: True}[args["status"]]
        tasks = [t for t in everything if level(t) and status(t)]
        page = tasks[args["offset"]:args["offset"] + args["limit"]]
        return {"total": len(tasks), "offset": args["offset"], "status": args["status"], "level": args["level"],
                "scope_project_id": args["project_id"], "scope_project_name": projects.get(args["project_id"]),
                "next_offset": args["offset"] + len(page) if args["offset"] + len(page) < len(tasks) else None,
                "tasks": [{**t.model_dump(mode="json"), "notes": t.notes[:200], "notes_truncated": len(t.notes) > 200,
                           "project_name": projects.get(t.project_id, ""),
                           "parent_title": by_id[t.parent_id].title if t.parent_id in by_id else None} for t in page]}
    if name == "search_tasks":
        query = args["query"].strip().casefold()
        if not query:
            raise ValueError("Enter a nonempty search query.")
        tasks = [t for t in list_tasks(db, args["project_id"]) if query in t.title.casefold() or query in t.notes.casefold()]
        page = tasks[args["offset"]:args["offset"] + args["limit"]]
        return {"total": len(tasks), "offset": args["offset"],
                "scope_project_id": args["project_id"], "scope_project_name": projects.get(args["project_id"]),
                "next_offset": args["offset"] + len(page) if args["offset"] + len(page) < len(tasks) else None,
                "tasks": [{**t.model_dump(mode="json"), "notes": t.notes[:400], "notes_truncated": len(t.notes) > 400,
                           "project_name": projects.get(t.project_id, "")} for t in page]}
    today, _ = application_today(instant)
    day = today if args["date"] is None else _date(args["date"], "date")
    start, end = (day, day) if name == "get_day_plan" else week_bounds(day)
    plan = get_planning(db, day, now=instant)
    closed = plan.closed_week
    placements = [p for p in (closed.placements if closed else plan.placements) if start <= p.planned_date <= end]
    tasks = {t.id: t for t in (closed.tasks if closed else plan.tasks)}
    items = []
    for placement in placements[:50]:
        task = tasks[placement.task_id]
        items.append({"placement_id": placement.id, "planned_date": str(placement.planned_date),
                      "task_id": task.id, "title": task.title, "project_name": getattr(task, "project_name", projects.get(task.project_id, "")),
                      "parent_title": getattr(task, "parent_title", tasks[task.parent_id].title if task.parent_id in tasks else None),
                      "deadline": str(task.deadline) if task.deadline else None, "completed": task.completed,
                      "estimate_minutes": task.estimate_minutes})
    leaves = {p.task_id: tasks[p.task_id] for p in placements if not tasks[p.task_id].is_parent}
    return {"today": str(today), "timezone": plan.timezone, "start_date": str(start), "end_date": str(end),
            "historical": closed is not None, "total_placements": len(placements), "truncated": len(placements) > 50,
            "unique_leaf_total": len(leaves), "completed_leaf_total": sum(t.completed for t in leaves.values()), "items": items}
