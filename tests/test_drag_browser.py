"""Native Chrome dragging, keyboard alternatives and durable placement identity.

All data is synthetic and lives in disposable test directories. Drag gestures use
real mouse/keyboard input; no dispatched DOM drag events substitute for Chrome.
"""

from datetime import date, timedelta
import json
import re
import sqlite3
from uuid import uuid4

import pytest

from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

pytestmark = pytest.mark.e2e
expect = playwright_sync.expect


def shown(day: date) -> str:
    return f"{day:%b} {day.day}, {day.year}"


def plan(service):
    status, result = http_json("GET", service.url + "/api/planning")
    assert status == 200
    return result


def day_column(page, day):
    return page.get_by_role("region", name=f"{day:%A}, {shown(day)}", exact=True)


def handle(page, title, day):
    return page.get_by_role("img", name=f"Drag “{title}” from {shown(day)}", exact=True)


def begin_drag(page, source, *, add=False):
    source.scroll_into_view_if_needed()
    box = source.bounding_box()
    assert box
    if add:
        page.keyboard.down("Alt")
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + 18, box["y"] + box["height"] / 2 + 3, steps=6)
    indicator = page.locator(".drag-indicator")
    expect(indicator).to_be_visible()
    expect(indicator).to_contain_text("Add" if add else "Move")
    return indicator


def hover_destination(page, target):
    # Measure the live destination after native dragstart/paint.
    target.scroll_into_view_if_needed()
    box = target.bounding_box()
    assert box
    x, y = box["x"] + box["width"] / 2, box["y"] + min(box["height"] / 2, 45)
    page.mouse.move(x, y, steps=12)
    page.mouse.move(x + 1, y, steps=2)
    if "drop-source" not in (target.get_attribute("class") or ""):
        expect(target).to_have_class(re.compile(r"\bdrop-over\b"))


def finish_drop(page, *, add=False):
    page.mouse.up()
    if add:
        page.keyboard.up("Alt")
    expect(page.locator(".drag-indicator")).to_have_count(0)


def drag_to(page, source, target, *, add=False):
    begin_drag(page, source, add=add)
    hover_destination(page, target)
    finish_drop(page, add=add)


def saved_rows(service):
    """Read live SQLite through its normal WAL-aware connection, never file-copy."""
    with sqlite3.connect(f"file:{service.data_dir / 'bearplans.sqlite3'}?mode=ro", uri=True) as conn:
        return {
            table: conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            for table in ("tasks", "planned_items", "closed_weeks", "closed_placements", "timer_sessions", "timer_intervals", "timer_operations")
        }


