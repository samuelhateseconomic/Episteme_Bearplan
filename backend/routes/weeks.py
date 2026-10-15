from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, StrictStr

from backend.domain.weeks import (
    CarryoverOptions, CarryoverPreview, CarryoverResult, ClosePreview, apply_carryover,
    close_week, get_carryover, preview_carryover, preview_close,
)
from backend.domain.planning import ClosedWeek

router = APIRouter(prefix="/api/weeks")


class CloseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preview_token: StrictStr


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: StrictStr
    planned_date: StrictStr


class CarryoverPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    selections: list[Selection]


class CarryoverRequest(CarryoverPreviewRequest):
    preview_token: StrictStr
    operation_id: StrictStr


@router.get("/{week}/close-preview")
def close_preview(week: str, request: Request) -> ClosePreview:
    return preview_close(request.app.state.db, week)


@router.post("/{week}/close")
def close(week: str, body: CloseRequest, request: Request) -> ClosedWeek:
    return close_week(request.app.state.db, week, body.preview_token)


@router.get("/{week}/carryover")
def carryover_options(week: str, request: Request) -> CarryoverOptions:
    return get_carryover(request.app.state.db, week)


@router.post("/{week}/carryover-preview")
def carryover_preview(week: str, body: CarryoverPreviewRequest, request: Request) -> CarryoverPreview:
    return preview_carryover(request.app.state.db, week, [item.model_dump() for item in body.selections])


@router.post("/{week}/carryover")
def carryover_apply(week: str, body: CarryoverRequest, request: Request) -> CarryoverResult:
    return apply_carryover(request.app.state.db, week, [item.model_dump() for item in body.selections], body.preview_token, body.operation_id)
