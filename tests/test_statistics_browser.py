"""Stats navigation, readable layouts, failure recovery and durable saved totals."""
from datetime import UTC, datetime, timedelta

import pytest

from backend.domain.projects import create_project
from backend.domain.tasks import create_task, set_task_completion
from backend.platform.paths import DATABASE_FILENAME, FRONTEND_DIST
from backend.storage.db import open_database
from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync
from tests.test_forest import all_rows
from tests.test_streaks import HOUR, saved_interval

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not (FRONTEND_DIST / "index.html").is_file(), reason="frontend not built")]


def test_statistics_known_totals_navigation_layout_retry_and_restart(browser, evidence, tmp_path, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    now = datetime(2026, 10, 23, 20, tzinfo=UTC)
    data_dir = tmp_path / "StatisticsJourney"
    data_dir.mkdir()
    db = open_database(data_dir / DATABASE_FILENAME)
    project = create_project(db, "Synthetic mathematics course")
    parent = create_task(db, "Weekly problem set", project_id=project.id, estimate_minutes=999)
    child = create_task(db, "Solve and review the induction exercises", parent_id=parent.id, estimate_minutes=60)
    essay = create_task(db, "Draft the argument and collect supporting references", estimate_minutes=30)
    saved_interval(db, now - timedelta(hours=2), now - timedelta(hours=1, minutes=20), 2_400_000_000, task=child)
    saved_interval(db, now - timedelta(hours=1), now - timedelta(minutes=40), 1_200_000_000, task=essay, outcome="finished_early")
    set_task_completion(db, child.id, True)
    before = all_rows(db)
    service = Service(data_dir, free_port()).start()
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, timezone_id="Asia/Tokyo")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    expect = playwright_sync.expect
    try:
        page.goto(service.url + "/#stats")
        stats = page.get_by_role("region", name="Statistics", exact=True)
        expect(stats.get_by_text("1 of 2 complete (50%)", exact=True)).to_be_visible()
        expect(stats.get_by_text("60 min 0 s", exact=True).first).to_be_visible()
        expect(stats.get_by_text("Estimate: 60 min", exact=True)).to_be_visible()
        expect(stats.get_by_text("Estimate: 999 min", exact=True)).to_have_count(0)
        expect(page.get_by_role("link", name="Stats", exact=True)).to_have_attribute("aria-current", "page")
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "stats-01-wide.png", full_page=True)
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "stats-02-narrow.png", full_page=True)
        page.emulate_media(color_scheme="dark")
        page.screenshot(path=evidence / "stats-03-dark.png", full_page=True)
        page.emulate_media(color_scheme="light")
        stats.get_by_role("combobox").select_option(project.id)
        expect(stats.get_by_role("list", name="Task statistics").get_by_text(essay.title, exact=True)).to_have_count(0)
        stats.get_by_role("combobox").select_option("")
        page.get_by_role("link", name="Plan", exact=True).click()
        expect(stats).to_be_hidden()
        page.get_by_role("link", name="Stats", exact=True).click()
        expect(stats.get_by_text("1 of 2 complete (50%)", exact=True)).to_be_visible()

        def unavailable(route):
            route.fulfill(status=503, content_type="application/json", body='{"error":{"message":"Synthetic unavailable saved data."}}')
        page.route("**/api/statistics", unavailable)
        refresh = stats.get_by_role("button", name="Refresh statistics", exact=True)
        refresh.focus()
        page.keyboard.press("Enter")
        expect(stats.get_by_role("alert")).to_contain_text("Showing the last loaded statistics")
        expect(stats.get_by_text("1 of 2 complete (50%)", exact=True)).to_be_visible()
        page.screenshot(path=evidence / "stats-04-read-error.png", full_page=True)
        page.unroute("**/api/statistics", unavailable)
        refresh.focus()
        page.keyboard.press("Enter")
        expect(stats.get_by_role("alert")).to_have_count(0)
        page.reload()
        expect(stats.get_by_text("1 of 2 complete (50%)", exact=True)).to_be_visible()
        report = http_json("GET", service.url + "/api/statistics")[1]
        assert all_rows(db) == before
        page.close()
        assert service.stop() == 0
        service = Service(data_dir, service.port).start()
        assert http_json("GET", service.url + "/api/statistics")[1] == report
        assert all_rows(db) == before
        assert errors == []
    finally:
        context.close()
        service.kill()
