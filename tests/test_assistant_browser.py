"""Assistant rendering/retry/cancel in real Chrome; deterministic provider replies."""
import json

import pytest

from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

pytestmark = pytest.mark.e2e


def test_assistant_sources_keyboard_narrow_failure_and_cancel(browser, evidence, tmp_path):
    expect = playwright_sync.expect
    service = Service(tmp_path / "AssistantBrowser", free_port()).start()
    status = {"available": True, "read_only": True, "prompt_version": "readonly-v1",
              "models": [{"name": "fixture:local", "digest": "fixture", "details": {}}]}
    source = {"tool": "get_day_plan", "arguments": {}, "data": {"today": "2026-11-01", "timezone": "America/Los_Angeles",
        "start_date": "2026-11-01", "end_date": "2026-11-01", "unique_leaf_total": 1, "completed_leaf_total": 0,
        "items": [{"task_id": "fixture-task", "title": "Draft proof", "project_name": "Seminar", "deadline": "2026-11-20", "completed": False}]}}
    reply = {"answer": "Draft proof is planned today.", "model": "fixture:local", "elapsed_seconds": 0.1, "rounds": 2,
             "read_only": True, "sources": [source]}
    try:
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.route("**/api/assistant/status", lambda route: route.fulfill(json=status))
        page.route("**/api/assistant/chat", lambda route: route.fulfill(json=reply))
        page.goto(service.url + "/#assistant")
        expect(page.get_by_role("heading", name="Local assistant")).to_be_visible()
        page.get_by_label("Local model").select_option("fixture:local")
        page.get_by_label("Question", exact=True).fill("What is planned today?")
        page.get_by_role("button", name="Ask", exact=True).focus()
        page.keyboard.press("Enter")
        expect(page.get_by_text("Draft proof is planned today.", exact=True)).to_be_visible()
        expect(page.get_by_text("Incomplete · Due 2026-11-20", exact=True)).to_be_visible()
        no_horizontal_overflow(page)
        page.screenshot(path=str(evidence / "assistant-01-wide.png"), full_page=True)
        page.set_viewport_size({"width": 375, "height": 850})
        no_horizontal_overflow(page)
        expect(page.get_by_role("link", name="Track", exact=True)).to_be_visible()
        page.screenshot(path=str(evidence / "assistant-02-narrow.png"), full_page=True)
        page.unroute("**/api/assistant/chat")
        page.route("**/api/assistant/chat", lambda route: route.fulfill(status=503, json={"error": {"message": "Ollama is unavailable. Refresh models."}}))
        page.get_by_role("button", name="Ask", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("Ollama is unavailable")
        expect(page.get_by_label("Question", exact=True)).to_have_value("What is planned today?")
        page.screenshot(path=str(evidence / "assistant-03-error.png"), full_page=True)
        page.unroute("**/api/assistant/chat")
        pending = []
        page.route("**/api/assistant/chat", lambda route: pending.append(route))
        page.get_by_role("button", name="Ask", exact=True).click()
        expect(page.get_by_role("button", name="Cancel question")).to_be_visible()
        page.get_by_role("button", name="Cancel question").click()
        expect(page.get_by_role("button", name="Ask", exact=True)).to_be_enabled()
        for route in pending:
            try: route.abort()
            except playwright_sync.Error: pass
        page.get_by_role("link", name="Plan", exact=True).click()
        expect(page.get_by_role("heading", name="Projects", exact=True)).to_be_visible()
        _, plan = http_json("GET", service.url + "/api/planning")
        assert plan["tasks"] == []  # Provider display fixtures did not create tasks.
        page.close()
    finally:
        service.stop()
