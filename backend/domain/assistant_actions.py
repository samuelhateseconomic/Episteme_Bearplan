"""Assistant actions: proposed during inference, applied only by explicit user request.

Model tool calls never mutate. A proposal records normalized arguments and the
revisions it was based on. Applying rechecks those revisions in the same
serialized transaction as the change and its immutable receipt, so a stale
proposal cannot overwrite newer work and a retried request replays the original
result. Undo restores the recorded before-state only while the target is still
exactly as the action left it. Timer actions reuse TimerService replay and have
no Undo: saved time and rewards follow the timer rules, so Track remains the
place to change them.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import date
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, ValidationError

from backend.domain.errors import InvalidInput
from backend.domain.planning import _create_placement_tx, _remove_placement_tx
from backend.domain.tasks import (
    _create_task_tx, _delete_unused_task_tx, _read_task, _require_task, _set_completion_tx, _update_task_tx,
)
from backend.domain.timer import TimerService
from backend.storage.db import Database, utc_now

TASK_KINDS = ("create_task", "update_task", "assign_task_date", "complete_task")
TIMER_KINDS = ("start_timer", "pause_timer", "finish_timer")
EDITABLE = ("title", "notes", "deadline", "estimate_minutes")


class ActionConflict(InvalidInput):
    """The reviewed proposal or applied action no longer matches saved records."""


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CreateTaskArguments(Arguments):
    title: str = Field(min_length=1, max_length=200)
    project_id: str | None = Field(default=None, max_length=100)
    parent_id: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)
    deadline: str | None = Field(default=None, max_length=10)
    estimate_minutes: int | None = Field(default=None, ge=1, le=10080)


class UpdateTaskArguments(Arguments):
    task_id: str = Field(min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    deadline: str | None = Field(default=None, max_length=10)
    estimate_minutes: int | None = Field(default=None, ge=1, le=10080)


class AssignDateArguments(Arguments):
    task_id: str = Field(min_length=1, max_length=100)
    date: str = Field(min_length=10, max_length=10)


class CompleteTaskArguments(Arguments):
    task_id: str = Field(min_length=1, max_length=100)
    complete: bool = True


class StartTimerArguments(Arguments):
    task_id: str = Field(min_length=1, max_length=100)
    duration_minutes: int = Field(ge=1, le=180)


ACTION_MODELS: dict[str, tuple[type[Arguments], str]] = {
    "create_task": (CreateTaskArguments, "Propose a new task, or a subtask with parent_id. Omit project_id for the default project. Not applied until the user presses Apply."),
    "update_task": (UpdateTaskArguments, "Propose editing title, notes, deadline (YYYY-MM-DD) or estimate of one task by exact ID. Include only fields to change; null clears notes/deadline/estimate. Not applied until the user presses Apply."),
    "assign_task_date": (AssignDateArguments, "Propose planning one incomplete leaf task by exact ID on a date (YYYY-MM-DD) in an open week. Not applied until the user presses Apply."),
    "complete_task": (CompleteTaskArguments, "Propose marking one leaf task by exact ID complete (or complete=false to reopen). Parents complete through subtasks. Not applied until the user presses Apply."),
    "start_timer": (StartTimerArguments, "Propose starting a countdown of 1–180 minutes on one incomplete leaf task by exact ID. Not applied until the user presses Apply."),
    "pause_timer": (Arguments, "Propose pausing the running countdown. Not applied until the user presses Apply."),
    "finish_timer": (Arguments, "Propose finishing and saving the current running or paused countdown. Not applied until the user presses Apply."),
}


class Expected(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    tasks: dict[str, StrictInt] = Field(default_factory=dict, max_length=3)
    session_id: str | None = Field(default=None, max_length=36)
    session_revision: StrictInt | None = None


class Proposal(BaseModel):
    """What the browser sends back to apply. Summary/preview are display-only and excluded."""
    model_config = ConfigDict(extra="ignore", strict=True)
    kind: Literal["create_task", "update_task", "assign_task_date", "complete_task",
                  "start_timer", "pause_timer", "finish_timer"]
    arguments: dict[str, Any]
    expected: Expected


def action_schemas() -> list[dict]:
    return [{"type": "function", "function": {"name": name, "description": description,
             "parameters": model.model_json_schema()}} for name, (model, description) in ACTION_MODELS.items()]


def _arguments(kind: str, raw: object) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise InvalidInput("arguments", "Action arguments must be an object.")
    model = ACTION_MODELS[kind][0]
    try:
        parsed = model.model_validate(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        field = ".".join(str(part) for part in first["loc"]) or "arguments"
        raise InvalidInput(field, f"Invalid {field}: {first['msg']}. Nothing was changed.") from None
    if kind == "update_task":
        values = parsed.model_dump(exclude_unset=True)
        if len(values) < 2:
            raise InvalidInput("arguments", "Choose at least one field to change. Nothing was changed.")
        if "title" in values and values["title"] is None:
            raise InvalidInput("title", "A task title cannot be cleared.")
        return values
    return parsed.model_dump(exclude_none=kind == "create_task")


def _key(value: object, field: str = "operation_id") -> str:
    try:
        if not isinstance(value, str):
            raise ValueError
        return str(UUID(value))
    except ValueError:
        raise InvalidInput(field, "Use a new UUID for this request and keep it when retrying.") from None


def _fingerprint(proposal: Proposal, arguments: dict[str, Any]) -> str:
    body = {"kind": proposal.kind, "arguments": arguments, "expected": proposal.expected.model_dump()}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _task_view(conn: sqlite3.Connection, task_id: str) -> dict[str, Any]:
    task = _read_task(conn, task_id)
    project = conn.execute("SELECT name FROM projects WHERE id = ?", (task.project_id,)).fetchone()
    parent = conn.execute("SELECT title FROM tasks WHERE id = ?", (task.parent_id,)).fetchone() if task.parent_id else None
    return {**task.model_dump(mode="json"), "project_name": project["name"] if project else "",
            "parent_title": parent["title"] if parent else None}


def _check_expected(conn: sqlite3.Connection, expected: Expected) -> None:
    for task_id, revision in expected.tasks.items():
        row = conn.execute("SELECT revision, title FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise ActionConflict("task_id", "A task in this proposal no longer exists. Ask again; nothing was changed.")
        if row["revision"] != revision:
            raise ActionConflict("revision", f'"{row["title"]}" changed after this proposal was prepared. '
                                 "Ask again to review its current state; nothing was changed.")


def _summary(kind: str, args: dict[str, Any], task: dict[str, Any] | None) -> str:
    title = f'"{task["title"]}"' if task else "the task"
    if kind == "create_task":
        where = f' under "{task["parent_title"]}"' if task and task.get("parent_title") else ""
        project = f' in {task["project_name"]}' if task and task.get("project_name") else ""
        due = f", due {_day(args['deadline'])}" if args.get("deadline") else ""
        estimate = f", estimate {args['estimate_minutes']} min" if args.get("estimate_minutes") else ""
        notes = ", with notes" if args.get("notes") else ""
        return f'Create task "{args["title"]}"{where}{project}{due}{estimate}{notes}'
    if kind == "update_task":
        changes = ", ".join(f"{name.replace('_', ' ')} → {_day(args[name]) if name == 'deadline' and args[name] else args[name] if args[name] is not None else 'cleared'}"
                            for name in EDITABLE if name in args)
        return f"Edit {title}: {changes}"
    if kind == "assign_task_date":
        return f"Plan {title} on {_day(args['date'])}"
    if kind == "complete_task":
        return f"{'Mark' if args['complete'] else 'Reopen'} {title}{' complete' if args['complete'] else ''}"
    if kind == "start_timer":
        return f"Start a {args['duration_minutes']}-minute countdown for {title}"
    return f"{'Pause' if kind == 'pause_timer' else 'Finish and save'} the current countdown for {title}"


def _before(result: dict[str, Any]) -> dict[str, Any]:
    """Name the task as the user knew it: a rename's summary shows the old title."""
    return {**result["task"], **{k: v for k, v in result.get("before", {}).items() if k == "title"}}


