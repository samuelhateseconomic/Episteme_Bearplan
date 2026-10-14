"""Real-browser journey against the built interface and a real service process.

Uses an installed Chrome or Edge through Playwright (no browser download needed).
Set BEARPLANS_E2E_CHANNEL to force a channel and BEARPLANS_EVIDENCE_DIR to keep screenshots.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from backend.platform.paths import FRONTEND_DIST
from tests.conftest import Service, free_port

playwright_sync = pytest.importorskip("playwright.sync_api")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not (FRONTEND_DIST / "index.html").is_file(), reason="frontend not built"),
]

CHANNELS = [os.environ["BEARPLANS_E2E_CHANNEL"]] if os.environ.get("BEARPLANS_E2E_CHANNEL") else ["chrome", "msedge", None]


@pytest.fixture
def browser() -> Iterator[object]:
    with playwright_sync.sync_playwright() as p:
        errors = []
        for channel in CHANNELS:
            try:
                browser = p.chromium.launch(channel=channel) if channel else p.chromium.launch()
                break
            except playwright_sync.Error as exc:
                errors.append(f"{channel or 'bundled chromium'}: {str(exc).splitlines()[0]}")
        else:
            pytest.skip("no Chromium-family browser available: " + "; ".join(errors))
        yield browser
        browser.close()


@pytest.fixture
def evidence(tmp_path: Path) -> Path:
    directory = Path(os.environ.get("BEARPLANS_EVIDENCE_DIR") or tmp_path / "evidence")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def no_horizontal_overflow(page) -> bool:
    return page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")


def test_enter_task_restart_service_and_still_see_it(browser, evidence: Path, tmp_path: Path) -> None:
    expect = playwright_sync.expect
    data_dir = tmp_path / "BearPlans"
    port = free_port()
    service = Service(data_dir, port).start()
    try:
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        console_errors: list[str] = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(service.url)
        expect(page).to_have_title("BearPlans")
        expect(page.get_by_text("No tasks yet")).to_be_visible()
        title_input = page.get_by_label("Task title")
        add = page.get_by_role("button", name="Add task")
        expect(title_input).to_be_focused()
        expect(add).to_be_disabled()
        page.screenshot(path=evidence / "01-empty-wide.png")

        title_input.fill("   ")
        expect(add).to_be_disabled()
        title_input.fill("Read chapter 4 for Math 55")
        title_input.press("Enter")
        expect(page.get_by_role("listitem").filter(has_text="Read chapter 4 for Math 55")).to_be_visible()
        expect(page.get_by_role("status")).to_have_text("Saved “Read chapter 4 for Math 55”.")
        expect(title_input).to_have_value("")
        expect(title_input).to_be_focused()

        title_input.fill("Problem set 2")
        add.click()
        expect(page.get_by_role("heading", name="Saved tasks (2)")).to_be_visible()
        page.screenshot(path=evidence / "02-two-tasks-wide.png")

        assert service.stop() == 0
        service = Service(data_dir, port).start()
        page.reload()
        expect(page.get_by_role("heading", name="Saved tasks (2)")).to_be_visible()
        items = page.get_by_role("listitem")
        expect(items.nth(0)).to_contain_text("Read chapter 4 for Math 55")
        expect(items.nth(1)).to_contain_text("Problem set 2")
        page.screenshot(path=evidence / "03-after-restart-wide.png")
        assert console_errors == []

        page.set_viewport_size({"width": 375, "height": 720})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "04-narrow.png", full_page=True)

        page.emulate_media(color_scheme="dark")
        page.set_viewport_size({"width": 1280, "height": 800})
        page.screenshot(path=evidence / "05-dark-wide.png")
        page.emulate_media(color_scheme="light")

        service.kill()
        title_input.fill("Saved while offline?")
        title_input.press("Enter")
        expect(page.get_by_role("alert")).to_contain_text("Cannot reach the BearPlans service")
        expect(title_input).to_have_value("Saved while offline?")
        page.screenshot(path=evidence / "06-service-down.png")
    finally:
        service.kill()
