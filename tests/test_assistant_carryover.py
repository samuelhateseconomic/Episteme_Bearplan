"""Assistant week carryover: same-weekday proposal, Apply with replay, all-or-nothing Undo, migration 0015."""
import asyncio
import sqlite3
from datetime import date
from uuid import uuid4

import pytest

from backend.domain.assistant import AssistantService
from backend.domain.assistant_actions import ActionConflict, apply_action, propose_action, undo_action
from backend.domain.errors import InvalidInput
from backend.domain.planning import create_placement, list_placements, move_placement
from backend.domain.projects import create_project
from backend.domain.tasks import create_task, get_task, set_task_completion, update_task
from backend.domain.weeks import close_week, preview_close
from backend.storage.db import Database
from backend.storage.migrations import current_version, load_migrations, migrate
from tests.test_assistant import FakeProvider, rows

WEEK = "2026-10-12"


def key():
    return str(uuid4())


def close(db, week=WEEK):
    close_week(db, week, preview_close(db, week).preview_token)


@pytest.fixture
def week(db):
    project = create_project(db, "Seminar")
    parent = create_task(db, "Assignment", project_id=project.id)
    proof = create_task(db, "Proof", parent_id=parent.id, deadline="2026-10-30")
    reading = create_task(db, "Reading", project_id=project.id)
    done = create_task(db, "Done task")
    later = create_task(db, "Finished after closing")
    create_placement(db, proof.id, "2026-10-13")      # Tuesday
    create_placement(db, reading.id, "2026-10-15")    # Thursday
    create_placement(db, reading.id, "2026-10-17")    # and Saturday: the last planned day wins
    create_placement(db, done.id, "2026-10-14")
    create_placement(db, later.id, "2026-10-16")
    set_task_completion(db, done.id, True)
    close(db)
    set_task_completion(db, later.id, True)
    return {"proof": proof, "reading": reading, "later": later}


def test_proposal_preselects_same_weekday_keeps_deadlines_and_writes_nothing(db, week):
    before = rows(db)
    proposal = propose_action(db, None, "carry_over_week", {"week_start": WEEK})
    assert rows(db) == before
    assert proposal["arguments"]["selections"] == sorted([
        {"task_id": week["proof"].id, "planned_date": "2026-10-20"},
        {"task_id": week["reading"].id, "planned_date": "2026-10-24"}], key=lambda item: item["task_id"])
    assert proposal["summary"] == ("Carry 2 unfinished tasks from the week of Mon 2026-10-12 to the same weekday "
                                   "next week (1 cannot carry over)")
    items = {item["title"]: item for item in proposal["preview"]["items"]}
    assert items["Proof"]["deadline"] == "2026-10-30" and items["Proof"]["parent_title"] == "Assignment"
    assert proposal["expected"]["preview_token"] and proposal["undoable"] is True


def test_apply_replays_and_undo_removes_every_carried_plan(db, week):
    proposal = propose_action(db, None, "carry_over_week", {"week_start": WEEK})
    operation = key()
    result = apply_action(db, None, proposal, operation)
    plans = {(p.task_id, str(p.planned_date)) for p in list_placements(db)}
    assert plans == {(week["proof"].id, "2026-10-20"), (week["reading"].id, "2026-10-24")}
    assert get_task(db, week["proof"].id).deadline == date(2026, 10, 30)
    assert result["undoable"] and not result["replayed"]
    assert apply_action(db, None, proposal, operation)["replayed"] is True
    assert len(list_placements(db)) == 2
    undo = key()
    assert undo_action(db, operation, undo)["summary"].startswith("Undid: Carry 2 unfinished tasks")
    assert list_placements(db) == []
    assert undo_action(db, operation, undo)["replayed"] is True
    # Carrying again works after an Undo, with a new request ID.
    apply_action(db, None, propose_action(db, None, "carry_over_week", {"week_start": WEEK}), key())
    assert len(list_placements(db)) == 2


def test_stale_proposal_and_reused_key_change_nothing(db, week):
    proposal = propose_action(db, None, "carry_over_week", {"week_start": WEEK})
    update_task(db, week["proof"].id, title="Proof v2")
    before = rows(db)
    with pytest.raises(ActionConflict, match="Review carryover again"):
        apply_action(db, None, proposal, key())
    assert rows(db) == before
    fresh = propose_action(db, None, "carry_over_week", {"week_start": WEEK})
    operation = key()
    apply_action(db, None, fresh, operation)
    edited = {**fresh, "arguments": {**fresh["arguments"], "selections": fresh["arguments"]["selections"][:1]}}
    with pytest.raises(ActionConflict, match="different change"):
        apply_action(db, None, edited, operation)


