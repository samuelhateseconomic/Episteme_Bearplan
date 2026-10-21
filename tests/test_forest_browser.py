"""Tree rendering and saved forest through Chromium and a disposable service.

Initial confirmed growth is seeded through shared domain functions with a fake
clock. The browser then uses a real process; this does not simulate Mac power.
"""

import sqlite3
from uuid import uuid4

import pytest

from backend.domain.tasks import create_task
from backend.domain.timer import TimerService
from backend.platform.paths import DATABASE_FILENAME
from backend.storage.db import open_database
from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync
from tests.test_timer import FakeClock, observed

pytestmark = pytest.mark.e2e


def test_forest_recovery_early_finish_retry_and_restart(browser, evidence, tmp_path):
    expect = playwright_sync.expect
    data_dir = tmp_path / "ForestJourney"
    data_dir.mkdir()
    db = open_database(data_dir / DATABASE_FILENAME)
    clock = FakeClock()
    timer = TimerService(db, clock)
    completed_task = create_task(db, "Synthetic completed forest work")
    completed = timer.start(completed_task.id, 1, str(uuid4())).active_session
    observed(timer, clock, 60)
    task = create_task(db, "Synthetic recovered forest work")
    active = timer.start(task.id, 1, str(uuid4())).active_session
    grown = observed(timer, clock, 36).active_session
    assert grown.tree.stage == "sapling"
    tree_id = grown.tree.id

    service = Service(data_dir, free_port()).start()
    context = browser.new_context(viewport={"width": 1440, "height": 950})
    try:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url + "/#track")
        current = page.get_by_role("region", name="Current session")
        forest = page.get_by_role("region", name="Forest collection")
        expect(current).to_contain_text("Needs review")
        expect(current.get_by_role("img", name="Pine sapling", exact=True)).to_be_visible()
        expect(forest).to_contain_text(completed_task.title)
        expect(forest).not_to_contain_text(task.title)
        _, reviewed = http_json("GET", service.url + "/api/timer")
        assert reviewed["active_session"]["tree"]["id"] == tree_id
        assert reviewed["active_session"]["tree"]["progress"] == 0.6
        page.screenshot(path=evidence / "forest-01-review-wide.png", full_page=True)
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "forest-02-review-narrow.png", full_page=True)

        current.get_by_role("button", name="Continue with confirmed time", exact=True).click()
        expect(current.get_by_role("button", name="Pause", exact=True)).to_be_visible()
        current.get_by_role("button", name="Pause", exact=True).click()
        expect(current.get_by_role("button", name="Resume", exact=True)).to_be_visible()
        _, paused = http_json("GET", service.url + "/api/timer")
        paused_tree = paused["active_session"]["tree"]
        page.reload()
        expect(current.get_by_role("img", name="Pine sapling", exact=True)).to_be_visible()
        assert http_json("GET", service.url + "/api/timer")[1]["active_session"]["tree"] == paused_tree

        # A committed response can be lost. The retry cannot plant twice.
        payloads = []

        def lose_finish_response(route):
            payloads.append(route.request.post_data_json)
            assert route.fetch().status == 200
            route.abort()

        page.route(f"**/api/timer/{active.id}/finish", lose_finish_response)
        current.get_by_role("button", name="Finish early", exact=True).click()
        expect(page.get_by_role("region", name="Saved session outcome")).to_contain_text("Unfinished")
        expect(forest).to_contain_text(task.title)
        assert len(payloads) == 1
        assert http_json("POST", service.url + f"/api/timer/{active.id}/finish", payloads[0])[0] == 200
        _, collection = http_json("GET", service.url + "/api/forest")
        assert len(collection["trees"]) == 2
        by_session = {tree["session_id"]: tree for tree in collection["trees"]}
        assert by_session[completed.id]["outcome"] == "mature"
        assert by_session[active.id]["outcome"] == "unfinished"
        assert by_session[active.id]["id"] == tree_id

        # The deliberately lost response shows actionable feedback. Recheck the
        # saved timer before capturing the ordinary collection layout.
        page.unroute(f"**/api/timer/{active.id}/finish", lose_finish_response)
        page.get_by_role("button", name="Refresh timer", exact=True).click()
        expect(page.get_by_role("alert")).to_have_count(0)

        page.set_viewport_size({"width": 1440, "height": 950})
        page.screenshot(path=evidence / "forest-03-collection-wide.png", full_page=True)
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "forest-04-collection-narrow.png", full_page=True)
        page.emulate_media(color_scheme="dark")
        page.screenshot(path=evidence / "forest-05-collection-dark.png", full_page=True)
        page.close()
        assert service.stop() == 0
        service = Service(data_dir, service.port).start()
        assert http_json("GET", service.url + "/api/forest")[1] == collection
        assert http_json("GET", service.url + "/api/tasks")[1]["progress"] == {"completed": 0, "total": 2}
        page = context.new_page()
        page.goto(service.url + "/#track")
        expect(page.get_by_role("region", name="Forest collection")).to_contain_text(task.title)
        with sqlite3.connect(data_dir / DATABASE_FILENAME) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert errors == []
    finally:
        context.close()
        service.kill()
