"""Read-only forest HTTP contract follows the shared timer application functions."""

from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app import create_app
from tests.test_timer import FakeClock


def test_forest_api_lists_finalized_outcomes_with_historical_session_context(db):
    clock = FakeClock()
    client = TestClient(create_app(db, timer_clock=clock), base_url="http://127.0.0.1:8765")
    assert client.get("/api/forest").json() == {"trees": []}
    task = client.post("/api/tasks", json={"title": "HTTP forest work"}).json()
    session = client.post("/api/timer/start", json={
        "task_id": task["id"], "duration_minutes": 1, "operation_id": str(uuid4()),
    }).json()["active_session"]
    assert session["tree"]["stage"] == "seedling" and session["tree"]["progress"] == 0
    assert client.get("/api/forest").json() == {"trees": []}
    clock.advance(2.5)
    saved = client.post(f"/api/timer/{session['id']}/finish", json={
        "expected_revision": session["revision"], "operation_id": str(uuid4()),
    }).json()["last_session"]
    trees = client.get("/api/forest").json()["trees"]
    assert len(trees) == 1
    tree = trees[0]
    assert tree["session_id"] == session["id"] and tree["id"] == session["tree"]["id"]
    assert tree["species"] == "pine" and tree["outcome"] == "unfinished"
    assert tree["stage"] == "seedling" and tree["active_seconds"] == 2.5
    assert tree["progress"] == 2.5 / 60 and tree["task_title"] == "HTTP forest work"
    assert tree["duration_minutes"] == 1 and tree["started_at"] == session["started_at"]
    assert tree["finished_at"] == saved["finished_at"]
    assert client.get("/api/tasks").json()["tasks"] == [task]
    other = TestClient(create_app(db, timer_clock=clock), base_url="http://127.0.0.1:8765")
    assert other.get("/api/forest").json() == {"trees": trees}


def test_forest_is_read_only_and_local_host_boundary_is_preserved(client):
    response = client.get("/api/forest", headers={"Host": "evil.example"})
    assert response.status_code == 400 and response.json()["error"]["code"] == "invalid_host"
    assert client.post("/api/forest", json={}).status_code == 405
    assert client.get("/api/forest").json() == {"trees": []}
