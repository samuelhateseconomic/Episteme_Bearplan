from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, StrictStr

from backend.domain.planning import (
    Placement, PlanningSnapshot, create_placement, get_planning, move_placement, remove_placement, set_placement_time,
)

from backend.domain.google_reading import SourceEvent, list_events

router = APIRouter(prefix="/api")


class PlanningView(PlanningSnapshot):
    # Events from the user's followed Google calendars for the shown week (read-only).
    calendar_events: list[SourceEvent] = []


class PlacementCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: StrictStr
    planned_date: StrictStr
    source_placement_id: StrictStr | None = None


class PlacementMoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    planned_date: StrictStr


class PlacementTimeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start_time: StrictStr | None


@router.get("/planning")
def planning(request: Request, week: str | None = None) -> PlanningView:
    snapshot = get_planning(request.app.state.db, week)
    try:
        events = list_events(request.app.state.db, snapshot.week_start.isoformat(), snapshot.week_end.isoformat())
    except sqlite3.Error:
        events = []
    return PlanningView(**snapshot.model_dump(), calendar_events=events)


@router.post("/placements", status_code=201)
def post_placement(body: PlacementCreateRequest, request: Request) -> Placement:
    return create_placement(
        request.app.state.db, body.task_id, body.planned_date, source_placement_id=body.source_placement_id,
    )


@router.patch("/placements/{placement_id}")
def patch_placement(placement_id: str, body: PlacementMoveRequest, request: Request) -> Placement:
    return move_placement(request.app.state.db, placement_id, body.planned_date)


@router.delete("/placements/{placement_id}")
def delete_placement(placement_id: str, request: Request) -> dict[str, str]:
    return {"removed": remove_placement(request.app.state.db, placement_id)}


@router.put("/placements/{placement_id}/time")
def put_placement_time(placement_id: str, body: PlacementTimeRequest, request: Request) -> Placement:
    return set_placement_time(request.app.state.db, placement_id, body.start_time)
