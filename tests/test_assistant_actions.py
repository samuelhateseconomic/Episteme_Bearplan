"""Assistant actions: proposals never write; explicit apply, revision checks, replay and Undo."""
import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from backend.app import create_app
from backend.domain.assistant import AssistantError, AssistantService
from backend.domain.assistant_actions import ActionConflict, apply_action, propose_action, undo_action
from backend.domain.errors import InvalidInput
from backend.domain.planning import create_placement, list_placements
from backend.domain.projects import create_project
from backend.domain.tasks import create_task, get_task, list_tasks, set_task_completion, update_task
from backend.domain.timer import TimerService
from backend.domain.weeks import close_week, preview_close
from backend.storage.db import open_database
from tests.test_assistant import FakeProvider, rows
from tests.test_timer import FakeClock


@pytest.fixture
def timer(db):
    return TimerService(db, FakeClock())


def key():
    return str(uuid4())


def ask(db, provider, prompt="request", timer=None, **kwargs):
    return asyncio.run(AssistantService(db, provider, timer).ask("fixture:local", prompt, **kwargs))


class RecordingProvider(FakeProvider):
    async def chat(self, model, messages, tools):
        self.tools = [tool["function"]["name"] for tool in tools]
        return await super().chat(model, messages, tools)


def test_reader_agent_has_only_read_tools(db):
    provider = RecordingProvider()
    reply = ask(db, provider, "What is planned today?")
    assert reply["kind"] == "answer" and reply["route"] == {"intent": "question", "agents": ["router", "reader"]}
    assert provider.tools == ["get_day_plan", "get_week_plan", "search_tasks", "list_tasks", "get_task", "get_time_summary"]


def test_sufficient_request_becomes_proposal_without_writing(db):
    project = create_project(db, "School")
    task = create_task(db, "Essay", project_id=project.id)
    provider = FakeProvider(routes=[{"intent": "update_task", "task": "essay", "deadline": "2026-11-20", "notes": ""}])
    before = rows(db)
    reply = ask(db, provider, "Move Essay's deadline to 2026-11-20")
    assert rows(db) == before and provider.messages == []  # the reader agent never ran
    assert reply["kind"] == "proposal" and reply["route"]["agents"] == ["router", "grounding", "action_library", "gate"]
    proposal = reply["proposals"][0]
    assert proposal["arguments"] == {"task_id": task.id, "deadline": "2026-11-20"}
    assert proposal["expected"]["tasks"] == {task.id: task.revision}
    assert "Nothing has changed yet" in reply["answer"]
    assert "never convert them" in provider.route_messages[0][0]["content"]  # dates are resolved by code


def test_ambiguous_task_asks_with_choices_until_selected(db):
    project = create_project(db, "History")
    first = create_task(db, "Reading")
    second = create_task(db, "Reading", project_id=project.id)
    before = rows(db)
    reply = ask(db, FakeProvider(routes=[{"intent": "complete_task", "task": "Reading"}]), "Complete Reading")
    assert reply["kind"] == "clarify" and reply["proposals"] == [] and rows(db) == before
    choices = reply["clarification"]["choices"]["task_id"]
    assert {c["value"] for c in choices} == {first.id, second.id}
    assert any("History" in c["label"] for c in choices)
    chosen = ask(db, FakeProvider(), "", pending=reply["clarification"]["pending"], choice={"slot": "task_id", "value": second.id})
    assert chosen["kind"] == "proposal" and chosen["proposals"][0]["arguments"] == {"task_id": second.id, "complete": True}
    assert chosen["route"]["agents"] == ["action_library", "gate"] and rows(db) == before


