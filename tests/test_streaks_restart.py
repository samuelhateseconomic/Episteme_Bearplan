"""Real service restarts retain exact derived daily credit and all original rows."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from backend.domain.rewards import RewardConfig, ShopService
from backend.domain.streaks import get_streaks
from backend.domain.tasks import create_task
from backend.domain.timer import TimerService
from backend.platform.paths import DATABASE_FILENAME
from backend.storage.db import open_database
from tests.conftest import http_json, running_service
from tests.test_forest import all_rows
from tests.test_streaks import HOUR, saved_interval
from tests.test_timer import FakeClock, observed


def test_real_process_restarts_and_retried_finish_derive_same_history_without_gap_credit(tmp_path, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    data_dir = tmp_path / "StreakRestart"
    data_dir.mkdir()
    db = open_database(data_dir / DATABASE_FILENAME)
    yesterday = datetime.now(UTC).replace(hour=10, minute=0, second=0, microsecond=0) - timedelta(days=1)
    saved_interval(db, yesterday, yesterday + timedelta(hours=1), HOUR)
    config = RewardConfig(birch_price=0)
    shop = ShopService(db, config)
    shop.purchase("birch", 0, str(uuid4()))
    clock = FakeClock(yesterday + timedelta(hours=2))
    timer = TimerService(db, clock, reward_config=config)
    task = create_task(db, "Restart excludes unfinished confirmed time")
    active = timer.start(task.id, 1, str(uuid4()), "birch").active_session
    observed(timer, clock, 1.25)
    paused = timer.control(active.id, "pause", expected_revision=active.revision).active_session
    before = all_rows(db)
    expected = get_streaks(db).model_dump(mode="json")
    assert expected["current_streak"] == 1 and expected["days"][-2]["active_microseconds"] == HOUR
    with running_service(data_dir) as first:
        assert http_json("GET", f"{first.url}/api/streaks") == (200, expected)
        assert http_json("GET", f"{first.url}/api/timer")[1]["active_session"]["id"] == paused.id
        assert first.stop() == 0
    assert all_rows(db) == before
    finish_body = {"operation_id": str(uuid4()), "expected_revision": paused.revision}
    with running_service(data_dir) as second:
        assert http_json("GET", f"{second.url}/api/streaks") == (200, expected)
        status, finished = http_json("POST", f"{second.url}/api/timer/{paused.id}/finish", finish_body)
        assert status == 200 and finished["last_session"]["active_seconds"] == 1.25
        assert finished["last_session"]["coin_award"] == 0 and finished["last_session"]["tree"]["species"] == "birch"
        final = http_json("GET", f"{second.url}/api/streaks")[1]
        assert final["days"][-2]["active_microseconds"] == HOUR + 1_250_000
        assert final["days"][-1]["active_microseconds"] == 0 and final["current_streak"] == 1
        assert second.stop() == 0
    after_finish = all_rows(db)
    with running_service(data_dir) as third:
        status, replay = http_json("POST", f"{third.url}/api/timer/{paused.id}/finish", finish_body)
        assert status == 200 and replay["active_session"] is None
        assert replay["last_session"] == finished["last_session"]
        assert http_json("GET", f"{third.url}/api/streaks") == (200, final)
        assert http_json("GET", f"{third.url}/api/streaks") == (200, final)
        assert third.stop() == 0
    assert all_rows(db) == after_finish
    with db.read() as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert before["tasks"] == after_finish["tasks"] and before["owned_species"] == after_finish["owned_species"]
