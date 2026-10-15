"""Closed historical weeks and idempotent carryover survive real process restarts."""

from pathlib import Path
from uuid import uuid4

from tests.conftest import Service, free_port, http_json, running_service


def test_closed_history_carryover_and_retry_survive_service_and_launcher_restart(tmp_path: Path) -> None:
    data_dir = tmp_path / "HistoryData"
    port = free_port()
    first = Service(data_dir, port, via_launcher=True).start()
    week = "2026-10-12"
    try:
        status, project = http_json("POST", f"{first.url}/api/projects", {"name": "Original course"})
        assert status == 201
        status, parent = http_json("POST", f"{first.url}/api/tasks", {"title": "Original assignment", "project_id": project["id"]})
        assert status == 201
        status, child = http_json("POST", f"{first.url}/api/tasks", {
            "title": "Original proof", "parent_id": parent["id"], "notes": "Original notes",
            "deadline": "2026-10-30", "estimate_minutes": 45,
        })
        assert status == 201
        status, placement = http_json("POST", f"{first.url}/api/placements", {"task_id": child["id"], "planned_date": "2026-10-15"})
        assert status == 201
        status, preview = http_json("GET", f"{first.url}/api/weeks/{week}/close-preview")
        assert status == 200
        close_payload = {"preview_token": preview["preview_token"]}
        status, history = http_json("POST", f"{first.url}/api/weeks/{week}/close", close_payload)
        assert status == 200 and history["completed"] == 0 and history["total"] == 1
        assert first.stop() == 0
    finally:
        first.kill()

    with running_service(data_dir, port) as second:
        status, planning = http_json("GET", f"{second.url}/api/planning?week={week}")
        assert status == 200 and planning["closed_week"] == history
        assert planning["placements"] == []
        # A close response lost before restart can safely be requested again.
        assert http_json("POST", f"{second.url}/api/weeks/{week}/close", close_payload) == (200, history)
        selected = [{"task_id": child["id"], "planned_date": "2026-10-20"}]
        status, carry_preview = http_json("POST", f"{second.url}/api/weeks/{week}/carryover-preview", {"selections": selected})
        assert status == 200
        carry_payload = {"selections": selected, "preview_token": carry_preview["preview_token"], "operation_id": str(uuid4())}
        status, carried = http_json("POST", f"{second.url}/api/weeks/{week}/carryover", carry_payload)
        assert status == 200 and carried["placements"][0]["task_id"] == child["id"]
        assert carried["placements"][0]["id"] != placement["id"]
        assert http_json("PATCH", f"{second.url}/api/projects/{project['id']}", {"name": "Current course"})[0] == 200
        assert http_json("PATCH", f"{second.url}/api/tasks/{child['id']}", {
            "title": "Current proof", "notes": "Current notes", "deadline": "2027-01-01",
        })[0] == 200
        assert http_json("PUT", f"{second.url}/api/tasks/{child['id']}/completion", {"complete": True})[0] == 200
        assert second.stop() == 0

    third = Service(data_dir, port, via_launcher=True).start()
    try:
        status, planning = http_json("GET", f"{third.url}/api/planning?week={week}")
        assert status == 200 and planning["closed_week"] == history
        assert planning["placements"] == carried["placements"]
        saved = {task["id"]: task for task in planning["tasks"]}
        assert saved[child["id"]]["title"] == "Current proof" and saved[child["id"]]["completed"] is True
        assert saved[child["id"]]["deadline"] == "2027-01-01"
        assert saved[parent["id"]]["completed"] is True
        historical = {task["id"]: task for task in history["tasks"]}
        assert historical[child["id"]]["title"] == "Original proof" and historical[child["id"]]["completed"] is False
        assert historical[child["id"]]["deadline"] == "2026-10-30"
        assert historical[child["id"]]["project_name"] == "Original course"
        assert http_json("POST", f"{third.url}/api/weeks/{week}/carryover", carry_payload) == (200, carried)
        assert http_json("POST", f"{third.url}/api/weeks/{week}/close", close_payload) == (200, history)
        assert http_json("GET", f"{third.url}/api/planning?week={week}")[1] == planning
        assert third.stop() == 0
    finally:
        third.kill()
