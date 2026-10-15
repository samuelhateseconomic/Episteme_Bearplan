"""HTTP planning contracts, safe failures and the existing loopback boundary."""

import pytest
from fastapi.testclient import TestClient

from backend.domain.planning import list_placements
from backend.domain.tasks import create_task, list_tasks
from backend.storage.db import Database


def make_task(client: TestClient, title: str = "Work") -> dict:
    response = client.post("/api/tasks", json={"title": title, "deadline": "2026-10-30", "notes": "Keep"})
    assert response.status_code == 201
    return response.json()


def assign(client: TestClient, task_id: str, day: str) -> dict:
    response = client.post("/api/placements", json={"task_id": task_id, "planned_date": day})
    assert response.status_code == 201
    return response.json()


def test_assign_move_unschedule_keeps_one_task_and_separate_deadline(client: TestClient, db: Database) -> None:
    task = make_task(client)
    first = assign(client, task["id"], "2026-10-15")
    second = assign(client, task["id"], "2026-10-16")
    moved = client.patch(f"/api/placements/{first['id']}", json={"planned_date": "2026-10-22"})
    assert moved.status_code == 200
    assert moved.json()["id"] == first["id"]
    assert moved.json()["planned_date"] == "2026-10-22"
    snapshot = client.get("/api/planning", params={"week": "2026-10-21"})
    assert snapshot.status_code == 200
    body = snapshot.json()
    assert (body["week_start"], body["week_end"]) == ("2026-10-19", "2026-10-25")
    assert body["today"] and body["timezone"]
    assert body["tasks"] == [task]
    assert {p["id"]: p for p in body["placements"]} == {first["id"]: moved.json(), second["id"]: second}
    removed = client.delete(f"/api/placements/{first['id']}")
    assert removed.status_code == 200 and removed.json() == {"removed": first["id"]}
    assert client.get("/api/tasks").json()["tasks"] == [task]
    assert [p.model_dump(mode="json") for p in list_placements(db)] == [second]
    assert len(list_tasks(db)) == 1


def test_duplicate_assignment_and_move_return_clear_conflicts_without_mutation(client: TestClient) -> None:
    task = make_task(client)
    first = assign(client, task["id"], "2026-10-15")
    assign(client, task["id"], "2026-10-22")
    before = client.get("/api/planning").json()
    for method, path, payload in (
        ("POST", "/api/placements", {"task_id": task["id"], "planned_date": "2026-10-15"}),
        ("PATCH", f"/api/placements/{first['id']}", {"planned_date": "2026-10-22"}),
    ):
        response = client.request(method, path, json=payload)
        assert response.status_code == 409
        error = response.json()["error"]
        assert error["code"] == "placement_conflict"
        assert "already" in error["message"].lower()
        assert client.get("/api/planning").json() == before


def test_completed_state_comes_from_shared_task_in_all_weeks(client: TestClient) -> None:
    parent = make_task(client, "Assignment")
    child = client.post("/api/tasks", json={"title": "Proof", "parent_id": parent["id"]}).json()
    first = assign(client, child["id"], "2026-10-15")
    second = assign(client, child["id"], "2026-10-22")
    for complete in (True, False):
        assert client.put(f"/api/tasks/{child['id']}/completion", json={"complete": complete}).status_code == 200
        for week in ("2026-10-12", "2026-10-19"):
            snapshot = client.get("/api/planning", params={"week": week}).json()
            assert all(task["completed"] is complete for task in snapshot["tasks"])
            assert {p["id"]: p for p in snapshot["placements"]} == {first["id"]: first, second["id"]: second}
        assert client.get("/api/tasks").json()["progress"] == {"completed": int(complete), "total": 1}


