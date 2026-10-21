"""Real local process restart with synthetic data and configured zero-price shop."""

import os
import subprocess
import sys
from uuid import uuid4

from tests.conftest import ROOT, free_port, http_json, running_service


def test_shop_ownership_receipt_selected_tree_and_zero_award_survive_process_restart(tmp_path, monkeypatch):
    monkeypatch.setenv("BEARPLANS_BIRCH_PRICE", "0")
    data_dir = tmp_path / "ShopRestart"
    key = str(uuid4())
    purchase_body = {"species": "birch", "expected_price": 0, "operation_id": key}
    with running_service(data_dir) as first:
        status, purchase = http_json("POST", f"{first.url}/api/shop/purchases", purchase_body)
        assert status == 201 and purchase["balance"] == 0
        _, task = http_json("POST", f"{first.url}/api/tasks", {"title": "Synthetic species session"})
        start_body = {"task_id": task["id"], "duration_minutes": 1, "species": "birch", "operation_id": str(uuid4())}
        _, started = http_json("POST", f"{first.url}/api/timer/start", start_body)
        current = started["active_session"]
        _, paused = http_json("POST", f"{first.url}/api/timer/{current['id']}/pause", {"expected_revision": current["revision"]})
        session = paused["active_session"]
        assert session["state"] == "paused" and session["tree"]["species"] == "birch"
        assert first.stop() == 0
    # Configuration changes cannot rewrite an original purchase receipt.
    monkeypatch.setenv("BEARPLANS_BIRCH_PRICE", "30")
    with running_service(data_dir) as second:
        assert http_json("POST", f"{second.url}/api/shop/purchases", purchase_body) == (201, purchase)
        _, view = http_json("GET", f"{second.url}/api/shop")
        assert view["species"][1] == {"id": "birch", "name": "Birch", "price": 30, "owned": True}
        assert http_json("GET", f"{second.url}/api/timer")[1]["active_session"] == session
        finish_body = {"operation_id": str(uuid4()), "expected_revision": session["revision"]}
        _, finished = http_json("POST", f"{second.url}/api/timer/{session['id']}/finish", finish_body)
        saved = finished["last_session"]
        assert saved["coin_award"] == 0 and saved["tree"]["species"] == "birch"
        assert second.stop() == 0
    with running_service(data_dir) as third:
        assert http_json("POST", f"{third.url}/api/timer/{session['id']}/finish", finish_body)[1]["last_session"] == saved
        assert http_json("POST", f"{third.url}/api/timer/start", start_body)[1]["last_session"] == saved
        entries = http_json("GET", f"{third.url}/api/shop")[1]["recent_entries"]
        assert len(entries) == 2 and [e["amount"] for e in entries] == [0, 0]
        assert http_json("GET", f"{third.url}/api/forest")[1]["trees"][0]["species"] == "birch"
        assert third.stop() == 0


def test_invalid_reward_configuration_fails_before_creating_user_data(tmp_path):
    data_dir = tmp_path / "InvalidConfig"
    result = subprocess.run(
        [sys.executable, "-m", "backend", "--no-browser", "--port", str(free_port())],
        cwd=ROOT, env={**os.environ, "BEARPLANS_DATA_DIR": str(data_dir), "BEARPLANS_COINS_PER_MINUTE": "wrong"},
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 1 and "BEARPLANS_COINS_PER_MINUTE" in result.stderr
    assert "BearPlans cannot start" in result.stderr and "Traceback" not in result.stderr
    assert not data_dir.exists()
