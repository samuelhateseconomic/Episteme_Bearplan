from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from backend.domain.tasks import Task, create_task, list_tasks
from backend.storage.db import Database
from backend.storage.migrations import current_version

router = APIRouter(prefix="/api")


class TaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str


class TaskList(BaseModel):
    tasks: list[Task]


def _db(request: Request) -> Database:
    return request.app.state.db


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    return {"status": "ok", "schema_version": current_version(_db(request))}


@router.get("/tasks")
def get_tasks(request: Request) -> TaskList:
    return TaskList(tasks=list_tasks(_db(request)))


@router.post("/tasks", status_code=201)
def post_task(body: TaskCreateRequest, request: Request) -> Task:
    return create_task(_db(request), body.title)