@pytest.mark.parametrize("payload", [
    {}, {"task_id": "missing", "planned_date": "2026-10-15"},
    {"task_id": None, "planned_date": "2026-10-15"},
    {"task_id": 5, "planned_date": "2026-10-15"},
    {"task_id": "{task}", "planned_date": "2026-02-30"},
    {"task_id": "{task}", "planned_date": "20261015"},
    {"task_id": "{task}", "planned_date": "2026-10-15T12:00:00Z"},
    {"task_id": "{task}", "planned_date": None},
    {"task_id": "{task}", "planned_date": "2026-10-15", "complete": True},
    None,
])
def test_invalid_assignments_use_error_shape_without_changes(client: TestClient, payload) -> None:
    task = make_task(client)
    if payload is not None:
        payload = {key: task["id"] if value == "{task}" else value for key, value in payload.items()}
    before = client.get("/api/planning").json()
    response = client.post("/api/placements", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert response.json()["error"]["message"]
    assert client.get("/api/planning").json() == before


@pytest.mark.parametrize("payload", [{}, {"planned_date": None}, {"planned_date": "2026-02-30"},
                                        {"planned_date": "2026-10-20", "task_id": "another"}])
def test_invalid_moves_preserve_source_placement(client: TestClient, payload) -> None:
    task = make_task(client)
    placement = assign(client, task["id"], "2026-10-15")
    before = client.get("/api/planning").json()
    response = client.patch(f"/api/placements/{placement['id']}", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert client.get("/api/planning").json() == before


@pytest.mark.parametrize("week", ["20261015", "2026-02-30", "2026-10-15T00:00:00Z", "9999-12-31"])
def test_invalid_week_queries_use_structured_errors(client: TestClient, week: str) -> None:
    response = client.get("/api/planning", params={"week": week})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_unknown_placement_update_and_removal_are_actionable(client: TestClient) -> None:
    for method, payload in (("PATCH", {"planned_date": "2026-10-15"}), ("DELETE", None)):
        response = client.request(method, "/api/placements/missing", json=payload)
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_input"
        assert response.json()["error"]["message"]


def test_scheduled_parent_conversion_and_subtask_deletion_require_unscheduling(client: TestClient) -> None:
    parent = make_task(client, "Standalone")
    placement = assign(client, parent["id"], "2026-10-15")
    before = client.get("/api/planning").json()
    assert client.post("/api/tasks", json={"title": "Work", "parent_id": parent["id"]}).status_code == 422
    assert client.get("/api/planning").json() == before
    assert client.delete(f"/api/placements/{placement['id']}").status_code == 200
    child = client.post("/api/tasks", json={"title": "Work", "parent_id": parent["id"]}).json()
    assert client.post("/api/placements", json={"task_id": parent["id"], "planned_date": "2026-10-15"}).status_code == 422
    placement = assign(client, child["id"], "2026-10-15")
    before = client.get("/api/planning").json()
    assert client.delete(f"/api/tasks/{child['id']}").status_code == 422
    assert client.get("/api/planning").json() == before
    assert client.delete(f"/api/placements/{placement['id']}").status_code == 200
    assert client.delete(f"/api/tasks/{child['id']}").status_code == 200


@pytest.mark.parametrize("method", ["POST", "PATCH", "DELETE"])
def test_failed_planning_saves_are_actionable_atomic_and_retryable(client: TestClient, db: Database, monkeypatch, method: str) -> None:
    from backend.storage import db as storage

    task = make_task(client)
    placement = assign(client, task["id"], "2026-10-15")
    before = client.get("/api/planning").json()
    path = "/api/placements" if method == "POST" else f"/api/placements/{placement['id']}"
    payload = {"task_id": task["id"], "planned_date": "2026-10-22"} if method == "POST" else (
        {"planned_date": "2026-10-22"} if method == "PATCH" else None
    )
    monkeypatch.setattr(storage, "BUSY_TIMEOUT_MS", 10)
    with db.read() as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        response = client.request(method, path, json=payload)
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "storage_unavailable"
        assert "try again" in response.json()["error"]["message"]
        assert client.get("/api/planning").json() == before
        blocker.execute("ROLLBACK")
    retried = client.request(method, path, json=payload)
    assert retried.status_code == (201 if method == "POST" else 200)
    assert client.get("/api/tasks").json()["tasks"] == [task]


@pytest.mark.parametrize("method", ["POST", "PATCH", "DELETE"])
@pytest.mark.parametrize("headers,status", [({"Origin": "https://evil.example"}, 403), ({"Host": "evil.example"}, 400)])
def test_planning_mutations_retain_local_protection(client: TestClient, method: str, headers, status: int) -> None:
    task = make_task(client)
    placement = assign(client, task["id"], "2026-10-15")
    before = client.get("/api/planning").json()
    path = "/api/placements" if method == "POST" else f"/api/placements/{placement['id']}"
    payload = {"task_id": task["id"], "planned_date": "2026-10-22"} if method == "POST" else (
        {"planned_date": "2026-10-22"} if method == "PATCH" else None
    )
    response = client.request(method, path, json=payload, headers=headers)
    assert response.status_code == status
    assert client.get("/api/planning").json() == before
