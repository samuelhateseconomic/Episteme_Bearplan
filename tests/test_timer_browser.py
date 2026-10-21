"""Countdown journeys through real Chrome and a real local service.

All task/session data is synthetic, in disposable directories outside the repo.
"""

from datetime import date, timedelta
import os
import sqlite3
import time
from uuid import uuid4

import pytest

from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

pytestmark = pytest.mark.e2e


def test_countdown_navigation_tabs_pause_retry_and_history(browser, evidence, tmp_path):
    expect = playwright_sync.expect
    service = Service(tmp_path / "CountdownJourney", free_port()).start()
    context = browser.new_context(viewport={"width": 1440, "height": 950}, locale="en-US")
    try:
        _, parent = http_json("POST", service.url + "/api/tasks", {"title": "Seminar"})
        _, child = http_json("POST", service.url + "/api/tasks", {
            "title": "Read the argument", "parent_id": parent["id"],
            "deadline": "2026-11-18", "notes": "Track existing work",
        })
        _, other = http_json("POST", service.url + "/api/tasks", {"title": "Another unscheduled task"})
        _, original_tasks = http_json("GET", service.url + "/api/tasks")
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url)
        row = page.locator(".subtasks > .task").filter(has=page.get_by_label(child["title"], exact=True))
        row.get_by_role("button", name="Start tracking", exact=True).click()
        expect(page.get_by_label("Task to track", exact=True)).to_have_value(child["id"])
        expect(page.get_by_label("Task to track").locator("option").filter(has_text="Seminar")).not_to_have_attribute("value", parent["id"])
        page.get_by_label("Duration (minutes)").fill("1")
        page.get_by_role("button", name="Start countdown", exact=True).focus()
        page.keyboard.press("Enter")
        current = page.get_by_role("region", name="Current session")
        expect(current.get_by_role("heading", name=child["title"], exact=True)).to_be_visible()
        expect(current.get_by_role("button", name="Pause", exact=True)).to_be_enabled()
        _, started = http_json("GET", service.url + "/api/timer")
        session_id = started["active_session"]["id"]
        assert started["active_session"]["task_id"] == child["id"]
        assert http_json("GET", service.url + "/api/planning")[1]["placements"] == []

        page.get_by_role("link", name="Plan", exact=True).click()
        compact = page.get_by_role("complementary", name="Active countdown")
        expect(compact).to_contain_text(child["title"])
        # A normal task mutation remains responsive while the monitor is tracking.
        before = time.monotonic()
        page.get_by_label("Title", exact=True).fill("A normal task during tracking")
        page.get_by_role("button", name="Add task", exact=True).click()
        expect(page.get_by_label("A normal task during tracking", exact=True)).to_be_visible()
        latency = time.monotonic() - before
        assert latency < 3, f"normal UI task mutation took {latency:.3f}s"
        print(f"normal task creation during countdown: {latency:.3f}s")
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=evidence / "timer-01-plan-compact.png", full_page=True)

        second = context.new_page()
        second.goto(service.url + "/#track")
        second_current = second.get_by_role("region", name="Current session")
        expect(second_current).to_contain_text(child["title"])
        second.screenshot(path=evidence / "timer-07-active-wide.png", full_page=True)
        second.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(second)
        second.screenshot(path=evidence / "timer-08-active-narrow.png", full_page=True)
        second.set_viewport_size({"width": 1440, "height": 950})
        competing = second.request.post(service.url + "/api/timer/start", data={
            "task_id": other["id"], "duration_minutes": 1, "operation_id": str(uuid4()),
        })
        assert competing.status == 409
        assert "already" in competing.json()["error"]["message"]
        second_current.get_by_role("button", name="Pause", exact=True).focus()
        second.keyboard.press("Enter")
        expect(second_current.get_by_role("button", name="Resume", exact=True)).to_be_visible()
        _, paused = http_json("GET", service.url + "/api/timer")
        paused_seconds = paused["active_session"]["active_seconds"]
        time.sleep(1.1)
        page.reload()
        expect(page.get_by_role("complementary", name="Active countdown")).to_contain_text("Paused")
        assert http_json("GET", service.url + "/api/timer")[1]["active_session"]["active_seconds"] == paused_seconds
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "timer-09-compact-narrow.png", full_page=True)
        second.reload()
        expect(second.get_by_role("button", name="Resume", exact=True)).to_be_enabled()
        second.get_by_role("button", name="Resume", exact=True).click()
        expect(second.get_by_role("button", name="Pause", exact=True)).to_be_visible()

        # Lose a committed finish response, then retry the same saved session.
        finish_requests = []

        def lose_finish_response(route):
            finish_requests.append(route.request.post_data_json)
            response = route.fetch()
            assert response.status == 200
            route.abort()

        second.route(f"**/api/timer/{session_id}/finish", lose_finish_response)
        second.get_by_role("button", name="Finish early", exact=True).click()
        expect(second.get_by_role("region", name="Saved session outcome")).to_contain_text("Finished early")
        assert len(finish_requests) == 1
        code, saved = http_json("POST", service.url + f"/api/timer/{session_id}/finish", finish_requests[0])
        assert code == 200 and saved["active_session"] is None
        result = saved["last_session"]
        assert result["id"] == session_id and result["outcome"] == "finished_early"
        assert 0 < result["active_seconds"] < 60
        assert http_json("GET", service.url + "/api/tasks")[1]["tasks"][:3] == original_tasks["tasks"]

        # Scheduling/moving/editing work cannot move or alter recorded intervals.
        database = service.data_dir / "bearplans.sqlite3"
        with sqlite3.connect(database) as conn:
            sessions_before = conn.execute("SELECT * FROM timer_sessions").fetchall()
            intervals_before = conn.execute("SELECT * FROM timer_intervals ORDER BY rowid").fetchall()
            assert len(sessions_before) == 1 and len(intervals_before) == 2
        _, plan = http_json("GET", service.url + "/api/planning")
        monday = date.fromisoformat(plan["week_start"])
        _, placement = http_json("POST", service.url + "/api/placements", {
            "task_id": child["id"], "planned_date": monday.isoformat(),
        })
        assert "id" in placement, placement
        status, _ = http_json("PATCH", service.url + f"/api/placements/{placement['id']}", {
            "planned_date": (monday + timedelta(days=8)).isoformat(),
        })
        assert status == 200
        http_json("PATCH", service.url + f"/api/tasks/{child['id']}", {"title": "Read the revised argument"})
        with sqlite3.connect(database) as conn:
            assert conn.execute("SELECT * FROM timer_sessions").fetchall() == sessions_before
            assert conn.execute("SELECT * FROM timer_intervals ORDER BY rowid").fetchall() == intervals_before
        assert http_json("GET", service.url + "/api/tasks")[1]["progress"]["completed"] == 0

        second.reload()
        expect(second.get_by_role("region", name="Saved session outcome")).to_contain_text("Finished early")
        second.screenshot(path=evidence / "timer-02-saved-wide.png", full_page=True)
        second.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(second)
        second.screenshot(path=evidence / "timer-03-track-narrow.png", full_page=True)
        second.emulate_media(color_scheme="dark")
        second.set_viewport_size({"width": 1024, "height": 900})
        second.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        expect(second.get_by_role("main")).to_have_count(1)
        second.screenshot(path=evidence / "timer-04-dark-laptop.png", full_page=True)
        # The first build's restart safeguard must be visible and require an
        # explicit decision to save confirmed time without the unknown gap.
        second.get_by_label("Task to track").select_option(other["id"])
        second.get_by_label("Duration (minutes)").fill("1")
        second.get_by_role("button", name="Start countdown", exact=True).click()
        expect(second.get_by_role("region", name="Current session")).to_contain_text(other["title"])
        assert service.stop() == 0
        service = Service(service.data_dir, service.port).start()
        second.reload()
        expect(second.get_by_role("region", name="Current session")).to_contain_text("Needs review")
        expect(second.get_by_role("button", name="Resume", exact=True)).to_have_count(0)
        second.screenshot(path=evidence / "timer-06-restart-review.png", full_page=True)
        second.get_by_role("button", name="Save confirmed time and finish", exact=True).click()
        expect(second.get_by_role("region", name="Saved session outcome")).to_contain_text("Interrupted · uncertain time excluded")
        assert errors == []
    finally:
        context.close()
        service.kill()


