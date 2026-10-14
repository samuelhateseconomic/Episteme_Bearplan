from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.tasks import list_tasks
from backend.storage.db import Database
from backend.storage.migrations import load_migrations

ORIGIN = "http://127.0.0.1:8765"


def test_health_reports_schema_version(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok", "schema_version": len(load_migrations())}


def test_create_then_list(client: TestClient) -> None:
    created = client.post("/api/tasks", json={"title": " Lab report "}, headers={"Origin": ORIGIN})
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Lab report"
    assert body["created_at"].endswith("Z")
    assert client.get("/api/tasks").json() == {"tasks": [body], "progress": {"completed": 0, "total": 1}}


def test_route_uses_shared_domain_function(client: TestClient, db: Database) -> None:
    client.post("/api/tasks", json={"title": "Via HTTP"})
    assert [t.title for t in list_tasks(db)] == ["Via HTTP"]


def test_blank_title_returns_actionable_error(client: TestClient) -> None:
    response = client.post("/api/tasks", json={"title": "   "})
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "invalid_input", "field": "title", "message": "Enter a task title."}
    }
    assert client.get("/api/tasks").json() == {"tasks": [], "progress": {"completed": 0, "total": 0}}


@pytest.mark.parametrize("payload", [{}, {"title": 5}, {"title": "ok", "extra": 1}, None])
def test_malformed_bodies_are_rejected_without_saving(client: TestClient, payload: object) -> None:
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert client.get("/api/tasks").json() == {"tasks": [], "progress": {"completed": 0, "total": 0}}