def test_missing_details_are_asked_then_a_bare_answer_continues(db, timer):
    task = create_task(db, "Math 55")
    first = ask(db, FakeProvider(routes=[{"intent": "start_timer", "task": "math 55"}]), "Start Math 55", timer)
    assert first["kind"] == "clarify" and first["clarification"]["questions"] == [
        "How many minutes should the countdown run (1–180)?"]
    pending = first["clarification"]["pending"]
    assert pending["slots"]["task_id"] == task.id and pending["round"] == 1
    provider = FakeProvider(routes=[{"intent": "other", "duration_minutes": 45}])
    second = ask(db, provider, "45 minutes", timer, pending=pending)
    assert "start_timer request is waiting" in provider.route_messages[0][0]["content"]
    assert second["kind"] == "proposal" and second["proposals"][0]["arguments"] == {"task_id": task.id, "duration_minutes": 45}
    assert timer.get().active_session is None


def test_unknown_names_invalid_dates_and_missing_fields_are_questions(db):
    create_task(db, "Essay")
    cases = [({"intent": "complete_task", "task": "Nonexistent"}, "couldn't find a task"),
             ({"intent": "assign_task_date", "task": "Essay", "date": "2026-02-30"}, "couldn't tell which date"),
             ({"intent": "assign_task_date", "task": "Essay", "date": "11/12"}, "couldn't tell which date"),
             ({"intent": "assign_task_date", "task": "Essay"}, "Which date"),
             ({"intent": "update_task", "task": "Essay"}, "What should change"),
             ({"intent": "create_task"}, "What should the new task be called"),
             ({"intent": "create_task", "title": "X", "project": "Nowhere"}, "couldn't find a project")]
    before = rows(db)
    for route, text in cases:
        said = " ".join(str(value) for key, value in route.items() if key != "intent")
        reply = ask(db, FakeProvider(routes=[route]), f"please {said}")
        assert reply["kind"] == "clarify" and text in reply["answer"], route
    assert rows(db) == before


def test_unsupported_multiple_and_blocked_requests_never_propose(db):
    parent = create_task(db, "Seminar")
    create_task(db, "Read", parent_id=parent.id)
    before = rows(db)
    for intent in ("unsupported", "multiple"):
        reply = ask(db, FakeProvider(routes=[{"intent": intent, "task": "Seminar"}]))
        assert reply["kind"] == "unsupported" and reply["proposals"] == []
    blocked = ask(db, FakeProvider(routes=[{"intent": "complete_task", "task": "Seminar"}]), "Complete Seminar")
    assert blocked["kind"] == "blocked" and "subtasks" in blocked["answer"]
    assert rows(db) == before


def test_clarification_stops_after_round_limit(db):
    pending = {"intent": "start_timer", "slots": {}, "round": 3}
    reply = ask(db, FakeProvider(routes=[{"intent": "start_timer", "task": "nothing here"}]), "x", pending=pending)
    assert reply["kind"] == "stopped" and reply["clarification"] is None


def test_tampered_pending_state_is_revalidated(db):
    for bad in ({"intent": "delete_task", "slots": {}}, {"intent": "create_task", "slots": {"sql": "x"}},
                {"intent": "create_task", "slots": {}, "round": 99}):
        with pytest.raises(AssistantError) as raised:
            ask(db, FakeProvider(), "x", pending=bad)
        assert raised.value.code == "assistant_pending"
    stale = {"intent": "complete_task", "slots": {"task_id": "00000000-0000-4000-8000-000000000000"}}
    reply = ask(db, FakeProvider(routes=[{"intent": "complete_task"}]), "that one", pending=stale)
    assert reply["kind"] == "clarify" and "Which task" in reply["answer"]
    with pytest.raises(AssistantError):
        ask(db, FakeProvider(), "", choice={"slot": "task_id", "value": "x"})


def test_router_output_is_validated(db):
    with pytest.raises(AssistantError) as raised:
        ask(db, FakeProvider(routes=[{"intent": "drop_everything"}]))
    assert raised.value.code == "assistant_route"
    with pytest.raises(AssistantError):
        ask(db, FakeProvider(routes=[{"intent": "create_task", "title": "x" * 500}]))


