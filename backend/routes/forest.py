from fastapi import APIRouter, Request
from pydantic import BaseModel

from backend.domain.forest import ForestTree, list_forest

router = APIRouter(prefix="/api/forest")


class ForestView(BaseModel):
    trees: list[ForestTree]


@router.get("")
def get_forest(request: Request) -> ForestView:
    # Like Track, navigation can settle an expired countdown before rendering.
    request.app.state.timer.get()
    return ForestView(trees=list_forest(request.app.state.db))
