"""Pause / Resume automatic Google sync, safer Disconnect (cancel, wait, revoke) and the status summary."""

from __future__ import annotations

import json
import threading
import time

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.google_tasks import GoogleSyncService, is_paused, set_paused
from backend.domain.tasks import create_task
from backend.platform.google import GoogleAuth, GoogleUnavailable, client_file, token_file
from tests.test_google_tasks import FakeTasks

CLIENT = {"installed": {"client_id": "1-a.apps.googleusercontent.com", "client_secret": "s",
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}}


def _signed_in(scope="https://www.googleapis.com/auth/tasks https://www.googleapis.com/auth/calendar.app.created "
                     "https://www.googleapis.com/auth/calendar.calendarlist.readonly https://www.googleapis.com/auth/calendar.events.readonly"):
    client_file().parent.mkdir(parents=True, exist_ok=True)
    client_file().write_text(json.dumps(CLIENT))
    token_file().write_text(json.dumps({"refresh_token": "refresh-1", "scope": scope}))


def _app(db, fake=None):
    return TestClient(create_app(db, google_tasks_client=fake or FakeTasks()), base_url="http://127.0.0.1:8765")


def test_pause_survives_restart_and_stops_only_automatic_sync(db):
    fake = FakeTasks()
    create_task(db, "Essay")
    with _app(db, fake) as client:
        state = client.post("/api/google/pause").json()
        assert state["tasks"]["paused_at"] and state["status"] == "not_set_up"  # No sign-in file in this test.
        first = state["tasks"]["paused_at"]
        assert client.post("/api/google/pause").json()["tasks"]["paused_at"] == first  # Pausing again keeps the time.
    service = GoogleSyncService(db, lambda: fake, GoogleUnavailable, lambda: True)
    assert is_paused(db)  # A new service (restart) is still paused.
    assert service.sync_now(automatic=True) is None and fake.calls == []
    with _app(db, fake) as client:
        assert client.post("/api/google/tasks/sync").status_code == 200  # Sync now still runs once ...
        assert fake.calls and client.get("/api/google").json()["tasks"]["paused_at"] == first  # ... and stays paused.
        assert client.post("/api/google/resume").json()["tasks"]["paused_at"] is None
    assert service.sync_now(automatic=True) is not None  # Automatic sync runs again after Resume.


def test_background_worker_does_nothing_while_paused(db, monkeypatch):
    from backend.domain import google_tasks

    monkeypatch.setattr(google_tasks, "NUDGE_DELAY_SECONDS", 0)
    fake = FakeTasks()
    create_task(db, "Essay")
    set_paused(db, True)
    service = GoogleSyncService(db, lambda: fake, GoogleUnavailable, lambda: True)
    service.start()
    try:
        service.nudge()
        time.sleep(0.3)
        assert fake.calls == []
        set_paused(db, False)
        service.nudge()
        deadline = time.monotonic() + 3
        while not fake.calls and time.monotonic() < deadline:
            time.sleep(0.02)
        assert fake.calls
    finally:
        service.stop()


def test_pause_waits_for_a_running_sync(db):
    release, started = threading.Event(), threading.Event()

    class Slow(FakeTasks):
        def lists(self):
            started.set()
            release.wait(5)
            return super().lists()
    fake = Slow()
    with _app(db, fake) as client:
        service = client.app.state.google_sync
        worker = threading.Thread(target=service.sync_now)
        worker.start()
        assert started.wait(2) and service.syncing
        threading.Timer(0.2, release.set).start()
        state = client.post("/api/google/pause").json()
        assert not service.syncing and state["tasks"]["paused_at"]  # Returned only after the sync finished.
        worker.join(2)
        assert service.sync_now(automatic=True) is None


def test_status_summary(db):
    with _app(db) as client:
        assert client.get("/api/google").json()["status"] == "not_set_up"
        client_file().parent.mkdir(parents=True, exist_ok=True)
        client_file().write_text(json.dumps(CLIENT))
        assert client.get("/api/google").json()["status"] == "signed_out"
        _signed_in(scope="https://www.googleapis.com/auth/tasks")
        assert client.get("/api/google").json()["status"] == "needs_attention"  # Permissions missing.
        _signed_in()
        assert client.get("/api/google").json()["status"] == "working"
        client.post("/api/google/pause")
        assert client.get("/api/google").json()["status"] == "paused"


def test_disconnect_deletes_locally_then_revokes(db, revoked_tokens):
    _signed_in()
    with _app(db) as client:
        state = client.post("/api/google/disconnect").json()
        assert state["revoked"] is True and state["connected"] is False and not token_file().exists()
        assert revoked_tokens == ["refresh-1"]
        assert client.post("/api/google/disconnect").json()["revoked"] is None  # Nothing left to revoke.
        assert "refresh-1" not in client.get("/api/google").text


def test_disconnect_reports_when_google_could_not_be_asked(db, monkeypatch):
    from backend.platform import google

    monkeypatch.setattr(google, "revoke_token", lambda token: False)
    _signed_in()
    with _app(db) as client:
        state = client.post("/api/google/disconnect").json()
        assert state["revoked"] is False and not token_file().exists()  # Still signed out here.


def test_removing_the_sign_in_file_revokes_too(client, revoked_tokens):
    _signed_in()
    assert client.delete("/api/connections/google").json()["google"]["connected"] is False
    assert revoked_tokens == ["refresh-1"]


def test_a_sign_in_finishing_after_disconnect_is_dropped(monkeypatch, revoked_tokens):
    """The late-callback race: Disconnect wins, the late token is not saved and is revoked."""
    from backend.platform import google

    client_file().parent.mkdir(parents=True, exist_ok=True)
    client_file().write_text(json.dumps(CLIENT))
    exchange_started, finish_exchange = threading.Event(), threading.Event()

    def slow_exchange(url, fields):
        exchange_started.set()
        finish_exchange.wait(5)
        return {"refresh_token": "late-token", "access_token": "a", "expires_in": 3600, "scope": ""}
    monkeypatch.setattr(google, "_post_form", slow_exchange)
    auth = GoogleAuth()
    url = auth.start_sign_in()
    redirect = [part for part in url.split("&") if part.startswith("redirect_uri=")][0]
    port = int(redirect.rsplit("%3A", 1)[1])
    state = [part for part in url.split("&") if part.startswith("state=")][0].split("=", 1)[1]
    import urllib.request
    urllib.request.urlopen(f"http://127.0.0.1:{port}/?code=c&state={state}", timeout=5).read()
    assert exchange_started.wait(5)
    assert auth.disconnect() is None  # Not signed in yet, so nothing to revoke now.
    finish_exchange.set()
    deadline = time.monotonic() + 5
    while auth.sign_in_pending() and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not token_file().exists() and not auth.connected()
    assert revoked_tokens == ["late-token"]
    assert "cancelled" in (auth.last_sign_in_error() or "")
