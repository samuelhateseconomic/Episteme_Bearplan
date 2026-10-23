#!/usr/bin/env python3
"""Collect disposable M2 observations without changing clocks or power settings.

Examples (from the checkout):
  .venv/bin/python tools/m2_probe.py precision --seconds 600 --output /tmp/m2-precision.json
  .venv/bin/python tools/m2_probe.py sleep --seconds 300 --output /tmp/m2-sleep.json

The sleep operator closes the lid or initiates sleep separately. This program
never resumes a paused timer. Exit 0 means this scenario passed, 1 means failure,
and 2 means observation only (short run, no sleep, or interrupted collection).
Neither exit 0 nor a Linux run certifies the complete Mac M2 acceptance gate.
"""

from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import math
import os
import platform
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
DATABASE_FILENAME = "bearplans.sqlite3"
PRECISION_TARGET_SECONDS = 2.0
SESSION_FIELDS = frozenset({
    "id", "state", "duration_minutes", "requested_seconds", "active_seconds",
    "remaining_seconds", "started_at", "checkpoint_at", "deadline_at",
    "finished_at", "outcome", "review_reason", "revision", "recovery",
})
RECOVERY_FIELDS = frozenset({
    "id", "kind", "reason", "checkpoint_at", "detected_at", "confirmed_active_seconds",
    "measured_sleep_seconds", "resolved_at", "resolution",
})


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def safe_session(session: dict[str, Any] | None) -> dict[str, Any] | None:
    if session is None:
        return None
    result = {key: value for key, value in session.items() if key in SESSION_FIELDS and key != "recovery"}
    recovery = session.get("recovery")
    if isinstance(recovery, dict):
        result["recovery"] = {key: value for key, value in recovery.items() if key in RECOVERY_FIELDS}
    return result


def safe_view(view: dict[str, Any]) -> dict[str, Any]:
    return {
        "server_now": view.get("server_now"),
        "active_session": safe_session(view.get("active_session")),
        "last_session": safe_session(view.get("last_session")),
    }


def clock_sample() -> dict[str, Any]:
    awake = time.monotonic_ns()
    kind = "unavailable"
    continuous = awake
    if sys.platform == "darwin" and hasattr(time, "CLOCK_MONOTONIC"):
        continuous = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
        kind = "macOS CLOCK_MONOTONIC"
    elif hasattr(time, "CLOCK_BOOTTIME"):
        continuous = time.clock_gettime_ns(time.CLOCK_BOOTTIME)
        kind = "CLOCK_BOOTTIME"
    return {
        "at": utc_now(), "awake_ns": awake, "continuous_ns": continuous,
        "continuous_kind": kind,
    }


def sleep_delta(before: dict[str, Any], after: dict[str, Any]) -> float | None:
    if before["continuous_kind"] == "unavailable" or before["continuous_kind"] != after["continuous_kind"]:
        return None
    awake = (after["awake_ns"] - before["awake_ns"]) / 1e9
    continuous = (after["continuous_ns"] - before["continuous_ns"]) / 1e9
    if awake < 0 or continuous < 0:
        return None
    return max(0.0, continuous - awake)


