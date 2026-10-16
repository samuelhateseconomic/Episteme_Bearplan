"""One joined M1 journey in real Chrome, using synthetic/disposable data only."""

from datetime import date, timedelta
import re

import pytest

from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

pytestmark = pytest.mark.e2e


def test_m1_create_plan_move_close_revisit_and_carry_same_work(browser, evidence, tmp_path) -> None:
    expect = playwright_sync.expect
    data_dir, port = tmp_path / "M1JoinedJourney", free_port()
    service = Service(data_dir, port).start()
    try:
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, locale="en-US")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url)
        page.get_by_label("New project").fill("M1 review seminar")
        page.get_by_role("button", name="Add project", exact=True).click()
        expect(page.get_by_role("heading", name="M1 review seminar", exact=True)).to_be_visible()
        page.get_by_label("Title", exact=True).fill("Prove the theorem")
        page.get_by_label("Deadline", exact=True).fill("2026-11-20")
        page.get_by_label("Notes", exact=True).fill("Parent context")
        page.get_by_role("button", name="Add task", exact=True).click()
        expect(page.get_by_label("Prove the theorem", exact=True)).to_be_visible()

        parent_row = page.locator(".tasks > .task").filter(has=page.get_by_label("Prove the theorem", exact=True))
        for title in ("Draft the argument", "Check the lemma"):
            parent_row.get_by_role("button", name="Add subtask", exact=True).click()
            form = parent_row.locator(".task-form")
            form.get_by_label("Title", exact=True).fill(title)
            form.get_by_label("Deadline", exact=True).fill("2026-11-18")
            form.get_by_label("Notes", exact=True).fill("Original child notes")
            form.get_by_label("Estimate (minutes)", exact=True).fill("45")
            form.get_by_role("button", name="Add subtask", exact=True).click()
            expect(page.get_by_label(title, exact=True)).to_be_visible()
        expect(page.get_by_label("Prove the theorem", exact=True)).to_be_disabled()
        expect(page.get_by_text("0 of 2 work items complete", exact=True)).to_be_visible()
        _, created = http_json("GET", service.url + "/api/planning")
        tasks = {task["title"]: task for task in created["tasks"]}
        parent, draft, lemma = (tasks[title] for title in ("Prove the theorem", "Draft the argument", "Check the lemma"))
        assert len(tasks) == 3 and draft["parent_id"] == lemma["parent_id"] == parent["id"]
        assert draft["project_id"] == lemma["project_id"] == parent["project_id"]
        monday = date.fromisoformat(created["week_start"])
        friday = monday + timedelta(days=4)
        destination = monday + timedelta(days=8)

        for offset, task in enumerate((draft, lemma)):
            row = page.locator(".subtasks > .task").filter(has=page.get_by_label(task["title"], exact=True))
            row.get_by_text("Plan task", exact=True).click()
            form = row.locator(".planning-form")
            form.get_by_label(f'Planned date for “{task["title"]}”').fill((monday + timedelta(days=offset)).isoformat())
            form.get_by_role("button", name="Add to day", exact=True).click()
            expect(page.locator(".week-board .planned-card")).to_have_count(offset + 1)
        _, assigned = http_json("GET", service.url + "/api/planning")
        assert assigned["tasks"] == created["tasks"]
        original_placement = next(item for item in assigned["placements"] if item["task_id"] == draft["id"])
        draft_card = page.locator(".week-board .planned-card").filter(has_text="Draft the argument")
        draft_card.get_by_text("Move or remove", exact=True).click()
        draft_card.locator(".planning-form").filter(has=page.get_by_role("button", name="Move placement", exact=True)).locator('input[type="date"]').fill(friday.isoformat())
        draft_card.get_by_role("button", name="Move placement", exact=True).click()
        expect(draft_card.get_by_text(f"Planned {friday:%b} {friday.day}, {friday.year}", exact=True)).to_be_visible()
        _, moved = http_json("GET", service.url + "/api/planning")
        moved_placement = next(item for item in moved["placements"] if item["task_id"] == draft["id"])
        assert moved_placement["id"] == original_placement["id"]
        assert moved_placement["planned_date"] == friday.isoformat()
        assert moved_placement["created_at"] == original_placement["created_at"]
        assert moved["tasks"] == created["tasks"]

        page.get_by_label("Check the lemma", exact=True).click()
        expect(page.get_by_label("Check the lemma", exact=True)).to_be_checked()
        expect(page.get_by_label("Prove the theorem", exact=True)).not_to_be_checked()
        expect(page.get_by_text("1 of 2 subtasks done", exact=True)).to_be_visible()
        expect(page.get_by_text("1 of 2 work items complete", exact=True)).to_be_visible()
        _, before_close = http_json("GET", service.url + "/api/planning")
        page.screenshot(path=evidence / "m1-joined-01-planned.png", full_page=True)
        page.get_by_role("button", name="End Week", exact=True).focus()
        page.keyboard.press("Enter")
        expect(page.get_by_role("region", name="End week preview")).to_contain_text("1 of 2 work items complete (50%)")
        page.get_by_role("button", name="Close week", exact=True).click()
        expect(page.get_by_text("Closed week · read-only history", exact=True)).to_be_visible()
        _, closed = http_json("GET", service.url + "/api/planning")
        frozen = closed["closed_week"]
        assert closed["tasks"] == before_close["tasks"] and closed["placements"] == []
        assert frozen["completed"] == 1 and frozen["total"] == 2
        assert {item["id"] for item in frozen["placements"]} == {item["id"] for item in before_close["placements"]}
        assert next(item for item in frozen["placements"] if item["task_id"] == draft["id"]) == moved_placement

        # A current edit must not rewrite the saved closed view or its deadline.
        row = page.locator(".subtasks > .task").filter(has=page.get_by_label("Draft the argument", exact=True))
        row.get_by_role("button", name="Edit", exact=True).click()
        row.get_by_label("Title", exact=True).fill("Revise the argument")
        row.get_by_label("Notes", exact=True).fill("Current child notes")
        row.get_by_role("button", name="Save changes", exact=True).click()
        expect(page.get_by_label("Revise the argument", exact=True)).to_be_visible()
        assert service.stop() == 0
        service = Service(data_dir, port).start()
        page.reload()
        page.get_by_role("button", name="M1 review seminar", exact=True).click()
        page.get_by_label("Closed-week history").select_option(monday.isoformat())
        board = page.locator(".week-board")
        expect(board.get_by_text("Draft the argument", exact=True)).to_be_visible()
        expect(board.get_by_text("Original child notes", exact=True)).to_have_count(2)
        expect(board.get_by_text("Due Nov 18, 2026", exact=True)).to_have_count(2)
        expect(board.get_by_role("checkbox")).to_have_count(0)
        _, revisited = http_json("GET", service.url + "/api/planning")
        assert revisited["closed_week"] == frozen
        current_draft = next(task for task in revisited["tasks"] if task["id"] == draft["id"])
        assert current_draft["deadline"] == draft["deadline"]
        page.screenshot(path=evidence / "m1-joined-02-revisited.png", full_page=True)

        page.get_by_role("button", name="Carry unfinished work", exact=True).click()
        choices = page.get_by_role("region", name="Carryover choices")
        choice = choices.get_by_role("checkbox", name="Revise the argument", exact=True)
        expect(choice).to_be_enabled()
        choice.check()
        choices.get_by_label('Carry “Revise the argument” to').fill(destination.isoformat())
        choices.get_by_role("button", name="Review carryover", exact=True).click()
        expect(page.get_by_role("region", name="Carryover preview")).to_contain_text("Due Nov 18, 2026")
        page.get_by_role("button", name="Apply carryover", exact=True).click()
        expect(page.locator(".week-actions").get_by_role("status")).to_contain_text("Carried over 1 work item")
        _, carried = http_json("GET", service.url + "/api/planning")
        assert carried["tasks"] == revisited["tasks"]
        assert carried["closed_week"] == frozen and len(carried["placements"]) == 1
        new_placement = carried["placements"][0]
        assert new_placement["task_id"] == draft["id"] and new_placement["id"] != original_placement["id"]
        assert new_placement["planned_date"] == destination.isoformat()
        page.get_by_role("button", name="Next week", exact=True).click()
        expect(board.get_by_text("Revise the argument", exact=True)).to_be_visible()
        page.set_viewport_size({"width": 375, "height": 850})
        page.get_by_role("group", name="Selected day").get_by_role("button", name=re.compile("Tue")).click()
        expect(board.locator(".planned-card:visible")).to_have_count(1)
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "m1-joined-03-carried-narrow.png", full_page=True)

        # Current completion follows the original children, with frozen history untouched.
        page.get_by_label("Revise the argument", exact=True).click()
        expect(page.get_by_label("Prove the theorem", exact=True)).to_be_checked()
        expect(page.get_by_text("2 of 2 work items complete", exact=True)).to_be_visible()
        page.get_by_label("Revise the argument", exact=True).click()
        expect(page.get_by_label("Prove the theorem", exact=True)).not_to_be_checked()
        _, final = http_json("GET", service.url + f"/api/planning?week={monday.isoformat()}")
        assert final["closed_week"] == frozen and len(final["tasks"]) == 3
        assert next(task for task in final["tasks"] if task["id"] == draft["id"])["deadline"] == draft["deadline"]
        assert errors == []
    finally:
        service.kill()
