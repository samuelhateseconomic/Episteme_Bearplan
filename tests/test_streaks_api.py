"""Daily progress HTTP contract, expiry settlement, safety and data errors."""

from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from backend.app import create_app
from backend.domain.tasks import create_task
from backend.storage.db import StorageError, open_database
from tests.test_forest import all_rows
from tests.test_streaks import HOUR, NOW, saved_interval
from tests.test_timer import FakeClock, observed


def setup_api(db):
    clock = FakeClock(NOW)
    app = create_app(db, timer_clock=clock)
    return app, TestClient(app, base_url="http://127.0.0.1:8765"), clock


def test_api_returns_exact_service_calendar_contract_and_read_only_refresh(db, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    saved_interval(db, NOW - timedelta(hours=2), NOW - timedelta(hours=1), HOUR)
    _, client, _ = setup_api(db)
    before = all_rows(db)
    response = client.get("/api/streaks")
    assert response.status_code == 200
    assert response.json() == {
        "today": "2026-10-21", "timezone": "America/Los_Angeles", "threshold_microseconds": HOUR,
        "current_streak": 1, "streak_through": "2026-10-21",
        "days": [{"date": f"2026-10-{day}", "active_microseconds": HOUR if day == 21 else 0,
                  "qualified": day == 21} for day in range(15, 22)],
    }
    assert client.get("/api/streaks").json() == response.json() and all_rows(db) == before
    reopened = TestClient(create_app(open_database(db.path), timer_clock=FakeClock(NOW)), base_url="http://localhost:8765")
    assert reopened.get("/api/streaks").json() == response.json() and all_rows(db) == before


def test_streak_navigation_settles_expiry_once_without_changing_other_records(db, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    saved_interval(db, NOW - timedelta(hours=2), NOW - timedelta(hours=1), HOUR - 60_000_000)
    app, client, clock = setup_api(db)
    task = create_task(db, "Real expiry")
    start_body = {"task_id": task.id, "duration_minutes": 1, "operation_id": str(uuid4())}
    current = client.post("/api/timer/start", json=start_body).json()["active_session"]
    observed(app.state.timer, clock, 56)
    assert client.get("/api/streaks").json()["current_streak"] == 0
    clock.advance(4)
    view = client.get("/api/streaks").json()
    assert view["current_streak"] == 1 and view["days"][-1]["active_microseconds"] == HOUR
    saved = client.get("/api/timer").json()["last_session"]
    assert saved["id"] == current["id"] and saved["coin_award"] == 1 and saved["tree"]["outcome"] == "mature"
    before = all_rows(db)
    client.post(f"/api/timer/{current['id']}/finish", json={"operation_id": str(uuid4())})
    # A new timer receipt is expected; derived progress, awards and saved records stay unchanged.
    after_finish = all_rows(db)
    assert client.get("/api/streaks").json() == view and all_rows(db) == after_finish
    for table in before:
        if table != "timer_operations":
            assert before[table] == after_finish[table]


@pytest.mark.parametrize("start,end", [
    ("invalid", "2026-10-21T20:00:00.000000Z"),
    ("2026-10-21T20:00:00.000000Z", "2026-10-21T19:59:59.999999Z"),
])
def test_bad_saved_dates_return_structured_actionable_error_and_keep_data(db, monkeypatch, start, end):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    saved_interval(db, start, end, HOUR)
    _, client, _ = setup_api(db)
    before = all_rows(db)
    response = client.get("/api/streaks")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "streak_data_invalid"
    assert "records were kept" in response.json()["error"]["message"]
    assert "no missing time was estimated" in response.json()["error"]["message"]
    assert all_rows(db) == before


def test_streak_api_uses_same_invalid_timezone_error_as_planning(db, monkeypatch):
    _, client, _ = setup_api(db)
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "invalid/zone")
    response = client.get("/api/streaks")
    assert response.status_code == 422
    assert response.json()["error"]["field"] == "timezone"
    assert response.json() == client.get("/api/planning").json()


def test_local_host_boundary_no_mutation_route_and_structured_storage_failure(db, monkeypatch):
    _, client, _ = setup_api(db)
    before = all_rows(db)
    assert client.get("/api/streaks", headers={"Host": "untrusted.example"}).json()["error"]["code"] == "invalid_host"
    assert client.post("/api/streaks", json={}).status_code == 405
    assert client.post("/api/streaks", headers={"Origin": "https://untrusted.example"}).status_code == 403
    assert all_rows(db) == before

    def unavailable():
        raise StorageError("injected disk error")

    monkeypatch.setattr(db, "connect", unavailable)
    response = client.get("/api/streaks")
    assert response.status_code == 503 and response.json()["error"]["code"] == "storage_unavailable"
    assert "try again" in response.json()["error"]["message"]