def test_native_move_add_cancel_controls_keyboard_and_narrow_days(browser, evidence, tmp_path):
    service = Service(tmp_path / "NativeDragJourney", free_port()).start()
    context = browser.new_context(viewport={"width": 1600, "height": 1100}, locale="en-US")
    try:
        _, task = http_json("POST", service.url + "/api/tasks", {
            "title": "Read the primary source", "deadline": "2026-11-20", "notes": "Keep all task fields", "estimate_minutes": 35,
        })
        initial = plan(service)
        monday = date.fromisoformat(initial["week_start"])
        tuesday, wednesday, thursday, friday = [monday + timedelta(days=n) for n in range(1, 5)]
        _, placement = http_json("POST", service.url + "/api/placements", {"task_id": task["id"], "planned_date": monday.isoformat()})
        # Save a genuine timer result before scheduling changes; compare every field.
        _, timer = http_json("POST", service.url + "/api/timer/start", {"task_id": task["id"], "duration_minutes": 1, "operation_id": str(uuid4())})
        session = timer["active_session"]
        assert http_json("POST", service.url + f"/api/timer/{session['id']}/finish", {"operation_id": str(uuid4())})[0] == 200
        history_before = saved_rows(service)
        page = context.new_page()
        page.set_default_timeout(5000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url)
        expect(handle(page, task["title"], monday)).to_be_visible()
        expect(page.get_by_text("Option (Mac) / Alt (Windows)", exact=True)).to_be_visible()

        begin_drag(page, handle(page, task["title"], monday))
        expect(day_column(page, tuesday)).to_have_class(re.compile(r"\bdrop-valid\b"))
        hover_destination(page, day_column(page, tuesday))
        page.screenshot(path=evidence / "drag-01-move-wide.png", full_page=True, timeout=5000)
        finish_drop(page)
        expect(handle(page, task["title"], tuesday)).to_be_visible()
        moved = plan(service)["placements"]
        assert len(moved) == 1 and moved[0]["id"] == placement["id"]
        assert moved[0]["created_at"] == placement["created_at"]
        assert moved[0]["revision"] == placement["revision"] + 1
        assert moved[0]["planned_date"] == tuesday.isoformat()
        assert plan(service)["tasks"] == [task]

        begin_drag(page, handle(page, task["title"], tuesday), add=True)
        hover_destination(page, day_column(page, wednesday))
        expect(page.locator(".drag-indicator")).to_contain_text("Add")
        page.screenshot(path=evidence / "drag-02-add-wide.png", full_page=True, timeout=5000)
        finish_drop(page, add=True)
        expect(handle(page, task["title"], wednesday)).to_be_visible()
        both = plan(service)["placements"]
        assert len(both) == 2 and moved[0] in both
        assert {p["task_id"] for p in both} == {task["id"]}
        expect(page.get_by_text("Weekly completion: 0 of 1 work items complete (0%).", exact=True)).to_be_visible()

        # Same-day drop in either mode is an exact no-op, including timestamps.
        for add in (False, True):
            begin_drag(page, handle(page, task["title"], tuesday), add=add)
            hover_destination(page, day_column(page, tuesday))
            expect(page.locator(".drag-indicator")).to_contain_text("same day: no change")
            finish_drop(page, add=add)
            assert plan(service)["placements"] == both

        # Escape and an outside drop leave all saved rows untouched.
        begin_drag(page, handle(page, task["title"], tuesday))
        page.keyboard.press("Escape")
        page.mouse.up()
        expect(page.locator(".drag-indicator")).to_have_count(0)
        begin_drag(page, handle(page, task["title"], tuesday))
        page.mouse.move(12, 12, steps=15)
        page.mouse.up()
        expect(page.locator(".drag-indicator")).to_have_count(0)
        assert plan(service)["placements"] == both

        for add in (False, True):
            begin_drag(page, handle(page, task["title"], tuesday), add=add)
            expect(day_column(page, wednesday)).to_have_class(re.compile(r"\bdrop-conflict\b"))
            hover_destination(page, day_column(page, wednesday))
            expect(page.locator(".drag-indicator")).to_contain_text("already planned here")
            finish_drop(page, add=add)
            expect(page.get_by_role("alert")).to_contain_text("Both existing placements are kept")
            assert plan(service)["placements"] == both

        card = day_column(page, tuesday).locator(".planned-card")
        # Native attempts from controls never initiate board dragging.
        for control in (card.get_by_role("checkbox"), card.get_by_role("button", name="Start tracking"), card.get_by_text("Move or remove", exact=True)):
            control.scroll_into_view_if_needed()
            box = control.bounding_box()
            assert box
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down()
            page.mouse.move(box["x"] + box["width"] / 2 + 20, box["y"] + box["height"] / 2 + 10, steps=6)
            expect(page.locator(".drag-indicator")).to_have_count(0)
            page.mouse.move(12, 12, steps=10)
            page.mouse.up()
            assert plan(service)["placements"] == both

        card.get_by_role("checkbox").click()
        expect(day_column(page, wednesday).get_by_role("checkbox")).to_be_checked()
        expect(card.get_by_role("button", name="Start tracking")).to_be_disabled()
        card.get_by_role("checkbox").click()
        expect(card.get_by_role("button", name="Start tracking")).to_be_enabled()
        card.get_by_role("button", name="Start tracking").focus()
        page.keyboard.press("Enter")
        expect(page.get_by_label("Task to track", exact=True)).to_have_value(task["id"])
        assert http_json("GET", service.url + "/api/timer")[1]["active_session"] is None
        page.get_by_role("link", name="Plan", exact=True).click()

        # Fully keyboard-accessible date alternative adds a third day.
        card.get_by_text("Add another planned day", exact=True).focus()
        page.keyboard.press("Enter")
        date_input = card.get_by_label(f'Planned date for “{task["title"]}”')
        date_input.fill(thursday.isoformat())
        date_input.focus()
        add_button = card.get_by_role("button", name="Add to day")
        # Native Chrome's date input has separate month/day/year tab stops.
        for _ in range(4):
            page.keyboard.press("Tab")
            if add_button.evaluate("element => element === document.activeElement"):
                break
        expect(add_button).to_be_focused()
        page.keyboard.press("Enter")
        expect(handle(page, task["title"], thursday)).to_be_visible()
        three = plan(service)["placements"]
        assert len(three) == 3 and all(p in three for p in both)

        page.set_viewport_size({"width": 375, "height": 900})
        selector = page.get_by_role("group", name="Selected day")
        selector.get_by_role("button", name=re.compile("Tue")).click()
        selected_label = selector.get_by_role("button", pressed=True).inner_text()
        narrow_target = selector.get_by_role("button", name=re.compile("Fri"))
        begin_drag(page, handle(page, task["title"], tuesday))
        hover_destination(page, narrow_target)
        expect(narrow_target).to_have_class(re.compile(r"\bdrop-valid\b"))
        page.screenshot(path=evidence / "drag-03-move-narrow.png", full_page=True, timeout=5000)
        finish_drop(page)
        expect(page.locator(".week-board .planned-card:visible")).to_have_count(0)
        assert selector.get_by_role("button", pressed=True).inner_text() == selected_label
        assert plan(service)["week_start"] == initial["week_start"]
        final = plan(service)
        assert len(final["placements"]) == 3
        assert next(p for p in final["placements"] if p["id"] == placement["id"])["planned_date"] == friday.isoformat()
        selector.get_by_role("button", name=re.compile("Fri")).click()
        expect(handle(page, task["title"], friday)).to_be_visible()
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "drag-04-saved-narrow.png", full_page=True, timeout=5000)
        rows = saved_rows(service)
        for table in ("timer_sessions", "timer_intervals", "timer_operations", "closed_weeks", "closed_placements"):
            assert rows[table] == history_before[table]
        # Two deliberate completion toggles change its task revision, never fields.
        actual = final["tasks"][0]
        for field in ("id", "project_id", "parent_id", "title", "notes", "deadline", "estimate_minutes", "created_at", "completed", "completed_at"):
            assert actual[field] == task[field]
        assert service.stop() == 0
        service = Service(service.data_dir, service.port).start()
        assert saved_rows(service) == rows
        assert plan(service) == final
        page.reload()
        page.get_by_role("group", name="Selected day").get_by_role("button", name=re.compile("Fri")).click()
        expect(page.locator(".week-board .planned-card:visible")).to_have_count(1)
        assert errors == []
    finally:
        context.close()
        service.kill()


