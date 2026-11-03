"""Reading followed Google calendars: picker, cached events by day, event -> task."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.errors import InvalidInput
from backend.domain.google_reading import add_event_task, list_calendars, list_events, read_calendars, refresh_calendars, refresh_events, set_followed
from backend.domain.planning import list_placements
from backend.domain.tasks import get_task
from backend.storage.migrations import load_migrations

TODAY = date.today()
D1 = (TODAY + timedelta(days=1)).isoformat()
D3 = (TODAY + timedelta(days=3)).isoformat()


@pytest.fixture(autouse=True)
def _pacific(monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")


class FakeReader:
    def __init__(self) -> None:
        self.calendars = [
            {"id": "me@example.com", "summary": "Me", "primary": True, "backgroundColor": "#9fc6e7"},
            {"id": "work@group", "summary": "Work", "summaryOverride": "Lab job"},
            {"id": "own@group", "summary": "BearPlans"},  # the calendar BearPlans writes
        ]
        self.events = {
            "me@example.com": [
                {"id": "a", "summary": "Office hours", "location": "Soda 283", "htmlLink": "https://www.google.com/calendar/event?eid=a",
                 "start": {"dateTime": f"{D1}T15:00:00-08:00"}, "end": {"dateTime": f"{D1}T16:30:00-08:00"}},
                {"id": "b", "summary": "Trip", "start": {"date": D1}, "end": {"date": D3}},  # D1 and D2
                {"id": "c", "summary": "Cancelled", "status": "cancelled", "start": {"date": D1}, "end": {"date": D1}},
                {"id": "d", "summary": "Bad link", "htmlLink": "https://evil.example/x", "start": {"date": D3}, "end": {"date": D3}},
            ],
            "work@group": [{"id": "w", "summary": "Shift", "start": {"dateTime": f"{D3}T09:00:00-08:00"}, "end": {"dateTime": f"{D3}T12:00:00-08:00"}}],
        }
        self.reads: list[str] = []

    def calendar_list(self):
        return self.calendars

    def list_events(self, calendar_id, time_min, time_max):
        self.reads.append(calendar_id)
        return self.events.get(calendar_id, [])


def own_calendar(db):
    with db.write() as conn:
        conn.execute("INSERT INTO google_calendar (id, calendar_id, created_at) VALUES (1, 'own@group', '2026-11-01T00:00:00Z')")


def test_picker_lists_calendars_except_bearplans_own_and_follows_none_by_default(db):
    own_calendar(db)
    fake = FakeReader()
    read_calendars(db, fake)
    calendars = list_calendars(db)
    assert [c.summary for c in calendars] == ["Me", "Lab job"]
    assert calendars[0].is_primary and not any(c.followed for c in calendars)
    assert fake.reads == []


def test_followed_calendar_events_are_cached_by_day(db):
    fake = FakeReader()
    refresh_calendars(db, fake)
    set_followed(db, ["me@example.com"])
    refresh_events(db, fake)
    assert fake.reads == ["me@example.com"]
    d2 = (TODAY + timedelta(days=2)).isoformat()
    assert [e.summary for e in list_events(db, D1, D1)] == ["Trip", "Office hours"]
    assert [e.summary for e in list_events(db, d2, d2)] == ["Trip"]
    office = list_events(db, D1, D1)[1]
    assert office.location == "Soda 283" and office.html_link.startswith("https://www.google.com/calendar/")
    bad = [e for e in list_events(db, D3, D3) if e.summary == "Bad link"][0]
    assert bad.html_link == ""
    assert not any(e.summary == "Cancelled" for e in list_events(db, D1, D3))


def test_unfollowing_drops_cached_events(db):
    fake = FakeReader()
    refresh_calendars(db, fake)
    set_followed(db, ["me@example.com", "work@group"])
    refresh_events(db, fake)
    set_followed(db, ["work@group"])
    assert [e.summary for e in list_events(db, D1, D3)] == ["Shift"]
    with pytest.raises(InvalidInput):
        set_followed(db, ["nope"])


def test_event_becomes_a_planned_task_once(db):
    fake = FakeReader()
    refresh_calendars(db, fake)
    set_followed(db, ["me@example.com"])
    refresh_events(db, fake)
    added = add_event_task(db, "me@example.com", "a")
    assert added.planned and added.task.title == "Office hours" and added.task.estimate_minutes == 90
    assert "From Google Calendar (Me)" in added.task.notes and "Where: Soda 283" in added.task.notes
    [placement] = list_placements(db)
    assert placement.planned_date.isoformat() == D1 and placement.start_time is None  # no second calendar event
    again = add_event_task(db, "me@example.com", "a")
    assert again.task.id == added.task.id and len(list_placements(db)) == 1
    assert list_events(db, D1, D1)[1].task_id == added.task.id
    trip = add_event_task(db, "me@example.com", "b")
    assert get_task(db, trip.task.id).estimate_minutes is None and "all day" in trip.task.notes


def test_routes(db):
    fake = FakeReader()
    with TestClient(create_app(db, google_calendar_client=fake), base_url="http://127.0.0.1:8765") as client:
        assert client.get("/api/google/calendars").json() == []
        calendars = client.post("/api/google/calendars/refresh").json()
        assert [c["summary"] for c in calendars] == ["Me", "BearPlans", "Lab job"]  # no own calendar recorded here
        followed = client.put("/api/google/calendars", json={"calendar_ids": ["work@group"]}).json()
        assert [c["followed"] for c in followed] == [False, False, True]
        events = client.get("/api/google/events", params={"start": D1, "end": D3}).json()
        assert [e["summary"] for e in events] == ["Shift"]
        added = client.post("/api/google/events/add", json={"calendar_id": "work@group", "event_id": "w"}).json()
        assert added["task"]["title"] == "Shift" and added["planned"] is True
        assert client.get("/api/google/events", params={"start": D1, "end": "2027-12-31"}).status_code == 422


def test_reading_routes_need_google(db):
    with TestClient(create_app(db), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/google/calendars/refresh")
        assert response.status_code == 502 and response.json()["error"]["code"] == "google_not_connected"


def test_migration_0019_is_last():
    assert [m.name for m in load_migrations()][-1] == "google_calendar_reading"