def test_non_json_body_uses_error_shape(client: TestClient) -> None:
    response = client.post("/api/tasks", content=b"title=x", headers={"Content-Type": "text/plain"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"


def test_lone_surrogate_title_is_a_validation_error_not_a_crash(client: TestClient) -> None:
    response = client.post(
        "/api/tasks", content=b'{"title": "a\\ud800b"}', headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["field"] == "title"


def test_unknown_api_path_uses_error_shape(client: TestClient) -> None:
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize("host", ["evil.example", "evil.example:8765", "127.0.0.1.evil.example", "192.168.1.5:8765"])
def test_rejects_non_loopback_host(client: TestClient, host: str) -> None:
    response = client.get("/api/tasks", headers={"Host": host})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_host"


@pytest.mark.parametrize("host", ["127.0.0.1:8765", "localhost:8765", "[::1]:8765", "LOCALHOST:8765"])
def test_accepts_loopback_hosts(client: TestClient, host: str) -> None:
    assert client.get("/api/tasks", headers={"Host": host}).status_code == 200


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://evil.example"},
        {"Origin": "http://localhost:3000"},
        {"Origin": "null"},
        {"Origin": "http://127.0.0.1:8765", "Sec-Fetch-Site": "cross-site"},
    ],
)
def test_rejects_cross_origin_mutation(client: TestClient, headers: dict[str, str]) -> None:
    response = client.post("/api/tasks", json={"title": "Injected"}, headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "cross_origin"
    assert client.get("/api/tasks").json() == {"tasks": [], "progress": {"completed": 0, "total": 0}}


def test_same_origin_mutation_through_dev_proxy_is_allowed(client: TestClient) -> None:
    headers = {"Host": "127.0.0.1:5173", "Origin": "http://127.0.0.1:5173", "Sec-Fetch-Site": "same-origin"}
    assert client.post("/api/tasks", json={"title": "From Vite"}, headers=headers).status_code == 201


def test_no_cors_headers_are_granted(client: TestClient) -> None:
    response = client.get("/api/tasks", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in response.headers


def test_serves_built_interface(db: Database, tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<!doctype html><title>BearPlans UI</title>")
    client = TestClient(create_app(db, tmp_path), base_url=ORIGIN)
    assert "BearPlans UI" in client.get("/").text
    assert client.get("/api/tasks").status_code == 200


def test_explains_missing_interface(db: Database, tmp_path: Path) -> None:
    client = TestClient(create_app(db, tmp_path / "missing"), base_url=ORIGIN)
    response = client.get("/")
    assert response.status_code == 503
    assert "launch.py" in response.text


def test_m1_edit_completion_progress_and_removal(client: TestClient) -> None:
    project = client.post("/api/projects", json={"name": "Course"}).json()
    renamed = client.patch(f"/api/projects/{project['id']}", json={"name": "Course renamed"})
    assert renamed.status_code == 200 and renamed.json()["name"] == "Course renamed"
    parent = client.post("/api/tasks", json={"title": "Assignment", "project_id": project["id"]}).json()
    child = client.post("/api/tasks", json={"title": "Draft", "parent_id": parent["id"]}).json()
    edited = client.patch(f"/api/tasks/{child['id']}", json={"title": "Final draft", "notes": "Proof", "deadline": "2026-10-20", "estimate_minutes": 45})
    assert edited.status_code == 200
    assert edited.json()["parent_id"] == parent["id"]
    assert edited.json()["notes"] == "Proof"
    assert edited.json()["deadline"] == "2026-10-20"
    assert edited.json()["estimate_minutes"] == 45
    url = f"/api/tasks?project_id={project['id']}"
    assert client.get(url).json()["progress"] == {"completed": 0, "total": 1}
    completed = client.put(f"/api/tasks/{child['id']}/completion", json={"complete": True})
    assert completed.status_code == 200
    assert client.put(f"/api/tasks/{child['id']}/completion", json={"complete": True}).json() == completed.json()
    for complete in (True, False):
        assert client.put(f"/api/tasks/{parent['id']}/completion", json={"complete": complete}).status_code == 422
    assert client.get(url).json()["progress"] == {"completed": 1, "total": 1}
    assert client.get(url).json()["tasks"][0]["completed"] is True
    removed = client.delete(f"/api/tasks/{child['id']}")
    assert removed.status_code == 200 and removed.json()["completed"] is False
    assert client.get(url).json()["progress"] == {"completed": 0, "total": 1}
    assert client.delete(f"/api/tasks/{parent['id']}").status_code == 422


@pytest.mark.parametrize("payload", [
    {"title": None}, {"notes": "x" * 2001}, {"deadline": "2026-02-30"},
    {"estimate_minutes": True}, {"estimate_minutes": 1.5}, {"estimate_minutes": "30"},
    {"parent_id": "missing"}, {"project_id": "missing"},
])
def test_m1_invalid_edits_leave_everything_unchanged(client: TestClient, payload: dict) -> None:
    created = client.post("/api/tasks", json={"title": "Keep"}).json()
    before = client.get("/api/tasks").json()
    response = client.patch(f"/api/tasks/{created['id']}", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert "field" in response.json()["error"]
    assert client.get("/api/tasks").json() == before


@pytest.mark.parametrize("method,path,payload", [
    ("POST", "/api/projects", {"name": "Injected"}),
    ("PATCH", "/api/projects/{project}", {"name": "Injected"}),
    ("PATCH", "/api/tasks/{child}", {"title": "Injected"}),
    ("PUT", "/api/tasks/{child}/completion", {"complete": True}),
    ("DELETE", "/api/tasks/{child}", None),
])
@pytest.mark.parametrize("headers,status", [({"Origin": "https://evil.example"}, 403), ({"Host": "evil.example"}, 400)])
def test_m1_routes_retain_local_protection(client: TestClient, method, path, payload, headers, status) -> None:
    project = client.post("/api/projects", json={"name": "Keep"}).json()
    parent = client.post("/api/tasks", json={"title": "Keep", "project_id": project["id"]}).json()
    child = client.post("/api/tasks", json={"title": "Keep child", "parent_id": parent["id"]}).json()
    before_tasks = client.get("/api/tasks").json()
    before_projects = client.get("/api/projects").json()
    response = client.request(method, path.format(project=project["id"], child=child["id"]), json=payload, headers=headers)
    assert response.status_code == status
    assert client.get("/api/tasks").json() == before_tasks
    assert client.get("/api/projects").json() == before_projects


def test_failed_database_save_is_actionable_atomic_and_retryable(client: TestClient, db: Database, monkeypatch) -> None:
    from backend.storage import db as storage

    created = client.post("/api/tasks", json={"title": "Keep"}).json()
    before = client.get("/api/tasks").json()
    monkeypatch.setattr(storage, "BUSY_TIMEOUT_MS", 10)
    with db.read() as blocker:  # external SQLite writer, outside the service's write lock
        blocker.execute("BEGIN IMMEDIATE")
        response = client.patch(f"/api/tasks/{created['id']}", json={"title": "Changed", "notes": "New"})
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "storage_unavailable"
        assert "try again" in response.json()["error"]["message"]
        assert client.get("/api/tasks").json() == before
        blocker.execute("ROLLBACK")
    assert client.patch(f"/api/tasks/{created['id']}", json={"title": "Changed", "notes": "New"}).status_code == 200
    assert client.get("/api/tasks").json()["tasks"][0]["notes"] == "New"
