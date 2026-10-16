"""Backend-owned countdowns and trusted active intervals.

Only a continuously observed process-local monotonic clock earns time. UTC values
describe when that work occurred; they never determine credit. The one-second
monitor runs independently of browsers. Restart, a processing gap over five seconds,
or clock disagreement stops credit at the last saved checkpoint and requires review.
This is a conservative first-build safeguard, not sleep/crash reconciliation.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Iterator, Literal, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict

from backend.domain.errors import InvalidInput
from backend.domain.tasks import _require_task
from backend.storage.db import Database, StorageError

CHECKPOINT_SECONDS = 1.0
MAX_OBSERVATION_GAP_SECONDS = 5.0
CLOCK_TOLERANCE_SECONDS = 2.0
_LOG = logging.getLogger(__name__)


class TimerConflict(InvalidInput):
    """The current countdown changed or still needs the user's attention."""


@dataclass(frozen=True)
class ClockSample:
    wall: datetime
    monotonic_ns: int
    continuous_ns: int


class Clock(Protocol):
    def sample(self) -> ClockSample: ...


class SystemClock:
    def sample(self) -> ClockSample:
        # On the measured target Mac Python's monotonic clock excludes suspend;
        # CLOCK_MONOTONIC includes it. Other platforms still have wall/gap checks.
        awake = time.monotonic_ns()
        continuous = (
            time.clock_gettime_ns(time.CLOCK_MONOTONIC)
            if hasattr(time, "clock_gettime_ns") and hasattr(time, "CLOCK_MONOTONIC")
            else awake
        )
        return ClockSample(datetime.now(UTC), awake, continuous)


def _utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


