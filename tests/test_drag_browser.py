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
    return page.get_by_role("img", name=f"Move “{title}” from {shown(day)}", exact=True)


def check_context_grip(page, day):
    row = day_column(page, day).locator(".planned-card-heading")
    grip = row.locator(".placement-drag-handle")
    expect(grip).to_have_text("")
    expect(day_column(page, day).locator(".planned-title .placement-drag-handle")).to_have_count(0)
    geometry = row.evaluate("""row => {
        const grip = row.querySelector('.placement-drag-handle').getBoundingClientRect();
        const context = row.querySelector('.planned-context');
        const range = document.createRange();
        range.selectNodeContents(context);
        const firstLine = range.getClientRects()[0];
        return {gripLeft: grip.left, gripRight: grip.right, gripTop: grip.top,
            gripBottom: grip.bottom, contextLeft: firstLine.left,
            contextTop: firstLine.top, contextBottom: firstLine.bottom};
    }""")
    assert geometry["gripRight"] <= geometry["contextLeft"]
    assert max(geometry["gripTop"], geometry["contextTop"]) < min(geometry["gripBottom"], geometry["contextBottom"])
    print(f"context grip alignment at {page.viewport_size['width']}px: {geometry}")


def check_board_dates(page, *, placements):
    board = page.locator(".week-board")
    expect(board.locator(".planned-meta").filter(has_text=re.compile(r"^Planned "))).to_have_count(0)
    expect(board.get_by_text("Due Nov 20, 2026", exact=True)).to_have_count(placements)


def begin_drag(page, source, *, alt=False):
    source.scroll_into_view_if_needed()
    box = source.bounding_box()
    assert box
    if alt:
        page.keyboard.down("Alt")
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + 18, box["y"] + box["height"] / 2 + 3, steps=6)
    indicator = page.locator(".drag-indicator")
    expect(indicator).to_be_visible()
    expect(indicator).to_contain_text("Move")
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


def finish_drop(page, *, alt=False):
    page.mouse.up()
    if alt:
        page.keyboard.up("Alt")
    expect(page.locator(".drag-indicator")).to_have_count(0)


def drag_to(page, source, target, *, alt=False):
    begin_drag(page, source, alt=alt)
    hover_destination(page, target)
    finish_drop(page, alt=alt)


def saved_rows(service):
    """Read live SQLite through its normal WAL-aware connection, never file-copy."""
    with sqlite3.connect(f"file:{service.data_dir / 'bearplans.sqlite3'}?mode=ro", uri=True) as conn:
        return {
            table: conn.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall()
            for table in ("tasks", "planned_items", "closed_weeks", "closed_placements", "timer_sessions", "timer_intervals", "timer_operations")
        }


