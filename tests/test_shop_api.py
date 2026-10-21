"""Shop HTTP validation, local boundaries and retryable failures."""

from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from backend.app import create_app
from backend.domain.rewards import RewardConfig
from tests.test_forest import all_rows
from tests.test_timer import FakeClock, observed


def setup_shop_api(db):
    clock = FakeClock()
    app = create_app(db, timer_clock=clock, reward_config=RewardConfig(birch_price=1))
    client = TestClient(app, base_url="http://127.0.0.1:8765")
    return app, client, clock


def test_api_earn_purchase_start_and_restart_contract(db):
    app, client, clock = setup_shop_api(db)
    view = client.get("/api/shop").json()
    assert view == {
        "balance": 0, "coins_per_minute": 1, "species": [
            {"id": "pine", "name": "Pine", "price": 0, "owned": True},
            {"id": "birch", "name": "Birch", "price": 1, "owned": False},
            {"id": "oak", "name": "Oak", "price": 60, "owned": False},
            {"id": "cherry", "name": "Cherry", "price": 120, "owned": False},
        ], "recent_entries": [],
    }
    task = client.post("/api/tasks", json={"title": "HTTP earned time"}).json()
    start_body = {"task_id": task["id"], "duration_minutes": 1, "operation_id": str(uuid4())}
    session = client.post("/api/timer/start", json=start_body).json()["active_session"]
    assert session["tree"]["species"] == "pine" and session["coin_award"] is None
    observed(app.state.timer, clock, 56)
    clock.advance(4)
    # Shop navigation settles a countdown that expired since its last checkpoint.
    earned = client.get("/api/shop").json()
    assert earned["balance"] == 1 and len(earned["recent_entries"]) == 1
    assert earned["recent_entries"][0]["kind"] == "session_award"
    saved = client.get("/api/timer").json()["last_session"]
    assert saved["coin_award"] == 1 and saved["tree"]["outcome"] == "mature"
    body = {"species": "Birch", "expected_price": 1, "operation_id": str(uuid4())}
    purchase = client.post("/api/shop/purchases", json=body)
    assert purchase.status_code == 201
    assert purchase.json() == {"operation_id": body["operation_id"], "species": "birch", "price": 1, "balance": 0}
    assert client.post("/api/shop/purchases", json=body).json() == purchase.json()
    purchased = client.get("/api/shop").json()
    assert purchased["balance"] == 0 and purchased["species"][1]["owned"]
    assert purchased["recent_entries"][0]["kind"] == "purchase" and purchased["recent_entries"][0]["amount"] == -1
    selected = client.post("/api/timer/start", json={**start_body, "operation_id": str(uuid4()), "species": "birch"})
    assert selected.status_code == 201 and selected.json()["active_session"]["tree"]["species"] == "birch"
    other = TestClient(create_app(db, timer_clock=clock, reward_config=RewardConfig(birch_price=20)), base_url="http://127.0.0.1:8765")
    assert other.get("/api/shop").json()["species"][1]["owned"]
    assert other.post("/api/shop/purchases", json=body).json() == purchase.json()
    assert client.get("/api/tasks").json()["tasks"] == [task]


@pytest.mark.parametrize("changes,status,field", [
    ({"species": "unknown"}, 422, "species"), ({"species": "pine"}, 409, "species"),
    ({"expected_price": 2}, 409, "expected_price"), ({}, 409, "balance"),
    ({"expected_price": -1}, 422, "expected_price"), ({"expected_price": True}, 422, "expected_price"),
    ({"expected_price": "1"}, 422, "expected_price"), ({"operation_id": "invalid"}, 422, "operation_id"),
    ({"species": 1}, 422, "species"), ({"extra": "unexpected"}, 422, "extra"),
])
def test_bad_or_conflicting_purchase_is_structured_and_does_not_write(db, changes, status, field):
    _, client, _ = setup_shop_api(db)
    body = {"species": "birch", "expected_price": 1, "operation_id": str(uuid4()), **changes}
    before = all_rows(db)
    response = client.post("/api/shop/purchases", json=body)
    assert response.status_code == status
    error = response.json()["error"]
    assert error["code"] == ("shop_conflict" if status == 409 else "invalid_input")
    assert error["field"] == field and len(error["message"]) > 15
    assert all_rows(db) == before


def test_unowned_species_start_rejected_and_local_origin_protection_preserved(db):
    _, client, _ = setup_shop_api(db)
    task = client.post("/api/tasks", json={"title": "Local only"}).json()
    before = all_rows(db)
    response = client.post("/api/timer/start", json={
        "task_id": task["id"], "duration_minutes": 1, "operation_id": str(uuid4()), "species": "cherry",
    })
    assert response.status_code == 422 and response.json()["error"]["field"] == "species"
    body = {"species": "birch", "expected_price": 1, "operation_id": str(uuid4())}
    assert client.get("/api/shop", headers={"Host": "evil.example"}).status_code == 400
    foreign = client.post("/api/shop/purchases", json=body, headers={"Origin": "https://evil.example"})
    assert foreign.status_code == 403 and foreign.json()["error"]["code"] == "cross_origin"
    assert all_rows(db) == before


def test_purchase_storage_failure_retains_retry_key_and_returns_actionable_error(db):
    app, client, clock = setup_shop_api(db)
    task = client.post("/api/tasks", json={"title": "Failure recovery"}).json()
    client.post("/api/timer/start", json={"task_id": task["id"], "duration_minutes": 1, "operation_id": str(uuid4())})
    observed(app.state.timer, clock, 60)
    with db.write() as conn:
        conn.execute("CREATE TRIGGER fail_shop_receipt BEFORE INSERT ON shop_operations BEGIN SELECT RAISE(ABORT, 'injected receipt failure'); END")
    before = all_rows(db)
    body = {"species": "birch", "expected_price": 1, "operation_id": str(uuid4())}
    response = client.post("/api/shop/purchases", json=body)
    assert response.status_code == 503 and response.json()["error"]["code"] == "storage_unavailable"
    assert "disk space" in response.json()["error"]["message"] and all_rows(db) == before
    with db.write() as conn:
        conn.execute("DROP TRIGGER fail_shop_receipt")
    assert client.post("/api/shop/purchases", json=body).status_code == 201
    assert client.get("/api/shop").json()["balance"] == 0
    other = {**body, "species": "oak", "expected_price": 60}
    conflict = client.post("/api/shop/purchases", json=other)
    assert conflict.status_code == 409 and conflict.json()["error"]["field"] == "operation_id"
