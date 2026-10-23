from datetime import timedelta
from uuid import uuid4

from backend.domain.tasks import create_task
from backend.storage.db import StorageError
from tests.test_forest import all_rows
from tests.test_streaks import HOUR, NOW, saved_interval
from tests.test_streaks_api import setup_api
from tests.test_timer import observed


def test_read_only_api_contract_refresh_and_validation(db, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    saved_interval(db, NOW - timedelta(hours=1), NOW, HOUR)
    _, client, _ = setup_api(db)
    before = all_rows(db)
    response = client.get("/api/statistics")
    assert response.status_code == 200
    body = response.json()
    assert body["today"] == "2026-10-21" and body["timezone"] == "UTC"
    assert body["active_microseconds"] == HOUR and body["session_count"] == 1
    assert body["completion"] == {"completed": 0, "total": 1, "percent": 0}
    assert client.get("/api/statistics").json() == body and all_rows(db) == before
    assert client.post("/api/statistics", json={}).status_code == 405
    assert client.get("/api/statistics", headers={"Host": "external.example"}).status_code == 400
    assert client.post("/api/statistics", headers={"Origin": "https://external.example"}).status_code == 403
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "invalid/zone")
    assert client.get("/api/statistics").json()["error"]["field"] == "timezone"


def test_statistics_navigation_settles_expiry_once_with_unchanged_task_and_one_award(db, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    app, client, clock = setup_api(db)
    task = create_task(db, "Report expiry")
    app.state.timer.start(task.id, 1, str(uuid4()))
    observed(app.state.timer, clock, 56)
    assert client.get("/api/statistics").json()["active_microseconds"] == 0
    clock.advance(4)
    view = client.get("/api/statistics").json()
    assert view["active_microseconds"] == 60_000_000 and view["session_count"] == 1
    before = all_rows(db)
    assert client.get("/api/statistics").json() == view and all_rows(db) == before
    assert len(before["trees"]) == len(before["coin_ledger"]) == 1
    assert view["completion"]["completed"] == 0


def test_structured_storage_and_corrupt_interval_errors_keep_records(db, monkeypatch):
    saved_interval(db, "invalid", "2026-10-21T20:00:00Z", HOUR)
    _, client, _ = setup_api(db)
    before = all_rows(db)
    result = client.get("/api/statistics")
    assert result.status_code == 503 and "records were kept" in result.json()["error"]["message"]
    assert all_rows(db) == before
    def unavailable():
        raise StorageError("injected storage failure")
    monkeypatch.setattr(db, "connect", unavailable)
    result = client.get("/api/statistics")
    assert result.status_code == 503 and result.json()["error"]["code"] == "storage_unavailable"
