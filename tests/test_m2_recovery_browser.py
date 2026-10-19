"""Recovery decisions in a real browser with a disposable service/database."""

import sqlite3
from uuid import uuid4

import pytest

from tests.conftest import Service, free_port, http_json
from tests.test_e2e_browser import browser, evidence, no_horizontal_overflow, playwright_sync

pytestmark = pytest.mark.e2e


def test_recover_same_session_retry_restart_and_finish(browser, evidence, tmp_path):
    expect = playwright_sync.expect
    service = Service(tmp_path / "RecoveryJourney", free_port()).start()
    context = browser.new_context(viewport={"width": 1440, "height": 950})
    try:
        _, task = http_json("POST", service.url + "/api/tasks", {"title": "Synthetic recovery work"})
        _, started = http_json("POST", service.url + "/api/timer/start", {
            "task_id": task["id"], "duration_minutes": 10, "operation_id": str(uuid4()),
        })
        session_id = started["active_session"]["id"]
        # Graceful process restart still cannot establish service-off work time.
        assert service.stop() == 0
        service = Service(service.data_dir, service.port).start()
        _, reviewed = http_json("GET", service.url + "/api/timer")
        review = reviewed["active_session"]
        assert review["state"] == "needs_review"
        confirmed = review["active_seconds"]
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(service.url + "/#track")
        current = page.get_by_role("region", name="Current session")
        expect(current).to_contain_text("Needs review")
        expect(current).to_contain_text("Confirmed active time")
        continue_button = current.get_by_role("button", name="Continue with confirmed time", exact=True)
        expect(continue_button).to_be_enabled()
        page.screenshot(path=evidence / "recovery-01-review-wide.png", full_page=True)

        # A failed write keeps the same decision/key, and leaves saved time intact.
        requests = []

        def fail_before_commit(route):
            requests.append(route.request.post_data_json)
            route.abort()

        url = f"**/api/timer/{session_id}/recover"
        page.route(url, fail_before_commit)
        continue_button.click()
        expect(page.get_by_role("alert")).to_be_visible()
        expect(continue_button).to_be_enabled()
        assert http_json("GET", service.url + "/api/timer")[1]["active_session"]["active_seconds"] == confirmed
        page.unroute(url, fail_before_commit)

        def lose_committed_response(route):
            requests.append(route.request.post_data_json)
            response = route.fetch()
            assert response.status == 200
            route.abort()

        page.route(url, lose_committed_response)
        continue_button.focus()
        page.keyboard.press("Enter")
        expect(current.get_by_role("button", name="Pause", exact=True)).to_be_visible()
        assert len(requests) == 2 and requests[0] == requests[1]
        assert requests[1]["resolution"] == "resume" and requests[1]["discard_uncertain"] is True
        _, resumed = http_json("GET", service.url + "/api/timer")
        active = resumed["active_session"]
        assert active["id"] == session_id and active["task_id"] == task["id"]
        assert active["recovery"]["resolution"] == "resume"
        assert active["recovery"]["confirmed_active_seconds"] == confirmed
        # Replaying the acknowledged decision cannot open another interval.
        assert http_json("POST", service.url + f"/api/timer/{session_id}/recover", requests[1])[0] == 200
        current.get_by_role("button", name="Pause", exact=True).click()
        expect(current.get_by_role("button", name="Resume", exact=True)).to_be_visible()
        _, paused = http_json("GET", service.url + "/api/timer")
        paused_credit = paused["active_session"]["active_seconds"]
        assert service.stop() == 0
        service = Service(service.data_dir, service.port).start()
        page.reload()
        expect(current.get_by_role("button", name="Resume", exact=True)).to_be_visible()
        assert http_json("GET", service.url + "/api/timer")[1]["active_session"]["active_seconds"] == paused_credit
        current.get_by_role("button", name="Resume", exact=True).click()
        expect(current.get_by_role("button", name="Pause", exact=True)).to_be_visible()
        service.kill()
        service = Service(service.data_dir, service.port).start()
        page.reload()
        expect(current).to_contain_text("Needs review")
        page.set_viewport_size({"width": 375, "height": 850})
        assert no_horizontal_overflow(page)
        page.screenshot(path=evidence / "recovery-02-review-narrow.png", full_page=True)
        page.unroute(url, lose_committed_response)
        current.get_by_role("button", name="Save confirmed time and finish", exact=True).click()
        expect(page.get_by_role("region", name="Saved session outcome")).to_contain_text("Interrupted")
        page.screenshot(path=evidence / "recovery-03-saved-narrow.png", full_page=True)
        _, finished = http_json("GET", service.url + "/api/timer")
        assert finished["active_session"] is None
        assert finished["last_session"]["id"] == session_id
        assert http_json("GET", service.url + "/api/tasks")[1]["tasks"] == [task]
        with sqlite3.connect(service.data_dir / "bearplans.sqlite3") as conn:
            assert conn.execute("SELECT COUNT(*) FROM timer_sessions").fetchone()[0] == 1
            assert conn.execute("SELECT COUNT(*) FROM timer_intervals WHERE ended_at IS NULL").fetchone()[0] == 0
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert errors == []
    finally:
        context.close()
        service.kill()
