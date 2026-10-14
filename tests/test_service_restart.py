"""M0 acceptance: a task created through the running service survives a restart."""

import os
import socket
import subprocess
import sys
from pathlib import Path

from backend.platform.instance_lock import INSTANCE_FILENAME
from backend.platform.paths import DATABASE_FILENAME, SOURCE_ROOT
from backend.storage.migrations import load_migrations
from tests.conftest import ROOT, Service, free_port, http_json, running_service


def test_task_survives_graceful_restart(tmp_path: Path) -> None:
    data_dir = tmp_path / "BearPlans"
    port = free_port()

    first = Service(data_dir, port).start()
    status, created = http_json("POST", f"{first.url}/api/tasks", {"title": "Survive a restart"})
    assert status == 201
    assert first.stop() == 0
    assert "BearPlans stopped." in first.output
    assert not (data_dir / INSTANCE_FILENAME).exists()

    with running_service(data_dir, port) as second:
        status, listed = http_json("GET", f"{second.url}/api/tasks")
    assert status == 200
    assert listed == {"tasks": [created], "progress": {"completed": 0, "total": 1}}


def test_project_edits_and_completion_survive_restart(tmp_path: Path) -> None:
    """M1 acceptance: a whole project, its edits and its derived completion come back."""
    data_dir = tmp_path / "BearPlans"
    port = free_port()

    first = Service(data_dir, port).start()
    _, project = http_json("POST", f"{first.url}/api/projects", {"name": "Math 55"})
    _, parent = http_json("POST", f"{first.url}/api/tasks", {"title": "Write PS7", "project_id": project["id"]})
    _, child = http_json("POST", f"{first.url}/api/tasks", {"title": "read ch.4", "parent_id": parent["id"]})
    http_json(
        "PATCH",
        f"{first.url}/api/tasks/{parent['id']}",
        {"notes": "due Friday", "deadline": "2026-10-20", "estimate_minutes": 90},
    )
    http_json("PUT", f"{first.url}/api/tasks/{child['id']}/completion", {"complete": True})
    _, before = http_json("GET", f"{first.url}/api/tasks?project_id={project['id']}")
    assert first.stop() == 0

    with running_service(data_dir, port) as second:
        _, after = http_json("GET", f"{second.url}/api/tasks?project_id={project['id']}")
        _, projects = http_json("GET", f"{second.url}/api/projects")

    assert after == before
    saved_parent, saved_child = after["tasks"]
    assert (saved_parent["notes"], saved_parent["deadline"], saved_parent["estimate_minutes"]) == (
        "due Friday",
        "2026-10-20",
        90,
    )
    # The parent had one subtask and it was completed, so the parent reads complete.
    assert saved_parent["completed"] is True and saved_child["completed"] is True
    assert "Math 55" in [p["name"] for p in projects["projects"]]


def test_task_survives_abrupt_termination(tmp_path: Path) -> None:
    data_dir = tmp_path / "BearPlans"
    with running_service(data_dir) as first:
        _, created = http_json("POST", f"{first.url}/api/tasks", {"title": "Survive a crash"})
        first.kill()
    with running_service(data_dir) as second:
        _, listed = http_json("GET", f"{second.url}/api/tasks")
    assert listed == {"tasks": [created], "progress": {"completed": 0, "total": 1}}


def test_data_is_written_to_data_dir_not_source_tree(tmp_path: Path) -> None:
    data_dir = tmp_path / "BearPlans"
    before = set(SOURCE_ROOT.rglob("*.sqlite3*"))
    with running_service(data_dir) as service:
        http_json("POST", f"{service.url}/api/tasks", {"title": "Where am I stored?"})
    assert (data_dir / DATABASE_FILENAME).is_file()
    assert set(SOURCE_ROOT.rglob("*.sqlite3*")) == before


def test_startup_transcript_reports_location_and_schema(tmp_path: Path) -> None:
    data_dir = tmp_path / "BearPlans"
    service = Service(data_dir, free_port()).start()
    service.stop()
    assert f"data:   {data_dir.resolve()}" in service.output
    assert f"schema: version {len(load_migrations())}" in service.output
    assert f"http://127.0.0.1:{service.port}/" in service.output


def test_second_instance_on_same_data_dir_defers_to_the_first(tmp_path: Path) -> None:
    data_dir = tmp_path / "BearPlans"
    with running_service(data_dir) as first:
        second = subprocess.run(
            [sys.executable, "-m", "backend", "--no-browser", "--port", str(free_port())],
            cwd=ROOT,
            env={**os.environ, "BEARPLANS_DATA_DIR": str(data_dir)},
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert second.returncode == 0
        assert "already running" in second.stdout
        assert f"{first.url}/" in second.stdout
        assert http_json("GET", f"{first.url}/api/health")[0] == 200


def _run_service(data_dir: Path, port: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "backend", "--no-browser", "--port", str(port)],
        cwd=ROOT,
        env={**os.environ, "BEARPLANS_DATA_DIR": str(data_dir)},
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_busy_port_gives_clear_message_and_no_banner(tmp_path: Path) -> None:
    data_dir = tmp_path / "BearPlans"
    with socket.socket() as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen()
        port = blocker.getsockname()[1]
        result = _run_service(data_dir, port)
    assert result.returncode == 1
    assert f"port {port} is unavailable" in result.stderr
    assert "--port" in result.stderr
    assert "open:" not in result.stdout
    assert not (data_dir / INSTANCE_FILENAME).exists()


def test_corrupt_database_gives_clear_message_and_is_left_untouched(tmp_path: Path) -> None:
    data_dir = tmp_path / "BearPlans"
    data_dir.mkdir()
    db_file = data_dir / DATABASE_FILENAME
    db_file.write_bytes(b"not a database" * 200)
    result = _run_service(data_dir, free_port())
    assert result.returncode == 1
    assert "cannot start" in result.stderr and "was not changed" in result.stderr
    assert "Traceback" not in result.stderr
    assert db_file.read_bytes() == b"not a database" * 200


def test_refuses_data_dir_inside_repository() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "backend", "--no-browser", "--port", str(free_port())],
        cwd=ROOT,
        env={**os.environ, "BEARPLANS_DATA_DIR": str(ROOT / "data")},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "inside the source tree" in result.stderr
    assert not (ROOT / "data").exists()


def test_real_launcher_preserves_m1_records_across_restart(tmp_path: Path) -> None:
    data_dir = tmp_path / "LauncherData"
    port = free_port()
    before = None
    for run in range(2):
        service = Service(data_dir, port, via_launcher=True).start()
        try:
            if run == 0:
                status, project = http_json("POST", f"{service.url}/api/projects", {"name": "Launch check"})
                assert status == 201
                status, task = http_json("POST", f"{service.url}/api/tasks", {
                    "title": "Persist from launcher", "project_id": project["id"],
                    "notes": "Disposable data", "deadline": "2026-10-20", "estimate_minutes": 25,
                })
                assert status == 201
                assert http_json("PUT", f"{service.url}/api/tasks/{task['id']}/completion", {"complete": True})[0] == 200
            _, listed = http_json("GET", f"{service.url}/api/tasks")
            assert listed["progress"] == {"completed": 1, "total": 1}
            if run == 0:
                before = listed
            else:
                assert listed == before
            assert service.stop() == 0
            assert "schema: version 2" in service.output
            assert "BearPlans stopped." in service.output
        finally:
            service.kill()
