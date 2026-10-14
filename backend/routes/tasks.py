from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt, StrictStr

from backend.domain.tasks import (
    UNSET, CompletionProgress, Task, completion_progress, create_task, list_tasks,
    remove_subtask, set_task_completion, update_task,
)
from backend.storage.db import Database
from backend.storage.migrations import current_version

router = APIRouter(prefix="/api")


class TaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: StrictStr
    project_id: StrictStr | None = None
    parent_id: StrictStr | None = None
    notes: StrictStr | None = None
    deadline: StrictStr | None = None
    # Strict so that true does not quietly become an estimate of one minute.
    estimate_minutes: StrictInt | None = None


class TaskUpdateRequest(BaseModel):
    """Only the fields actually sent are changed; an explicit null clears one."""

    model_config = ConfigDict(extra="forbid")

    title: StrictStr | None = None
    notes: StrictStr | None = None
    deadline: StrictStr | None = None
    estimate_minutes: StrictInt | None = None

    def supplied(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in self.model_fields_set}


class CompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    complete: StrictBool


class TaskList(BaseModel):
    tasks: list[Task]
    progress: CompletionProgress


def _db(request: Request) -> Database:
    return request.app.state.db


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    return {"status": "ok", "schema_version": current_version(_db(request))}


@router.get("/tasks")
def get_tasks(request: Request, project_id: str | None = None) -> TaskList:
    stored = list_tasks(_db(request), project_id)
    return TaskList(tasks=stored, progress=completion_progress(stored))


@router.post("/tasks", status_code=201)
def post_task(body: TaskCreateRequest, request: Request) -> Task:
    return create_task(
        _db(request),
        body.title,
        project_id=body.project_id,
        parent_id=body.parent_id,
        notes=body.notes,
        deadline=body.deadline,
        estimate_minutes=body.estimate_minutes,
    )


@router.patch("/tasks/{task_id}")
def patch_task(task_id: str, body: TaskUpdateRequest, request: Request) -> Task:
    supplied = body.supplied()
    return update_task(
        _db(request),
        task_id,
        title=supplied.get("title", UNSET),
        notes=supplied.get("notes", UNSET),
        deadline=supplied.get("deadline", UNSET),
        estimate_minutes=supplied.get("estimate_minutes", UNSET),
    )


@router.put("/tasks/{task_id}/completion")
def put_task_completion(task_id: str, body: CompletionRequest, request: Request) -> Task:
    return set_task_completion(_db(request), task_id, body.complete)


@router.delete("/tasks/{task_id}")
def delete_subtask(task_id: str, request: Request) -> Task:
    return remove_subtask(_db(request), task_id)
