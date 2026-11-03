"""Google tab and calendar events in real Chrome, with fake Google clients.

Flow: connected tab → choose calendars → event shown beside its day → Add as task →
give it a start time → sync puts it in the BearPlans calendar with a 30-minute
reminder → a tick made in Google appears without reloading → narrow layout.
No network or real token is involved.
"""
from __future__ import annotations

import threading
import time
from datetime import date

import pytest
import uvicorn

from backend.app import create_app
from backend.domain.tasks import list_tasks
from backend.platform.google import GoogleAuth
from backend.platform.paths import FRONTEND_DIST
from backend.storage.db import open_database
from tests.conftest import free_port
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync
from tests.test_google_calendar import FakeCalendar
from tests.test_google_tasks import FakeTasks

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not (FRONTEND_DIST / "index.html").is_file(), reason="frontend not built")]

TODAY = date.today().isoformat()


class ConnectedAuth(GoogleAuth):
    def configured(self) -> bool:
        return True

    def connected(self) -> bool:
        return True

    def granted_scopes(self) -> set[str]:
        from backend.platform.google import SCOPES
        return set(SCOPES)


class FakeGoogleCalendar(FakeCalendar):
    """Writes like FakeCalendar; reads the user's calendars like Google's calendarList."""

    def __init__(self) -> None:
        super().__init__()
        self.lock = threading.Lock()
        self.user_calendars = [{"id": "me@example.com", "summary": "Me", "primary": True, "backgroundColor": "#9fc6e7"},
                               {"id": "club@group", "summary": "Climbing club"}]
        self.user_events = {"me@example.com": [{
            "id": "oh", "summary": "Office hours", "location": "Soda 283",
            "start": {"dateTime": f"{TODAY}T23:00:00-08:00"}, "end": {"dateTime": f"{TODAY}T23:45:00-08:00"}}]}

    def calendar_list(self):
        return self.user_calendars

    def list_events(self, calendar_id, time_min, time_max):
        return self.user_events.get(calendar_id, [])


@pytest.fixture
def served(tmp_path, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    db = open_database(tmp_path / "bearplans.sqlite3")
    tasks, calendar = FakeTasks(), FakeGoogleCalendar()
    port = free_port()
    app = create_app(db, FRONTEND_DIST, google_auth=ConnectedAuth(), google_tasks_client=tasks, google_calendar_client=calendar)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}", db, tasks, calendar
    server.should_exit = True
    thread.join(10)


def test_calendars_events_start_time_and_ticks_from_google(browser, evidence, served):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    if datetime.now(ZoneInfo("America/Los_Angeles")).hour >= 23:
        pytest.skip("the test plans an event at 23:15 today; too late to be upcoming")
    expect = playwright_sync.expect
    url, db, tasks, calendar = served
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="en-US", timezone_id="America/Los_Angeles")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    try:
        page.goto(url + "/#google")
        tab = page.get_by_role("region", name="Google")
        expect(tab.get_by_text("Connected to Google.")).to_be_visible()
        tab.get_by_role("checkbox", name="Me · main calendar").check()
        page.screenshot(path=str(evidence / "google-01-calendars.png"), full_page=True)
        tab.get_by_role("button", name="Save calendars").click()
        expect(tab.get_by_role("status")).to_contain_text("Saved your calendars")

        page.get_by_role("link", name="Plan", exact=True).click()
        events = page.locator(".day-events")
        expect(events).to_have_count(1)
        expect(events.get_by_text("Office hours")).not_to_be_visible()  # closed until opened
        events.get_by_text("From your calendar (1)").click()
        expect(events).to_contain_text("Office hours")
        expect(events).to_contain_text("Me · Soda 283")
        assert no_horizontal_overflow(page)
        page.screenshot(path=str(evidence / "google-02-day-event.png"), full_page=True)
        events.get_by_role("button", name="Add as task").click()
        expect(events).to_contain_text("Added as a task")
        card = page.locator(".planned-card", has_text="Office hours")
        expect(card).to_have_count(1)
        [task] = [t for t in list_tasks(db) if t.title == "Office hours"]
        assert task.estimate_minutes == 45 and "Where: Soda 283" in task.notes

        card.get_by_text("Move or remove").click()
        card.get_by_label("Start time on", exact=False).fill("23:15")
        card.get_by_role("button", name="Save time").click()
        expect(page.locator(".planned-card", has_text="Office hours")).to_contain_text("At 11:15 PM")

        page.get_by_role("link", name="Google", exact=True).click()
        tab.get_by_role("button", name="Sync now").click()
        expect(tab.get_by_role("status")).to_contain_text("up to date")
        expect(tab).to_contain_text("1 upcoming event in the “BearPlans” calendar")
        [event] = calendar.live()
        assert event["summary"] == "Office hours"
        assert event["reminders"] == {"useDefault": False, "overrides": [{"method": "popup", "minutes": 30}]}
        page.screenshot(path=str(evidence / "google-03-synced.png"), full_page=True)

        # Tick it in Google; the open page picks it up when the window regains focus.
        page.get_by_role("link", name="Plan", exact=True).click()
        page.evaluate("window.dispatchEvent(new Event('focus'))")  # learn the current version
        page.wait_for_timeout(300)
        google_task = next(item for items in tasks.items.values() for item in items.values() if item.get("title") == "Office hours")
        google_task["status"] = "completed"
        assert page.request.post(url + "/api/google/tasks/sync").ok
        page.evaluate("window.dispatchEvent(new Event('focus'))")
        expect(page.locator(".planned-card", has_text="Office hours").get_by_role("checkbox")).to_be_checked()

        page.set_viewport_size({"width": 375, "height": 850})
        page.get_by_role("link", name="Google", exact=True).click()
        assert no_horizontal_overflow(page)
        page.screenshot(path=str(evidence / "google-04-narrow.png"), full_page=True)
        assert errors == []
    finally:
        page.close()
