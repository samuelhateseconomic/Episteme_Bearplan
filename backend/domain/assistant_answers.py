"""Direct answers: common, fully specified questions answered by code without a model.

The orchestrator supplies only a topic and details it copied from the message
(already checked against the message text). Filters such as day versus week,
incomplete versus complete, or subtasks are recognized here from the user's own
words. When anything is unclear the caller falls back to a model specialist, so
a direct answer is never a guess. Each answer reuses the bounded read tools, so
its source cards hold the same exact records the model would have seen.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Any

from backend.domain.action_library import parse_day
from backend.domain.assistant_tools import read_tool
from backend.domain.errors import InvalidInput
from backend.storage.db import Database

_WEEK = re.compile(r"\bweek(ly)?\b")
_RELATIVE = re.compile(r"\b(yesterday|last|previous|next|ago|tomorrow|month|year|between|since)\b")
_TOTAL = re.compile(r"\b(total|all[- ]time|overall|altogether|so far|ever)\b")
_INCOMPLETE = re.compile(r"\b(incomplete|unfinished|open|remaining|left|to ?do|pending|outstanding|not\s+(yet\s+)?(done|complete|completed|finished))\b")
_COMPLETE = re.compile(r"\b(done|complete|completed|finished)\b")
_SUBTASKS = re.compile(r"\bsub-?tasks?\b")
_TOP_LEVEL = re.compile(r"\b(top[- ]level|parent|main)\s+tasks?\b")
_LIST = re.compile(r"\b(list|show|check|which|what|all|my)\b")
_DUE = re.compile(r"\b(due|deadlines?|overdue)\b")
_TITLED = re.compile(r"\b(?:titled|named|called)\s+[\"“']?(.+?)[\"”']?(?=\s+(?:and|in|from|with)\b|[.?!,;]|$)", re.IGNORECASE)


@dataclass
class Direct:
    answer: str
    sources: list[dict[str, Any]]


def duration(microseconds: int) -> str:
    """Readable saved time; the source card keeps the exact microseconds."""
    seconds, micros = divmod(microseconds, 1_000_000)
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    if hours:
        return f"{hours} h {minutes} min"
    if minutes:
        return f"{minutes} min {seconds} s" if seconds else f"{minutes} min"
    return f"{seconds + micros / 1_000_000:g} s"


def _day(value: str) -> str:
    return f"{date.fromisoformat(value).strftime('%a')} {value}"


def _task_line(item: dict) -> str:
    where = item.get("project_name") or ""
    if item.get("parent_title"):
        where = f"{where} / {item['parent_title']}" if where else item["parent_title"]
    due = f", due {item['deadline']}" if item.get("deadline") else ""
    state = "complete" if item.get("completed") else "incomplete"
    return f"• {item['title']}" + (f" — {where}" if where else "") + f" ({state}{due})"


def _source(tool: str, arguments: dict, data: dict) -> list[dict]:
    return [{"tool": tool, "arguments": arguments, "data": data}]


def answer(db: Database, topic: str | None, message: str, *, task: str | None = None,
           project: str | None = None, day_words: str | None = None, now: datetime) -> Direct | None:
    """Return a direct answer, or None when a model specialist should handle it."""
    said = message.casefold()
    # The router often omits details on questions; read them from the user's words.
    titled = _TITLED.search(message)
    task = task or (titled.group(1).strip() if titled else None)
    try:
        project = project or _mentioned_project(db, said)
        if project and topic in ("plan", "time"):
            return None  # Plans and time totals have no project filter; a specialist must scope them.
        if topic == "plan":
            return _plan(db, said, day_words, now)
        if topic == "time":
            return _time(db, said, day_words, now)
        if topic == "tasks":
            return _tasks(db, said, task, project, now)
    except InvalidInput:
        return None  # e.g. an unknown project name: let the specialist explain or ask.
    return None


def _mentioned_project(db: Database, said: str) -> str | None:
    """An exact project name in the message, when exactly one appears."""
    from backend.domain.projects import list_projects

    named = [p.name for p in list_projects(db) if re.search(rf"\b{re.escape(p.name.casefold())}\b", said)]
    return named[0] if len(named) == 1 else None


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def _plan(db: Database, said: str, day_words: str | None, now: datetime) -> Direct | None:
    from backend.domain.calendar import application_today

    today = application_today(now)[0]
    if day_words:
        day = parse_day(day_words, today)
        if day is None:
            return None
    elif _RELATIVE.search(said):
        return None  # "last week", "next week": not a single stated date.
    else:
        day = today
    week = bool(_WEEK.search(said))
    tool = "get_week_plan" if week else "get_day_plan"
    arguments = {"date": day.isoformat()}
    data = read_tool(db, tool, arguments, now=now)
    if week:
        span = f"Week of {_day(data['start_date'])} – {_day(data['end_date'])}"
    else:
        span = f"Today ({_day(data['start_date'])})" if day == today else _day(data["start_date"])
    history = " Closed week: showing the frozen snapshot." if data["historical"] else ""
    if not data["items"]:
        return Direct(f"{span}: nothing is planned.{history}", _source(tool, arguments, data))
    lines = [_task_line(item) + (f" · {_day(item['planned_date'])}" if week else "") for item in data["items"]]
    more = f"\nShowing {len(data['items'])} of {data['total_placements']} placements." if data["truncated"] else ""
    head = (f"{span}: {_count(data['total_placements'], 'planned item')}; {data['completed_leaf_total']} of "
            f"{data['unique_leaf_total']} work items complete.{history}")
    return Direct(head + "\n" + "\n".join(lines) + more, _source(tool, arguments, data))


def _time(db: Database, said: str, day_words: str | None, now: datetime) -> Direct | None:
    if day_words or _WEEK.search(said) or _RELATIVE.search(said) or "today" in said or not _TOTAL.search(said):
        return None  # Dated or period totals need the time specialist.
    data = read_tool(db, "get_time_summary", {}, now=now)
    completion = data["completion"]
    text = (f"All-time saved active time: {duration(data['active_microseconds'])} across "
            f"{_count(data['session_count'], 'saved session')}. Current completion: {completion['completed']} of "
            f"{completion['total']} work items. Running or uncertain time is not included.")
    return Direct(text, _source("get_time_summary", {}, data))


def _tasks(db: Database, said: str, task: str | None, project: str | None, now: datetime) -> Direct | None:
    status = "incomplete" if _INCOMPLETE.search(said) else "complete" if _COMPLETE.search(said) else None
    level = "subtasks" if _SUBTASKS.search(said) else "top_level" if _TOP_LEVEL.search(said) else None
    scope = {"project": project} if project else {}
    where = f" in {project}" if project else " across all projects"
    if _DUE.search(said) and not task:
        arguments = {"status": "incomplete", "level": "work_items", "has_deadline": True, "order": "deadline", **scope}
        data = read_tool(db, "list_tasks", arguments, now=now)
        if not data["tasks"]:
            return Direct(f"No incomplete tasks{where} have a deadline.", _source("list_tasks", arguments, data))
        from backend.domain.calendar import application_today
        today = application_today(now)[0].isoformat()
        lines = [_task_line({**item, "deadline": None}) + f" — due {_day(item['deadline'])}" +
                 (" (overdue)" if item["deadline"] < today else "") for item in data["tasks"]]
        more = f"\nShowing {len(lines)} of {data['total']}; ask for more to see the rest." if data["next_offset"] is not None else ""
        return Direct(f"Upcoming deadlines{where}, earliest first:\n" + "\n".join(lines) + more,
                      _source("list_tasks", arguments, data))
    if task and status is None and level is None:
        arguments = {"query": task, **scope}
        data = read_tool(db, "search_tasks", arguments, now=now)
        if not data["tasks"]:
            return Direct(f"No current tasks match “{task}”{where}.", _source("search_tasks", arguments, data))
        lines = [_task_line(item) for item in data["tasks"]]
        more = f"\nShowing {len(lines)} of {data['total']}; ask for more to see the rest." if data["next_offset"] is not None else ""
        return Direct(f"{_count(data['total'], 'task')} {'matches' if data['total'] == 1 else 'match'} “{task}”{where}:\n" + "\n".join(lines) + more,
                      _source("search_tasks", arguments, data))
    if task or (status is None and level is None) or not _LIST.search(said):
        return None
    arguments = {"status": status or "any", "level": level or "any", **scope}
    data = read_tool(db, "list_tasks", arguments, now=now)
    noun = {"subtasks": "subtask", "top_level": "top-level task", "any": "task"}[arguments["level"]]
    kind = f"{status} {noun}" if status else noun
    if not data["tasks"]:
        return Direct(f"No {kind}s{where}.", _source("list_tasks", arguments, data))
    lines = [_task_line(item) for item in data["tasks"]]
    more = f"\nShowing {len(lines)} of {data['total']}; ask for more to see the rest." if data["next_offset"] is not None else ""
    return Direct(f"{_count(data['total'], kind)}{where}:\n" + "\n".join(lines) + more, _source("list_tasks", arguments, data))