def test_create_apply_replay_and_undo(db):
    project = create_project(db, "School")
    proposal = propose_action(db, None, "create_task", {"title": "Lab report", "project_id": project.id, "deadline": "2026-11-09"})
    assert len(list_tasks(db)) == 0 and proposal["summary"] == 'Create task "Lab report" in School, due Mon 2026-11-09'
    op = key()
    applied = apply_action(db, None, proposal, op)
    task = get_task(db, applied["task"]["id"])
    assert task.project_id == project.id and str(task.deadline) == "2026-11-09" and applied["undoable"]
    assert apply_action(db, None, proposal, op) == {**applied, "replayed": True}
    assert len(list_tasks(db)) == 1
    with pytest.raises(ActionConflict, match="different change"):
        apply_action(db, None, {**proposal, "arguments": {"title": "Other"}}, op)
    undo = key()
    result = undo_action(db, op, undo)
    assert result["summary"] == 'Undid: Create task "Lab report" in School, due Mon 2026-11-09' and list_tasks(db) == []
    assert undo_action(db, op, undo) == {**result, "replayed": True}
    with pytest.raises(ActionConflict, match="already undone"):
        undo_action(db, op, key())


def test_undo_create_refused_after_dependent_work(db):
    op = key()
    applied = apply_action(db, None, propose_action(db, None, "create_task", {"title": "Plan me"}), op)
    create_placement(db, applied["task"]["id"], "2026-11-03")
    before = rows(db)
    with pytest.raises(InvalidInput, match="planned dates"):
        undo_action(db, op, key())
    assert rows(db) == before


def test_update_stale_proposal_changes_nothing_and_undo_respects_later_edits(db):
    task = create_task(db, "Draft", notes="v1")
    proposal = propose_action(db, None, "update_task", {"task_id": task.id, "notes": "v2", "deadline": None})
    update_task(db, task.id, title="Draft (user edit)")
    before = rows(db)
    with pytest.raises(ActionConflict, match="changed after this proposal"):
        apply_action(db, None, proposal, key())
    assert rows(db) == before

    fresh = propose_action(db, None, "update_task", {"task_id": task.id, "notes": "v2"})
    op = key()
    apply_action(db, None, fresh, op)
    assert get_task(db, task.id).notes == "v2"
    undo_action(db, op, key())
    restored = get_task(db, task.id)
    assert restored.notes == "v1" and restored.title == "Draft (user edit)"

    again = key()
    apply_action(db, None, propose_action(db, None, "update_task", {"task_id": task.id, "estimate_minutes": 30}), again)
    update_task(db, task.id, notes="user wrote this")
    snapshot = rows(db)
    with pytest.raises(ActionConflict, match="changed after this action"):
        undo_action(db, again, key())
    assert rows(db) == snapshot


def test_complete_rules_and_undo_restores_exact_instant(db):
    parent = create_task(db, "Seminar")
    child = create_task(db, "Read", parent_id=parent.id)
    with pytest.raises(InvalidInput, match="subtasks"):
        propose_action(db, None, "complete_task", {"task_id": parent.id})
    op = key()
    apply_action(db, None, propose_action(db, None, "complete_task", {"task_id": child.id}), op)
    assert get_task(db, parent.id).completed
    undo_action(db, op, key())
    assert not get_task(db, child.id).completed and not get_task(db, parent.id).completed

    other = create_task(db, "Done earlier")
    original = set_task_completion(db, other.id, True).completed_at
    reopen = key()
    apply_action(db, None, propose_action(db, None, "complete_task", {"task_id": other.id, "complete": False}), reopen)
    undo_action(db, reopen, key())
    assert get_task(db, other.id).completed_at == original


