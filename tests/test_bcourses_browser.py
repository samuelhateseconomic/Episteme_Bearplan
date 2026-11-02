"""bCourses tab in real Chrome: choose courses → review → Add → due-date change → narrow layout.

The app runs in-process (uvicorn thread) with a fake bCourses client, so no
network or real token is involved; Add/Refresh go through the real routes and DB.
"""
from __future__ import annotations

import threading
import time

import pytest
import uvicorn

from backend.app import create_app
from backend.domain.tasks import list_tasks
from backend.platform.paths import FRONTEND_DIST
from backend.storage.db import open_database
from tests.conftest import free_port
from tests.test_bcourses import FakeClient
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not (FRONTEND_DIST / "index.html").is_file(), reason="frontend not built")]


@pytest.fixture
def served(tmp_path, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    db = open_database(tmp_path / "bearplans.sqlite3")
    fake = FakeClient()
    port = free_port()
    server = uvicorn.Server(uvicorn.Config(create_app(db, FRONTEND_DIST, bcourses_client=fake),
                                           host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}", db, fake
    server.should_exit = True
    thread.join(10)


def test_choose_courses_add_assignment_and_review_due_change(browser, evidence, served):
    expect = playwright_sync.expect
    url, db, fake = served
    page = browser.new_page(viewport={"width": 1440, "height": 1000}, locale="en-US", timezone_id="America/Los_Angeles")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    fake.by_course["1"][0]["due_at"] = "2099-11-07T07:59:00Z"
    try:
        page.goto(url + "/#bcourses")
        tab = page.get_by_role("region", name="bCourses")
        expect(tab.get_by_text("Choose at least one course above, then Save courses.")).to_be_visible()
        assert fake.calls == ["courses"]
        tab.get_by_role("checkbox", name="MATH 54 - Linear Algebra").check()
        page.screenshot(path=str(evidence / "bcourses-01-choose.png"), full_page=True)
        tab.get_by_role("button", name="Save courses").click()

        upcoming = tab.get_by_role("list", name="Upcoming assignments")
        expect(upcoming.get_by_role("listitem")).to_have_count(1)
        expect(upcoming).to_contain_text("Problem set 5")
        expect(upcoming).to_contain_text("Due Fri, Nov 6")
        expect(upcoming.get_by_role("link", name="Open in bCourses")).to_have_attribute("href", fake.by_course["1"][0]["html_url"])
        expect(tab.get_by_role("list", name="Assignments with no due date").get_by_role("listitem")).to_have_count(2)
        assert [t.title for t in list_tasks(db)] == []  # Nothing imported before Add.
        assert no_horizontal_overflow(page)
        page.screenshot(path=str(evidence / "bcourses-02-review.png"), full_page=True)

        tab.get_by_role("button", name="Add “Problem set 5” as a task").click()
        expect(tab.get_by_role("status")).to_contain_text("Added “Problem set 5” to MATH 54 - Linear Algebra, due Fri, Nov 6")
        tasks = [t for t in list_tasks(db) if t.title == "Problem set 5"]
        assert len(tasks) == 1 and str(tasks[0].deadline) == "2099-11-06"
        page.get_by_role("link", name="Plan", exact=True).click()
        expect(page.get_by_role("button", name="MATH 54 - Linear Algebra", exact=True)).to_be_visible()

        page.get_by_role("link", name="bCourses", exact=True).click()
        fake.by_course["1"][0]["due_at"] = "2099-11-10T07:59:00Z"
        tab.get_by_role("button", name="Refresh", exact=True).click()
        changed = tab.get_by_role("list", name="Due date changed")
        expect(changed).to_contain_text("Your task: Fri, Nov 6 → bCourses: Mon, Nov 9")
        page.screenshot(path=str(evidence / "bcourses-03-due-changed.png"), full_page=True)
        changed.get_by_role("button", name="Use new due date").click()
        expect(tab.get_by_role("status")).to_contain_text("Updated the due date")
        expect(tab.get_by_role("list", name="Due date changed")).to_have_count(0)
        assert str(next(t for t in list_tasks(db) if t.title == "Problem set 5").deadline) == "2099-11-09"

        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=str(evidence / "bcourses-04-narrow.png"), full_page=True)
        assert errors == []
    finally:
        page.close()
