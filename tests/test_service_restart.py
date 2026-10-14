"""M0 acceptance: a task created through the running service survives a restart."""

import os
import socket
import subprocess
import sys
from pathlib import Path

from backend.platform.instance_lock import INSTANCE_FILENAME
from backend.platform.paths import DATABASE_FILENAME, SOURCE_ROOT
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
    assert listed == {"tasks": [created]}


def test_task_survives_abrupt_termination(tmp_path: Path) -> None:
    data_dir = tmp_path / "BearPlans"
    with running_service(data_dir) as first:
        _, created = http_json("POST", f"{first.url}/api/tasks", {"title": "Survive a crash"})
        first.kill()
    with running_service(data_dir) as second:
        _, listed = http_json("GET", f"{second.url}/api/tasks")
    assert listed == {"tasks": [created]}


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
    assert "schema: version 1" in service.output
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
