"""Typed timer HTTP controls, repeat requests and the loopback boundary."""

import sqlite3
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.storage.db import Database
from tests.test_timer import FakeClock, stored


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


@pytest.mark.parametrize("subtask", [False, True])
def test_stale_tab_cannot_start_completed_leaf(timer_client, db: Database, subtask):
    client, _ = timer_client
    parent = task(client) if subtask else None
    work = client.post("/api/tasks", json={
        "title": "Initially eligible", "parent_id": parent["id"] if parent else None,
    }).json()
    # A second tab completes work after the first tab has loaded its choices.
    stale_choice = next(row for row in client.get("/api/tasks").json()["tasks"] if row["id"] == work["id"])
    assert not stale_choice["completed"]
    second = TestClient(client.app, base_url="http://127.0.0.1:8765")
    completed = second.put(f"/api/tasks/{work['id']}/completion", json={"complete": True})
    assert completed.status_code == 200
    before = stored(db)
    key = str(uuid4())
    rejected = start(client, stale_choice["id"], operation_id=key)
    assert rejected.status_code == 422
    error = rejected.json()["error"]
    assert error["code"] == "invalid_input" and error["field"] == "task_id"
    assert "complete" in error["message"] and "Reopen" in error["message"]
    assert stored(db) == before
    assert client.get("/api/timer").json()["active_session"] is None
    assert next(row for row in client.get("/api/tasks").json()["tasks"] if row["id"] == work["id"]) == completed.json()
    second.put(f"/api/tasks/{work['id']}/completion", json={"complete": False})
    assert start(client, work["id"], operation_id=key).status_code == 201


def test_api_completion_keeps_session_and_acknowledged_start_replay(timer_client, db: Database):
    client, clock = timer_client
    work = task(client)
    key = str(uuid4())
    original = start(client, work["id"], operation_id=key).json()["active_session"]
    clock.advance(2)
    running = client.get("/api/timer").json()["active_session"]
    completed = client.put(f"/api/tasks/{work['id']}/completion", json={"complete": True}).json()
    before = stored(db)
    assert start(client, work["id"], operation_id=key).json()["active_session"] == running
    assert stored(db) == before
    paused = client.post(f"/api/timer/{original['id']}/pause", json={"expected_revision": 1})
    assert paused.status_code == 200 and paused.json()["active_session"]["state"] == "paused"
    saved = client.post(f"/api/timer/{original['id']}/finish", json={}).json()["last_session"]
    assert saved["id"] == original["id"] and saved["task_id"] == work["id"]
    assert saved["active_seconds"] == 2 and saved["outcome"] == "finished_early"
    assert client.get("/api/tasks").json()["tasks"] == [completed]
    before = stored(db)
    assert start(client, work["id"], operation_id=key).json()["last_session"] == saved
    assert start(client, work["id"]).status_code == 422
    assert stored(db) == before


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
    saved = client.post(f"/api/timer/{session['id']}/finish", json={
        "discard_uncertain": True, "expected_revision": review["revision"],
    })
    assert saved.status_code == 200
    assert saved.json()["last_session"]["outcome"] == "interrupted"
    assert saved.json()["last_session"]["active_seconds"] == 2


@pytest.mark.parametrize("resolution", ["resume", "finish"])
def test_api_recovery_retains_session_and_replays_without_duplicate_intervals(timer_client, db: Database, resolution):
    client, clock = timer_client
    work = task(client)
    session = start(client, work["id"]).json()["active_session"]
    clock.advance(2.5)
    client.get("/api/timer")
    clock.advance(30)
    review = client.get("/api/timer").json()["active_session"]
    recovery = review["recovery"]
    assert recovery["kind"] == "checkpoint_gap"
    assert recovery["confirmed_active_seconds"] == 2.5
    assert recovery["resolved_at"] is None and recovery["resolution"] is None
    payload = {"resolution": resolution, "expected_revision": review["revision"],
               "operation_id": str(uuid4()), "discard_uncertain": True}
    response = client.post(f"/api/timer/{session['id']}/recover", json=payload)
    assert response.status_code == 200
    saved = response.json()["active_session" if resolution == "resume" else "last_session"]
    assert saved["id"] == session["id"] and saved["active_seconds"] == 2.5
    assert saved["recovery"]["id"] == recovery["id"]
    assert saved["recovery"]["resolution"] == resolution
    assert saved["recovery"]["resolved_at"] is not None
    assert saved["state"] == ("running" if resolution == "resume" else "finished")
    assert client.post(f"/api/timer/{session['id']}/recover", json=payload).json() == response.json()
    with db.read() as conn:
        assert conn.execute("SELECT COUNT(*) FROM timer_intervals").fetchone()[0] == (2 if resolution == "resume" else 1)
        assert conn.execute("SELECT COUNT(*) FROM timer_interruptions").fetchone()[0] == 1
    assert client.get("/api/tasks").json()["tasks"] == [work]


@pytest.mark.parametrize("patch", [
    {"resolution": "pause"}, {"resolution": True}, {"expected_revision": True},
    {"expected_revision": "2"}, {"expected_revision": 0}, {"expected_revision": 1.5},
    {"operation_id": "invalid"}, {"discard_uncertain": False}, {"discard_uncertain": "true"},
    {"discard_uncertain": 1}, {"extra": "invalid"},
])
def test_api_recovery_rejects_invalid_payload_without_mutation(timer_client, db: Database, patch):
    client, clock = timer_client
    session = start(client, task(client)["id"]).json()["active_session"]
    clock.advance(10)
    review = client.get("/api/timer").json()["active_session"]
    payload = {"resolution": "resume", "expected_revision": review["revision"],
               "operation_id": str(uuid4()), "discard_uncertain": True, **patch}
    before = stored(db)
    response = client.post(f"/api/timer/{session['id']}/recover", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert stored(db) == before
    assert client.get("/api/timer").json()["active_session"] == review


def test_api_recovery_requires_every_review_field_and_preserves_origin_boundary(timer_client):
    client, clock = timer_client
    session = start(client, task(client)["id"]).json()["active_session"]
    clock.advance(10)
    review = client.get("/api/timer").json()["active_session"]
    payload = {"resolution": "resume", "expected_revision": review["revision"],
               "operation_id": str(uuid4()), "discard_uncertain": True}
    for field in payload:
        incomplete = {key: value for key, value in payload.items() if key != field}
        assert client.post(f"/api/timer/{session['id']}/recover", json=incomplete).status_code == 422
    for headers, status in [({"Host": "evil.example"}, 400), ({"Origin": "https://evil.example"}, 403)]:
        assert client.post(f"/api/timer/{session['id']}/recover", json=payload, headers=headers).status_code == status
    assert client.get("/api/timer").json()["active_session"] == review


def test_api_legacy_review_finish_requires_current_revision(timer_client):
    client, clock = timer_client
    session = start(client, task(client)["id"]).json()["active_session"]
    clock.advance(10)
    review = client.get("/api/timer").json()["active_session"]
    for payload in [{"discard_uncertain": True}, {"discard_uncertain": True, "expected_revision": 1}]:
        response = client.post(f"/api/timer/{session['id']}/finish", json=payload)
        assert response.status_code == 409 and response.json()["error"]["field"] == "revision"
    assert client.get("/api/timer").json()["active_session"] == review


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
