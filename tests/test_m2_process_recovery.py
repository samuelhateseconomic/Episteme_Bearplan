"""Process interruption evidence on the actual host, not simulated laptop sleep."""

import os
import signal
import sqlite3
import time
from uuid import uuid4

import pytest

from tests.conftest import Service, free_port, http_json, running_service


@pytest.mark.skipif(not hasattr(signal, "SIGSTOP"), reason="requires POSIX process stop/continue")
def test_real_process_stall_excludes_gap_and_recovery_replays_after_restart(tmp_path):
    service = Service(tmp_path / "StalledTimer", free_port()).start()
    try:
        _, task = http_json("POST", service.url + "/api/tasks", {"title": "Synthetic stalled work"})
        _, started = http_json("POST", service.url + "/api/timer/start", {
            "task_id": task["id"], "duration_minutes": 10, "operation_id": str(uuid4()),
        })
        session_id = started["active_session"]["id"]
        time.sleep(1.1)
        assert service.process is not None
        os.kill(service.process.pid, signal.SIGSTOP)
        try:
            # SIGSTOP preserves the process but stops all checkpoint threads.
            with sqlite3.connect(service.data_dir / "bearplans.sqlite3") as conn:
                credit, checkpoint = conn.execute(
                    "SELECT active_microseconds, checkpoint_at FROM timer_sessions WHERE id = ?", (session_id,),
                ).fetchone()
            time.sleep(6)
        finally:
            os.kill(service.process.pid, signal.SIGCONT)
        _, interrupted = http_json("GET", service.url + "/api/timer")
        review = interrupted["active_session"]
        assert review["state"] == "needs_review"
        assert review["recovery"]["kind"] == "checkpoint_gap", "a stopped awake process is not laptop sleep"
        assert review["active_seconds"] == credit / 1_000_000
        assert review["checkpoint_at"] == checkpoint
        payload = {
            "resolution": "resume", "discard_uncertain": True,
            "expected_revision": review["revision"], "operation_id": str(uuid4()),
        }
        status, resumed = http_json("POST", service.url + f"/api/timer/{session_id}/recover", payload)
        assert status == 200 and resumed["active_session"]["state"] == "running"
        assert resumed["active_session"]["id"] == session_id
        assert resumed["active_session"]["recovery"]["confirmed_active_seconds"] == credit / 1_000_000
        # Simulate a crash after the recovery committed but its response was lost.
        service.kill()
        service = Service(service.data_dir, service.port).start()
        _, restarted = http_json("GET", service.url + "/api/timer")
        next_review = restarted["active_session"]
        assert next_review["state"] == "needs_review"
        status, replayed = http_json("POST", service.url + f"/api/timer/{session_id}/recover", payload)
        assert status == 200
        assert replayed["active_session"]["state"] == "needs_review", "replayed old intent must not resolve a new interruption"
        assert replayed["active_session"]["revision"] == next_review["revision"]
        finish = {
            "resolution": "finish", "discard_uncertain": True,
            "expected_revision": next_review["revision"], "operation_id": str(uuid4()),
        }
        status, saved = http_json("POST", service.url + f"/api/timer/{session_id}/recover", finish)
        assert status == 200 and saved["active_session"] is None
        assert saved["last_session"]["active_seconds"] == next_review["active_seconds"]
        assert saved["last_session"]["outcome"] == "interrupted"
        assert http_json("GET", service.url + "/api/tasks")[1]["tasks"] == [task]
    finally:
        service.kill()


def test_paused_session_survives_abrupt_restart_without_reclassifying_work(tmp_path):
    data_dir = tmp_path / "PausedCrash"
    first = Service(data_dir, free_port()).start()
    try:
        _, task = http_json("POST", first.url + "/api/tasks", {"title": "Synthetic paused work"})
        _, started = http_json("POST", first.url + "/api/timer/start", {
            "task_id": task["id"], "duration_minutes": 5, "operation_id": str(uuid4()),
        })
        session = started["active_session"]
        _, paused = http_json("POST", first.url + f"/api/timer/{session['id']}/pause", {
            "expected_revision": session["revision"], "operation_id": str(uuid4()),
        })
        first.kill()
        with running_service(data_dir) as second:
            _, view = http_json("GET", second.url + "/api/timer")
            assert view["active_session"] == paused["active_session"]
            with sqlite3.connect(data_dir / "bearplans.sqlite3") as conn:
                assert conn.execute("SELECT COUNT(*) FROM timer_intervals WHERE ended_at IS NULL").fetchone()[0] == 0
    finally:
        first.kill()
