from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from backend.domain.projects import Project, create_project, list_projects, rename_project
from backend.storage.db import Database

router = APIRouter(prefix="/api")


class ProjectNameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str


class ProjectList(BaseModel):
    projects: list[Project]


def _db(request: Request) -> Database:
    return request.app.state.db


@router.get("/projects")
def get_projects(request: Request) -> ProjectList:
    return ProjectList(projects=list_projects(_db(request)))


@router.post("/projects", status_code=201)
def post_project(body: ProjectNameRequest, request: Request) -> Project:
    return create_project(_db(request), body.name)


@router.patch("/projects/{project_id}")
def patch_project(project_id: str, body: ProjectNameRequest, request: Request) -> Project:
    return rename_project(_db(request), project_id, body.name)
