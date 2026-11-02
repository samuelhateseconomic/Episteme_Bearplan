"""bCourses source routes: status/list, refresh, followed courses and reviewed decisions.

Refresh fetches from bCourses outside any transaction (sync route, worker thread).
The token is never returned; only whether one is configured.
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, StrictBool, StrictStr

from backend.domain.bcourses import AddResult, Assignment, BCoursesState, add_assignment, get_state, refresh, resolve_due_change, set_dismissed, set_followed
from backend.platform.bcourses import TOKEN_KEY, BCoursesClient, BCoursesUnavailable
from backend.platform.secrets import read_secret

router = APIRouter(prefix="/api/bcourses")


class FollowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    course_ids: list[StrictStr]


class DismissRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dismissed: StrictBool


class DueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use_new: StrictBool


def _client(request: Request) -> BCoursesClient:
    return getattr(request.app.state, "bcourses_client", None) or BCoursesClient()


def _state(request: Request) -> BCoursesState:
    configured = getattr(request.app.state, "bcourses_client", None) is not None or read_secret(TOKEN_KEY) is not None
    return get_state(request.app.state.db, configured)


@router.get("")
def bcourses_state(request: Request) -> BCoursesState:
    return _state(request)


@router.post("/refresh")
def bcourses_refresh(request: Request) -> BCoursesState:
    refresh(request.app.state.db, _client(request), BCoursesUnavailable)
    return _state(request)


@router.put("/courses")
def bcourses_follow(body: FollowRequest, request: Request) -> BCoursesState:
    set_followed(request.app.state.db, body.course_ids)
    refresh(request.app.state.db, _client(request), BCoursesUnavailable)
    return _state(request)


@router.post("/assignments/{assignment_id}/add")
def bcourses_add(assignment_id: str, request: Request) -> AddResult:
    return add_assignment(request.app.state.db, assignment_id)


@router.put("/assignments/{assignment_id}/dismissed")
def bcourses_dismiss(assignment_id: str, body: DismissRequest, request: Request) -> Assignment:
    return set_dismissed(request.app.state.db, assignment_id, body.dismissed)


@router.post("/assignments/{assignment_id}/due-date")
def bcourses_due(assignment_id: str, body: DueRequest, request: Request) -> Assignment:
    return resolve_due_change(request.app.state.db, assignment_id, body.use_new)