def test_assign_date_rules_and_undo(db):
    task = create_task(db, "Practice")
    create_placement(db, task.id, "2026-11-03")
    with pytest.raises(InvalidInput, match="already planned"):
        propose_action(db, None, "assign_task_date", {"task_id": task.id, "date": "2026-11-03"})
    preview_token = preview_close(db, "2026-10-26").preview_token
    close_week(db, "2026-10-26", preview_token)
    with pytest.raises(InvalidInput, match="closed"):
        propose_action(db, None, "assign_task_date", {"task_id": task.id, "date": "2026-10-28"})
    op = key()
    applied = apply_action(db, None, propose_action(db, None, "assign_task_date", {"task_id": task.id, "date": "2026-11-04"}), op)
    assert sorted(str(p.planned_date) for p in list_placements(db)) == ["2026-11-03", "2026-11-04"]
    undo_action(db, op, key())
    assert [str(p.planned_date) for p in list_placements(db)] == ["2026-11-03"]
    assert applied["placement"]["planned_date"] == "2026-11-04"


def test_invalid_arguments_are_rejected(db):
    task = create_task(db, "X")
    for kind, raw in [("update_task", {"task_id": task.id}), ("update_task", {"task_id": task.id, "title": None}),
                      ("assign_task_date", {"task_id": task.id, "date": "11/04/2026"}),
                      ("create_task", {"title": "x", "sql": "DROP TABLE tasks"}),
                      ("start_timer", {"task_id": task.id, "duration_minutes": "45"}), ("delete_task", {})]:
        with pytest.raises((InvalidInput, ValueError)):
            propose_action(db, None, kind, raw)
    with pytest.raises(InvalidInput):
        apply_action(db, None, {"kind": "create_task", "arguments": {"title": "x"}, "expected": {}}, "not-a-uuid")
    with pytest.raises(InvalidInput):
        apply_action(db, None, {"kind": "drop", "arguments": {}, "expected": {}}, key())
    assert [t.title for t in list_tasks(db)] == ["X"]


def test_timer_actions_apply_with_replay_and_no_undo(db, timer):
    task = create_task(db, "Math 55")
    start = propose_action(db, timer, "start_timer", {"task_id": task.id, "duration_minutes": 45})
    assert timer.get().active_session is None and not start["undoable"]
    op = key()
    started = apply_action(db, timer, start, op)
    assert started["session"]["state"] == "running" and started["session"]["duration_minutes"] == 45
    assert apply_action(db, timer, start, op)["replayed"]
    with pytest.raises(ActionConflict, match="Timer changes cannot be undone"):
        undo_action(db, op, key())
    with pytest.raises(ActionConflict, match="already running"):
        propose_action(db, timer, "start_timer", {"task_id": task.id, "duration_minutes": 10})

    pause = propose_action(db, timer, "pause_timer", {})
    session_id, revision = started["session"]["id"], pause["expected"]["session_revision"]
    timer.control(session_id, "pause", expected_revision=revision)
    timer.control(session_id, "resume", expected_revision=revision + 1)
    with pytest.raises(Exception, match="changed in another tab"):
        apply_action(db, timer, pause, key())
    finish = propose_action(db, timer, "finish_timer", {})
    done = apply_action(db, timer, finish, key())
    assert done["session"]["state"] == "finished" and timer.get().active_session is None


def test_receipts_survive_restart_and_are_immutable(db):
    op = key()
    apply_action(db, None, propose_action(db, None, "create_task", {"title": "Persist"}), op)
    reopened = open_database(db.path)
    assert apply_action(reopened, None, propose_action(reopened, None, "create_task", {"title": "Persist"}), op)["replayed"]
    with reopened.write() as conn, pytest.raises(Exception, match="immutable"):
        conn.execute("DELETE FROM assistant_actions")


