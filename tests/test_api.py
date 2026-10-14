from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.tasks import list_tasks
from backend.storage.db import Database

ORIGIN = "http://127.0.0.1:8765"


def test_health_reports_schema_version(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok", "schema_version": 1}


def test_create_then_list(client: TestClient) -> None:
    created = client.post("/api/tasks", json={"title": " Lab report "}, headers={"Origin": ORIGIN})
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Lab report"
    assert body["created_at"].endswith("Z")
    assert client.get("/api/tasks").json() == {"tasks": [body]}


def test_route_uses_shared_domain_function(client: TestClient, db: Database) -> None:
    client.post("/api/tasks", json={"title": "Via HTTP"})
    assert [t.title for t in list_tasks(db)] == ["Via HTTP"]


def test_blank_title_returns_actionable_error(client: TestClient) -> None:
    response = client.post("/api/tasks", json={"title": "   "})
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "invalid_input", "field": "title", "message": "Enter a task title."}
    }
    assert client.get("/api/tasks").json() == {"tasks": []}


@pytest.mark.parametrize("payload", [{}, {"title": 5}, {"title": "ok", "extra": 1}, None])
def test_malformed_bodies_are_rejected_without_saving(client: TestClient, payload: object) -> None:
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_input"
    assert client.get("/api/tasks").json() == {"tasks": []}


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
    assert client.get("/api/tasks").json() == {"tasks": []}


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
