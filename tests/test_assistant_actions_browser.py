"""Assistant change flow in real Chrome: choice → proposal card → Apply → Undo on the real service.

Chat replies are produced by the real pipeline (fake router only), then served to
the page; Apply and Undo go to the running service, so the card's effect on saved
records is checked end to end.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from backend.domain.assistant import AssistantService
from backend.domain.projects import create_project
from backend.domain.tasks import create_task
from backend.platform.paths import DATABASE_FILENAME, FRONTEND_DIST
from backend.storage.db import open_database
from tests.conftest import Service, free_port, http_json
from tests.test_assistant import FakeProvider
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync
from tests.test_forest import all_rows

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not (FRONTEND_DIST / "index.html").is_file(), reason="frontend not built")]

def run(coroutine):
    """Playwright's sync API owns this thread's event loop; run the pipeline on another thread."""
    with ThreadPoolExecutor(1) as pool:
        return pool.submit(asyncio.run, coroutine).result()


STATUS = {"available": True, "read_only": False, "prompt_version": "fixture",
          "models": [{"name": "fixture:local", "digest": "fixture", "details": {}}]}


def test_choice_proposal_apply_undo_and_dismiss(browser, evidence, tmp_path, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    expect = playwright_sync.expect
    data_dir = tmp_path / "AssistantActions"
    data_dir.mkdir()
    db = open_database(data_dir / DATABASE_FILENAME)
    history, biology = create_project(db, "History"), create_project(db, "Biology")
    create_task(db, "Reading", project_id=history.id)
    target = create_task(db, "Reading", project_id=biology.id)
    create_task(db, "Lab report")

    service = AssistantService(db, FakeProvider(routes=[{"intent": "complete_task", "task": "Reading", "complete": True}]))
    clarify = run(service.ask("fixture:local", "Complete Reading"))
    assert clarify["clarification"]["choices"], clarify
    slot, options = next(iter(clarify["clarification"]["choices"].items()))
    picked = next(o for o in options if "Biology" in o["label"])
    proposal = run(service.ask("fixture:local", "", pending=clarify["clarification"]["pending"],
                                       choice={"slot": slot, "value": picked["value"]}))
    assert proposal["proposals"] and proposal["proposals"][0]["arguments"]["task_id"] == target.id, proposal
    # The card names the chosen project, so duplicate titles are told apart before Apply.
    assert proposal["proposals"][0]["summary"] == 'Mark "Reading" (Biology) complete'
    dismissable = run(AssistantService(db, FakeProvider(routes=[
        {"intent": "complete_task", "task": "Lab report", "complete": True}])).ask("fixture:local", "Complete Lab report"))
    before = all_rows(db)

    app = Service(data_dir, free_port()).start()
    replies, requests = [clarify, proposal, dismissable], []

    def chat(route):
        requests.append(route.request.post_data_json)
        route.fulfill(json=replies.pop(0))

    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        page.route("**/api/assistant/status", lambda route: route.fulfill(json=STATUS))
        page.route("**/api/assistant/chat", chat)
        page.goto(app.url + "/#assistant")
        page.get_by_label("Local model").select_option("fixture:local")
        page.get_by_label("Question", exact=True).fill("Complete Reading")
        page.get_by_role("button", name="Ask", exact=True).click()

        details = page.get_by_label("Details needed")
        expect(details).to_be_visible()
        expect(page.get_by_role("button", name="Start over")).to_be_visible()
        page.screenshot(path=str(evidence / "assistant-actions-01-choice.png"), full_page=True)
        details.get_by_role("button", name=picked["label"], exact=True).click()

        card = page.get_by_role("article", name=f"Proposed change: {proposal['proposals'][0]['summary']}")
        expect(card).to_be_visible()
        expect(card.get_by_text("Not applied. Review it, then choose Apply.")).to_be_visible()
        assert requests[1]["choice"] == {"slot": slot, "value": picked["value"]} and requests[1]["pending"]
        assert all_rows(db) == before  # Showing a proposal changes nothing.
        no_horizontal_overflow(page)
        page.screenshot(path=str(evidence / "assistant-actions-02-proposal.png"), full_page=True)

        card.get_by_role("button", name="Apply", exact=True).click()
        expect(card.get_by_role("status")).to_contain_text("Applied.")
        tasks = {t["id"]: t for t in http_json("GET", app.url + "/api/planning")[1]["tasks"]}
        assert tasks[target.id]["completed"] and not any(
            t["completed"] for t in tasks.values() if t["id"] != target.id)
        page.screenshot(path=str(evidence / "assistant-actions-03-applied.png"), full_page=True)

        card.get_by_role("button", name="Undo", exact=True).click()
        expect(card.get_by_role("status")).to_contain_text("Undone.")
        tasks = {t["id"]: t for t in http_json("GET", app.url + "/api/planning")[1]["tasks"]}
        assert not tasks[target.id]["completed"]

        page.set_viewport_size({"width": 375, "height": 850})
        page.get_by_label("Question", exact=True).fill("Complete Lab report")
        page.get_by_role("button", name="Ask", exact=True).click()
        other = page.get_by_role("article", name=f"Proposed change: {dismissable['proposals'][0]['summary']}")
        other.get_by_role("button", name="Dismiss", exact=True).click()
        expect(other.get_by_text("Dismissed. Nothing was changed.")).to_be_visible()
        no_horizontal_overflow(page)
        page.screenshot(path=str(evidence / "assistant-actions-04-dismissed-narrow.png"), full_page=True)
        tasks = http_json("GET", app.url + "/api/planning")[1]["tasks"]
        assert not any(t["completed"] for t in tasks)
        assert errors == []
    finally:
        page.close()
        app.stop()