def test_api_apply_undo_and_error_shapes(db, timer):
    client = TestClient(create_app(db, timer_clock=FakeClock(), assistant_provider=FakeProvider()), base_url="http://127.0.0.1:8765")
    task = create_task(db, "API task")
    proposal = propose_action(db, None, "complete_task", {"task_id": task.id})
    op = key()
    response = client.post("/api/assistant/actions/apply", json={"proposal": proposal, "operation_id": op})
    assert response.status_code == 200 and response.json()["task"]["completed"]
    stale = client.post("/api/assistant/actions/apply", json={"proposal": proposal, "operation_id": key()})
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "assistant_action_conflict"
    undo = client.post(f"/api/assistant/actions/{op}/undo", json={"undo_operation_id": key()})
    assert undo.status_code == 200 and not get_task(db, task.id).completed
    missing = client.post(f"/api/assistant/actions/{key()}/undo", json={"undo_operation_id": key()})
    assert missing.status_code == 422 and "error" in missing.json()
    malformed = client.post("/api/assistant/actions/apply", json={"proposal": proposal, "operation_id": op, "extra": 1})
    assert malformed.status_code == 422
    status = client.get("/api/assistant/status").json()
    assert status["actions"] == "proposals_require_apply" and status["agents"][0] == "router"
    empty = client.post("/api/assistant/chat", json={"model": "fixture:local", "prompt": " "})
    assert empty.status_code == 422


def test_router_provider_call_is_structured_toolless_and_rejects_partial_output():
    from backend.platform.ollama import OllamaProvider
    from backend.domain.assistant import route_schema
    provider = OllamaProvider()
    provider._thinking["fixture:local"] = True
    sent = {}
    async def response(method, path, payload, **kwargs):
        sent.update(payload)
        return {"done": True, "done_reason": "stop", "message": {"content": '{"intent": "pause_timer"}', "thinking": "x"}}
    provider._json = response
    assert asyncio.run(provider.classify("fixture:local", [], route_schema())) == {"intent": "pause_timer"}
    assert sent["format"] == route_schema() and sent["think"] is False and "tools" not in sent
    for message in ({"content": "not json"}, {"content": "[1]"}):
        async def bad(*args, message=message, **kwargs):
            return {"done": True, "done_reason": "stop", "message": message}
        provider._json = bad
        with pytest.raises(AssistantError):
            asyncio.run(provider.classify("fixture:local", [], route_schema()))
    async def partial(*args, **kwargs):
        return {"done": True, "done_reason": "length", "message": {"content": "{"}}
    provider._json = partial
    with pytest.raises(AssistantError, match="incomplete"):
        asyncio.run(provider.classify("fixture:local", [], route_schema()))


def test_day_words_are_resolved_by_code_not_the_model():
    from datetime import date
    from backend.domain.action_library import parse_day
    sunday = date(2026, 11, 1)
    cases = {"Tuesday": "2026-11-03", "this tue": "2026-11-03", "on Sunday": "2026-11-01", "next Tuesday": "2026-11-03",
             "next sunday": "2026-11-08", "tomorrow": "2026-11-02", "today": "2026-11-01", "November 12": "2026-11-12",
             "Nov 12th": "2026-11-12", "12 November 2027": "2027-11-12", "October 3": "2027-10-03", "2026-12-01": "2026-12-01"}
    for text, expected in cases.items():
        assert str(parse_day(text, sunday)) == expected, text
    for text in ("11/12", "soon", "next week", "February 30", "Tuesday or Wednesday", "2026-13-01"):
        assert parse_day(text, sunday) is None, text
    tuesday = date(2026, 11, 3)
    assert str(parse_day("Tuesday", tuesday)) == "2026-11-03" and str(parse_day("next Tuesday", tuesday)) == "2026-11-10"


