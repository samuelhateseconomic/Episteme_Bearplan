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
                browser = p.chromium.launch(channel=channel, args=["--disable-gpu"])
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


def test_project_task_subtask_journey_survives_restart(browser, evidence: Path, tmp_path: Path) -> None:
    """M1 acceptance, in a real browser: build a project with a task and subtasks,
    complete them, restart the service, and find everything exactly as it was."""
    expect = playwright_sync.expect
    data_dir = tmp_path / "BearPlans"
    port = free_port()
    service = Service(data_dir, port).start()
    try:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        console_errors: list[str] = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(service.url)
        expect(page).to_have_title("BearPlans")
        # Migration 0002 always leaves a default project, so there is somewhere to start.
        expect(page.get_by_role("button", name="Inbox", exact=True)).to_be_visible()
        expect(page.get_by_text("No tasks in this project yet.")).to_be_visible()
        page.screenshot(path=evidence / "01-empty-wide.png")

        page.get_by_label("New project").fill("Math 55")
        page.get_by_role("button", name="Add project").click()
        expect(page.get_by_role("heading", name="Math 55")).to_be_visible()
        page.get_by_role("button", name="Rename “Math 55”").click()
        page.get_by_label("Rename “Math 55”").fill("Math 55 — Honors")
        page.get_by_role("button", name="Save name").click()
        expect(page.get_by_role("heading", name="Math 55 — Honors")).to_be_visible()

        page.get_by_label("Title").first.fill("Write PS7")
        page.get_by_label("Deadline").first.fill("2026-10-20")
        page.get_by_label("Estimate (minutes)").first.fill("90")
        page.get_by_label("Notes").first.fill("Ch.4 and Ch.5 exercises.")
        page.get_by_role("button", name="Add task").click()
        expect(page.get_by_text("Write PS7")).to_be_visible()
        expect(page.get_by_text("Due Oct 20, 2026")).to_be_visible()
        expect(page.get_by_text("1 h 30 min")).to_be_visible()

        for subtask in ("read ch.4", "draft the proof"):
            page.get_by_role("button", name="Add subtask").first.click()
            page.get_by_label("Title").last.fill(subtask)
            page.get_by_role("button", name="Add subtask").last.click()
            expect(page.get_by_text(subtask)).to_be_visible()

        parent_box = page.get_by_label("Write PS7")
        # The parent's completion is derived, so it offers no control of its own.
        expect(parent_box).to_be_disabled()
        expect(page.get_by_text("0 of 2 subtasks done")).to_be_visible()

        # The checkbox reflects what the service stored, so it flips after the round
        # trip rather than on the click; the expectations below retry until it does.
        page.get_by_label("read ch.4").click()
        expect(page.get_by_text("1 of 2 subtasks done")).to_be_visible()
        expect(parent_box).not_to_be_checked()
        page.get_by_label("draft the proof").click()
        expect(page.get_by_text("2 of 2 subtasks done")).to_be_visible()
        expect(parent_box).to_be_checked()
        expect(page.get_by_text("2 of 2 work items complete")).to_be_visible()
        # Editing a subtask exercises the same fields as a task, without changing identity.
        child_row = page.locator(".subtasks > .task").filter(has_text="read ch.4")
        child_row.get_by_role("button", name="Edit", exact=True).click()
        child_row.get_by_label("Title").fill("read ch.4 carefully")
        child_row.get_by_label("Notes").fill("Check definitions.")
        child_row.get_by_label("Deadline").fill("2026-10-19")
        child_row.get_by_label("Estimate (minutes)").fill("25")
        child_row.get_by_role("button", name="Save changes").click()
        expect(page.get_by_text("Check definitions.")).to_be_visible()
        # Keyboard editing of the root task also survives a real process restart.
        page.get_by_role("button", name="Edit", exact=True).first.click()
        page.locator(".tasks > .task > .task-form").get_by_label("Notes").fill("Ch.4 and Ch.5 exercises, final pass.")
        page.get_by_role("button", name="Save changes").click()
        expect(page.get_by_text("Ch.4 and Ch.5 exercises, final pass.")).to_be_visible()
        page.screenshot(path=evidence / "02-derived-completion-wide.png", full_page=True)

        assert service.stop() == 0
        service = Service(data_dir, port).start()
        page.reload()
        page.get_by_role("button", name="Math 55 — Honors", exact=True).click()

        expect(page.get_by_text("Write PS7")).to_be_visible()
        expect(page.get_by_text("Due Oct 20, 2026")).to_be_visible()
        expect(page.get_by_text("Ch.4 and Ch.5 exercises, final pass.")).to_be_visible()
        expect(page.get_by_text("Check definitions.")).to_be_visible()
        expect(page.get_by_text("Due Oct 19, 2026")).to_be_visible()
        expect(page.get_by_text("25 min")).to_be_visible()
        expect(page.get_by_text("2 of 2 subtasks done")).to_be_visible()
        expect(page.get_by_label("Write PS7")).to_be_checked()
        expect(page.get_by_label("read ch.4 carefully")).to_be_checked()
        page.screenshot(path=evidence / "03-after-restart-wide.png", full_page=True)
        assert console_errors == []

        page.set_viewport_size({"width": 375, "height": 720})
        page.reload()
        page.get_by_role("button", name="Math 55 — Honors", exact=True).click()
        expect(page.get_by_text("2 of 2 subtasks done")).to_be_visible()
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "04-narrow.png", full_page=True)

        page.emulate_media(color_scheme="dark")
        page.set_viewport_size({"width": 1280, "height": 900})
        page.reload()
        page.get_by_role("button", name="Math 55 — Honors", exact=True).click()
        expect(page.get_by_text("2 of 2 subtasks done")).to_be_visible()
        page.screenshot(path=evidence / "05-dark-wide.png", full_page=True)
        page.emulate_media(color_scheme="light")
        page.reload()
        page.get_by_role("button", name="Math 55 — Honors", exact=True).click()

        # Reopening and adding work must both make a completed container incomplete.
        page.get_by_label("draft the proof").click()
        expect(page.get_by_label("Write PS7")).not_to_be_checked()
        expect(page.get_by_text("1 of 2 work items complete")).to_be_visible()
        page.get_by_label("draft the proof").click()
        page.get_by_role("button", name="Add subtask", exact=True).click()
        page.get_by_label("Title").last.fill("Additional parent work")
        page.get_by_role("button", name="Add subtask", exact=True).last.click()
        expect(page.get_by_text("2 of 3 subtasks done")).to_be_visible()
        expect(page.get_by_label("Write PS7")).not_to_be_checked()
        for title in ("Additional parent work", "draft the proof", "read ch.4 carefully"):
            row = page.locator(".subtasks > .task").filter(has_text=title)
            row.get_by_role("button", name="Edit", exact=True).click()
            row.get_by_role("button", name="Remove subtask", exact=True).click()
            row.get_by_role("button", name="Confirm removal", exact=True).click()
            expect(page.get_by_label(title, exact=True)).to_have_count(0)
        expect(page.get_by_label("Write PS7")).to_be_enabled()
        expect(page.get_by_label("Write PS7")).not_to_be_checked()
        expect(page.get_by_text("0 of 1 work items complete")).to_be_visible()
        page.get_by_label("Write PS7").click()
        expect(page.get_by_text("1 of 1 work items complete")).to_be_visible()
        assert service.stop() == 0
        service = Service(data_dir, port).start()
        page.reload()
        page.get_by_role("button", name="Math 55 — Honors", exact=True).click()
        expect(page.get_by_label("Write PS7")).to_be_checked()
        expect(page.get_by_label("Write PS7")).to_be_enabled()
        page.screenshot(path=evidence / "07-after-last-child-removal.png")

        service.kill()
        page.get_by_label("Title").first.fill("Saved while offline?")
        page.get_by_role("button", name="Add task").click()
        expect(page.get_by_role("alert").first).to_contain_text("Cannot reach the BearPlans service")
        expect(page.get_by_label("Title").first).to_have_value("Saved while offline?")
        page.screenshot(path=evidence / "06-service-down.png")
    finally:
        service.kill()


def test_long_text_layout_and_keyboard_creation(browser, evidence: Path, tmp_path: Path) -> None:
    expect = playwright_sync.expect
    service = Service(tmp_path / "BearPlans", free_port()).start()
    try:
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(service.url)
        page.get_by_label("New project").fill("P" * 100)
        page.get_by_label("New project").press("Enter")
        expect(page.get_by_role("heading", name="P" * 100)).to_be_visible()
        page.get_by_label("Title").fill("T" * 200)
        page.get_by_label("Notes").fill("N" * 2000)
        page.get_by_label("Title").press("Enter")
        expect(page.get_by_label("T" * 200, exact=True)).to_be_visible()
        expect(page.get_by_label("Title")).to_have_value("")
        expect(page.get_by_label("Title")).to_be_focused()
        for width in (1280, 375):
            page.set_viewport_size({"width": width, "height": 900})
            page.reload()
            page.get_by_role("button", name="P" * 100, exact=True).click()
            expect(page.get_by_label("T" * 200, exact=True)).to_be_visible()
            assert no_horizontal_overflow(page)
            page.screenshot(path=evidence / f"08-long-text-{width}.png", full_page=True)
    finally:
        service.kill()
