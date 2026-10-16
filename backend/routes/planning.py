from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, StrictStr

from backend.domain.planning import (
    Placement, PlanningSnapshot, create_placement, get_planning, move_placement, remove_placement,
)

router = APIRouter(prefix="/api")


class PlacementCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: StrictStr
    planned_date: StrictStr
    source_placement_id: StrictStr | None = None


class PlacementMoveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    planned_date: StrictStr


@router.get("/planning")
def planning(request: Request, week: str | None = None) -> PlanningSnapshot:
    return get_planning(request.app.state.db, week)


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
