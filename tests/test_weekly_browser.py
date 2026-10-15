"""Weekly planning journey in installed Chrome with disposable service/data."""

from datetime import date, timedelta
import re

from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

import pytest

pytestmark = pytest.mark.e2e


def display(day: date) -> str:
    return f"{day:%b} {day.day}, {day.year}"


def test_weekly_assignment_movement_completion_and_recovery(browser, evidence, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    expect = playwright_sync.expect
    data_dir = tmp_path / "WeeklyJourney"
    port = free_port()
    service = Service(data_dir, port).start()
    try:
        _, parent = http_json("POST", service.url + "/api/tasks", {"title": "Homework", "notes": "Keep parent notes"})
        _, child = http_json("POST", service.url + "/api/tasks", {
            "title": "Draft proof", "parent_id": parent["id"], "deadline": "2026-11-20", "notes": "Keep proof notes", "estimate_minutes": 45,
        })
        _, other = http_json("POST", service.url + "/api/tasks", {"title": "Review proof", "parent_id": parent["id"]})
        _, backlog = http_json("POST", service.url + "/api/tasks", {"title": "Unscheduled reading"})
        _, initial = http_json("GET", service.url + "/api/planning")
        monday = date.fromisoformat(initial["week_start"])
        tuesday = monday + timedelta(days=1)
        friday = monday + timedelta(days=4)
        next_monday = monday + timedelta(days=7)
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, locale="en-US")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url)
        expect(page.get_by_role("heading", name="Weekly plan")).to_be_visible()
        expect(page.get_by_text("America/Los_Angeles", exact=False)).to_be_visible()
        expect(page.get_by_label("Homework", exact=True)).to_be_disabled()
        parent_row = page.locator(".tasks > .task").filter(has=page.get_by_label("Homework", exact=True))
        expect(parent_row.get_by_text("Plan the subtasks below.", exact=True)).to_be_visible()
        child_row = page.locator(".subtasks > .task").filter(has=page.get_by_label("Draft proof", exact=True))
        child_row.get_by_text("Plan task", exact=True).click()
        assign = child_row.locator(".planning-form").first
        assign.get_by_label('Planned date for “Draft proof”').fill(monday.isoformat())
        assign.get_by_role("button", name="Add to day", exact=True).click()
        expect(page.locator(".week-board .planned-card")).to_have_count(1)
        expect(child_row.get_by_text("Move or remove plan", exact=True)).to_be_visible()
        expect(child_row.get_by_role("button", name="Add to day", exact=True)).to_have_count(0)
        other_row = page.locator(".subtasks > .task").filter(has=page.get_by_label("Review proof", exact=True))
        other_row.get_by_text("Plan task", exact=True).click()
        other_assign = other_row.locator(".planning-form").first
        other_assign.get_by_label('Planned date for “Review proof”').fill(tuesday.isoformat())
        other_assign.get_by_role("button", name="Add to day", exact=True).click()
        expect(page.locator(".week-board .planned-card")).to_have_count(2)
        # The referenced task is not copied; deadline and planned dates are distinct.
        _, state = http_json("GET", service.url + "/api/planning")
        assert len(state["tasks"]) == len(initial["tasks"]) == 4
        assert next(task for task in state["tasks"] if task["id"] == child["id"]) == child
        expect(page.get_by_text("Due Nov 20, 2026").first).to_be_visible()
        expect(page.locator(".week-board").get_by_text("Inbox / Homework")).to_have_count(2)
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "single-day-01-wide.png", full_page=True)

        # A stale second tab cannot assign a second day, including in another week.
        backlog_row = page.locator(".tasks > .task").filter(has=page.get_by_label("Unscheduled reading", exact=True))
        backlog_row.get_by_text("Plan task", exact=True).click()
        backlog_assign = backlog_row.locator(".planning-form").first
        backlog_assign.get_by_label('Planned date for “Unscheduled reading”').fill(next_monday.isoformat())
        _, existing = http_json("POST", service.url + "/api/placements", {"task_id": backlog["id"], "planned_date": friday.isoformat()})
        _, before_conflict = http_json("GET", service.url + "/api/planning")
        backlog_assign.get_by_role("button", name="Add to day", exact=True).click()
        expect(backlog_assign.get_by_role("alert")).to_contain_text(f"already planned for {friday.isoformat()}")
        expect(backlog_assign.get_by_role("alert")).to_contain_text("Use Move placement")
        expect(backlog_assign.get_by_label('Planned date for “Unscheduled reading”')).to_have_value(next_monday.isoformat())
        _, after_conflict = http_json("GET", service.url + "/api/planning")
        assert after_conflict == before_conflict
        page.screenshot(path=evidence / "single-day-02-conflict.png", full_page=True)
        http_json("DELETE", service.url + f"/api/placements/{existing['id']}")
        page.reload()

        # Each day is separate child work; the parent waits for both children.
        boxes = page.locator(".week-board").get_by_role("checkbox")
        boxes.first.click()
        expect(boxes.first).to_be_checked()
        expect(boxes.last).not_to_be_checked()
        expect(page.get_by_label("Homework", exact=True)).not_to_be_checked()
        expect(page.get_by_label("Draft proof", exact=True)).to_be_checked()
        expect(page.get_by_text("1 of 2 subtasks done", exact=True)).to_be_visible()
        boxes.last.click()
        expect(page.get_by_label("Homework", exact=True)).to_be_checked()
        expect(page.get_by_text("2 of 2 subtasks done", exact=True)).to_be_visible()

        # Move only one child's placement across weeks; the other stays unchanged.
        monday_card = page.locator(".week-board .planned-card").filter(has=page.get_by_role("checkbox", name=f"Draft proof, planned {display(monday)}", exact=True))
        monday_card.get_by_text("Move or remove", exact=True).click()
        monday_card.get_by_label(f'Move “Draft proof” from {display(monday)} to').fill(next_monday.isoformat())
        monday_card.get_by_role("button", name="Move placement", exact=True).click()
        expect(page.locator(".week-board .planned-card")).to_have_count(1)
        page.get_by_role("button", name="Next week", exact=True).click()
        moved_card = page.locator(".week-board .planned-card")
        expect(moved_card).to_have_count(1)
        expect(moved_card.get_by_role("checkbox")).to_be_checked()
        moved_card.get_by_text("Move or remove", exact=True).click()
        move_input = moved_card.get_by_label(f'Move “Draft proof” from {display(next_monday)} to')
        move_input.fill(tuesday.isoformat())
        moved_card.get_by_role("button", name="Move placement", exact=True).click()
        expect(page.locator(".week-board .planned-card")).to_have_count(0)
        # Different tasks may share a date; moving never clones or completes work.
        _, after_move = http_json("GET", service.url + "/api/planning")
        assert len(after_move["placements"]) == 2
        assert all(p["planned_date"] == tuesday.isoformat() for p in after_move["placements"])
        assert len({p["task_id"] for p in after_move["placements"]}) == 2
        page.get_by_role("button", name="Previous week", exact=True).click()
        moved_card = page.locator(".week-board .planned-card").filter(has=page.get_by_role("checkbox", name=f"Draft proof, planned {display(tuesday)}", exact=True))
        expect(moved_card.get_by_role("checkbox")).to_be_checked()
        moved_card.get_by_text("Move or remove", exact=True).click()
        moved_card.get_by_role("button", name="Remove from plan", exact=True).click()
        expect(page.locator(".week-board .planned-card")).to_have_count(1)
        _, after_remove = http_json("GET", service.url + "/api/planning")
        assert len(after_remove["placements"]) == 1
        assert after_remove["placements"][0]["planned_date"] == tuesday.isoformat()
        assert len(after_remove["tasks"]) == 4

        # Persist across an actual process restart, then inspect selected-day laptop layout.
        assert service.stop() == 0
        service = Service(data_dir, port).start()
        _, after_restart = http_json("GET", service.url + "/api/planning")
        assert after_restart == after_remove
        page.set_viewport_size({"width": 1024, "height": 900})
        page.reload()
        day_selector = page.get_by_role("group", name="Selected day")
        day_selector.get_by_role("button", name=re.compile("Tue")).click()
        expect(page.locator(".week-board .planned-card:visible")).to_have_count(1)
        expect(page.locator(".week-board .day-column:visible")).to_have_count(1)
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "single-day-03-laptop.png", full_page=True)
        page.get_by_role("button", name="Previous week", exact=True).click()
        page.get_by_role("button", name="Today", exact=True).click()
        expect(page.locator(".planner-heading")).to_contain_text(display(monday))
        expect(page.get_by_role("group", name="Selected day").get_by_role("button", pressed=True)).to_contain_text("Today")

        # A stopped service must retain the intended date; retry succeeds after restart.
        child_row = page.locator(".subtasks > .task").filter(has=page.get_by_label("Draft proof", exact=True))
        child_row.get_by_text("Plan task", exact=True).click()
        assign = child_row.locator(".planning-form").first
        assign.get_by_label('Planned date for “Draft proof”').fill(friday.isoformat())
        service.kill()
        assign.get_by_role("button", name="Add to day", exact=True).click()
        expect(assign.get_by_role("alert")).to_contain_text("Cannot reach the BearPlans service")
        expect(assign.get_by_label('Planned date for “Draft proof”')).to_have_value(friday.isoformat())
        page.screenshot(path=evidence / "single-day-04-save-error.png", full_page=True)
        service = Service(data_dir, port).start()
        assign.get_by_role("button", name="Add to day", exact=True).click()
        expect(child_row.locator(".placement-list > li")).to_have_count(1)
        expect(child_row.get_by_role("button", name="Add to day", exact=True)).to_have_count(0)
        _, result = http_json("GET", service.url + "/api/planning")
        assert len(result["placements"]) == 2
        assert len(result["tasks"]) == 4
        final_child = next(task for task in result["tasks"] if task["id"] == child["id"])
        assert final_child["deadline"] == child["deadline"]
        assert final_child["notes"] == child["notes"]
        assert final_child["project_id"] == child["project_id"]
        assert final_child["completed"] is True
        expect(page.get_by_label("Unscheduled reading", exact=True)).to_be_visible()
        page.set_viewport_size({"width": 375, "height": 850})
        page.reload()
        page.get_by_role("group", name="Selected day").get_by_role("button", name=re.compile("Tue")).click()
        assert no_horizontal_overflow(page)
        expect(page.locator(".week-board .planned-card:visible")).to_have_count(1)
        page.screenshot(path=evidence / "single-day-05-narrow.png", full_page=True)
        page.set_viewport_size({"width": 1600, "height": 1000})
        page.emulate_media(color_scheme="dark")
        page.reload()
        expect(page.locator(".week-board .planned-card:visible")).to_have_count(2)
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "single-day-06-dark-wide.png", full_page=True)
        assert errors == []
    finally:
        service.kill()