def test_undo_is_all_or_nothing_when_a_carried_plan_changed(db, week):
    proposal = propose_action(db, None, "carry_over_week", {"week_start": WEEK})
    operation = key()
    apply_action(db, None, proposal, operation)
    moved = next(p for p in list_placements(db) if p.task_id == week["proof"].id)
    move_placement(db, moved.id, "2026-10-21")
    before = rows(db)
    with pytest.raises(ActionConflict, match="carried plan changed"):
        undo_action(db, operation, key())
    assert rows(db) == before and len(list_placements(db)) == 2


def test_open_week_and_nothing_eligible_are_blocked_without_change(db, week):
    task = create_task(db, "Open week work")
    create_placement(db, task.id, "2026-10-28")
    before = rows(db)
    with pytest.raises(InvalidInput, match="still open. Close it first"):
        propose_action(db, None, "carry_over_week", {"week_start": "2026-10-26"})
    apply_action(db, None, propose_action(db, None, "carry_over_week", {"week_start": WEEK}), key())
    with pytest.raises(InvalidInput, match="No unfinished work .* can carry over. 3 unfinished tasks"):
        propose_action(db, None, "carry_over_week", {"week_start": WEEK})
    assert rows(db)["closed_weeks"] == before["closed_weeks"]


def test_malformed_carry_proposals_are_refused(db, week):
    proposal = propose_action(db, None, "carry_over_week", {"week_start": WEEK})
    before = rows(db)
    for broken in ({**proposal, "arguments": {"week_start": WEEK}},
                   {**proposal, "expected": {**proposal["expected"], "preview_token": None}},
                   {**proposal, "arguments": {**proposal["arguments"], "sql": "DROP TABLE tasks"}}):
        with pytest.raises(InvalidInput):
            apply_action(db, None, broken, key())
    assert rows(db) == before


def ask(db, route, prompt):
    provider = FakeProvider(routes=[route])
    return asyncio.run(AssistantService(db, provider).ask("fixture:local", prompt))


def test_router_intent_reaches_the_gate_for_this_or_last_week(db, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    from backend.domain import action_library
    real = action_library.evaluate

    def on_day(db_, timer, pending, today=None, message=""):
        return real(db_, timer, pending, date(2026, 10, 19), message)
    monkeypatch.setattr("backend.domain.assistant.evaluate", on_day)
    task = create_task(db, "Essay")
    create_placement(db, task.id, "2026-10-16")  # Friday of the week of Oct 12
    close(db)
    this_week = ask(db, {"intent": "carry_over_week"}, "Move this week's unfinished tasks to next week")
    assert this_week["kind"] == "blocked" and "still open" in this_week["answer"]
    last_week = ask(db, {"intent": "carry_over_week"}, "Carry over last week's unfinished work")
    assert last_week["kind"] == "proposal"
    assert last_week["proposals"][0]["arguments"]["selections"] == [{"task_id": task.id, "planned_date": "2026-10-23"}]
    assert list_placements(db) == []  # Nothing applied until the user presses Apply.


def test_migration_0015_keeps_receipts_and_immutability(tmp_path):
    shipped = load_migrations()
    assert [m.name for m in shipped][-1] == "assistant_carryover"
    db = Database(tmp_path / "old.sqlite3")
    migrate(db, shipped[:14])
    assert current_version(db) == 14
    receipt, undo = key(), key()
    with db.write() as conn:
        conn.execute("INSERT INTO assistant_actions VALUES (?, 'complete_task', 'f', '{}', '{}', '{\"summary\": \"x\"}', 't')", (receipt,))
        conn.execute("INSERT INTO assistant_action_undos VALUES (?, ?, '{}', 't')", (undo, receipt))
    migrate(db, shipped)
    assert current_version(db) == len(shipped)
    with db.read() as conn:
        assert conn.execute("SELECT kind FROM assistant_actions").fetchall()[0][0] == "complete_task"
        assert conn.execute("SELECT action_operation_id FROM assistant_action_undos").fetchone()[0] == receipt
    for statement in ("UPDATE assistant_actions SET kind = 'update_task'", "DELETE FROM assistant_actions",
                      "UPDATE assistant_action_undos SET created_at = 'x'", "DELETE FROM assistant_action_undos"):
        with pytest.raises(sqlite3.DatabaseError, match="immutable"):
            with db.write() as conn:
                conn.execute(statement)
    with db.write() as conn:
        conn.execute("INSERT INTO assistant_actions VALUES (?, 'carry_over_week', 'f', '{}', '{}', '{}', 't')", (key(),))
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO assistant_actions VALUES (?, 'drop_everything', 'f', '{}', NULL, '{}', 't')", (key(),))