def test_native_drag_failures_stale_conflicts_and_closed_source(browser, evidence, tmp_path):
    service = Service(tmp_path / "DragFailureJourney", free_port()).start()
    context = browser.new_context(viewport={"width": 1600, "height": 1100}, locale="en-US")
    try:
        _, task = http_json("POST", service.url + "/api/tasks", {"title": "Work with save failures", "deadline": "2026-11-20", "notes": "No task cloning"})
        initial = plan(service)
        monday = date.fromisoformat(initial["week_start"])
        tuesday, wednesday = monday + timedelta(days=1), monday + timedelta(days=2)
        _, source = http_json("POST", service.url + "/api/placements", {"task_id": task["id"], "planned_date": monday.isoformat()})
        page = context.new_page()
        page.set_default_timeout(5000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url)
        expect(handle(page, task["title"], monday)).to_be_visible()
        before = saved_rows(service)

        def fail_save(route):
            if route.request.method in ("POST", "PATCH"):
                route.fulfill(status=503, content_type="application/json", body=json.dumps({"error": {"code": "storage_error", "message": "Synthetic save unavailable. Nothing was changed."}}))
            else:
                route.continue_()

        page.route("**/api/placements**", fail_save)
        for add in (False, True):
            drag_to(page, handle(page, task["title"], monday), day_column(page, tuesday), add=add)
            expect(page.get_by_role("alert")).to_contain_text("Synthetic save unavailable")
            expect(handle(page, task["title"], monday)).to_be_visible()
            expect(handle(page, task["title"], tuesday)).to_have_count(0)
            assert saved_rows(service) == before
        page.screenshot(path=evidence / "drag-05-save-error-wide.png", full_page=True, timeout=5000)
        page.unroute("**/api/placements**", fail_save)
        # Retry the exact failed Add, then free its destination and retry Move.
        drag_to(page, handle(page, task["title"], monday), day_column(page, tuesday), add=True)
        expect(handle(page, task["title"], tuesday)).to_be_visible()
        expect(handle(page, task["title"], monday)).to_be_visible()
        drag_to(page, handle(page, task["title"], tuesday), day_column(page, wednesday))
        expect(handle(page, task["title"], wednesday)).to_be_visible()
        drag_to(page, handle(page, task["title"], monday), day_column(page, tuesday))
        expect(handle(page, task["title"], tuesday)).to_be_visible()
        assert next(p for p in plan(service)["placements"] if p["id"] == source["id"])["planned_date"] == tuesday.isoformat()

        # Backend rejects the destination another tab saved after this plan loaded.
        friday = monday + timedelta(days=4)
        _, competing = http_json("POST", service.url + "/api/placements", {"task_id": task["id"], "planned_date": friday.isoformat()})
        stale_before = saved_rows(service)
        drag_to(page, handle(page, task["title"], tuesday), day_column(page, friday), add=True)
        expect(page.get_by_role("alert")).to_contain_text(f"already planned for {friday.isoformat()}")
        assert saved_rows(service) == stale_before
        page.get_by_role("button", name="Refresh weekly plan", exact=True).click()
        expect(handle(page, task["title"], friday)).to_be_visible()
        assert competing in plan(service)["placements"]

        # Begin an Add from the open view, then close its source in another tab.
        # The shared start/add function must reject its archived source atomically.
        begin_drag(page, handle(page, task["title"], tuesday), add=True)
        _, preview = http_json("GET", service.url + f"/api/weeks/{monday.isoformat()}/close-preview")
        code, closed = http_json("POST", service.url + f"/api/weeks/{monday.isoformat()}/close", {"preview_token": preview["preview_token"]})
        assert code == 200
        assert (closed["completed"], closed["total"]) == (0, 1)
        frozen = saved_rows(service)
        hover_destination(page, day_column(page, monday))
        finish_drop(page, add=True)
        expect(page.get_by_role("alert")).to_contain_text("closed week")
        assert saved_rows(service) == frozen
        page.get_by_role("button", name="Refresh weekly plan", exact=True).click()
        expect(page.get_by_text("Closed week · read-only history", exact=True)).to_be_visible()
        expect(page.locator(".placement-drag-handle")).to_have_count(0)
        expect(page.locator(".week-board").get_by_role("checkbox")).to_have_count(0)
        expect(page.locator(".week-board").get_by_text("Add another planned day", exact=True)).to_have_count(0)
        page.screenshot(path=evidence / "drag-06-closed-wide.png", full_page=True, timeout=5000)
        page.set_viewport_size({"width": 375, "height": 900})
        page.get_by_role("group", name="Selected day").get_by_role("button", name=re.compile("Tue")).click()
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "drag-07-closed-narrow.png", full_page=True, timeout=5000)
        assert service.stop() == 0
        service = Service(service.data_dir, service.port).start()
        assert saved_rows(service) == frozen
        code, after = http_json("GET", service.url + f"/api/planning?week={monday.isoformat()}")
        assert code == 200 and after["closed_week"] == closed and after["placements"] == []
        assert after["tasks"] == [task]
        assert errors == []
    finally:
        context.close()
        service.kill()