def test_native_move_alt_move_cancel_controls_keyboard_and_narrow_days(browser, evidence, tmp_path):
    service = Service(tmp_path / "NativeDragJourney", free_port()).start()
    context = browser.new_context(viewport={"width": 1600, "height": 1100}, locale="en-US")
    try:
        _, parent = http_json("POST", service.url + "/api/tasks", {"title": "Seminar paper"})
        _, task = http_json("POST", service.url + "/api/tasks", {
            "title": "Read the primary source", "deadline": "2026-11-20", "notes": "Keep all task fields", "estimate_minutes": 35,
            "parent_id": parent["id"],
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
        placement_requests = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: placement_requests.append(request.method) if "/api/placements" in request.url and request.method != "GET" else None)
        page.goto(service.url)
        expect(handle(page, task["title"], monday)).to_be_visible()
        expect(day_column(page, monday).locator(".planned-context")).to_have_text("Inbox / Seminar paper")
        check_context_grip(page, monday)
        check_board_dates(page, placements=1)
        expect(page.locator(".planning-summary").filter(has_text=f"Planned: {shown(monday)}")).to_be_visible()
        expect(page.get_by_text("Option (Mac) / Alt (Windows)", exact=True)).to_have_count(0)
        expect(page.get_by_text("Add another planned day", exact=True)).to_have_count(0)
        expect(page.locator(".weekly-planner").get_by_text("Drag a card’s handle", exact=False)).to_have_count(0)

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
        assert plan(service)["tasks"] == initial["tasks"]

        # Option/Alt is no longer an Add gesture: it still moves the same row.
        begin_drag(page, handle(page, task["title"], tuesday), alt=True)
        hover_destination(page, day_column(page, wednesday))
        expect(page.locator(".drag-indicator")).not_to_contain_text("Add")
        page.screenshot(path=evidence / "drag-02-alt-move-wide.png", full_page=True, timeout=5000)
        finish_drop(page, alt=True)
        expect(handle(page, task["title"], wednesday)).to_be_visible()
        alt_moved = plan(service)["placements"]
        assert len(alt_moved) == 1 and alt_moved[0]["id"] == placement["id"]
        assert alt_moved[0]["created_at"] == placement["created_at"]
        assert alt_moved[0]["revision"] == placement["revision"] + 2
        assert placement_requests == ["PATCH", "PATCH"]
        # Existing extra dates survive the interface simplification unchanged.
        _, other_placement = http_json("POST", service.url + "/api/placements", {"task_id": task["id"], "planned_date": thursday.isoformat()})
        page.reload()
        expect(handle(page, task["title"], thursday)).to_be_visible()
        both = plan(service)["placements"]
        assert len(both) == 2 and alt_moved[0] in both and other_placement in both
        check_board_dates(page, placements=2)
        assert {p["task_id"] for p in both} == {task["id"]}
        expect(page.get_by_text("Weekly completion: 0 of 1 work items complete (0%).", exact=True)).to_be_visible()

        # Same-day drop in either mode is an exact no-op, including timestamps.
        for alt in (False, True):
            begin_drag(page, handle(page, task["title"], wednesday), alt=alt)
            hover_destination(page, day_column(page, wednesday))
            expect(page.locator(".drag-indicator")).to_contain_text("same day: no change")
            finish_drop(page, alt=alt)
            assert plan(service)["placements"] == both

        # Escape and an outside drop leave all saved rows untouched.
        begin_drag(page, handle(page, task["title"], wednesday))
        page.keyboard.press("Escape")
        page.mouse.up()
        expect(page.locator(".drag-indicator")).to_have_count(0)
        begin_drag(page, handle(page, task["title"], wednesday))
        page.mouse.move(12, 12, steps=15)
        page.mouse.up()
        expect(page.locator(".drag-indicator")).to_have_count(0)
        assert plan(service)["placements"] == both

        for alt in (False, True):
            begin_drag(page, handle(page, task["title"], wednesday), alt=alt)
            expect(day_column(page, thursday)).to_have_class(re.compile(r"\bdrop-conflict\b"))
            hover_destination(page, day_column(page, thursday))
            expect(page.locator(".drag-indicator")).to_contain_text("already planned here")
            finish_drop(page, alt=alt)
            expect(page.get_by_role("alert")).to_contain_text("Both existing placements are kept")
            assert plan(service)["placements"] == both

        card = day_column(page, wednesday).locator(".planned-card")
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
        expect(day_column(page, thursday).get_by_role("checkbox")).to_be_checked()
        expect(card.get_by_role("button", name="Start tracking")).to_be_disabled()
        card.get_by_role("checkbox").click()
        expect(card.get_by_role("button", name="Start tracking")).to_be_enabled()
        card.get_by_role("button", name="Start tracking").focus()
        page.keyboard.press("Enter")
        expect(page.get_by_label("Task to track", exact=True)).to_have_value(task["id"])
        assert http_json("GET", service.url + "/api/timer")[1]["active_session"] is None
        page.get_by_role("link", name="Plan", exact=True).click()

        # Fully keyboard-accessible Move remains available without dragging.
        card.get_by_text("Move or remove", exact=True).focus()
        page.keyboard.press("Enter")
        date_input = card.get_by_label(f'Move “{task["title"]}” from {shown(wednesday)} to')
        date_input.fill(tuesday.isoformat())
        date_input.focus()
        move_button = card.get_by_role("button", name="Move placement")
        # Native Chrome's date input has separate month/day/year tab stops.
        for _ in range(4):
            page.keyboard.press("Tab")
            if move_button.evaluate("element => element === document.activeElement"):
                break
        expect(move_button).to_be_focused()
        page.keyboard.press("Enter")
        expect(handle(page, task["title"], tuesday)).to_be_visible()
        after_keyboard = plan(service)["placements"]
        assert len(after_keyboard) == 2 and other_placement in after_keyboard
        assert next(p for p in after_keyboard if p["id"] == placement["id"])["planned_date"] == tuesday.isoformat()

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
        assert len(final["placements"]) == 2 and other_placement in final["placements"]
        assert next(p for p in final["placements"] if p["id"] == placement["id"])["planned_date"] == friday.isoformat()
        selector.get_by_role("button", name=re.compile("Fri")).click()
        expect(handle(page, task["title"], friday)).to_be_visible()
        check_context_grip(page, friday)
        check_board_dates(page, placements=2)
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "drag-04-saved-narrow.png", full_page=True, timeout=5000)
        rows = saved_rows(service)
        for table in ("timer_sessions", "timer_intervals", "timer_operations", "closed_weeks", "closed_placements"):
            assert rows[table] == history_before[table]
        # Two deliberate completion toggles change its task revision, never fields.
        actual = next(item for item in final["tasks"] if item["id"] == task["id"])
        for field in ("id", "project_id", "parent_id", "title", "notes", "deadline", "estimate_minutes", "created_at", "completed", "completed_at"):
            assert actual[field] == task[field]
        assert service.stop() == 0
        service = Service(service.data_dir, service.port).start()
        assert saved_rows(service) == rows
        assert plan(service) == final
        assert placement_requests and set(placement_requests) == {"PATCH"}
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
        tuesday = monday + timedelta(days=1)
        _, source = http_json("POST", service.url + "/api/placements", {"task_id": task["id"], "planned_date": monday.isoformat()})
        page = context.new_page()
        page.set_default_timeout(5000)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url)
        expect(handle(page, task["title"], monday)).to_be_visible()
        check_board_dates(page, placements=1)
        before = saved_rows(service)

        def fail_save(route):
            if route.request.method == "PATCH":
                route.fulfill(status=503, content_type="application/json", body=json.dumps({"error": {"code": "storage_error", "message": "Synthetic save unavailable. Nothing was changed."}}))
            else:
                route.continue_()

        page.route("**/api/placements**", fail_save)
        for alt in (False, True):
            drag_to(page, handle(page, task["title"], monday), day_column(page, tuesday), alt=alt)
            expect(page.get_by_role("alert")).to_contain_text("Synthetic save unavailable")
            expect(handle(page, task["title"], monday)).to_be_visible()
            expect(handle(page, task["title"], tuesday)).to_have_count(0)
            assert saved_rows(service) == before
        page.screenshot(path=evidence / "drag-05-save-error-wide.png", full_page=True, timeout=5000)
        page.unroute("**/api/placements**", fail_save)
        # Retry the exact failed Move; Option/Alt never creates a placement.
        drag_to(page, handle(page, task["title"], monday), day_column(page, tuesday))
        expect(handle(page, task["title"], tuesday)).to_be_visible()
        assert next(p for p in plan(service)["placements"] if p["id"] == source["id"])["planned_date"] == tuesday.isoformat()

        # Backend rejects the destination another tab saved after this plan loaded.
        friday = monday + timedelta(days=4)
        _, competing = http_json("POST", service.url + "/api/placements", {"task_id": task["id"], "planned_date": friday.isoformat()})
        stale_before = saved_rows(service)
        drag_to(page, handle(page, task["title"], tuesday), day_column(page, friday), alt=True)
        expect(page.get_by_role("alert")).to_contain_text(f"already planned for {friday.isoformat()}")
        assert saved_rows(service) == stale_before
        page.get_by_role("button", name="Refresh weekly plan", exact=True).click()
        expect(handle(page, task["title"], friday)).to_be_visible()
        assert competing in plan(service)["placements"]

        # Begin a Move from the open view, then close its source in another tab.
        # The shared Move function must reject its archived source atomically.
        begin_drag(page, handle(page, task["title"], tuesday), alt=True)
        _, preview = http_json("GET", service.url + f"/api/weeks/{monday.isoformat()}/close-preview")
        code, closed = http_json("POST", service.url + f"/api/weeks/{monday.isoformat()}/close", {"preview_token": preview["preview_token"]})
        assert code == 200
        assert (closed["completed"], closed["total"]) == (0, 1)
        frozen = saved_rows(service)
        hover_destination(page, day_column(page, monday))
        finish_drop(page, alt=True)
        expect(page.get_by_role("alert")).to_contain_text("closed week")
        assert saved_rows(service) == frozen
        page.get_by_role("button", name="Refresh weekly plan", exact=True).click()
        expect(page.get_by_text("Closed week · read-only history", exact=True)).to_be_visible()
        expect(page.locator(".placement-drag-handle")).to_have_count(0)
        expect(page.locator(".week-board").get_by_role("checkbox")).to_have_count(0)
        expect(page.locator(".week-board").get_by_text("Add another planned day", exact=True)).to_have_count(0)
        check_board_dates(page, placements=2)
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
