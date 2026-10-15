"""Closed history and reviewed carryover against real Chrome/disposable storage."""

from datetime import date, timedelta
import re

import pytest

from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

pytestmark = pytest.mark.e2e


def test_closed_week_and_reviewed_carryover_survive_changes_restart_and_lost_response(browser, evidence, tmp_path) -> None:
    expect = playwright_sync.expect
    data_dir, port = tmp_path / "HistoryJourney", free_port()
    service = Service(data_dir, port).start()
    try:
        _, project = http_json("POST", service.url + "/api/projects", {"name": "Proof seminar"})
        _, parent = http_json("POST", service.url + "/api/tasks", {"title": "Assignment", "project_id": project["id"]})
        _, draft = http_json("POST", service.url + "/api/tasks", {
            "title": "Draft proof", "parent_id": parent["id"], "notes": "Frozen proof notes", "deadline": "2026-11-20", "estimate_minutes": 45,
        })
        _, review = http_json("POST", service.url + "/api/tasks", {"title": "Review proof", "parent_id": parent["id"]})
        http_json("PUT", service.url + f"/api/tasks/{review['id']}/completion", {"complete": True})
        _, later = http_json("POST", service.url + "/api/tasks", {"title": "Reading", "project_id": project["id"]})
        _, backlog = http_json("POST", service.url + "/api/tasks", {"title": "Unscheduled exercise", "project_id": project["id"]})
        _, initial = http_json("GET", service.url + "/api/planning")
        monday = date.fromisoformat(initial["week_start"])
        following = monday + timedelta(days=7)
        destination = following + timedelta(days=3)
        for offset, task in enumerate((draft, review, later)):
            http_json("POST", service.url + "/api/placements", {"task_id": task["id"], "planned_date": (monday + timedelta(days=offset)).isoformat()})
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, locale="en-US")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url)
        expect(page.get_by_text("Open week", exact=True)).to_be_visible()
        page.get_by_role("button", name="End Week", exact=True).focus()
        page.keyboard.press("Enter")
        preview = page.get_by_role("region", name="End week preview")
        expect(preview).to_contain_text("1 of 3 work items complete (33%)")
        expect(preview).to_contain_text("Frozen proof notes")
        page.screenshot(path=evidence / "history-01-close-preview.png", full_page=True)
        preview.get_by_role("button", name="Cancel", exact=True).focus()
        page.keyboard.press("Enter")
        _, still_open = http_json("GET", service.url + "/api/planning")
        assert still_open["closed_week"] is None and len(still_open["placements"]) == 3
        page.get_by_role("button", name="End Week", exact=True).click()
        page.get_by_role("button", name="Close week", exact=True).focus()
        page.keyboard.press("Enter")
        expect(page.get_by_text("Closed week · read-only history", exact=True)).to_be_visible()
        expect(page.locator(".week-board .historical-card")).to_have_count(3)
        expect(page.locator(".week-board").get_by_role("checkbox")).to_have_count(0)
        expect(page.locator(".week-board").get_by_text("Move or remove", exact=True)).to_have_count(0)
        _, after_close = http_json("GET", service.url + "/api/planning")
        frozen = after_close["closed_week"]
        assert after_close["placements"] == []

        # All later edits affect current tasks only, including current completion.
        http_json("PATCH", service.url + f"/api/tasks/{draft['id']}", {"title": "Revise proof", "notes": "Current notes", "deadline": "2026-12-31"})
        http_json("PATCH", service.url + f"/api/tasks/{parent['id']}", {"title": "Current assignment"})
        http_json("PATCH", service.url + f"/api/projects/{project['id']}", {"name": "Current seminar"})
        http_json("PUT", service.url + f"/api/tasks/{later['id']}/completion", {"complete": True})
        http_json("PUT", service.url + f"/api/tasks/{review['id']}/completion", {"complete": False})
        assert service.stop() == 0
        service = Service(data_dir, port).start()
        page.reload()
        board = page.locator(".week-board")
        expect(board.get_by_text("Draft proof", exact=True)).to_be_visible()
        expect(board.get_by_text("Proof seminar / Assignment", exact=True)).to_have_count(2)
        expect(board.get_by_text("Frozen proof notes", exact=True)).to_be_visible()
        expect(board.get_by_text("Due Nov 20, 2026", exact=True)).to_be_visible()
        review_card = board.locator(".historical-card").filter(has=page.get_by_text("Review proof", exact=True))
        expect(review_card).to_contain_text("At closure: Complete")
        expect(review_card).to_contain_text("Current task: Unfinished")
        _, restarted = http_json("GET", service.url + "/api/planning")
        assert restarted["closed_week"] == frozen
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "history-02-frozen-wide.png", full_page=True)

        page.get_by_role("button", name="Carry unfinished work", exact=True).click()
        choices = page.get_by_role("region", name="Carryover choices")
        expect(choices.get_by_role("checkbox", name="Reading", exact=True)).to_be_disabled()
        expect(choices).to_contain_text("Currently complete")
        expect(choices.get_by_role("checkbox", name="Review proof", exact=True)).to_have_count(0)

        def select_and_review():
            choice = choices.get_by_role("checkbox", name="Revise proof", exact=True)
            expect(choice).to_be_enabled()
            choice.check()
            choices.get_by_label('Carry “Revise proof” to').fill(destination.isoformat())
            choices.get_by_role("button", name="Review carryover", exact=True).click()
            expect(page.get_by_role("region", name="Carryover preview")).to_contain_text("Due Dec 31, 2026")

        select_and_review()
        http_json("PUT", service.url + f"/api/tasks/{draft['id']}/completion", {"complete": True})
        page.get_by_role("button", name="Apply carryover", exact=True).click()
        expect(page.locator(".week-actions").get_by_role("alert")).to_contain_text("Currently complete")
        _, rejected = http_json("GET", service.url + "/api/planning")
        assert rejected["placements"] == [] and rejected["closed_week"] == frozen
        http_json("PUT", service.url + f"/api/tasks/{draft['id']}/completion", {"complete": False})
        page.get_by_role("button", name="Refresh carryover choices", exact=True).click()
        select_and_review()
        page.screenshot(path=evidence / "history-03-carryover-preview.png", full_page=True)

        # Save on the service but lose its response. Retrying must use the same ID.
        attempts = []

        def lose_first_response(route):
            if route.request.method != "POST":
                route.continue_()
                return
            attempts.append(route.request.post_data_json)
            if len(attempts) == 1:
                response = route.fetch()
                assert response.status == 200
                route.abort()
            else:
                route.continue_()

        page.route("**/api/weeks/*/carryover", lose_first_response)
        page.get_by_role("button", name="Apply carryover", exact=True).click()
        expect(page.locator(".week-actions").get_by_role("alert")).to_contain_text("Cannot reach")
        expect(choices.get_by_label('Carry “Revise proof” to')).to_have_value(destination.isoformat())
        _, committed = http_json("GET", service.url + "/api/planning")
        assert len(committed["placements"]) == 1
        page.get_by_role("button", name="Apply carryover", exact=True).click()
        expect(page.locator(".week-actions").get_by_role("status")).to_contain_text("Carried over 1 work item")
        assert len(attempts) == 2 and attempts[0] == attempts[1]
        _, result = http_json("GET", service.url + "/api/planning")
        assert result["placements"] == committed["placements"]
        assert result["placements"][0]["task_id"] == draft["id"]
        assert len(result["tasks"]) == 5 and result["closed_week"] == frozen
        page.get_by_role("button", name="Next week", exact=True).click()
        expect(page.get_by_text("Open week", exact=True)).to_be_visible()
        expect(board.get_by_text("Revise proof", exact=True)).to_be_visible()
        expect(board.get_by_text("Due Dec 31, 2026", exact=True)).to_be_visible()
        page.set_viewport_size({"width": 1024, "height": 900})
        page.get_by_role("group", name="Selected day").get_by_role("button", name=re.compile("Thu")).click()
        expect(board.locator(".planned-card:visible")).to_have_count(1)
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "history-04-destination-laptop.png", full_page=True)
        page.get_by_label("Closed-week history").select_option(monday.isoformat())
        page.get_by_role("group", name="Selected day").get_by_role("button", name=re.compile("Mon")).click()
        page.set_viewport_size({"width": 375, "height": 850})
        expect(board.locator(".historical-card:visible")).to_have_count(1)
        expect(page.get_by_text("Closed week · read-only history", exact=True)).to_be_visible()
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "history-05-closed-narrow.png", full_page=True)
        assert errors == []
    finally:
        service.kill()