class TimerSession(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    start_operation_id: str
    task_id: str
    task_title: str
    project_id: str
    project_name: str
    parent_title: str | None
    state: Literal["running", "paused", "needs_review", "finished"]
    duration_minutes: int
    requested_seconds: int
    active_seconds: float
    remaining_seconds: float
    started_at: str
    checkpoint_at: str
    deadline_at: str | None
    finished_at: str | None
    outcome: Literal["completed", "finished_early", "interrupted"] | None
    review_reason: str | None
    revision: int


class TimerView(BaseModel):
    server_now: str
    active_session: TimerSession | None
    last_session: TimerSession | None


def _operation_id(value: object) -> str:
    if not isinstance(value, str):
        raise InvalidInput("operation_id", "Use a new UUID for this timer request, then retry.")
    try:
        return str(UUID(value))
    except ValueError:
        raise InvalidInput("operation_id", "Use a valid UUID for this timer request, then retry.") from None


def _duration(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 180:
        raise InvalidInput("duration_minutes", "Choose a whole-minute duration from 1 to 180 minutes.")
    return value


def _fingerprint(action: str, **values: object) -> str:
    return json.dumps({"action": action, **values}, sort_keys=True, separators=(",", ":"))


def _session(row: sqlite3.Row | None) -> TimerSession | None:
    if row is None:
        return None
    active = row["active_microseconds"] / 1_000_000
    remaining = max(0.0, row["duration_minutes"] * 60 - active)
    deadline = None
    if row["state"] == "running":
        checkpoint = datetime.fromisoformat(row["checkpoint_at"].replace("Z", "+00:00"))
        deadline = _utc(checkpoint + timedelta(seconds=remaining))
    return TimerSession(
        **{key: row[key] for key in (
            "id", "start_operation_id", "task_id", "task_title", "project_id", "project_name",
            "parent_title", "state", "duration_minutes", "started_at", "checkpoint_at", "finished_at",
            "outcome", "review_reason", "revision",
        )},
        requested_seconds=row["duration_minutes"] * 60,
        active_seconds=active, remaining_seconds=remaining, deadline_at=deadline,
    )


def _active(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM timer_sessions WHERE state <> 'finished'").fetchone()


class TimerService:
    """Shared countdown application functions; one instance for the local service.

    The service lock protects process clock anchors, while Database.write and the
    unique database index serialize all saved mutations. No provider or browser
    callback participates in the clock or finalization path.
    """

    def __init__(self, db: Database, clock: Clock | None = None) -> None:
        self.db = db
        self.clock = clock or SystemClock()
        self._lock = threading.RLock()
        self._anchor: ClockSample | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        # Process-local monotonic values cannot establish any cross-restart gap,
        # including a graceful shutdown. Preserve only saved interval credit.
        with self.db.write() as conn:
            row = _active(conn)
            if row is not None and row["state"] != "needs_review":
                self._review(conn, row, "The service restarted. Only time saved before the interruption is confirmed.")

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        previous = self._anchor
        try:
            with self.db.write() as conn:
                yield conn
        except BaseException:
            # A failed SQLite commit must not advance the in-memory checkpoint.
            self._anchor = previous
            raise

    def _view(self, conn: sqlite3.Connection, sample: ClockSample) -> TimerView:
        return TimerView(
            server_now=_utc(sample.wall), active_session=_session(_active(conn)),
            last_session=_session(conn.execute(
                "SELECT * FROM timer_sessions WHERE state = 'finished' ORDER BY rowid DESC LIMIT 1"
            ).fetchone()),
        )

    def _review(self, conn: sqlite3.Connection, row: sqlite3.Row, reason: str) -> None:
        conn.execute(
            "UPDATE timer_intervals SET ended_at = checkpoint_at WHERE session_id = ? AND ended_at IS NULL",
            (row["id"],),
        )
        conn.execute(
            "UPDATE timer_sessions SET state = 'needs_review', review_reason = ?, revision = revision + 1 WHERE id = ?",
            (reason, row["id"]),
        )
        self._anchor = None

    def _reconcile(self, conn: sqlite3.Connection, sample: ClockSample) -> None:
        row = _active(conn)
        if row is None or row["state"] != "running":
            if row is not None and row["state"] == "paused" and sample.wall < datetime.fromisoformat(row["checkpoint_at"].replace("Z", "+00:00")):
                self._review(conn, row, "The system clock moved before the last saved interval. Only the last saved time is confirmed.")
            self._anchor = None
            return
        if self._anchor is None:
            self._review(conn, row, "The timer's clock continuity is unknown. Only the last saved time is confirmed.")
            return
        awake = (sample.monotonic_ns - self._anchor.monotonic_ns) / 1_000_000_000
        continuous = (sample.continuous_ns - self._anchor.continuous_ns) / 1_000_000_000
        wall = (sample.wall - self._anchor.wall).total_seconds()
        reason = None
        if awake < 0 or continuous < 0 or wall < 0:
            reason = "A timer clock moved backwards. Only the last saved time is confirmed."
        elif abs(continuous - awake) > CLOCK_TOLERANCE_SECONDS:
            reason = "A possible laptop sleep interrupted timing. The uncertain gap was not counted."
        elif abs(wall - continuous) > CLOCK_TOLERANCE_SECONDS:
            reason = "The system clock changed during tracking. The uncertain interval was not counted."
        elif awake > MAX_OBSERVATION_GAP_SECONDS:
            reason = "The service missed a timing checkpoint. The uncertain gap was not counted."
        if reason:
            self._review(conn, row, reason)
            return
        elapsed_us = max(0, (sample.monotonic_ns - self._anchor.monotonic_ns) // 1000)
        remaining_us = row["duration_minutes"] * 60_000_000 - row["active_microseconds"]
        credited_us = min(elapsed_us, remaining_us)
        # Clip both credit and the interval endpoint to actual countdown expiry.
        ended = sample.wall - timedelta(microseconds=elapsed_us - credited_us)
        previous_checkpoint = datetime.fromisoformat(row["checkpoint_at"].replace("Z", "+00:00"))
        if ended < previous_checkpoint:
            self._review(conn, row, "The system clock would move a saved interval backwards. The uncertain interval was not counted.")
            return
        checkpoint = _utc(ended)
        conn.execute(
            "UPDATE timer_intervals SET active_microseconds = active_microseconds + ?, checkpoint_at = ?"
            " WHERE session_id = ? AND ended_at IS NULL",
            (credited_us, checkpoint, row["id"]),
        )
        conn.execute(
            "UPDATE timer_sessions SET active_microseconds = active_microseconds + ?, checkpoint_at = ? WHERE id = ?",
            (credited_us, checkpoint, row["id"]),
        )
        self._anchor = sample
        if credited_us == remaining_us:
            self._finish(conn, row["id"], checkpoint, "completed")

    def _refresh_locked(self) -> TimerView:
        with self._write() as conn:
            sample = self.clock.sample()
            self._reconcile(conn, sample)
            return self._view(conn, sample)

    def get(self) -> TimerView:
        """Resolve expiry/uncertainty before reporting authoritative remaining time."""
        with self._lock:
            return self._refresh_locked()

    @staticmethod
    def _replay(conn: sqlite3.Connection, operation_id: str | None, fingerprint: str) -> bool:
        if operation_id is None:
            return False
        row = conn.execute("SELECT fingerprint FROM timer_operations WHERE operation_id = ?", (operation_id,)).fetchone()
        if row is None:
            return False
        if row["fingerprint"] != fingerprint:
            raise TimerConflict("operation_id", "This timer request ID was already used for different work. Refresh and try again.")
        return True

    @staticmethod
    def _receipt(conn: sqlite3.Connection, operation_id: str | None, session_id: str, action: str, fingerprint: str) -> None:
        if operation_id is not None:
            conn.execute("INSERT INTO timer_operations VALUES (?, ?, ?, ?)", (operation_id, session_id, action, fingerprint))

    def start(self, task_id: str, duration_minutes: int, operation_id: str) -> TimerView:
        duration = _duration(duration_minutes)
        key = _operation_id(operation_id)
        fingerprint = _fingerprint("start", task_id=task_id, duration_minutes=duration)
        with self._lock:
            self._refresh_locked()
            with self._write() as conn:
                sample = self.clock.sample()
                if self._replay(conn, key, fingerprint):
                    return self._view(conn, sample)
                existing = _active(conn)
                if existing is not None:
                    raise TimerConflict("session", "A countdown is already running, paused, or needs review. Open Track and finish it before starting another.")
                task = _require_task(conn, task_id)
                if conn.execute("SELECT 1 FROM tasks WHERE parent_id = ? LIMIT 1", (task_id,)).fetchone():
                    raise InvalidInput("task_id", "Select a task without subtasks, or select one of its subtasks.")
                project = conn.execute("SELECT name FROM projects WHERE id = ?", (task["project_id"],)).fetchone()
                parent = conn.execute("SELECT title FROM tasks WHERE id = ?", (task["parent_id"],)).fetchone()
                session_id = str(uuid4())
                at = _utc(sample.wall)
                conn.execute(
                    "INSERT INTO timer_sessions (id, start_operation_id, task_id, task_title, project_id, project_name,"
                    " parent_title, duration_minutes, state, started_at, checkpoint_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'running', ?, ?)",
                    (session_id, key, task_id, task["title"], task["project_id"], project["name"],
                     parent["title"] if parent else None, duration, at, at),
                )
                self._open_interval(conn, session_id, at)
                self._receipt(conn, key, session_id, "start", fingerprint)
                self._anchor = sample
                return self._view(conn, sample)

    @staticmethod
    def _open_interval(conn: sqlite3.Connection, session_id: str, at: str) -> None:
        conn.execute(
            "INSERT INTO timer_intervals (id, session_id, started_at, checkpoint_at) VALUES (?, ?, ?, ?)",
            (str(uuid4()), session_id, at, at),
        )

    def _finish(self, conn: sqlite3.Connection, session_id: str, at: str, outcome: str) -> None:
        conn.execute("UPDATE timer_intervals SET ended_at = checkpoint_at WHERE session_id = ? AND ended_at IS NULL", (session_id,))
        conn.execute(
            "UPDATE timer_sessions SET state = 'finished', finished_at = ?, outcome = ?, revision = revision + 1"
            " WHERE id = ? AND state <> 'finished'", (at, outcome, session_id),
        )
        self._anchor = None

    def control(
        self, session_id: str, action: Literal["pause", "resume", "finish"], *,
        expected_revision: int | None = None, operation_id: str | None = None, discard_uncertain: bool = False,
    ) -> TimerView:
        if action not in {"pause", "resume", "finish"}:
            raise InvalidInput("action", "Choose pause, resume, or finish.")
        if not isinstance(discard_uncertain, bool):
            raise InvalidInput("discard_uncertain", "Confirm whether to discard the uncertain gap.")
        if action != "finish" and discard_uncertain:
            raise InvalidInput("discard_uncertain", "Only finishing can discard an uncertain gap.")
        if expected_revision is not None and (
            isinstance(expected_revision, bool) or not isinstance(expected_revision, int) or expected_revision < 1
        ):
            raise InvalidInput("expected_revision", "Refresh the timer and try this control again.")
        if action != "finish" and expected_revision is None:
            raise InvalidInput("expected_revision", "Refresh the timer before pausing or resuming.")
        key = _operation_id(operation_id) if operation_id is not None else None
        fingerprint = _fingerprint(action, session_id=session_id, expected_revision=expected_revision, discard_uncertain=discard_uncertain)
        with self._lock:
            # Save automatic expiry/review even if the requested control is stale.
            self._refresh_locked()
            with self._write() as conn:
                sample = self.clock.sample()
                self._reconcile(conn, sample)
                if self._replay(conn, key, fingerprint):
                    return self._view(conn, sample)
                row = conn.execute("SELECT * FROM timer_sessions WHERE id = ?", (session_id,)).fetchone()
                if row is None:
                    raise InvalidInput("session_id", "This countdown does not exist. Refresh Track to load the current timer.")
                if row["state"] == "finished":
                    if action != "finish":
                        raise TimerConflict("session", "This countdown is already saved. Refresh Track.")
                elif action == "finish":
                    if row["state"] == "needs_review" and not discard_uncertain:
                        raise TimerConflict("discard_uncertain", "Review the confirmed time, then explicitly save it and discard the uncertain gap.")
                    if expected_revision is not None and expected_revision != row["revision"]:
                        raise TimerConflict("revision", "The countdown changed in another tab. Review its current state and try again.")
                    outcome = "interrupted" if row["state"] == "needs_review" else "finished_early"
                    self._finish(conn, session_id, _utc(sample.wall), outcome)
                else:
                    desired, required = ("paused", "running") if action == "pause" else ("running", "paused")
                    if row["state"] != desired:
                        if expected_revision != row["revision"]:
                            raise TimerConflict("revision", "The countdown changed in another tab. Review its current state and try again.")
                        if row["state"] != required:
                            raise TimerConflict("session", "This countdown needs review. Save its confirmed time before starting again.")
                        at = _utc(sample.wall)
                        if action == "pause":
                            conn.execute("UPDATE timer_intervals SET ended_at = checkpoint_at WHERE session_id = ? AND ended_at IS NULL", (session_id,))
                            self._anchor = None
                        else:
                            self._open_interval(conn, session_id, at)
                            self._anchor = sample
                        conn.execute(
                            "UPDATE timer_sessions SET state = ?, checkpoint_at = ?, revision = revision + 1 WHERE id = ?",
                            (desired, at, session_id),
                        )
                self._receipt(conn, key, session_id, action, fingerprint)
                return self._view(conn, sample)

    def start_monitor(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()

        def run() -> None:
            failed = False
            while not self._stop.wait(CHECKPOINT_SECONDS):
                try:
                    self.get()
                    failed = False
                except (sqlite3.Error, StorageError):
                    if not failed:
                        _LOG.warning("The timer checkpoint could not be saved; retrying. Uncertain gaps require review.")
                    failed = True

        self._thread = threading.Thread(target=run, daemon=True, name="bearplans-countdown")
        self._thread.start()

    def stop_monitor(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=6)
            self._thread = None
        # Graceful shutdown saves one last trusted checkpoint. Startup will still
        # require review because the following service-off interval is unknown.
        self.get()
