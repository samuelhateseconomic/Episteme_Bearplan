"""Real macOS/service observations use disposable databases, never user data."""

import sqlite3
import statistics
import time
from pathlib import Path
from uuid import uuid4

from backend.platform.paths import DATABASE_FILENAME
from tests.conftest import Service, free_port, http_json, running_service


def test_short_real_session_monitor_pause_and_task_responsiveness(tmp_path: Path):
    with running_service(tmp_path / "RealTimer") as service:
        _, task = http_json("POST", f"{service.url}/api/tasks", {"title": "Synthetic timer work"})
        reference_start = time.monotonic()
        status, started = http_json("POST", f"{service.url}/api/timer/start", {
            "task_id": task["id"], "duration_minutes": 1, "operation_id": str(uuid4()),
        })
        assert status == 201
        session = started["active_session"]
        # No timer requests/browser callbacks for this interval: monitor persists it.
        time.sleep(2.2)
        latencies = []
        for index in range(6):
            before = time.monotonic()
            status, _ = http_json("POST", f"{service.url}/api/tasks", {"title": f"Responsive task {index}"})
            latencies.append(time.monotonic() - before)
            assert status == 201
        _, paused = http_json("POST", f"{service.url}/api/timer/{session['id']}/pause", {"expected_revision": 1})
        reference_before_pause = time.monotonic() - reference_start
        saved_active = paused["active_session"]["active_seconds"]
        assert abs(saved_active - reference_before_pause) < 0.25
        time.sleep(0.5)
        _, still_paused = http_json("GET", f"{service.url}/api/timer")
        assert still_paused["active_session"]["active_seconds"] == saved_active
        _, resumed = http_json("POST", f"{service.url}/api/timer/{session['id']}/resume", {"expected_revision": 2})
        assert resumed["active_session"]["state"] == "running"
        time.sleep(0.3)
        _, finished = http_json("POST", f"{service.url}/api/timer/{session['id']}/finish", {"expected_revision": 3})
        result = finished["last_session"]
        assert result["outcome"] == "finished_early"
        assert 0.25 <= result["active_seconds"] - saved_active <= 0.6
        _, tasks = http_json("GET", f"{service.url}/api/tasks")
        assert tasks["tasks"][0] == task
        assert max(latencies) < 1
        print(f"Real timer: {result['active_seconds']:.6f}s saved; task writes median={statistics.median(latencies):.6f}s max={max(latencies):.6f}s")


def test_crashed_running_session_reopens_in_review_without_gap_credit(tmp_path: Path):
    data_dir = tmp_path / "CrashTimer"
    first = Service(data_dir, free_port()).start()
    try:
        _, task = http_json("POST", f"{first.url}/api/tasks", {"title": "Synthetic interrupted work"})
        key = str(uuid4())
        _, started = http_json("POST", f"{first.url}/api/timer/start", {
            "task_id": task["id"], "duration_minutes": 1, "operation_id": key,
        })
        session = started["active_session"]
        time.sleep(1.3)
        first.kill()
        with sqlite3.connect(data_dir / DATABASE_FILENAME) as conn:
            checkpoint_credit, checkpoint_at = conn.execute(
                "SELECT active_microseconds, checkpoint_at FROM timer_sessions"
            ).fetchone()
        assert checkpoint_credit > 0
        time.sleep(0.2)
        with running_service(data_dir) as second:
            _, reopened = http_json("GET", f"{second.url}/api/timer")
            review = reopened["active_session"]
            assert review["state"] == "needs_review" and review["id"] == session["id"]
            assert review["active_seconds"] == checkpoint_credit / 1_000_000
            assert review["checkpoint_at"] == checkpoint_at
            payload = {"operation_id": str(uuid4()), "discard_uncertain": True}
            _, finished = http_json("POST", f"{second.url}/api/timer/{session['id']}/finish", payload)
            result = finished["last_session"]
            assert result["active_seconds"] == review["active_seconds"] and result["outcome"] == "interrupted"
            assert second.stop() == 0
        with running_service(data_dir) as third:
            assert http_json("POST", f"{third.url}/api/timer/{session['id']}/finish", payload)[1]["last_session"] == result
            # A lost start response remains replay-safe across both restarts.
            assert http_json("POST", f"{third.url}/api/timer/start", {
                "task_id": task["id"], "duration_minutes": 1, "operation_id": key,
            })[1]["last_session"] == result
    finally:
        first.kill()