def test_real_one_minute_countdown_expires_with_browser_closed(browser, evidence, tmp_path):
    expect = playwright_sync.expect
    service = Service(tmp_path / "RealCountdown", free_port()).start()
    try:
        _, task = http_json("POST", service.url + "/api/tasks", {"title": "One real minute, unscheduled"})
        page = browser.new_page(viewport={"width": 1280, "height": 900}, locale="en-US")
        page.goto(service.url + "/#track")
        page.get_by_label("Task to track").select_option(task["id"])
        page.get_by_label("Duration (minutes)").fill("1")
        before = time.monotonic()
        page.get_by_role("button", name="Start countdown", exact=True).click()
        expect(page.get_by_role("region", name="Current session")).to_contain_text(task["title"])
        _, started = http_json("GET", service.url + "/api/timer")
        session_id = started["active_session"]["id"]
        page.reload()
        expect(page.get_by_role("region", name="Current session")).to_contain_text(task["title"])
        browser_type = browser.browser_type
        browser.close()
        # No timer API calls or browser callbacks can resolve expiry here. Observe
        # the saved row read-only until the independent service monitor finishes.
        deadline = before + 70
        terminal = None
        while time.monotonic() < deadline:
            with sqlite3.connect(service.data_dir / "bearplans.sqlite3") as conn:
                terminal = conn.execute(
                    "SELECT state, outcome, active_microseconds FROM timer_sessions WHERE id = ?", (session_id,)
                ).fetchone()
            if terminal[0] == "finished":
                break
            time.sleep(0.25)
        elapsed = time.monotonic() - before
        assert terminal == ("finished", "completed", 60_000_000), terminal
        # The monitor, with no browser or timer API callback, atomically plants
        # exactly one mature tree alongside that fully confirmed session.
        with sqlite3.connect(service.data_dir / "bearplans.sqlite3") as conn:
            assert conn.execute(
                "SELECT session_id, outcome FROM trees"
            ).fetchall() == [(session_id, "mature")]
        assert 60 <= elapsed < 64, f"one-minute monitor expiry took {elapsed:.3f}s"
        print(f"real countdown: 60.000000s credited; independent elapsed {elapsed:.3f}s; browser closed")
        _, tasks = http_json("GET", service.url + "/api/tasks")
        assert tasks["tasks"] == [task] and tasks["progress"] == {"completed": 0, "total": 1}
        reopened = browser_type.launch(channel=os.environ.get("BEARPLANS_E2E_CHANNEL", "chrome"), args=["--disable-gpu"])
        try:
            page = reopened.new_page(viewport={"width": 1280, "height": 900})
            page.goto(service.url + "/#track")
            expect(page.get_by_role("region", name="Saved session outcome")).to_contain_text("Countdown completed")
            expect(page.get_by_role("region", name="Forest collection")).to_contain_text("Mature Pine")
            page.screenshot(path=evidence / "timer-05-real-expiry.png", full_page=True)
        finally:
            reopened.close()
    finally:
        service.kill()
