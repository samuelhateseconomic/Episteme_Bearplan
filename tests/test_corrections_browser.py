"""A real saved-time correction, lost response, reload/replay and audited reversal."""
import re
from uuid import uuid4

import pytest

from backend.domain.corrections import list_saved_sessions
from backend.domain.forest import list_forest
from backend.domain.planning import create_placement
from backend.domain.rewards import RewardConfig, ShopService
from backend.domain.weeks import close_week, preview_close
from backend.platform.paths import DATABASE_FILENAME, FRONTEND_DIST
from backend.storage.db import open_database
from tests.conftest import Service, free_port, http_json
from tests.test_corrections import HOUR, seeded
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync
from tests.test_forest import all_rows

pytestmark = [pytest.mark.e2e, pytest.mark.skipif(not (FRONTEND_DIST / "index.html").is_file(), reason="frontend not built")]


def test_reviewed_correction_lost_response_reload_reversal_and_restart(browser, evidence, tmp_path, monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "UTC")
    data_dir = tmp_path / "CorrectionJourney"
    data_dir.mkdir()
    db = open_database(data_dir / DATABASE_FILENAME)
    session, task = seeded(db)
    shop = ShopService(db, RewardConfig(birch_price=60))
    shop.purchase("birch", 60, str(uuid4()))
    create_placement(db, task.id, "2026-10-23")
    close_week(db, "2026-10-19", preview_close(db, "2026-10-19").preview_token)
    original = all_rows(db)
    tree_id = list_forest(db)[0].id
    service = Service(data_dir, free_port()).start()
    context = browser.new_context(viewport={"width": 1440, "height": 1000}, timezone_id="Asia/Tokyo")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    expect = playwright_sync.expect
    packets = []

    def lose_first_response(route):
        packets.append(route.request.post_data_json)
        if len(packets) == 1:
            assert route.fetch().status == 200
            route.abort()
        else:
            route.continue_()

    try:
        page.route(f"**/api/sessions/{session}/correction", lose_first_response)
        page.goto(service.url + "/#stats")
        page.get_by_role("button", name="Saved session corrections", exact=True).click()
        correction = page.get_by_role("region", name="Saved session corrections", exact=True)
        correction.get_by_role("button", name="Correct saved time", exact=True).click()
        correction.get_by_label(re.compile("Interval 1 active seconds")).fill("1800")
        correction.get_by_label("Reason for correction", exact=True).fill("Synthetic correction: exclude an unattended break")
        correction.get_by_role("button", name="Review correction", exact=True).click()
        review = correction.get_by_role("region", name="Correction preview", exact=True)
        expect(review).to_contain_text("Balance: 0 → -30")
        expect(review).to_contain_text("Qualified → Below goal")
        assert all_rows(db) == original
        page.screenshot(path=evidence / "correction-01-preview-wide.png", full_page=True)
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "correction-02-preview-narrow.png", full_page=True)
        page.emulate_media(color_scheme="dark")
        page.screenshot(path=evidence / "correction-03-preview-dark.png", full_page=True)
        page.emulate_media(color_scheme="light")
        apply = review.get_by_role("button", name="Apply correction", exact=True)
        apply.focus(); page.keyboard.press("Enter")
        expect(correction.get_by_role("alert")).to_contain_text("Cannot reach")
        expect(correction.get_by_role("button", name="Retry correction", exact=True)).to_be_visible()
        page.screenshot(path=evidence / "correction-04-lost-response.png", full_page=True)
        assert shop.get().balance == -30 and shop.get().species[1].owned
        assert list_forest(db)[0].id == tree_id and list_forest(db)[0].outcome == "unfinished"
        after_apply = all_rows(db)
        page.reload()
        page.get_by_role("button", name="Saved session corrections", exact=True).click()
        correction.get_by_role("button", name="Retry correction", exact=True).click()
        expect(correction.get_by_text(re.compile("Correction saved"))).to_be_visible()
        assert packets[0] == packets[1] and all_rows(db) == after_apply
        assert http_json("GET", service.url + "/api/statistics")[1]["active_microseconds"] == HOUR // 2
        assert http_json("GET", service.url + "/api/streaks")[1]["days"][-1]["active_microseconds"] == HOUR // 2
        # The actual shop reflects the adjustment and blocks new purchases.
        page.get_by_role("link", name="Track", exact=True).click()
        expect(page.get_by_role("button", name="Buy Oak for 60 coins", exact=True)).to_be_disabled()
        expect(page.get_by_text("Session correction", exact=True)).to_have_count(1)
        page.get_by_role("link", name="Stats", exact=True).click()
        expect(correction.get_by_role("button", name="Refresh saved sessions", exact=True)).to_be_enabled()
        correction.get_by_text("Correction history (1)", exact=True).click()
        correction.get_by_role("button", name="Prepare reversal of latest correction", exact=True).click()
        expect(correction.get_by_label(re.compile("Interval 1 active seconds"))).to_have_value("3600")
        correction.get_by_role("button", name="Review correction", exact=True).click()
        expect(review).to_contain_text("Below goal → Qualified")
        review.get_by_role("button", name="Apply correction", exact=True).click()
        expect(correction.get_by_text("Correction history (2)", exact=True)).to_be_visible()
        assert shop.get().balance == 0 and list_forest(db)[0].outcome == "mature"
        assert list_forest(db)[0].id == tree_id
        page.screenshot(path=evidence / "correction-05-reversed.png", full_page=True)
        final = all_rows(db)
        for name in original.keys() - {"session_correction_baselines", "session_corrections", "coin_adjustments", "timer_intervals", "timer_sessions", "trees"}:
            assert final[name] == original[name]
        assert len(final["coin_adjustments"]) == len(final["session_corrections"]) == 2
        page.close()
        assert service.stop() == 0
        service = Service(data_dir, service.port).start()
        assert http_json("POST", f"{service.url}/api/sessions/{session}/correction", packets[0])[0] == 200
        assert all_rows(db) == final and len(list_saved_sessions(db)[0]["history"]) == 2
        assert errors == []
    finally:
        context.close()
        service.kill()
