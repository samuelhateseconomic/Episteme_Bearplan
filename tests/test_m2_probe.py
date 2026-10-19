"""Evidence collection never borrows the normal service or user data."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tools.m2_probe import ROOT, observe_sleep, parse_args, safe_view, sleep_delta, validate_records


def test_evidence_view_omits_task_context_and_unknown_fields():
    session = {
        "id": "synthetic", "task_title": "Private coursework", "project_name": "Private class",
        "task_id": "task", "state": "paused", "active_seconds": 2,
        "recovery": {"kind": "sleep", "measured_sleep_seconds": 30, "resolution": None, "secret": "nested private value"},
        "unexpected_secret": "never copy",
    }
    saved = safe_view({"server_now": "now", "active_session": session, "extra": "unknown"})
    encoded = json.dumps(saved)
    assert "Private" not in encoded and "secret" not in encoded and "task_id" not in encoded
    assert "nested private value" not in encoded
    assert saved["active_session"]["recovery"]["measured_sleep_seconds"] == 30


def test_sleep_measurement_distinguishes_suspend_from_awake_stall():
    before = {"awake_ns": 1_000_000_000, "continuous_ns": 2_000_000_000, "continuous_kind": "measured"}
    awake = {"awake_ns": 11_000_000_000, "continuous_ns": 12_000_000_000, "continuous_kind": "measured"}
    sleep = {"awake_ns": 2_000_000_000, "continuous_ns": 33_000_000_000, "continuous_kind": "measured"}
    assert sleep_delta(before, awake) == 0
    assert sleep_delta(before, sleep) == 30
    assert sleep_delta(before, {**sleep, "continuous_kind": "unavailable"}) is None
    assert sleep_delta(before, {**sleep, "awake_ns": 0}) is None


def test_record_validation_detects_bounds_partial_credit_and_duplicate_unfinished():
    sessions = [{"id": "one", "state": "paused", "duration_minutes": 1, "active_microseconds": 61_000_000}]
    records = {"sessions": sessions, "intervals": []}
    assert len(validate_records(records)) == 2
    sessions.append({"id": "two", "state": "needs_review", "duration_minutes": 1, "active_microseconds": 0})
    assert "More than one unfinished session was saved." in validate_records(records)


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "10801"])
def test_invalid_seconds_fail_before_starting_any_process(value):
    with pytest.raises(SystemExit):
        parse_args(["precision", "--seconds", value, "--output", "/tmp/unused-m2.json"])


def test_existing_output_is_preserved_without_launching_service(tmp_path: Path):
    output = tmp_path / "keep.json"
    output.write_text("existing evidence", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/m2_probe.py"), "precision", "--seconds", ".1", "--output", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 1 and output.read_text() == "existing evidence"


def test_short_real_probe_uses_disposable_data_and_reports_observation(tmp_path: Path, monkeypatch):
    normal_data = tmp_path / "normal-app"
    normal_data.mkdir()
    sentinel = normal_data / "do-not-touch.txt"
    sentinel.write_text("user data", encoding="utf-8")
    monkeypatch.setenv("BEARPLANS_DATA_DIR", str(normal_data))
    monkeypatch.setenv("M2_TEST_SECRET", "not-for-evidence")
    output = tmp_path / "observation.json"
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/m2_probe.py"), "precision", "--seconds", ".2", "--output", str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    encoded = output.read_text()
    report = json.loads(encoded)
    assert report["result"] == "observation" and report["failures"] == []
    assert report["final"]["active_session"]["state"] == "paused"
    assert report["measurement"]["saved_active_seconds"] > 0
    assert "not-for-evidence" not in encoded
    assert "Synthetic M2" not in encoded
    assert sentinel.read_text() == "user data"
    assert list(normal_data.iterdir()) == [sentinel]


@pytest.mark.skipif(os.name == "nt", reason="POSIX SIGINT smoke; Windows Ctrl+Break is operator evidence")
def test_ctrl_c_saves_partial_evidence_and_stops_owned_child(tmp_path: Path):
    output = tmp_path / "interrupted.json"
    log = tmp_path / "probe.log"
    with log.open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "tools/m2_probe.py"), "precision", "--seconds", "600", "--output", str(output)],
            cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 10
            while "no timer API requests" not in log.read_text():
                assert process.poll() is None, log.read_text()
                assert time.monotonic() < deadline, "probe did not reach observation window"
                time.sleep(0.05)
            process.send_signal(signal.SIGINT)
            assert process.wait(timeout=15) == 2, log.read_text()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
    report = json.loads(output.read_text())
    assert report["result"] == "observation" and report["interrupted"] is True
    assert len(report["records"]["sessions"]) == 1
    assert report["service_source_sha256_at_start"]["backend/domain/timer.py"]


def sleep_journey(db, *, resume: bool):
    """Use real domain responses so the probe recognizes the actual audit shape."""
    from uuid import uuid4

    from backend.domain.tasks import create_task
    from backend.domain.timer import TimerService
    from tests.test_timer_recovery import RecoveryClock

    clock = RecoveryClock()
    timer = TimerService(db, clock)
    task = create_task(db, "Synthetic probe test")
    started = timer.start(task.id, 180, str(uuid4()))
    session = started.active_session
    clock.advance(2)
    timer.get()
    clock.advance(1, wall=31, continuous=31)
    paused = timer.get()
    views = [paused.model_dump()]
    if resume:
        running = timer.control(session.id, "resume", expected_revision=paused.active_session.revision)
        views.append(running.model_dump())
        clock.advance(1)
        timer.get()
        revision = running.active_session.revision
    else:
        revision = paused.active_session.revision
    finished = timer.control(session.id, "finish", expected_revision=revision)
    views.append(finished.model_dump())

    class ProbeService:
        url = "http://127.0.0.1:12345"

        def request(self, path, method="GET", body=None):
            if path == "/api/tasks":
                return task.model_dump()
            if path == "/api/timer/start":
                return started.model_dump()
            assert path == "/api/timer" and method == "GET"
            return views.pop(0)

        def records(self):
            with db.read() as conn:
                return {
                    "sessions": [dict(row) for row in conn.execute("SELECT * FROM timer_sessions")],
                    "intervals": [dict(row) for row in conn.execute("SELECT * FROM timer_intervals")],
                }

    return ProbeService(), views


def run_sleep_journey(monkeypatch, service):
    import itertools
    import tools.m2_probe as probe

    samples = iter([
        {"at": "before", "awake_ns": 0, "continuous_ns": 0, "continuous_kind": "simulated"},
        {"at": "wake", "awake_ns": 1_000_000_000, "continuous_ns": 31_000_000_000, "continuous_kind": "simulated"},
        {"at": "decision", "awake_ns": 2_000_000_000, "continuous_ns": 32_000_000_000, "continuous_kind": "simulated"},
        {"at": "finish", "awake_ns": 3_000_000_000, "continuous_ns": 33_000_000_000, "continuous_kind": "simulated"},
    ])
    monkeypatch.setattr(probe, "clock_sample", lambda: next(samples))
    reference = itertools.count()
    monkeypatch.setattr(probe.time, "perf_counter", lambda: next(reference))
    monkeypatch.setattr(probe.time, "sleep", lambda seconds: None)
    report = {}
    observe_sleep(service, 300, report)
    return report


@pytest.mark.parametrize("resume", [False, True])
def test_sleep_probe_accepts_explicit_finish_of_its_same_session(db, monkeypatch, resume):
    service, _ = sleep_journey(db, resume=resume)
    report = run_sleep_journey(monkeypatch, service)
    assert report["failures"] == []
    assert report["result"] in {"pass", "observation"}
    assert report["final"]["last_session"]["active_seconds"] == (3 if resume else 2)
    if resume:
        assert report["explicit_recovery_resume_observed"] is True
        assert report["same_session_finish_after_explicit_resume_observed"] is True
    else:
        assert report["explicit_recovery_finish_observed"] is True


def test_sleep_probe_recognizes_durable_resume_and_finish_between_samples(db, monkeypatch):
    service, views = sleep_journey(db, resume=True)
    del views[1]  # Both explicit controls completed before the next one-second poll.
    report = run_sleep_journey(monkeypatch, service)
    assert report["failures"] == []
    assert report["resume_and_finish_between_samples"] is True
    assert report["explicit_recovery_resume_observed"] is True
    assert report["same_session_finish_after_explicit_resume_observed"] is True
    assert report["final"]["last_session"]["active_seconds"] == 3


@pytest.mark.parametrize("mismatch", ["session", "interruption"])
def test_sleep_probe_does_not_accept_an_unrelated_finished_session_or_event(db, monkeypatch, mismatch):
    service, views = sleep_journey(db, resume=False)
    final = views[-1]["last_session"]
    if mismatch == "session":
        final["id"] = "different-session"
    else:
        final["recovery"]["id"] = "different-interruption"
    report = run_sleep_journey(monkeypatch, service)
    assert report["result"] == "fail" and report["failures"]
    assert not report.get("explicit_recovery_finish_observed")
