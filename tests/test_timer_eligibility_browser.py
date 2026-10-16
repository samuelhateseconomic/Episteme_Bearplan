"""Incomplete-leaf selection and existing-session preservation in real Chrome."""

from uuid import uuid4

import pytest

from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

pytestmark = pytest.mark.e2e


def test_weekly_entry_completed_choices_stale_start_and_active_completion(browser, evidence, tmp_path):
    expect = playwright_sync.expect
    service = Service(tmp_path / "EligibilityJourney", free_port()).start()
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, locale="en-US")
    try:
        _, parent = http_json("POST", service.url + "/api/tasks", {"title": "Seminar paper"})
        _, planned = http_json("POST", service.url + "/api/tasks", {"title": "Read the source", "parent_id": parent["id"]})
        _, unplanned = http_json("POST", service.url + "/api/tasks", {"title": "Unscheduled exercises"})
        _, done = http_json("POST", service.url + "/api/tasks", {"title": "Finished proof"})
        _, plan = http_json("GET", service.url + "/api/planning")
        for work in (planned, done):
            status, _ = http_json("POST", service.url + "/api/placements", {"task_id": work["id"], "planned_date": plan["today"]})
            assert status == 201
        http_json("PUT", service.url + f"/api/tasks/{done['id']}/completion", {"complete": True})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url + "/#track")
        selector = page.get_by_label("Task to track", exact=True)
        expect(selector).to_be_enabled()
        expect(selector.locator("option")).to_have_count(3)
        assert set(selector.locator("option").evaluate_all("items => items.map(item => item.value)")) == {"", planned["id"], unplanned["id"]}
        page.screenshot(path=evidence / "eligibility-01-choices-wide.png", full_page=True)

        page.get_by_role("link", name="Plan", exact=True).click()
        completed_row = page.locator(".tasks > .task").filter(has=page.get_by_label(done["title"], exact=True))
        expect(completed_row.get_by_role("button", name="Start tracking", exact=True)).to_be_disabled()
        expect(completed_row).not_to_contain_text("Reopen this task")
        card = page.locator(".week-board .planned-card").filter(has_text=planned["title"])
        completed_card = page.locator(".week-board .planned-card").filter(has_text=done["title"])
        expect(completed_card.get_by_role("button", name="Start tracking", exact=True)).to_be_disabled()
        expect(completed_card).not_to_contain_text("Reopen this task")
        start = card.get_by_role("button", name="Start tracking", exact=True)
        start.focus()
        expect(start).to_be_focused()
        page.screenshot(path=evidence / "eligibility-02-board-wide.png", full_page=True)
        page.keyboard.press("Enter")
        expect(selector).to_have_value(planned["id"])
        page.get_by_label("Duration (minutes)").fill("1")
        page.get_by_role("button", name="Start countdown", exact=True).focus()
        page.keyboard.press("Enter")
        current = page.get_by_role("region", name="Current session")
        expect(current).to_contain_text(planned["title"])
        _, started = http_json("GET", service.url + "/api/timer")
        session_id = started["active_session"]["id"]

        # Completing the tracked child completes its parent, while the timer
        # remains linked to that same child and its controls remain available.
        page.get_by_role("link", name="Plan", exact=True).click()
        card.get_by_role("checkbox").click()
        expect(card.get_by_role("checkbox")).to_be_checked()
        expect(page.get_by_label(parent["title"], exact=True)).to_be_checked()
        expect(card.get_by_role("button", name="Start tracking", exact=True)).to_be_disabled()
        compact = page.get_by_role("complementary", name="Active countdown")
        expect(compact).to_contain_text(planned["title"])
        compact.get_by_role("button", name="Open Track", exact=True).click()
        expect(current.get_by_role("heading", name=planned["title"], exact=True)).to_be_visible()
        expect(current.get_by_role("button", name="Pause", exact=True)).to_be_enabled()
        _, completed_running = http_json("GET", service.url + "/api/timer")
        assert completed_running["active_session"]["id"] == session_id
        assert completed_running["active_session"]["task_id"] == planned["id"]
        assert completed_running["active_session"]["state"] == "running"
        current.get_by_role("button", name="Pause", exact=True).click()
        expect(current.get_by_role("button", name="Resume", exact=True)).to_be_enabled()
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "eligibility-03-completed-active-narrow.png", full_page=True)
        current.get_by_role("button", name="Resume", exact=True).focus()
        page.keyboard.press("Enter")
        expect(current.get_by_role("button", name="Pause", exact=True)).to_be_enabled()
        current.get_by_role("button", name="Finish early", exact=True).click()
        expect(page.get_by_role("region", name="Saved session outcome")).to_contain_text(planned["title"])
        expect(selector.locator(f'option[value="{planned["id"]}"]')).to_have_count(0)
        _, saved = http_json("GET", service.url + "/api/timer")
        result = saved["last_session"]
        assert result["id"] == session_id and result["task_id"] == planned["id"]

        # The tab has an eligible choice loaded, then another tab completes it.
        # Backend rejects the stale choice, UI refreshes it, and duration is kept.
        selector.select_option(unplanned["id"])
        page.get_by_label("Duration (minutes)").fill("17")
        other = context.new_page()
        response = other.request.put(service.url + f"/api/tasks/{unplanned['id']}/completion", data={"complete": True})
        assert response.ok
        page.get_by_role("button", name="Start countdown", exact=True).click()
        expect(page.get_by_role("alert").filter(has_text="This task is complete")).to_be_visible()
        expect(selector.locator("option")).to_have_count(1)
        expect(page.get_by_label("Duration (minutes)")).to_have_value("17")
        expect(page.get_by_role("button", name="Start countdown", exact=True)).to_be_disabled()
        expect(page.get_by_text("No incomplete tasks to track", exact=False)).to_be_visible()
        state = http_json("GET", service.url + "/api/timer")[1]
        assert state["active_session"] is None and state["last_session"] == result
        direct = other.request.post(service.url + "/api/timer/start", data={
            "task_id": unplanned["id"], "duration_minutes": 17, "operation_id": str(uuid4()),
        })
        assert direct.status == 422 and direct.json()["error"]["field"] == "task_id"
        page.screenshot(path=evidence / "eligibility-04-stale-empty-narrow.png", full_page=True)

        # Reload proves the empty state derives from stored completion, with no
        # untasked fallback. The completed board remains readable on a narrow view.
        page.reload()
        expect(page.get_by_text("No incomplete tasks to track", exact=False)).to_be_visible()
        expect(selector.locator("option")).to_have_count(1)
        page.get_by_role("link", name="Plan", exact=True).click()
        expect(card.get_by_role("button", name="Start tracking", exact=True)).to_be_disabled()
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "eligibility-05-board-narrow.png", full_page=True)
        for work in (planned, unplanned, done):
            all_tasks = http_json("GET", service.url + "/api/tasks")[1]["tasks"]
            assert next(task for task in all_tasks if task["id"] == work["id"])["completed"]
        assert errors == []
    finally:
        context.close()
        service.kill()
