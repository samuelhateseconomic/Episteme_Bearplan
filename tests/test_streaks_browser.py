"""Saved daily progress through Chrome and a disposable local service.

Long sessions are seeded through the real timer application functions with an
observed fake clock. Browser finish/retry/reload and process restart are real;
these checks do not constitute hardware sleep or long-duration acceptance.
"""

from datetime import UTC, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from backend.domain.planning import application_today, create_placement
from backend.domain.projects import create_project
from backend.domain.tasks import create_task
from backend.domain.timer import TimerService
from backend.domain.weeks import close_week, preview_close
from backend.platform.paths import DATABASE_FILENAME
from backend.storage.db import open_database
from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync
from tests.test_forest import all_rows
from tests.test_timer import FakeClock, observed

pytestmark = pytest.mark.e2e


def test_saved_streak_progress_finish_retry_timezone_and_restart(browser, evidence, tmp_path, monkeypatch):
    expect = playwright_sync.expect
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")
    today, _ = application_today()
    zone = ZoneInfo("America/Los_Angeles")
    data_dir = tmp_path / "StreakJourney"
    data_dir.mkdir()
    db = open_database(data_dir / DATABASE_FILENAME)
    project = create_project(db, "Synthetic streak course")
    parent = create_task(db, "Synthetic course container", project_id=project.id)
    task = create_task(db, "Synthetic saved focus", parent_id=parent.id,
                       project_id=project.id, notes="Keep all original fields")
    other = create_task(db, "Synthetic second project work")
    historical_day = today - timedelta(days=14)
    create_placement(db, task.id, historical_day)
    close_week(db, historical_day, preview_close(db, historical_day).preview_token)

    clock = FakeClock()
    timer = TimerService(db, clock)
    for days_ago, minutes, leaf in [(2, 60, task), (1, 60, other), (0, 30, task)]:
        clock.wall = datetime.combine(today - timedelta(days=days_ago), time(0), zone).astimezone(UTC)
        timer.start(leaf.id, minutes, str(uuid4()))
        assert observed(timer, clock, minutes * 60).last_session.outcome == "completed"
    session = timer.start(other.id, 31, str(uuid4())).active_session
    observed(timer, clock, 1800)
    paused = timer.control(session.id, "pause", expected_revision=session.revision).active_session
    assert paused.active_seconds == 1800
    unchanged = {key: value for key, value in all_rows(db).items()
                 if key in ("projects", "tasks", "planned_items", "closed_weeks", "closed_placements",
                            "carryover_operations", "schema_migrations", "owned_species", "shop_operations")}

    service = Service(data_dir, free_port()).start()
    # A different browser timezone must not shift service date-only labels.
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, timezone_id="Pacific/Auckland")
    try:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url + "/#track")
        streak = page.get_by_role("region", name="Daily streak", exact=True)
        expect(streak).to_contain_text("America/Los_Angeles")
        initial = http_json("GET", service.url + "/api/streaks")[1]
        assert initial["today"] == today.isoformat() and initial["current_streak"] == 2
        assert initial["days"][-1]["active_microseconds"] == 1_800_000_000
        assert not initial["days"][-1]["qualified"]
        expect(streak.get_by_role("progressbar")).to_have_attribute("value", "1800000000")
        page.screenshot(path=evidence / "streak-01-partial-wide.png", full_page=True)
        streak.screenshot(path=evidence / "streak-01-partial-section.png")

        # A failed read retains the last saved view; keyboard refresh recovers.
        def fail_read(route):
            route.fulfill(status=503, json={"error": {"code": "storage_unavailable", "message": "Synthetic streak read unavailable."}})

        page.route("**/api/streaks", fail_read)
        refresh = streak.get_by_role("button", name="Refresh streak", exact=True)
        refresh.focus()
        page.keyboard.press("Enter")
        expect(streak.get_by_role("alert")).to_contain_text("Synthetic streak read unavailable")
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "streak-02-retry-narrow.png", full_page=True)
        page.unroute("**/api/streaks", fail_read)
        refresh.focus()
        page.keyboard.press("Enter")
        expect(streak.get_by_role("alert")).to_have_count(0)

        # Finishing saves the second 30 minutes. A lost response and exact retry
        # cannot count it twice, award twice, or change task/week records.
        payloads = []

        def lose_finish(route):
            payloads.append(route.request.post_data_json)
            assert route.fetch().status == 200
            route.abort()

        page.route(f"**/api/timer/{session.id}/finish", lose_finish)
        page.get_by_role("region", name="Current session", exact=True).get_by_role("button", name="Finish early", exact=True).click()
        expect(streak.get_by_role("progressbar")).to_have_attribute("value", "3600000000")
        assert len(payloads) == 1
        assert http_json("POST", f"{service.url}/api/timer/{session.id}/finish", payloads[0])[0] == 200
        final = http_json("GET", service.url + "/api/streaks")[1]
        assert final["current_streak"] == 3 and final["streak_through"] == today.isoformat()
        assert final["days"][-1]["active_microseconds"] == 3_600_000_000
        assert final["days"][-1]["qualified"]
        page.unroute(f"**/api/timer/{session.id}/finish", lose_finish)
        page.get_by_role("button", name="Refresh timer", exact=True).click()
        page.reload()
        expect(streak.get_by_role("progressbar")).to_have_attribute("value", "3600000000")
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.screenshot(path=evidence / "streak-03-qualified-wide.png", full_page=True)
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "streak-04-qualified-narrow.png", full_page=True)
        streak.screenshot(path=evidence / "streak-04-qualified-section.png")
        page.emulate_media(color_scheme="dark")
        page.screenshot(path=evidence / "streak-05-qualified-dark.png", full_page=True)
        streak.screenshot(path=evidence / "streak-05-dark-section.png")

        before_restart = all_rows(db)
        for key, value in unchanged.items():
            assert before_restart[key] == value
        assert len(before_restart["trees"]) == 4 and len(before_restart["coin_ledger"]) == 4
        page.close()
        assert service.stop() == 0
        service = Service(data_dir, service.port).start()
        assert http_json("GET", service.url + "/api/streaks")[1] == final
        assert all_rows(db) == before_restart
        page = context.new_page()
        page.goto(service.url + "/#track")
        expect(page.get_by_role("region", name="Daily streak", exact=True).get_by_role("progressbar")).to_have_attribute("value", "3600000000")
        with db.read() as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert errors == []
    finally:
        context.close()
        service.kill()
