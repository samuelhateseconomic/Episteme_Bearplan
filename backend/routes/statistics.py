from datetime import datetime

from fastapi import APIRouter, Request

from backend.domain.statistics import StatisticsView, get_statistics

router = APIRouter(prefix="/api/statistics")


@router.get("")
def statistics(request: Request) -> StatisticsView:
    view = request.app.state.timer.get()
    return get_statistics(request.app.state.db, now=datetime.fromisoformat(view.server_now.replace("Z", "+00:00")))
