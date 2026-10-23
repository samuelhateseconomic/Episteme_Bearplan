from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.corrections import list_saved_sessions
from backend.storage.db import StorageError, open_database
from tests.test_corrections import HOUR, NOW, draft_for, seeded
from tests.test_forest import all_rows
from tests.test_timer import FakeClock


def client_for(db):
    return TestClient(create_app(db, timer_clock=FakeClock(NOW)), base_url="http://127.0.0.1:8765")


def test_preview_apply_lost_response_retry_restart_and_history_contract(db, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    session, _ = seeded(db)
    client = client_for(db)
    before = all_rows(db)
    sessions = client.get("/api/sessions")
    assert sessions.status_code == 200 and sessions.json()["sessions"] == list_saved_sessions(db)
    draft = draft_for(db, session, [HOUR // 2]).model_dump()
    preview = client.post(f"/api/sessions/{session}/correction/preview", json=draft)
    assert preview.status_code == 200 and all_rows(db) == before
    body = {**draft, "operation_id": str(uuid4()), "preview_token": preview.json()["preview_token"]}
    applied = client.post(f"/api/sessions/{session}/correction", json=body)
    assert applied.status_code == 200 and applied.json()["coin_delta"] == -30
    saved = all_rows(db)
    reopened = client_for(open_database(db.path))
    assert reopened.post(f"/api/sessions/{session}/correction", json=body).json() == applied.json()
    history = reopened.get("/api/sessions").json()["sessions"][0]
    assert history["history"][0]["before"][0]["active_microseconds"] == HOUR
    assert history["coin_contribution"] == 30 and history["intervals"][0]["maximum_microseconds"] == HOUR
    assert reopened.get("/api/statistics").json()["active_microseconds"] == HOUR // 2
    assert reopened.get("/api/streaks").json()["current_streak"] == 0
    assert reopened.get("/api/shop").json()["recent_entries"][0]["kind"] == "session_adjustment"
    assert all_rows(db) == saved
    changed = reopened.post(f"/api/sessions/{session}/correction", json={**body, "reason": "Different work"})
    assert changed.status_code == 409 and changed.json()["error"]["code"] == "correction_conflict"


@pytest.mark.parametrize("updates", [{"expected_revision": True}, {"expected_revision": "1"}, {"unknown": "bad"},
                                      {"intervals": [{"id": "bad", "active_microseconds": True}]},
                                      {"intervals": [{"id": "bad", "active_microseconds": 0.1}]}])
def test_request_validation_and_local_request_boundary(db, updates):
    session, _ = seeded(db)
    client = client_for(db)
    draft = draft_for(db, session, [HOUR // 2]).model_dump()
    before = all_rows(db)
    path = f"/api/sessions/{session}/correction/preview"
    assert client.post(path, json={**draft, **updates}).status_code == 422
    assert client.post(path, json=draft, headers={"Origin": "https://external.example"}).status_code == 403
    assert client.get("/api/sessions", headers={"Host": "external.example"}).status_code == 400
    assert all_rows(db) == before


def test_stale_preview_and_storage_failure_have_actionable_errors_and_no_changes(db, monkeypatch):
    session, _ = seeded(db)
    client = client_for(db)
    draft = draft_for(db, session, [HOUR // 2]).model_dump()
    preview = client.post(f"/api/sessions/{session}/correction/preview", json=draft).json()
    before = all_rows(db)
    path = f"/api/sessions/{session}/correction"
    body = {**draft, "operation_id": str(uuid4()), "preview_token": "wrong"}
    assert client.post(path, json=body).status_code == 409 and all_rows(db) == before
    def unavailable():
        raise StorageError("Injected storage failure")
    monkeypatch.setattr(db, "connect", unavailable)
    response = client.post(path, json={**body, "preview_token": preview["preview_token"]})
    assert response.status_code == 503 and response.json()["error"]["code"] == "storage_unavailable"


def test_missing_current_adjustment_ledger_cannot_silently_restore_spendable_coins(db):
    session, _ = seeded(db)
    client = client_for(db)
    draft = draft_for(db, session, [0]).model_dump()
    token = client.post(f"/api/sessions/{session}/correction/preview", json=draft).json()["preview_token"]
    assert client.post(f"/api/sessions/{session}/correction", json={**draft, "operation_id": str(uuid4()), "preview_token": token}).status_code == 200
    with db.write() as conn:
        conn.execute("DROP TABLE coin_adjustments")  # Disposable runtime-corruption fixture only.
    before = all_rows(db)
    assert client.get("/api/shop").status_code == 503
    purchase = client.post("/api/shop/purchases", json={"species": "birch", "expected_price": 30, "operation_id": str(uuid4())})
    assert purchase.status_code == 503 and purchase.json()["error"]["code"] == "storage_unavailable"
    assert all_rows(db) == before