def _day(value: str) -> str:
    """Show the weekday beside a date so the reviewed day is unmistakable."""
    try:
        return f"{date.fromisoformat(value).strftime('%a')} {value}"
    except ValueError:
        return value


class _DryRun(Exception):
    def __init__(self, value: Any) -> None:
        self.value = value


def _apply_task_kind(conn: sqlite3.Connection, kind: str, args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Run one task action through shared domain helpers; return its result and Undo record."""
    if kind == "create_task":
        task = _create_task_tx(conn, args["title"], project_id=args.get("project_id"), parent_id=args.get("parent_id"),
                               notes=args.get("notes"), deadline=args.get("deadline"),
                               estimate_minutes=args.get("estimate_minutes"))
        return {"task": _task_view(conn, task.id)}, {"task_id": task.id, "after_revision": task.revision}
    if kind == "update_task":
        before = _task_view(conn, args["task_id"])
        fields = {name: args[name] for name in EDITABLE if name in args}
        task = _update_task_tx(conn, args["task_id"], fields)
        restore = {name: before[name] for name in fields}
        return {"task": _task_view(conn, task.id), "before": restore}, {
            "task_id": task.id, "after_revision": task.revision, "before": restore}
    if kind == "assign_task_date":
        placement = _create_placement_tx(conn, args["task_id"], args["date"])
        return {"task": _task_view(conn, args["task_id"]), "placement": placement.model_dump(mode="json")}, {
            "placement_id": placement.id, "after_revision": placement.revision}
    row = _require_task(conn, args["task_id"])
    task = _set_completion_tx(conn, args["task_id"], args["complete"])
    return {"task": _task_view(conn, task.id)}, {
        "task_id": task.id, "after_revision": task.revision, "before_completed_at": row["completed_at"]}


def _expected_for(conn: sqlite3.Connection, kind: str, args: dict[str, Any]) -> dict[str, int]:
    # A new subtask is validated against its parent at apply time; pinning the
    # parent's revision would make sibling proposals stale one another.
    if kind == "create_task":
        return {}
    return {args["task_id"]: _require_task(conn, args["task_id"])["revision"]}


def propose_action(db: Database, timer: TimerService | None, kind: str, raw: object) -> dict[str, Any]:
    """Validate a model-requested action against current records without saving it."""
    if kind not in ACTION_MODELS:
        raise InvalidInput("tool", "Unknown action. No changes were made.")
    args = _arguments(kind, raw)
    if kind in TASK_KINDS:
        # Validate with the exact apply path, then roll back. The write lock is held
        # only for this short dry run, never while waiting on the model.
        try:
            with db.write() as conn:
                expected = _expected_for(conn, kind, args)
                result, undo = _apply_task_kind(conn, kind, args)
                raise _DryRun((expected, result))
        except _DryRun as dry:
            expected, result = dry.value
        task = result["task"]
        return {"kind": kind, "arguments": args, "expected": {"tasks": expected, "session_id": None, "session_revision": None},
                "summary": _summary(kind, args, _before(result)), "undoable": True, "preview": result}
    if timer is None:
        raise InvalidInput("tool", "Timer actions are unavailable in this service. Use Track.")
    view = timer.get()
    active = view.active_session
    if kind == "start_timer":
        if active is not None:
            raise ActionConflict("session", "A countdown is already running, paused or needs review. Finish it in Track first.")
        with db.read() as conn:
            task = _task_view(conn, args["task_id"])
        if task["subtask_count"]:
            raise InvalidInput("task_id", "Choose a subtask; tasks with subtasks cannot be timed directly.")
        if task["completed"]:
            raise InvalidInput("task_id", "This task is complete. Reopen it or choose another task.")
        return {"kind": kind, "arguments": args, "expected": {"tasks": {task["id"]: task["revision"]}, "session_id": None,
                "session_revision": None}, "summary": _summary(kind, args, task), "undoable": False, "preview": {"task": task}}
    if active is None:
        raise ActionConflict("session", "No countdown is running or paused. Nothing was changed.")
    if active.state == "needs_review":
        raise ActionConflict("session", "This countdown needs review in Track before it can be paused or finished.")
    if kind == "pause_timer" and active.state != "running":
        raise ActionConflict("session", "The countdown is already paused.")
    session = active.model_dump(mode="json")
    return {"kind": kind, "arguments": args, "expected": {"tasks": {}, "session_id": active.id,
            "session_revision": session["revision"]},
            "summary": _summary(kind, args, {"title": active.task_title}), "undoable": False, "preview": {"session": session}}


def _replay(row: sqlite3.Row, fingerprint: str) -> dict[str, Any]:
    if row["fingerprint"] != fingerprint:
        raise ActionConflict("operation_id", "This request ID was already used for a different change. Nothing else was changed.")
    return {**json.loads(row["result_json"]), "replayed": True}


def _receipt(conn: sqlite3.Connection, key: str, proposal: Proposal, args: dict[str, Any], fingerprint: str,
             summary: str, result: dict[str, Any], undo: dict[str, Any] | None) -> dict[str, Any]:
    now = utc_now()
    body = {"operation_id": key, "kind": proposal.kind, "summary": summary, "applied_at": now,
            "undoable": undo is not None, **result}
    conn.execute(
        "INSERT INTO assistant_actions (operation_id, kind, fingerprint, request_json, undo_json, result_json, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (key, proposal.kind, fingerprint, json.dumps({"arguments": args, "expected": proposal.expected.model_dump()}),
         json.dumps(undo) if undo is not None else None, json.dumps(body), now),
    )
    return {**body, "replayed": False}


def apply_action(db: Database, timer: TimerService | None, proposal: object, operation_id: object) -> dict[str, Any]:
    """Apply a reviewed proposal once; a retried key returns the original result."""
    key = _key(operation_id)
    try:
        parsed = Proposal.model_validate(proposal)
    except ValidationError:
        raise InvalidInput("proposal", "This proposal is malformed. Ask the assistant again; nothing was changed.") from None
    args = _arguments(parsed.kind, parsed.arguments)
    fingerprint = _fingerprint(parsed, args)
    with db.read() as conn:
        prior = conn.execute("SELECT * FROM assistant_actions WHERE operation_id = ?", (key,)).fetchone()
    if prior is not None:
        return _replay(prior, fingerprint)
    if parsed.kind in TIMER_KINDS:
        return _apply_timer(db, timer, key, parsed, args, fingerprint)
    with db.write() as conn:
        prior = conn.execute("SELECT * FROM assistant_actions WHERE operation_id = ?", (key,)).fetchone()
        if prior is not None:
            return _replay(prior, fingerprint)
        _check_expected(conn, parsed.expected)
        result, undo = _apply_task_kind(conn, parsed.kind, args)
        return _receipt(conn, key, parsed, args, fingerprint, _summary(parsed.kind, args, _before(result)), result, undo)


def _apply_timer(db: Database, timer: TimerService | None, key: str, proposal: Proposal, args: dict[str, Any],
                 fingerprint: str) -> dict[str, Any]:
    if timer is None:
        raise InvalidInput("kind", "Timer actions are unavailable in this service. Use Track.")
    # TimerService owns countdown writes and replays this same key after a lost response.
    if proposal.kind == "start_timer":
        with db.read() as conn:
            _check_expected(conn, proposal.expected)
        view = timer.start(args["task_id"], args["duration_minutes"], key)
        title = (view.active_session or view.last_session).task_title
    else:
        if proposal.expected.session_id is None or proposal.expected.session_revision is None:
            raise InvalidInput("expected", "This timer proposal lacks its reviewed countdown. Ask again; nothing was changed.")
        action = "pause" if proposal.kind == "pause_timer" else "finish"
        view = timer.control(proposal.expected.session_id, action,
                             expected_revision=proposal.expected.session_revision, operation_id=key)
        title = (view.active_session or view.last_session).task_title
    session = view.active_session or view.last_session
    result = {"session": session.model_dump(mode="json") if session else None}
    with db.write() as conn:
        prior = conn.execute("SELECT * FROM assistant_actions WHERE operation_id = ?", (key,)).fetchone()
        if prior is not None:
            return _replay(prior, fingerprint)
        return _receipt(conn, key, proposal, args, fingerprint, _summary(proposal.kind, args, {"title": title}), result, None)


def _require_after(conn: sqlite3.Connection, table: str, record_id: str, revision: int, label: str) -> None:
    row = conn.execute(f"SELECT revision FROM {table} WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        raise ActionConflict("undo", f"The {label} no longer exists, so this change cannot be undone. Nothing was changed.")
    if row["revision"] != revision:
        raise ActionConflict("undo", f"The {label} changed after this action. Undo would overwrite newer work, "
                             "so nothing was changed. Edit it in Plan instead.")


def undo_action(db: Database, operation_id: object, undo_operation_id: object) -> dict[str, Any]:
    """Restore an applied action's before-state if nothing has changed since; replay-safe."""
    key = _key(operation_id)
    undo_key = _key(undo_operation_id, "undo_operation_id")
    with db.write() as conn:
        receipt = conn.execute("SELECT * FROM assistant_actions WHERE operation_id = ?", (key,)).fetchone()
        if receipt is None:
            raise InvalidInput("operation_id", "No applied assistant action has this ID.")
        done = conn.execute("SELECT * FROM assistant_action_undos WHERE action_operation_id = ?", (key,)).fetchone()
        if done is not None:
            if done["operation_id"] != undo_key:
                raise ActionConflict("undo", "This action was already undone. Nothing else was changed.")
            return {**json.loads(done["result_json"]), "replayed": True}
        if conn.execute("SELECT 1 FROM assistant_action_undos WHERE operation_id = ?", (undo_key,)).fetchone():
            raise ActionConflict("undo_operation_id", "This Undo ID was already used for another action. Nothing was changed.")
        if receipt["undo_json"] is None:
            raise ActionConflict("undo", "Timer changes cannot be undone here. Use Track to pause, resume or finish the countdown.")
        undo = json.loads(receipt["undo_json"])
        kind = receipt["kind"]
        if kind == "assign_task_date":
            _require_after(conn, "planned_items", undo["placement_id"], undo["after_revision"], "planned date")
            _remove_placement_tx(conn, undo["placement_id"])
        else:
            _require_after(conn, "tasks", undo["task_id"], undo["after_revision"], "task")
            if kind == "create_task":
                _delete_unused_task_tx(conn, undo["task_id"])
            elif kind == "update_task":
                _update_task_tx(conn, undo["task_id"], undo["before"])
            else:
                before = undo["before_completed_at"]
                _set_completion_tx(conn, undo["task_id"], before is not None, completed_at=before)
        summary = json.loads(receipt["result_json"])["summary"]
        now = utc_now()
        body = {"operation_id": undo_key, "action_operation_id": key, "undone_at": now, "summary": f"Undid: {summary}"}
        conn.execute("INSERT INTO assistant_action_undos (operation_id, action_operation_id, result_json, created_at)"
                     " VALUES (?, ?, ?, ?)", (undo_key, key, json.dumps(body), now))
        return {**body, "replayed": False}
