"""Reviewed corrections within original confirmed interval ceilings.

Edits change integer credit, never interval dates or uncertain gaps. Baselines,
before/after audit and reward deltas remain append-only. Reversal is another
reviewed edit using the previous audit's before-values, never audit deletion.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import hashlib
import json
import sqlite3
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr

from backend.domain.calendar import ApplicationCalendar
from backend.domain.errors import InvalidInput
from backend.domain.rewards import _balance, session_award
from backend.domain.streaks import THRESHOLD_MICROSECONDS, StreakDataError, allocate_confirmed_time
from backend.domain.text import clean_text
from backend.storage.db import Database, utc_now


class CorrectionConflict(InvalidInput):
    """Saved work or its reviewed effects changed before applying."""


class IntervalEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: StrictStr
    active_microseconds: StrictInt


class CorrectionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: StrictInt
    reason: StrictStr
    intervals: list[IntervalEdit]


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _normalize(draft: CorrectionDraft) -> dict:
    if draft.expected_revision < 1:
        raise InvalidInput("expected_revision", "Refresh the saved session before editing it.")
    reason = clean_text(draft.reason, "reason", max_length=500, required=True,
                        empty_message="Enter a reason for this correction.", long_message="Keep the reason to 500 characters or fewer.")
    edits = [{"id": edit.id, "active_microseconds": edit.active_microseconds} for edit in draft.intervals]
    if len({edit["id"] for edit in edits}) != len(edits):
        raise InvalidInput("intervals", "Include each saved interval exactly once.")
    return {"expected_revision": draft.expected_revision, "reason": reason, "intervals": sorted(edits, key=lambda edit: edit["id"])}


def _load(conn: sqlite3.Connection, session_id: str) -> dict:
    session = conn.execute("SELECT * FROM timer_sessions WHERE id = ?", (session_id,)).fetchone()
    if session is None:
        raise InvalidInput("session_id", "This saved session does not exist. Refresh saved sessions.")
    rows = [dict(row) for row in conn.execute("SELECT * FROM timer_intervals WHERE session_id = ? ORDER BY rowid", (session_id,))]
    baseline = conn.execute("SELECT intervals_json FROM session_correction_baselines WHERE session_id = ?", (session_id,)).fetchone()
    originals = json.loads(baseline[0]) if baseline else rows
    ceilings = {row["id"]: row["active_microseconds"] for row in originals}
    reason = None
    if session["state"] != "finished":
        reason = "Finish or resolve this session in Track before correcting it."
    elif not rows or any(row["ended_at"] is None for row in rows):
        reason = "This session lacks complete saved intervals; no time will be inferred."
    elif conn.execute("SELECT 1 FROM timer_interruptions WHERE session_id = ? AND resolved_at IS NULL", (session_id,)).fetchone():
        reason = "Resolve this session's interruption in Track before correcting it."
    elif sum(row["active_microseconds"] for row in rows) != session["active_microseconds"]:
        reason = "Saved interval and session totals disagree. Keep your records and report this data error."
    elif set(ceilings) != {row["id"] for row in rows}:
        reason = "Saved interval identities changed. Keep your records and report this data error."
    else:
        try:
            for row in rows:
                allocate_confirmed_time(defaultdict(int), ApplicationCalendar.from_environment(),
                                        row["started_at"], row["ended_at"], row["active_microseconds"])
                if not 0 <= row["active_microseconds"] <= ceilings[row["id"]]:
                    raise StreakDataError()
        except StreakDataError:
            reason = "Saved interval dates or credit are invalid. Keep your records and report this data error."
    enrollment = conn.execute("SELECT coins_per_minute FROM coin_enrollments WHERE session_id = ?", (session_id,)).fetchone()
    award = session_award(conn, session_id)
    if session["state"] == "finished" and enrollment and (award is None or award != session["active_microseconds"] // 60_000_000 * enrollment[0]):
        reason = "Saved reward contribution disagrees with this session. Keep your records and report this data error."
    tree = conn.execute("SELECT * FROM trees WHERE session_id = ?", (session_id,)).fetchone()
    if tree and tree["outcome"] is None and session["state"] == "finished":
        reason = "The saved tree is not finalized. Keep your records and report this data error."
    return {"session": dict(session), "rows": rows, "originals": originals, "ceilings": ceilings,
            "blocked_reason": reason, "rate": enrollment[0] if enrollment else None,
            "award": award, "tree": dict(tree) if tree else None}


def list_saved_sessions(db: Database) -> list[dict]:
    with db.read() as conn:
        conn.execute("BEGIN")
        ids = [row[0] for row in conn.execute("SELECT id FROM timer_sessions WHERE state = 'finished' ORDER BY rowid DESC")]
        result = []
        for session_id in ids:
            data = _load(conn, session_id)
            session = data["session"]
            history = [dict(row) for row in conn.execute(
                "SELECT operation_id, reason, before_json, after_json, created_at FROM session_corrections "
                "WHERE session_id = ? ORDER BY rowid DESC", (session_id,),
            )]
            result.append({**{key: session[key] for key in ("id", "task_title", "project_name", "parent_title", "finished_at",
                                                          "duration_minutes", "active_microseconds", "outcome", "revision")},
                           "blocked_reason": data["blocked_reason"], "coin_contribution": data["award"],
                           "intervals": [{"id": row["id"], "started_at": row["started_at"], "ended_at": row["ended_at"],
                                          "active_microseconds": row["active_microseconds"],
                                          "maximum_microseconds": data["ceilings"].get(row["id"], 0)} for row in data["rows"]],
                           "history": [{"operation_id": row["operation_id"], "reason": row["reason"], "created_at": row["created_at"],
                                        "before": json.loads(row["before_json"]), "after": json.loads(row["after_json"])} for row in history]})
        return result


def _preview(conn: sqlite3.Connection, session_id: str, draft: dict) -> tuple[dict, dict]:
    data = _load(conn, session_id)
    session = data["session"]
    if data["blocked_reason"]:
        raise CorrectionConflict("session", data["blocked_reason"])
    if session["revision"] != draft["expected_revision"]:
        raise CorrectionConflict("expected_revision", "This session changed. Refresh saved sessions, then review the correction again.")
    edits = {edit["id"]: edit["active_microseconds"] for edit in draft["intervals"]}
    if edits.keys() != data["ceilings"].keys():
        raise InvalidInput("intervals", "Include every saved interval exactly once, without adding or removing intervals.")
    if any(not 0 <= value <= data["ceilings"][key] for key, value in edits.items()):
        raise InvalidInput("intervals", "Use time between zero and each interval's original confirmed maximum. Uncertain time cannot be added.")
    total = sum(edits.values())
    if total > session["duration_minutes"] * 60_000_000:
        raise InvalidInput("intervals", "Corrected time cannot exceed the original countdown duration.")
    if all(edits[row["id"]] == row["active_microseconds"] for row in data["rows"]):
        raise InvalidInput("intervals", "Change at least one interval before reviewing a correction.")
    calendar = ApplicationCalendar.from_environment()
    before, after = defaultdict(int), defaultdict(int)
    for row in data["rows"]:
        allocate_confirmed_time(before, calendar, row["started_at"], row["ended_at"], row["active_microseconds"])
        allocate_confirmed_time(after, calendar, row["started_at"], row["ended_at"], edits[row["id"]])
    day_totals = defaultdict(int)
    for row in conn.execute(
        "SELECT i.started_at, i.ended_at, i.active_microseconds FROM timer_intervals i "
        "JOIN timer_sessions s ON s.id = i.session_id WHERE s.state = 'finished' AND i.ended_at IS NOT NULL "
        "AND NOT EXISTS (SELECT 1 FROM timer_interruptions x WHERE x.session_id = s.id AND x.resolved_at IS NULL)"
    ):
        allocate_confirmed_time(day_totals, calendar, row["started_at"], row["ended_at"], row["active_microseconds"])
    contribution = None if data["rate"] is None else total // 60_000_000 * data["rate"]
    delta = 0 if contribution is None else contribution - data["award"]
    balance = _balance(conn)
    tree_after = None if not data["tree"] else "mature" if session["outcome"] == "completed" and total == session["duration_minutes"] * 60_000_000 else "unfinished"
    view = {"session_id": session_id, "before_microseconds": session["active_microseconds"], "after_microseconds": total,
            "coin_delta": delta, "balance_before": balance, "balance_after": balance + delta,
            "coin_contribution_after": contribution,
            "tree_before": data["tree"]["outcome"] if data["tree"] else None, "tree_after": tree_after,
            "timezone": calendar.label(datetime.now(UTC)),
            "days": [{"date": str(day), "before_microseconds": before[day], "after_microseconds": after[day],
                      "day_total_before_microseconds": day_totals[day],
                      "day_total_after_microseconds": day_totals[day] - before[day] + after[day],
                      "qualified_before": day_totals[day] >= THRESHOLD_MICROSECONDS,
                      "qualified_after": day_totals[day] - before[day] + after[day] >= THRESHOLD_MICROSECONDS}
                     for day in sorted(before.keys() | after.keys())]}
    token = hashlib.sha256(_json({"draft": draft, "view": view, "rows": data["rows"], "tree": data["tree"]}).encode()).hexdigest()
    return {**view, "preview_token": token}, data


def preview_correction(db: Database, session_id: str, draft: CorrectionDraft) -> dict:
    normalized = _normalize(draft)
    with db.read() as conn:
        conn.execute("BEGIN")
        return _preview(conn, session_id, normalized)[0]


def apply_correction(db: Database, session_id: str, draft: CorrectionDraft, preview_token: str, operation_id: str) -> dict:
    normalized = _normalize(draft)
    try:
        key = str(UUID(operation_id))
    except (ValueError, TypeError, AttributeError):
        raise InvalidInput("operation_id", "Use a valid new UUID for this correction.") from None
    fingerprint = _json({"session_id": session_id, "draft": normalized, "preview_token": preview_token})
    with db.write() as conn:
        receipt = conn.execute("SELECT fingerprint, result_json FROM session_corrections WHERE operation_id = ?", (key,)).fetchone()
        if receipt:
            if receipt["fingerprint"] != fingerprint:
                raise CorrectionConflict("operation_id", "This correction ID was used for different work. Refresh and review a new correction.")
            return json.loads(receipt["result_json"])
        preview, data = _preview(conn, session_id, normalized)
        if preview_token != preview["preview_token"]:
            raise CorrectionConflict("preview_token", "The session, wallet or date attribution changed. Review the correction again.")
        at = utc_now()
        result = {"operation_id": key, "session_id": session_id, "revision": normalized["expected_revision"] + 1,
                  "active_microseconds": preview["after_microseconds"], "coin_delta": preview["coin_delta"],
                  "balance_at_save": preview["balance_after"], "tree_outcome": preview["tree_after"]}
        before = [{"id": row["id"], "active_microseconds": row["active_microseconds"]} for row in data["rows"]]
        conn.execute("INSERT INTO session_correction_baselines VALUES (?, ?) ON CONFLICT(session_id) DO NOTHING",
                     (session_id, _json(data["originals"])))
        conn.execute("INSERT INTO session_corrections VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                     (key, session_id, fingerprint, normalized["reason"], _json(before), _json(normalized["intervals"]), at, _json(result)))
        for edit in normalized["intervals"]:
            conn.execute("UPDATE timer_intervals SET active_microseconds = ? WHERE id = ? AND session_id = ?",
                         (edit["active_microseconds"], edit["id"], session_id))
        conn.execute("UPDATE timer_sessions SET active_microseconds = ?, revision = revision + 1 WHERE id = ?",
                     (preview["after_microseconds"], session_id))
        if data["rate"] is not None:
            position = conn.execute("SELECT COALESCE(MAX(rowid), 0) FROM coin_ledger").fetchone()[0]
            conn.execute("INSERT INTO coin_adjustments VALUES (?, ?, ?, ?, ?, ?)",
                         (str(uuid4()), key, session_id, preview["coin_delta"], at, position))
        if data["tree"]:
            conn.execute("UPDATE trees SET outcome = ? WHERE session_id = ?", (preview["tree_after"], session_id))
        return result
