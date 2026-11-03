"""Google Tasks sync against an in-memory fake Google: push, ticks back, removals, failures."""
from __future__ import annotations

import itertools
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.google_tasks import get_status, sync
from backend.domain.projects import create_project, default_project_id, rename_project
from backend.domain.planning import create_placement
from backend.domain.tasks import create_task, get_task, remove_subtask, set_task_completion, update_task
from backend.platform.google import GoogleAuth, GoogleUnavailable
from backend.storage.migrations import load_migrations

TODAY = date.today()


class FakeTasks:
    """Just enough of Google Tasks: lists, tasks with one level of parent, soft deletes."""

    def __init__(self) -> None:
        self.ids = (f"g{n}" for n in itertools.count(1))
        self.lists_by_id: dict[str, str] = {"own": "My Tasks"}  # the user's own list
        self.items: dict[str, dict[str, dict]] = {"own": {"mine": {"id": "mine", "title": "Mine", "status": "needsAction"}}}
        self.calls: list[str] = []
        self.fail_after: int | None = None

    def _count(self, name: str) -> None:
        self.calls.append(name)
        if self.fail_after is not None and len([c for c in self.calls if c.startswith("insert")]) > self.fail_after:
            raise GoogleUnavailable("google_unreachable", "Cannot reach Google.")

    def lists(self):
        return [{"id": i, "title": t} for i, t in self.lists_by_id.items()]

    def insert_list(self, title):
        self._count("insert_list")
        list_id = next(self.ids)
        self.lists_by_id[list_id] = title
        self.items[list_id] = {}
        return {"id": list_id, "title": title}

    def rename_list(self, list_id, title):
        self.calls.append("rename_list")
        self.lists_by_id[list_id] = title
        return {"id": list_id, "title": title}

    def tasks(self, list_id):
        return [dict(item) for item in self.items[list_id].values()]

    def insert_task(self, list_id, body, parent):
        self._count("insert_task")
        task_id = next(self.ids)
        item = {"id": task_id, **body}
        if parent:
            assert parent in self.items[list_id] and not self.items[list_id][parent].get("parent"), "one level only"
            item["parent"] = parent
        self.items[list_id][task_id] = item
        return dict(item)

    def patch_task(self, list_id, task_id, body):
        self.calls.append("patch_task")
        item = self.items[list_id][task_id]
        for key, value in body.items():
            if value is None:
                item.pop(key, None)
            else:
                item[key] = value
        return dict(item)

    def move_task(self, list_id, task_id, parent):
        self.calls.append("move_task")
        item = self.items[list_id][task_id]
        if parent:
            item["parent"] = parent
        else:
            item.pop("parent", None)
        return dict(item)

    def delete_task(self, list_id, task_id):
        self.calls.append("delete_task")
        if task_id in self.items.get(list_id, {}):
            self.items[list_id][task_id]["deleted"] = True

    # helpers for assertions
    def list_named(self, title):
        return next(i for i, t in self.lists_by_id.items() if t == title)

    def live(self, list_id):
        return {item["title"]: item for item in self.items[list_id].values() if not item.get("deleted")}


def run(db, fake):
    return sync(db, fake, GoogleUnavailable)


def test_projects_tasks_and_subtasks_become_lists_tasks_and_subtasks(db):
    fake = FakeTasks()
    project = create_project(db, "CS 61B")
    essay = create_task(db, "Essay", project_id=project.id, deadline=TODAY + timedelta(days=3), notes="Draft first")
    parent = create_task(db, "Project 2", project_id=project.id)
    child = create_task(db, "Write tests", parent_id=parent.id)
    create_placement(db, child.id, TODAY + timedelta(days=1))
    create_task(db, "Someday", project_id=project.id)

    status = run(db, fake)

    items = fake.live(fake.list_named("CS 61B"))
    assert items["Essay"]["due"] == f"{(TODAY + timedelta(days=3)).isoformat()}T00:00:00.000Z"
    assert items["Essay"]["notes"] == "Draft first"
    assert items["Write tests"]["parent"] == items["Project 2"]["id"]
    assert items["Write tests"]["due"].startswith((TODAY + timedelta(days=1)).isoformat())  # planned day
    assert items["Project 2"]["due"].startswith((TODAY + timedelta(days=1)).isoformat())  # from its subtask
    assert "due" not in items["Someday"]
    assert status.last_error is None and status.synced_tasks == 4
    assert fake.lists_by_id["own"] == "My Tasks" and fake.live("own") == {"Mine": fake.items["own"]["mine"]}
    assert get_task(db, essay.id).title == "Essay"


def test_second_sync_changes_nothing(db):
    fake = FakeTasks()
    create_task(db, "Read", deadline=TODAY)
    run(db, fake)
    fake.calls.clear()
    run(db, fake)
    assert fake.calls == []


def test_edits_in_bearplans_are_sent_and_edits_in_google_overwritten(db):
    fake = FakeTasks()
    project = create_project(db, "History")
    task = create_task(db, "Read ch 1", project_id=project.id)
    run(db, fake)
    list_id = fake.list_named("History")
    google_id = fake.live(list_id)["Read ch 1"]["id"]
    fake.items[list_id][google_id]["title"] = "Changed in Google"

    rename_project(db, project.id, "History 7B")
    update_task(db, task.id, deadline=TODAY + timedelta(days=2))
    run(db, fake)

    assert fake.lists_by_id[list_id] == "History 7B"
    item = fake.items[list_id][google_id]
    assert item["title"] == "Read ch 1" and item["due"].startswith((TODAY + timedelta(days=2)).isoformat())


