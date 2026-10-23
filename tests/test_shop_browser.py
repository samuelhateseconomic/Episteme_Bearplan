"""Real Chrome coins/shop journey with disposable data and simulated seed credit.

The seed earns through shared timer functions with a fake clock; all browser
purchases, starts, retries and process restarts use the real local service.
No sleep or independently timed hardware acceptance is claimed here.
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


def test_shop_lost_response_reload_stale_balance_species_and_restart(browser, evidence, tmp_path, monkeypatch):
    expect = playwright_sync.expect
    # Exercise the configured rate through a real earned session, not a direct
    # ledger credit. The service inherits the same policy for subsequent starts.
    monkeypatch.setenv("BEARPLANS_COINS_PER_MINUTE", "60")
    data_dir = tmp_path / "ShopJourney"
    data_dir.mkdir()
    db = open_database(data_dir / DATABASE_FILENAME)
    task = create_task(db, "Synthetic shop work", notes="Preserve this task")
    clock = FakeClock()
    timer = TimerService(db, clock)
    seeded = timer.start(task.id, 1, str(uuid4())).active_session
    saved = observed(timer, clock, 60).last_session
    assert saved.coin_award == 60

    service = Service(data_dir, free_port()).start()
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    try:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url + "/#track")
        shop = page.get_by_role("region", name="Tree shop", exact=True)
        expect(shop).to_contain_text("Your coins: 60")
        expect(shop.get_by_role("button", name="Buy Cherry for 120 coins", exact=True)).to_be_disabled()
        expect(page.get_by_label("Tree species", exact=True)).to_have_value("pine")
        tasks_before = http_json("GET", service.url + "/api/tasks")[1]
        initial_shop = http_json("GET", service.url + "/api/shop")[1]
        page.screenshot(path=evidence / "shop-01-earned-wide.png", full_page=True)

        # Commit a purchase but lose its response AND the following wallet read.
        # Reloading must retain the exact pending request, not invent another ID.
        blocked = {"reads": False}
        purchase_payloads = []

        def shop_read(route):
            if blocked["reads"]:
                route.abort()
            else:
                route.continue_()

        def lose_purchase(route):
            purchase_payloads.append(route.request.post_data_json)
            assert route.fetch().status == 201
            blocked["reads"] = True
            route.abort()

        page.route("**/api/shop", shop_read)
        page.route("**/api/shop/purchases", lose_purchase)
        buy = shop.get_by_role("button", name="Buy Birch for 30 coins", exact=True)
        buy.focus()
        page.keyboard.press("Enter")
        retry = shop.get_by_role("button", name="Retry Birch purchase for 30 coins", exact=True)
        expect(retry).to_be_enabled()
        expect(shop).to_contain_text("Your purchase request is kept")
        assert len(purchase_payloads) == 1
        pending_before = page.evaluate("sessionStorage.getItem('bearplans.shop.pending')")
        assert pending_before is not None
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "shop-02-uncertain-narrow.png", full_page=True)
        page.reload()
        expect(retry).to_be_enabled()
        assert page.evaluate("sessionStorage.getItem('bearplans.shop.pending')") == pending_before
        page.unroute("**/api/shop/purchases", lose_purchase)

        def record_retry(route):
            purchase_payloads.append(route.request.post_data_json)
            # A focus/last-session refresh may acknowledge the owned species.
            # Keep wallet reads unavailable until this intended replay is sent.
            blocked["reads"] = False
            route.continue_()

        page.route("**/api/shop/purchases", record_retry)
        with page.expect_request(lambda request: request.method == "POST" and request.url.endswith("/api/shop/purchases")):
            # Reload can schedule another last-session wallet refresh between
            # focus and Enter, briefly disabling this control. Click waits for
            # actionability; the first purchase above still covers keyboard use.
            retry.click()
        expect(shop).to_contain_text("Your coins: 30")
        expect(retry).to_have_count(0)
        expect(shop.locator(".shop-species").filter(has_text="Birch")).to_contain_text("Owned")
        assert len(purchase_payloads) == 2 and purchase_payloads[0] == purchase_payloads[1]
        assert page.evaluate("sessionStorage.getItem('bearplans.shop.pending')") is None
        expect(shop.get_by_role("button", name="Buy Cherry for 120 coins", exact=True)).to_be_disabled()

        # A second tab still displaying the old 60-coin view tries a 60-coin Oak.
        # Its real mutation must reject; refreshed balance/controls reflect 30.
        stale_page = context.new_page()
        stale_reads = {"serve": True}

        def old_wallet(route):
            if stale_reads["serve"]:
                route.fulfill(json=initial_shop)
            else:
                route.continue_()

        def stale_purchase(route):
            stale_reads["serve"] = False
            route.continue_()

        stale_page.route("**/api/shop", old_wallet)
        stale_page.route("**/api/shop/purchases", stale_purchase)
        stale_page.goto(service.url + "/#track")
        stale_shop = stale_page.get_by_role("region", name="Tree shop", exact=True)
        expect(stale_shop).to_contain_text("Your coins: 60")
        stale_shop.get_by_role("button", name="Buy Oak for 60 coins", exact=True).click()
        expect(stale_shop).to_contain_text("not enough available coins")
        expect(stale_shop).to_contain_text("Your coins: 30")
        expect(stale_shop.get_by_role("button", name="Buy Oak for 60 coins", exact=True)).to_be_disabled()
        stale_page.close()

        # The owned species is selected before starting through keyboard controls
        # and locked into a real new countdown. Early finish saves it and 0 coins.
        page.bring_to_front()
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.get_by_label("Task to track", exact=True).select_option(task.id)
        page.get_by_label("Duration (minutes)", exact=True).fill("1")
        species = page.get_by_label("Tree species", exact=True)
        expect(species.get_by_role("option", name="Birch", exact=True)).to_have_count(1)
        expect(species).to_be_enabled()
        species.select_option("birch")
        species.focus()
        page.keyboard.press("Tab")
        expect(species).to_have_value("birch")
        expect(page.get_by_role("button", name="Start countdown", exact=True)).to_be_focused()
        page.keyboard.press("Enter")
        current = page.get_by_role("region", name="Current session", exact=True)
        expect(current.get_by_role("img", name="Birch seedling", exact=True)).to_be_visible()
        expect(species).to_have_count(0)
        current.get_by_role("button", name="Pause", exact=True).click()
        expect(current.get_by_role("button", name="Resume", exact=True)).to_be_visible()
        _, paused = http_json("GET", service.url + "/api/timer")
        birch = paused["active_session"]
        assert birch["tree"]["species"] == "birch" and birch["coin_award"] is None
        page.reload()
        expect(current.get_by_role("img", name="Birch seedling", exact=True)).to_be_visible()
        expect(current.get_by_role("button", name="Resume", exact=True)).to_be_visible()
        page.screenshot(path=evidence / "shop-03-owned-active-wide.png", full_page=True)
        current.get_by_role("button", name="Finish early", exact=True).click()
        outcome = page.get_by_role("region", name="Saved session outcome", exact=True)
        expect(outcome).to_contain_text("Unfinished Birch")
        expect(outcome).to_contain_text("Earned 0 coins")
        expect(shop).to_contain_text("Your coins: 30")
        forest = page.get_by_role("region", name="Forest collection", exact=True)
        expect(forest.get_by_role("img", name="Birch seedling", exact=True)).to_be_visible()
        expect(forest.get_by_role("img", name="Pine mature", exact=True)).to_be_visible()
        page.screenshot(path=evidence / "shop-04-owned-forest-wide.png", full_page=True)
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "shop-05-owned-forest-narrow.png", full_page=True)
        page.emulate_media(color_scheme="dark")
        page.screenshot(path=evidence / "shop-06-owned-forest-dark.png", full_page=True)

        _, shop_before_restart = http_json("GET", service.url + "/api/shop")
        _, forest_before_restart = http_json("GET", service.url + "/api/forest")
        with db.read() as conn:
            assert conn.execute("SELECT COUNT(*) FROM shop_operations").fetchone()[0] == 1
            assert conn.execute("SELECT COUNT(*) FROM owned_species").fetchone()[0] == 1
            awards = {r[0]: r[1] for r in conn.execute(
                "SELECT session_id, amount FROM coin_ledger WHERE kind = 'session_award'",
            )}
            assert awards == {seeded.id: 60, birch["id"]: 0}
            assert [tuple(r) for r in conn.execute(
                "SELECT amount, species FROM coin_ledger WHERE kind = 'purchase'",
            )] == [(-30, "birch")]
        assert http_json("GET", service.url + "/api/tasks")[1] == tasks_before
        page.close()
        assert service.stop() == 0
        service = Service(data_dir, service.port).start()
        assert http_json("GET", service.url + "/api/shop")[1] == shop_before_restart
        assert http_json("GET", service.url + "/api/forest")[1] == forest_before_restart
        page = context.new_page()
        page.goto(service.url + "/#track")
        expect(page.get_by_role("region", name="Tree shop", exact=True)).to_contain_text("Your coins: 30")
        expect(page.get_by_label("Tree species", exact=True).get_by_role("option", name="Birch", exact=True)).to_have_count(1)
        with sqlite3.connect(data_dir / DATABASE_FILENAME) as conn:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        assert errors == []
    finally:
        context.close()
        service.kill()
