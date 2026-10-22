from datetime import datetime

from fastapi import APIRouter, Request

from backend.domain.streaks import StreakView, get_streaks

router = APIRouter(prefix="/api/streaks")


@router.get("")
def get_daily_streaks(request: Request) -> StreakView:
    # As with Forest, visiting Track can settle a genuinely expired countdown.
    # Use the same service clock for Today, including deterministic API tests.
    view = request.app.state.timer.get()
    return get_streaks(request.app.state.db, now=datetime.fromisoformat(view.server_now.replace("Z", "+00:00")))