def test_tick_in_google_completes_in_bearplans_and_untick_reopens(db):
    fake = FakeTasks()
    task = create_task(db, "Laundry")
    run(db, fake)
    list_id = fake.list_named(_default_name(db))
    item = fake.live(list_id)["Laundry"]
    item["status"] = "completed"
    run(db, fake)
    assert get_task(db, task.id).completed

    fake.items[list_id][item["id"]]["status"] = "needsAction"
    run(db, fake)
    assert not get_task(db, task.id).completed


def test_change_in_bearplans_wins_over_a_tick_in_google(db):
    fake = FakeTasks()
    task = create_task(db, "Gym")
    run(db, fake)
    list_id = fake.list_named(_default_name(db))
    google_id = fake.live(list_id)["Gym"]["id"]
    set_task_completion(db, task.id, True)
    fake.items[list_id][google_id]["status"] = "needsAction"  # unchanged in Google
    fake.items[list_id][google_id]["title"] = "Gym"
    run(db, fake)
    assert get_task(db, task.id).completed
    assert fake.items[list_id][google_id]["status"] == "completed"


def test_ticking_a_parent_in_google_completes_its_subtasks(db):
    fake = FakeTasks()
    parent = create_task(db, "Lab")
    first = create_task(db, "Part A", parent_id=parent.id)
    second = create_task(db, "Part B", parent_id=parent.id)
    set_task_completion(db, first.id, True)
    run(db, fake)
    list_id = fake.list_named(_default_name(db))
    fake.live(list_id)["Lab"]["status"] = "completed"
    run(db, fake)
    assert get_task(db, second.id).completed and get_task(db, parent.id).completed


def test_removed_subtask_is_removed_from_google(db):
    fake = FakeTasks()
    parent = create_task(db, "Trip")
    child = create_task(db, "Pack", parent_id=parent.id)
    run(db, fake)
    remove_subtask(db, child.id)
    run(db, fake)
    assert set(fake.live(fake.list_named(_default_name(db)))) == {"Trip"}
    assert get_status(db).synced_tasks == 1


def test_tasks_the_user_added_in_a_bearplans_list_are_left_alone(db):
    fake = FakeTasks()
    create_task(db, "Mine in BearPlans")
    run(db, fake)
    list_id = fake.list_named(_default_name(db))
    fake.items[list_id]["user"] = {"id": "user", "title": "Added in Google", "status": "needsAction"}
    run(db, fake)
    assert "Added in Google" in fake.live(list_id)


def test_list_deleted_in_google_is_recreated(db):
    fake = FakeTasks()
    create_task(db, "Call home")
    run(db, fake)
    old = fake.list_named(_default_name(db))
    del fake.lists_by_id[old]
    run(db, fake)
    new = fake.list_named(_default_name(db))
    assert new != old and "Call home" in fake.live(new)


def test_task_deleted_in_google_is_sent_again(db):
    fake = FakeTasks()
    create_task(db, "Dentist")
    run(db, fake)
    list_id = fake.list_named(_default_name(db))
    fake.live(list_id)["Dentist"]["deleted"] = True
    run(db, fake)
    assert "Dentist" in fake.live(list_id)


def test_interrupted_sync_is_recorded_and_resumes_without_duplicates(db):
    fake = FakeTasks()
    for title in ("One", "Two", "Three"):
        create_task(db, title)
    fake.fail_after = 2  # the list and one task are created, then Google fails
    with pytest.raises(GoogleUnavailable):
        run(db, fake)
    assert get_status(db).last_error == "Cannot reach Google."
    fake.fail_after = None
    status = run(db, fake)
    live = fake.live(fake.list_named(_default_name(db)))
    assert sorted(live) == ["One", "Three", "Two"] and len(fake.lists_by_id) == 2
    assert status.last_error is None and status.last_success_at


def test_routes_report_status_and_sync_without_exposing_tokens(db):
    fake = FakeTasks()
    create_task(db, "Route task")
    with TestClient(create_app(db, google_tasks_client=fake), base_url="http://127.0.0.1:8765") as client:
        state = client.get("/api/google").json()
        assert state["configured"] is False and state["connected"] is False
        assert state["tasks"]["synced_tasks"] == 0
        synced = client.post("/api/google/tasks/sync").json()
        assert synced["tasks"]["synced_tasks"] == 1
        assert "token" not in str(synced).lower()


def test_sync_route_reports_google_failure(db):
    fake = FakeTasks()
    create_task(db, "Fails")
    fake.fail_after = 0
    with TestClient(create_app(db, google_tasks_client=fake), base_url="http://127.0.0.1:8765") as client:
        response = client.post("/api/google/tasks/sync")
        assert response.status_code == 502 and response.json()["error"]["code"] == "google_unreachable"
        assert client.get("/api/google").json()["tasks"]["last_error"] == "Cannot reach Google."


def test_not_connected_without_sign_in_files(db):
    auth = GoogleAuth()
    assert not auth.configured() and not auth.connected()
    with pytest.raises(GoogleUnavailable) as caught:
        auth.access_token()
    assert caught.value.code == "google_not_connected"


def test_migration_0017_is_last():
    assert [m.name for m in load_migrations()][-1] == "google_tasks"


def _default_name(db) -> str:
    with db.read() as conn:
        return conn.execute("SELECT name FROM projects WHERE id = ?", (default_project_id(conn),)).fetchone()["name"]
