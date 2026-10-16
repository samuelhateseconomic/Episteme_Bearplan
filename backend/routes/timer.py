from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt, StrictStr

from backend.domain.timer import TimerView

router = APIRouter(prefix="/api/timer")


class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: StrictStr
    duration_minutes: StrictInt
    operation_id: StrictStr


class ControlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: StrictInt | None = None
    operation_id: StrictStr | None = None
    discard_uncertain: StrictBool = False


@router.get("")
def get_timer(request: Request) -> TimerView:
    return request.app.state.timer.get()


@router.post("/start", status_code=201)
def start_timer(body: StartRequest, request: Request) -> TimerView:
    return request.app.state.timer.start(body.task_id, body.duration_minutes, body.operation_id)


@router.post("/{session_id}/pause")
def pause_timer(session_id: str, body: ControlRequest, request: Request) -> TimerView:
    return request.app.state.timer.control(session_id, "pause", **body.model_dump())


@router.post("/{session_id}/resume")
def resume_timer(session_id: str, body: ControlRequest, request: Request) -> TimerView:
    return request.app.state.timer.control(session_id, "resume", **body.model_dump())


@router.post("/{session_id}/finish")
def finish_timer(session_id: str, body: ControlRequest, request: Request) -> TimerView:
    return request.app.state.timer.control(session_id, "finish", **body.model_dump())
