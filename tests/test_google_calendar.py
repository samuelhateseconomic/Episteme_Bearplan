"""Planned start times and the BearPlans Google Calendar, against an in-memory fake."""
from __future__ import annotations

import itertools
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.errors import InvalidInput
from backend.domain.google_calendar import start_instant, sync_calendar
from backend.domain.planning import create_placement, move_placement, remove_placement, set_placement_time
from backend.domain.projects import create_project
from backend.domain.tasks import create_task, set_task_completion
from backend.storage.migrations import load_migrations

DAY = (date.today() + timedelta(days=2)).isoformat()


@pytest.fixture(autouse=True)
def _pacific(monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")


class FakeCalendar:
    def __init__(self) -> None:
        self.ids = (f"e{n}" for n in itertools.count(1))
        self.calendars: dict[str, dict[str, dict]] = {}
        self.names: dict[str, str] = {}
        self.calls: list[str] = []

    def calendar_exists(self, calendar_id):
        return calendar_id in self.calendars

    def insert_calendar(self, summary):
        self.calls.append("insert_calendar")
        calendar_id = f"cal{len(self.names) + 1}@group.calendar.google.com"
        self.calendars[calendar_id] = {}
        self.names[calendar_id] = summary
        return {"id": calendar_id, "summary": summary}

    def events(self, calendar_id):
        return [dict(event) for event in self.calendars[calendar_id].values()]

    def insert_event(self, calendar_id, body):
        self.calls.append("insert_event")
        event = {"id": next(self.ids), "status": "confirmed", **body}
        self.calendars[calendar_id][event["id"]] = event
        return dict(event)

    def patch_event(self, calendar_id, event_id, body):
        self.calls.append("patch_event")
        self.calendars[calendar_id][event_id].update(body)
        return dict(self.calendars[calendar_id][event_id])

    def delete_event(self, calendar_id, event_id):
        self.calls.append("delete_event")
        self.calendars[calendar_id][event_id]["status"] = "cancelled"

    def live(self):
        return [event for events in self.calendars.values() for event in events.values() if event["status"] != "cancelled"]


def timed(db, title="Problem set", time="14:00", **task_fields):
    task = create_task(db, title, **task_fields)
    placement = create_placement(db, task.id, DAY)
    return task, set_placement_time(db, placement.id, time)


def test_timed_placement_becomes_an_event_with_a_30_minute_reminder(db):
    fake = FakeCalendar()
    project = create_project(db, "MATH 54")
    parent = create_task(db, "Midterm prep", project_id=project.id)
    child = create_task(db, "Practice exam", parent_id=parent.id, estimate_minutes=90, notes="Bring calculator")
    placement = set_placement_time(db, create_placement(db, child.id, DAY).id, "14:00")
    create_placement(db, create_task(db, "No time").id, DAY)  # untimed: no event

    sync_calendar(db, fake)

    assert list(fake.names.values()) == ["BearPlans"]
    [event] = fake.live()
    assert event["summary"] == "Practice exam"
    assert event["description"].startswith("MATH 54 › Midterm prep\n\nBring calculator")
    start = datetime.fromisoformat(event["start"]["dateTime"])
    assert start == datetime.fromisoformat(f"{DAY}T14:00:00").replace(tzinfo=start_instant(DAY, "14:00").tzinfo)
    assert start.utcoffset() in (timedelta(hours=-7), timedelta(hours=-8))
    assert datetime.fromisoformat(event["end"]["dateTime"]) - start == timedelta(minutes=90)
    assert event["reminders"] == {"useDefault": False, "overrides": [{"method": "popup", "minutes": 30}]}
    assert event["extendedProperties"]["private"]["bearplansPlacement"] == placement.id


def test_no_calendar_is_created_without_timed_tasks(db):
    fake = FakeCalendar()
    create_placement(db, create_task(db, "Untimed").id, DAY)
    sync_calendar(db, fake)
    assert fake.calls == []


def test_second_sync_changes_nothing_and_default_length_is_30_minutes(db):
    fake = FakeCalendar()
    timed(db)
    sync_calendar(db, fake)
    [event] = fake.live()
    assert datetime.fromisoformat(event["end"]["dateTime"]) - datetime.fromisoformat(event["start"]["dateTime"]) == timedelta(minutes=30)
    fake.calls.clear()
    sync_calendar(db, fake)
    assert fake.calls == []


def test_moving_or_retiming_updates_the_same_event(db):
    fake = FakeCalendar()
    _, placement = timed(db)
    sync_calendar(db, fake)
    [before] = fake.live()
    later = (date.today() + timedelta(days=3)).isoformat()
    move_placement(db, placement.id, later)
    set_placement_time(db, placement.id, "09:30")
    sync_calendar(db, fake)
    [after] = fake.live()
    assert after["id"] == before["id"] and after["start"]["dateTime"].startswith(f"{later}T09:30")


def test_finishing_clearing_or_unplanning_removes_a_future_event(db):
    fake = FakeCalendar()
    done, _ = timed(db, "Done")
    _, cleared = timed(db, "Cleared")
    _, removed = timed(db, "Removed")
    timed(db, "Stays")
    sync_calendar(db, fake)
    assert len(fake.live()) == 4
    set_task_completion(db, done.id, True)
    set_placement_time(db, cleared.id, None)
    remove_placement(db, removed.id)
    sync_calendar(db, fake)
    assert [event["summary"] for event in fake.live()] == ["Stays"]


def test_past_events_are_kept(db):
    fake = FakeCalendar()
    _, placement = timed(db)
    sync_calendar(db, fake)
    remove_placement(db, placement.id)
    after_it_started = start_instant(DAY, "14:00").astimezone(UTC) + timedelta(minutes=5)
    sync_calendar(db, fake, now=after_it_started)
    assert len(fake.live()) == 1 and "delete_event" not in fake.calls


def test_edits_in_google_are_overwritten_and_deleted_future_events_come_back(db):
    fake = FakeCalendar()
    timed(db)
    sync_calendar(db, fake)
    [event] = fake.live()
    calendar_id = next(iter(fake.calendars))
    fake.calendars[calendar_id][event["id"]]["summary"] = "Edited in Google"
    fake.calendars[calendar_id][event["id"]]["reminders"] = {"useDefault": True}
    sync_calendar(db, fake)
    [event] = fake.live()
    assert event["summary"] == "Problem set" and event["reminders"]["overrides"] == [{"method": "popup", "minutes": 30}]
    fake.calendars[calendar_id][event["id"]]["status"] = "cancelled"
    sync_calendar(db, fake)
    assert len(fake.live()) == 1 and fake.live()[0]["id"] != event["id"]


def test_deleted_bearplans_calendar_is_created_again(db):
    fake = FakeCalendar()
    timed(db)
    sync_calendar(db, fake)
    fake.calendars.clear()
    sync_calendar(db, fake)
    assert len(fake.names) == 2 and len(fake.live()) == 1


@pytest.mark.parametrize("value", ["24:00", "9:00", "14:60", "2pm", "", 1400])
def test_invalid_start_times_are_rejected(db, value):
    task = create_task(db, "Bad time")
    placement = create_placement(db, task.id, DAY)
    with pytest.raises(InvalidInput):
        set_placement_time(db, placement.id, value)


def test_time_route_sets_and_clears(db):
    task = create_task(db, "Route")
    placement = create_placement(db, task.id, DAY)
    with TestClient(create_app(db), base_url="http://127.0.0.1:8765") as client:
        response = client.put(f"/api/placements/{placement.id}/time", json={"start_time": "08:15"})
        assert response.status_code == 200 and response.json()["start_time"] == "08:15"
        assert client.get("/api/planning").json()["placements"][0]["start_time"] == "08:15"
        assert client.put(f"/api/placements/{placement.id}/time", json={"start_time": None}).json()["start_time"] is None
        assert client.put(f"/api/placements/{placement.id}/time", json={"start_time": "25:00"}).status_code == 422


def test_migration_0018_is_shipped():
    assert [m.name for m in load_migrations()][17] == "planned_time_and_calendar"