def json_request(url: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not echo request bodies, credentials, or arbitrary server responses.
        raise RuntimeError(f"The disposable service returned HTTP {exc.code}.") from None


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def checkout_python() -> Path:
    python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        raise RuntimeError("The checkout .venv is missing. Complete README setup before running this probe.")
    return python


class OwnedService:
    """One child, one temporary data directory; never connect to the normal app."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.port = free_port()
        self.url = f"http://127.0.0.1:{self.port}"
        self.process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        env = os.environ.copy()
        env["BEARPLANS_DATA_DIR"] = str(self.data_dir)
        env["PYTHONUNBUFFERED"] = "1"
        # Inherited bindings are used in place; their values are never reported.
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        self.process = subprocess.Popen(
            [str(checkout_python()), "-m", "backend", "--no-browser", "--port", str(self.port)],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=flags, start_new_session=os.name != "nt",
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError(f"The disposable service stopped during startup (exit {self.process.returncode}).")
            try:
                json_request(f"{self.url}/api/health")
                return
            except (OSError, RuntimeError):
                time.sleep(0.1)
        raise RuntimeError("The disposable service did not become healthy within 30 seconds.")

    def stop(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        self.process.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)

    def request(self, path: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("The disposable service is no longer running.")
        return json_request(f"{self.url}{path}", method, body)

    def records(self) -> dict[str, Any]:
        path = self.data_dir / DATABASE_FILENAME
        if not path.is_file():
            return {}
        # sqlite3's transaction context does not close its connection. Explicit
        # close is required before TemporaryDirectory removes files on Windows.
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN")
            sessions = [dict(row) for row in conn.execute(
                "SELECT id, state, duration_minutes, active_microseconds, started_at, checkpoint_at,"
                " finished_at, outcome, review_reason, revision FROM timer_sessions ORDER BY rowid"
            )]
            intervals = [dict(row) for row in conn.execute(
                "SELECT id, session_id, started_at, checkpoint_at, ended_at, active_microseconds"
                " FROM timer_intervals ORDER BY rowid"
            )]
            records = {"sessions": sessions, "intervals": intervals}
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='timer_interruptions'").fetchone():
                records["interruptions"] = [dict(row) for row in conn.execute(
                    "SELECT id, session_id, kind, reason, checkpoint_at, detected_at,"
                    " confirmed_active_microseconds, measured_sleep_microseconds, resolved_at, resolution"
                    " FROM timer_interruptions ORDER BY rowid"
                )]
            return records


def validate_records(records: dict[str, Any]) -> list[str]:
    failures = []
    for session in records.get("sessions", []):
        credit = session["active_microseconds"]
        if not 0 <= credit <= session["duration_minutes"] * 60_000_000:
            failures.append("Saved active duration exceeded the configured bounds.")
        total = sum(row["active_microseconds"] for row in records.get("intervals", []) if row["session_id"] == session["id"])
        if total != credit:
            failures.append("Saved interval credit did not equal the session total.")
    if sum(row["state"] != "finished" for row in records.get("sessions", [])) > 1:
        failures.append("More than one unfinished session was saved.")
    for interval in records.get("intervals", []):
        def instant(key: str) -> datetime:
            return datetime.fromisoformat(interval[key].replace("Z", "+00:00"))
        if instant("checkpoint_at") < instant("started_at"):
            failures.append("A saved interval checkpoint preceded its own start.")
        if interval.get("ended_at") and instant("ended_at") != instant("checkpoint_at"):
            failures.append("A closed interval endpoint differed from its saved checkpoint.")
    return failures


def source_digests() -> dict[str, str]:
    """Identify observed service sources while other agents may still be editing."""
    paths = [*ROOT.joinpath("backend").rglob("*.py"), *ROOT.joinpath("backend/storage/migrations").glob("*.sql")]
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}


def precision(service: OwnedService, seconds: float, report: dict[str, Any]) -> None:
    duration = max(1, math.ceil(seconds / 60))
    task = service.request("/api/tasks", "POST", {"title": "Synthetic M2 precision observation"})
    before = time.perf_counter()
    started = service.request("/api/timer/start", "POST", {
        "task_id": task["id"], "duration_minutes": duration, "operation_id": str(uuid4()),
    })
    after = time.perf_counter()
    session = started["active_session"]
    report["initial"] = safe_view(started)
    report["reference"] = "Separate probe-process time.perf_counter; same-host clock, not an external stopwatch."
    print(f"Precision: observing {seconds:g}s; no timer API requests during this window.", flush=True)
    next_notice = 60.0
    while time.perf_counter() - after < seconds:
        elapsed = time.perf_counter() - after
        if elapsed >= next_notice:
            print(f"Observed {int(elapsed)}s / {seconds:g}s.", flush=True)
            next_notice += 60
        time.sleep(min(0.25, max(0.001, seconds - elapsed)))
    full_duration = seconds == duration * 60
    completed_without_api = False
    if full_duration:
        # Read-only SQLite observation precedes final GET, so GET cannot be the
        # operation that expires this timer. Allow the documented 1s monitor tick.
        deadline = time.perf_counter() + 2.5
        while True:
            records = service.records()
            rows = records.get("sessions", [])
            if rows and rows[-1]["state"] == "finished":
                completed_without_api = True
                break
            if time.perf_counter() >= deadline:
                break
            time.sleep(0.05)
        observed = time.perf_counter()
        final = service.request("/api/timer")
        reference_seconds = observed - (before + after) / 2
        report["expired_without_timer_api"] = completed_without_api
    else:
        pause_before = time.perf_counter()
        final = service.request(f"/api/timer/{session['id']}/pause", "POST", {"expected_revision": session["revision"]})
        pause_after = time.perf_counter()
        reference_seconds = (pause_before + pause_after - before - after) / 2
    report["final"] = safe_view(final)
    result = final.get("active_session") or final.get("last_session")
    active_seconds = result["active_seconds"]
    error = active_seconds - reference_seconds
    report["measurement"] = {
        "requested_observation_seconds": seconds, "reference_seconds": reference_seconds,
        "saved_active_seconds": active_seconds, "saved_minus_reference_seconds": error,
        "proposed_precision_target_seconds": PRECISION_TARGET_SECONDS,
        "start_request_bracket_seconds": after - before,
    }
    failures = validate_records(service.records())
    if full_duration and not completed_without_api:
        failures.append("The service monitor did not finalize expiry before the final timer API request.")
    if abs(error) > PRECISION_TARGET_SECONDS:
        failures.append("Saved time differed from the same-host reference by more than two seconds.")
    if result["state"] not in {"paused", "finished"}:
        failures.append("The precision observation ended in an unexpected state.")
    report["failures"] = failures
    report["result"] = "fail" if failures else "pass" if seconds >= 600 else "observation"
    report["scope"] = "One uninterrupted awake precision scenario; Mac sleep and external timing evidence remain separate."


def observe_sleep(service: OwnedService, seconds: float, report: dict[str, Any]) -> None:
    task = service.request("/api/tasks", "POST", {"title": "Synthetic M2 sleep observation"})
    started = service.request("/api/timer/start", "POST", {
        "task_id": task["id"], "duration_minutes": 180, "operation_id": str(uuid4()),
    })
    report["initial"] = safe_view(started)
    target_session_id = started["active_session"]["id"]
    report["samples"] = []
    print(f"Disposable service: {service.url}/#track", flush=True)
    print("Initiate sleep yourself; this probe never changes power settings or resumes the session.", flush=True)
    print("Use Ctrl+C to stop early and save evidence. Keep the normal BearPlans service untouched.", flush=True)
    previous = clock_sample()
    started_reference = time.perf_counter()
    observed_sleep = 0.0
    paused_credit = None
    interruption_id = None
    paused_after_sleep = False
    failures = []
    # The elapsed budget uses continuous time when available so lid sleep does
    # not silently extend a five-minute observation by hours.
    while True:
        sample = clock_sample()
        gap_sleep = sleep_delta(previous, sample)
        if gap_sleep is not None and gap_sleep > 0.1:
            observed_sleep += gap_sleep
        view = service.request("/api/timer")
        active = view.get("active_session")
        last = view.get("last_session")
        target = (
            active if active and active["id"] == target_session_id
            else last if last and last["id"] == target_session_id else None
        )
        recovery = target.get("recovery") if target else None
        resolved_interruption = (
            recovery is not None and interruption_id is not None
            and recovery.get("id") == interruption_id and recovery.get("resolved_at") is not None
        )
        sample["measured_sleep_seconds"] = gap_sleep
        sample["timer"] = safe_view(view)
        report["samples"].append(sample)
        report["measured_sleep_seconds"] = observed_sleep
        completed = target is not None and target["state"] == "finished"
        if target is None:
            failures.append("The observed timer no longer matched the probe's session.")
        elif completed:
            if interruption_id is not None:
                if resolved_interruption and recovery.get("resolution") == "finish":
                    report["explicit_recovery_finish_observed"] = True
                    if paused_credit is not None and target["active_seconds"] != paused_credit:
                        failures.append("Finishing a paused/review session changed its confirmed credit.")
                elif resolved_interruption and recovery.get("resolution") == "resume":
                    if not report.get("explicit_recovery_resume_observed"):
                        report["resume_and_finish_between_samples"] = True
                    report["explicit_recovery_resume_observed"] = True
                    report["same_session_finish_after_explicit_resume_observed"] = True
                else:
                    failures.append("The finished session did not retain its observed explicit recovery resolution.")
        elif target["state"] in {"paused", "needs_review"}:
            if observed_sleep > 2:
                paused_after_sleep = True
            if paused_credit is None:
                paused_credit = target["active_seconds"]
                interruption_id = recovery.get("id") if recovery else None
            elif target["active_seconds"] != paused_credit:
                failures.append("Time continued to earn while paused or awaiting review.")
        elif paused_credit is not None:
            # An operator may use the displayed disposable URL to Resume. Record
            # that fact without mistaking it for automatic resumption.
            if target["state"] == "running" and resolved_interruption and recovery.get("resolution") == "resume":
                report["explicit_recovery_resume_observed"] = True
            else:
                failures.append("A paused/review session changed without an observed explicit recovery resolution.")
            paused_credit = None
        previous = sample
        elapsed = time.perf_counter() - started_reference + observed_sleep
        if elapsed >= seconds or completed or target is None:
            break
        time.sleep(min(1, max(0.001, seconds - elapsed)))
    report["final"] = safe_view(view)
    failures.extend(validate_records(service.records()))
    if observed_sleep > 2 and not paused_after_sleep:
        failures.append("A measured sleep did not leave the session paused or explicitly unresolved.")
    report["failures"] = failures
    report["result"] = "fail" if failures else "pass" if observed_sleep > 2 and sys.platform == "darwin" else "observation"
    report["scope"] = "One sleep observation only; repeat with AC/battery and standby/hibernate, and corroborate suspends externally."


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=("precision", "sleep"))
    parser.add_argument("--seconds", type=float, default=600, help="observation length, 0 < seconds <= 10800 (default: 600)")
    parser.add_argument("--output", type=Path, required=True, help="sanitized JSON evidence path; an existing file is never overwritten")
    args = parser.parse_args(argv)
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 10_800:
        parser.error("--seconds must be finite and greater than zero, at most 10800")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output = args.output.expanduser().resolve()
    # Reserve the path before starting; preserve existing user evidence.
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        output.open("x", encoding="utf-8").close()
    except FileExistsError:
        print("The output file already exists; choose a new evidence path.", file=sys.stderr)
        return 1
    report: dict[str, Any] = {
        "format_version": 1, "mode": args.mode, "started_at": utc_now(),
        "platform": {"system": platform.system(), "release": platform.release(), "python": platform.python_version()},
        "result": "observation", "scope": "Incomplete collection; no milestone readiness claim.",
        "safety": "Synthetic task and owned temporary service/data only; no automatic power, clock, or Resume action.",
    }
    service = None
    try:
        with tempfile.TemporaryDirectory(prefix="bearplans-m2-") as directory:
            data_dir = Path(directory).resolve()
            if data_dir == ROOT or ROOT in data_dir.parents:
                raise RuntimeError("The temporary data directory must be outside the checkout.")
            service = OwnedService(data_dir)
            try:
                report["service_source_sha256_at_start"] = source_digests()
                service.start()
                if args.mode == "precision":
                    precision(service, args.seconds, report)
                else:
                    observe_sleep(service, args.seconds, report)
            finally:
                if service is not None:
                    try:
                        report["records"] = service.records()
                        report["service_source_sha256_at_end"] = source_digests()
                    finally:
                        service.stop()
    except KeyboardInterrupt:
        report["result"] = "observation"
        report["interrupted"] = True
        report["scope"] = "Collection interrupted; partial records retained, no readiness claim."
    except Exception as exc:
        report["result"] = "fail"
        # Known errors are crafted without arbitrary server bodies or environment.
        report["error"] = str(exc) if isinstance(exc, RuntimeError) else type(exc).__name__
    finally:
        report["finished_at"] = utc_now()
        output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{report['result'].upper()}: {report.get('scope', '')}", flush=True)
    print(f"Evidence: {output}", flush=True)
    if "measurement" in report:
        measured = report["measurement"]
        print(f"Saved {measured['saved_active_seconds']:.6f}s; reference {measured['reference_seconds']:.6f}s; difference {measured['saved_minus_reference_seconds']:+.6f}s.")
    for failure in report.get("failures", []):
        print(f"Failure: {failure}", file=sys.stderr)
    if report.get("error"):
        print(f"Error: {report['error']}", file=sys.stderr)
    return {"pass": 0, "fail": 1, "observation": 2}[report["result"]]


if __name__ == "__main__":
    sys.exit(main())