def test_router_day_words_reach_the_card_with_weekday(db, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    from backend.domain import action_library
    from datetime import date
    task = create_task(db, "Essay")
    pending = action_library.Pending(intent="assign_task_date", slots=action_library.Slots(task="Essay", date="Tuesday"))
    gate = action_library.evaluate(db, None, pending, today=date(2026, 11, 1))
    assert gate.proposal["arguments"] == {"task_id": task.id, "date": "2026-11-03"}
    assert gate.proposal["summary"] == 'Plan "Essay" (Inbox) on Tue 2026-11-03'


def test_grounding_drops_invented_or_misplaced_details(db):
    from backend.domain.action_library import Slots, ground
    invented = Slots(title="Outline chapter 2", deadline="November 12", date="November 12", estimate_minutes=60,
                     duration_minutes=60, complete=False, project="History")
    kept, ignored = ground("create_task", invented, "Create a task called Outline chapter 2 due November 12 in History.")
    assert kept.model_dump(exclude_none=True) == {"title": "Outline chapter 2", "deadline": "November 12", "project": "History"}
    assert set(ignored) == {"date", "estimate_minutes", "duration_minutes", "complete"}
    assert ground("start_timer", Slots(task="Math", duration_minutes=90), "start math for 1.5 hours")[0].duration_minutes == 90
    assert ground("start_timer", Slots(task="Math", duration_minutes=60), "start math for an hour")[0].duration_minutes == 60
    assert ground("start_timer", Slots(task="Math", duration_minutes=45), "start math")[0].duration_minutes is None
    assert ground("complete_task", Slots(task="Reading", complete=False), "Complete Reading")[0].complete is None
    assert ground("complete_task", Slots(task="Reading", complete=False), "Reopen Reading")[0].complete is False
    assert ground("complete_task", Slots(task="Reading", complete=False), "Reading is not done yet")[0].complete is False
    assert ground("complete_task", Slots(task="Essay"), "Complete Reading")[0].task is None


def test_invented_estimate_never_reaches_the_card_and_named_project_narrows(db):
    history = create_project(db, "History")
    create_task(db, "Reading")
    target = create_task(db, "Reading", project_id=history.id)
    route = {"intent": "create_task", "title": "Outline", "estimate_minutes": 60, "date": "Friday"}
    reply = ask(db, FakeProvider(routes=[route]), "Create a task called Outline")
    assert reply["proposals"][0]["arguments"] == {"title": "Outline"}
    assert set(reply["route"]["ignored_details"]) == {"estimate_minutes", "date"}
    reopen = ask(db, FakeProvider(routes=[{"intent": "complete_task", "task": "Reading", "complete": False}]),
                 "Reopen Reading in History")
    assert reopen["kind"] == "blocked" and "already incomplete" in reopen["answer"]
    set_task_completion(db, target.id, True)
    reopen = ask(db, FakeProvider(routes=[{"intent": "complete_task", "task": "Reading", "complete": False}]),
                 "Reopen Reading in History")
    assert reopen["kind"] == "proposal"
    assert reopen["proposals"][0]["arguments"] == {"task_id": target.id, "complete": False}


def test_creation_details_are_read_from_the_users_words_when_the_router_omits_them(db):
    biology = create_project(db, "Biology")
    writing = create_project(db, "Writing")
    essay = create_task(db, "Essay", project_id=writing.id)
    reply = ask(db, FakeProvider(routes=[{"intent": "create_task", "title": "Problem set 5", "deadline": "2026-11-11"}]),
                "Create a task called Problem set 5 due 2026-11-11 in Biology.")
    assert reply["proposals"][0]["arguments"] == {"title": "Problem set 5", "project_id": biology.id, "deadline": "2026-11-11"}
    sub = ask(db, FakeProvider(routes=[{"intent": "create_task", "task": "Conclusion"}]), "Add a subtask called Conclusion under Essay.")
    assert sub["proposals"][0]["arguments"] == {"title": "Conclusion", "parent_id": essay.id}
    titled = ask(db, FakeProvider(routes=[{"intent": "create_task"}]), "Create a task called Writing practice")
    assert titled["proposals"][0]["arguments"] == {"title": "Writing practice"}  # project name inside the title is not a scope


def test_rename_summary_names_the_old_title(db):
    task = create_task(db, "Groceries")
    proposal = propose_action(db, None, "update_task", {"task_id": task.id, "title": "Weekly groceries"})
    assert proposal["summary"] == 'Edit "Groceries" (Inbox): title → Weekly groceries'
    assert apply_action(db, None, proposal, key())["summary"] == proposal["summary"]
