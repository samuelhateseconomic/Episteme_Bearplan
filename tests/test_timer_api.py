"""Typed timer HTTP controls, repeat requests and the loopback boundary."""

import sqlite3
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.storage.db import Database
from tests.test_timer import FakeClock


@pytest.fixture
def timer_client(db: Database):
    clock = FakeClock()
    client = TestClient(create_app(db, timer_clock=clock), base_url="http://127.0.0.1:8765")
    return client, clock


def start(client: TestClient, task_id: str, *, operation_id: str | None = None):
    return client.post("/api/timer/start", json={
        "task_id": task_id, "duration_minutes": 1, "operation_id": operation_id or str(uuid4()),
    })


def task(client: TestClient):
    return client.post("/api/tasks", json={"title": "Unscheduled", "deadline": "2026-10-30"}).json()


def test_api_refresh_cross_client_controls_and_saved_result(timer_client, db: Database):
    client, clock = timer_client
    work = task(client)
    key = str(uuid4())
    response = start(client, work["id"], operation_id=key)
    assert response.status_code == 201
    session = response.json()["active_session"]
    assert session["start_operation_id"] == key and session["requested_seconds"] == 60
    assert set(response.json()) == {"server_now", "active_session", "last_session"}
    # Different browser clients use the very same application timer instance.
    second = TestClient(client.app, base_url="http://127.0.0.1:8765")
    clock.advance(1.25)
    refreshed = second.get("/api/timer").json()["active_session"]
    assert refreshed["id"] == session["id"] and refreshed["active_seconds"] == 1.25
    assert refreshed["revision"] == session["revision"]
    conflict = start(second, work["id"])
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "timer_conflict"
    paused = second.post(f"/api/timer/{session['id']}/pause", json={"expected_revision": 1}).json()["active_session"]
    clock.advance(100)
    assert client.get("/api/timer").json()["active_session"] == paused
    resumed = client.post(f"/api/timer/{session['id']}/resume", json={"expected_revision": paused["revision"]})
    assert resumed.status_code == 200
    stale = second.post(f"/api/timer/{session['id']}/pause", json={"expected_revision": 1})
    assert stale.status_code == 409 and "another tab" in stale.json()["error"]["message"]
    clock.advance(0.75)
    finish_payload = {"expected_revision": 3, "operation_id": str(uuid4())}
    saved = client.post(f"/api/timer/{session['id']}/finish", json=finish_payload)
    assert saved.status_code == 200 and saved.json()["active_session"] is None
    result = saved.json()["last_session"]
    assert result["active_seconds"] == 2 and result["outcome"] == "finished_early"
    assert second.post(f"/api/timer/{session['id']}/finish", json=finish_payload).json()["last_session"] == result
    assert client.get("/api/tasks").json()["tasks"] == [work]
    assert client.get("/api/timer").json()["last_session"] == result


@pytest.mark.parametrize("body", [
    {}, {"task_id": "{task}", "duration_minutes": 0, "operation_id": "{key}"},
    {"task_id": "{task}", "duration_minutes": 181, "operation_id": "{key}"},
    {"task_id": "{task}", "duration_minutes": 1.5, "operation_id": "{key}"},
    {"task_id": "{task}", "duration_minutes": True, "operation_id": "{key}"},
    {"task_id": "{task}", "duration_minutes": "1", "operation_id": "{key}"},
    {"task_id": "{task}", "duration_minutes": 1, "operation_id": "invalid"},
    {"task_id": "missing", "duration_minutes": 1, "operation_id": "{key}"},
    {"task_id": "{task}", "duration_minutes": 1, "operation_id": "{key}", "complete": True},
])
def test_invalid_start_is_structured_without_saved_result(timer_client, body):
    client, _ = timer_client
    work = task(client)
    values = {"{task}": work["id"], "{key}": str(uuid4())}
    payload = {key: values.get(value, value) if isinstance(value, str) else value for key, value in body.items()}
    response = client.post("/api/timer/start", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert client.get("/api/timer").json()["active_session"] is None


def test_api_review_requires_explicit_discard_and_retains_confirmed_time(timer_client):
    client, clock = timer_client
    session = start(client, task(client)["id"]).json()["active_session"]
    clock.advance(2)
    client.get("/api/timer")
    clock.advance(20)
    review = client.get("/api/timer").json()["active_session"]
    assert review["state"] == "needs_review" and review["active_seconds"] == 2
    response = client.post(f"/api/timer/{session['id']}/finish", json={})
    assert response.status_code == 409 and response.json()["error"]["field"] == "discard_uncertain"
    saved = client.post(f"/api/timer/{session['id']}/finish", json={"discard_uncertain": True})
    assert saved.status_code == 200
    assert saved.json()["last_session"]["outcome"] == "interrupted"
    assert saved.json()["last_session"]["active_seconds"] == 2


def test_timer_failed_save_is_actionable_and_same_operation_retries(timer_client, db: Database, monkeypatch):
    from backend.storage import db as storage

    client, _ = timer_client
    work = task(client)
    key = str(uuid4())
    monkeypatch.setattr(storage, "BUSY_TIMEOUT_MS", 10)
    with db.read() as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        failed = start(client, work["id"], operation_id=key)
        assert failed.status_code == 503
        assert failed.json()["error"]["code"] == "storage_unavailable"
        assert "try again" in failed.json()["error"]["message"]
        blocker.execute("ROLLBACK")
    saved = start(client, work["id"], operation_id=key)
    assert saved.status_code == 201
    assert start(client, work["id"], operation_id=key).json() == saved.json()
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timer_sessions").fetchone()[0] == 1


@pytest.mark.parametrize("action", ["start", "pause", "resume", "finish"])
@pytest.mark.parametrize("headers,status", [({"Host": "evil.example"}, 400), ({"Origin": "https://evil.example"}, 403)])
def test_timer_mutations_preserve_local_protection(timer_client, action, headers, status):
    client, _ = timer_client
    work = task(client)
    session = start(client, work["id"]).json()["active_session"]
    before = client.get("/api/timer").json()
    path = "/api/timer/start" if action == "start" else f"/api/timer/{session['id']}/{action}"
    payload = {"task_id": work["id"], "duration_minutes": 1, "operation_id": str(uuid4())} if action == "start" else {"expected_revision": 1}
    assert client.post(path, json=payload, headers=headers).status_code == status
    assert client.get("/api/timer").json() == before
