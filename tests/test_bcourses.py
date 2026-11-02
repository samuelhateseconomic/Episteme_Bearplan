"""bCourses source: refresh cache, followed courses, reviewed Add, due-date changes, failures."""
from __future__ import annotations

import json
import os
import urllib.error
from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.domain.bcourses import add_assignment, get_state, refresh, resolve_due_change, set_dismissed, set_followed
from backend.domain.errors import InvalidInput
from backend.domain.projects import list_projects
from backend.domain.tasks import _delete_unused_task_tx, get_task, update_task
from backend.platform import bcourses as platform
from backend.platform.bcourses import BCoursesClient, BCoursesUnavailable
from backend.platform.secrets import read_secret
from backend.storage.migrations import load_migrations
from tests.test_assistant import rows

URL = "https://bcourses.berkeley.edu/courses/1/assignments/"


class FakeClient:
    def __init__(self) -> None:
        self.course_list = [
            {"id": "1", "name": "MATH 54 - Linear Algebra", "course_code": "MATH 54", "term": {"name": "Fall 2026"}},
            {"id": "2", "name": "Old club", "course_code": "CLUB"},
        ]
        self.by_course = {
            "1": [
                {"id": "11", "name": "Problem set 5", "due_at": "2026-11-07T07:59:00Z", "html_url": URL + "11",
                 "points_possible": 10, "updated_at": "2026-10-30T10:00:00Z"},
                {"id": "12", "name": "Reading reflection", "due_at": None, "html_url": URL + "12"},
                {"id": "13", "name": "Bad link", "due_at": "not a date", "html_url": "https://evil.example/x"},
            ],
            "2": [{"id": "21", "name": "Club survey", "due_at": None}],
        }
        self.calls: list[str] = []
        self.fail: BCoursesUnavailable | None = None

    def courses(self):
        self.calls.append("courses")
        if self.fail:
            raise self.fail
        return self.course_list

    def assignments(self, course_id):
        self.calls.append(course_id)
        return self.by_course[course_id]


@pytest.fixture(autouse=True)
def pacific(monkeypatch):
    monkeypatch.setenv("BEARPLANS_TIMEZONE", "America/Los_Angeles")


@pytest.fixture
def fake():
    return FakeClient()


def sync(db, fake):
    refresh(db, fake, BCoursesUnavailable)


def test_first_refresh_lists_courses_only_and_writes_no_tasks(db, fake):
    before = rows(db)
    sync(db, fake)
    state = get_state(db, True)
    assert [c.name for c in state.courses] == ["MATH 54 - Linear Algebra", "Old club"]
    assert not any(c.followed for c in state.courses) and state.assignments == []
    assert fake.calls == ["courses"]  # No assignments fetched until a course is followed.
    assert rows(db)["tasks"] == before["tasks"] and rows(db)["projects"] == before["projects"]
    assert state.sync.last_success_at and state.sync.last_error is None


def test_followed_course_lists_assignments_with_local_due_dates_and_safe_links(db, fake):
    sync(db, fake)
    set_followed(db, ["1"])
    sync(db, fake)
    items = {a.title: a for a in get_state(db, True).assignments}
    assert set(items) == {"Problem set 5", "Reading reflection", "Bad link"}
    # 07:59 UTC on Nov 7 is 11:59 PM on Nov 6 in Berkeley.
    assert items["Problem set 5"].due_date == date(2026, 11, 6) and items["Problem set 5"].status == "new"
    assert items["Reading reflection"].due_date is None
    assert items["Bad link"].due_at is None and items["Bad link"].html_url == ""
    assert [a.title for a in get_state(db, True).assignments][0] == "Problem set 5"  # Dated first.


def test_add_creates_course_project_and_task_once(db, fake):
    sync(db, fake); set_followed(db, ["1"]); sync(db, fake)
    first = add_assignment(db, "11")
    assert first.project_created and first.task.title == "Problem set 5"
    assert first.task.deadline == date(2026, 11, 6) and first.task.notes == f"From bCourses: {URL}11"
    project = next(p for p in list_projects(db) if p.id == first.task.project_id)
    assert project.name == "MATH 54 - Linear Algebra"
    again = add_assignment(db, "11")
    assert again.task.id == first.task.id and not again.project_created
    undated = add_assignment(db, "12")
    assert undated.task.project_id == project.id and undated.task.deadline is None and not undated.project_created
    assert len(list_projects(db)) == 2  # Default project + one course project.


def test_refresh_never_changes_the_users_task_and_flags_due_date_changes(db, fake):
    sync(db, fake); set_followed(db, ["1"]); sync(db, fake)
    task = add_assignment(db, "11").task
    update_task(db, task.id, title="PS5 (my name)", notes="my notes")
    fake.by_course["1"][0] = {**fake.by_course["1"][0], "name": "Problem set 5 (revised)", "due_at": "2026-11-10T07:59:00Z"}
    sync(db, fake)
    kept = get_task(db, task.id)
    assert (kept.title, kept.notes, kept.deadline) == ("PS5 (my name)", "my notes", date(2026, 11, 6))
    item = next(a for a in get_state(db, True).assignments if a.assignment_id == "11")
    assert item.due_changed and item.due_date == date(2026, 11, 9) and item.accepted_due_date == date(2026, 11, 6)
    resolve_due_change(db, "11", use_new=True)
    assert get_task(db, task.id).deadline == date(2026, 11, 9)
    assert not next(a for a in get_state(db, True).assignments if a.assignment_id == "11").due_changed
    fake.by_course["1"][0]["due_at"] = "2026-11-12T07:59:00Z"
    sync(db, fake)
    resolve_due_change(db, "11", use_new=False)
    assert get_task(db, task.id).deadline == date(2026, 11, 9)
    assert not next(a for a in get_state(db, True).assignments if a.assignment_id == "11").due_changed


def test_time_only_change_is_not_flagged(db, fake):
    sync(db, fake); set_followed(db, ["1"]); sync(db, fake)
    add_assignment(db, "11")
    fake.by_course["1"][0]["due_at"] = "2026-11-07T06:00:00Z"  # 10 PM the same local day
    sync(db, fake)
    assert not next(a for a in get_state(db, True).assignments if a.assignment_id == "11").due_changed


def test_dismiss_restore_and_removed_items(db, fake):
    sync(db, fake); set_followed(db, ["1"]); sync(db, fake)
    assert set_dismissed(db, "12", True).status == "dismissed"
    sync(db, fake)
    assert next(a for a in get_state(db, True).assignments if a.assignment_id == "12").status == "dismissed"
    assert set_dismissed(db, "12", False).status == "new"
    add_assignment(db, "11")
    with pytest.raises(InvalidInput, match="already a task"):
        set_dismissed(db, "11", True)
    fake.by_course["1"] = fake.by_course["1"][1:]
    sync(db, fake)
    gone = next(a for a in get_state(db, True).assignments if a.assignment_id == "11")
    assert not gone.in_source and gone.status == "added"  # The task stays; bCourses no longer lists it.


def test_removed_task_makes_assignment_available_again(db, fake):
    sync(db, fake); set_followed(db, ["1"]); sync(db, fake)
    task = add_assignment(db, "11").task
    with db.write() as conn:
        _delete_unused_task_tx(conn, task.id)
    item = next(a for a in get_state(db, True).assignments if a.assignment_id == "11")
    assert item.status == "new" and item.task_id is None
    assert add_assignment(db, "11").task.id != task.id


def test_unfollowing_hides_assignments_and_unknown_courses_are_refused(db, fake):
    sync(db, fake); set_followed(db, ["1", "2"]); sync(db, fake)
    assert {a.course_id for a in get_state(db, True).assignments} == {"1", "2"}
    set_followed(db, ["2"])
    assert {a.course_id for a in get_state(db, True).assignments} == {"2"}
    with pytest.raises(InvalidInput, match="not in the bCourses list"):
        set_followed(db, ["999"])
    assert [c.followed for c in get_state(db, True).courses] == [False, True]


def test_failed_refresh_keeps_cache_and_records_the_message(db, fake):
    sync(db, fake); set_followed(db, ["1"]); sync(db, fake)
    before = get_state(db, True)
    fake.fail = BCoursesUnavailable("bcourses_unreachable", "Cannot reach bCourses.")
    with pytest.raises(BCoursesUnavailable):
        sync(db, fake)
    after = get_state(db, True)
    assert after.assignments == before.assignments and after.courses == before.courses
    assert after.sync.last_error == "Cannot reach bCourses." and after.sync.last_success_at == before.sync.last_success_at
    fake.fail = None
    sync(db, fake)
    assert get_state(db, True).sync.last_error is None


def test_http_flow_and_errors(db, fake):
    api = TestClient(create_app(db, bcourses_client=fake), base_url="http://127.0.0.1:8765")
    state = api.post("/api/bcourses/refresh").json()
    assert state["configured"] and len(state["courses"]) == 2 and "token" not in json.dumps(state).lower()
    state = api.put("/api/bcourses/courses", json={"course_ids": ["1"]}).json()
    assert len(state["assignments"]) == 3
    added = api.post("/api/bcourses/assignments/11/add").json()
    assert added["task"]["deadline"] == "2026-11-06" and added["assignment"]["status"] == "added"
    assert api.put("/api/bcourses/assignments/12/dismissed", json={"dismissed": True}).json()["status"] == "dismissed"
    assert api.post("/api/bcourses/assignments/99/add").status_code == 422
    assert api.put("/api/bcourses/courses", json={"course_ids": [1]}).status_code == 422
    fake.fail = BCoursesUnavailable("bcourses_token_rejected", "bCourses did not accept the token.")
    failed = api.post("/api/bcourses/refresh")
    assert failed.status_code == 502 and failed.json()["error"]["code"] == "bcourses_token_rejected"
    assert api.post("/api/bcourses/refresh", headers={"Origin": "https://evil.example"}).status_code == 403


def test_unconfigured_service_reports_missing_token_without_network(client):
    assert client.get("/api/bcourses").json()["configured"] is False
    response = client.post("/api/bcourses/refresh")
    assert response.status_code == 502 and response.json()["error"]["code"] == "bcourses_not_configured"


def test_secrets_file_parsing(tmp_path, monkeypatch):
    path = tmp_path / "s.env"
    path.write_text("# BCOURSES_TOKEN=commented\nOTHER=x\nBCOURSES_TOKEN = abc~123 \n")
    path.chmod(0o644)
    monkeypatch.setenv("BEARPLANS_SECRETS_FILE", str(path))
    assert read_secret("BCOURSES_TOKEN") == "abc~123" and read_secret("MISSING") is None
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    path.write_text("BCOURSES_TOKEN=\n")
    assert read_secret("BCOURSES_TOKEN") is None


class FakeResponse:
    def __init__(self, body, link=""):
        self.body, self.headers = json.dumps(body).encode(), {"Link": link}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, *args):
        data, self.body = self.body, b""
        return data


def test_client_sends_header_token_follows_pagination_and_refuses_other_hosts(monkeypatch):
    seen = []
    pages = [FakeResponse([{"id": "1"}], '<https://bcourses.berkeley.edu/api/v1/courses?page=2>; rel="next"'),
             FakeResponse([{"id": "2"}], "")]
    client = BCoursesClient(token="secret-token")
    monkeypatch.setattr(client._opener, "open", lambda request, timeout: (seen.append(request), pages.pop(0))[1])
    assert [c["id"] for c in client.courses()] == ["1", "2"]
    assert all(r.get_header("Authorization") == "Bearer secret-token" and "secret-token" not in r.full_url for r in seen)
    assert all(r.full_url.startswith("https://bcourses.berkeley.edu/api/v1/") and r.get_method() == "GET" for r in seen)
    monkeypatch.setattr(client._opener, "open", lambda request, timeout: FakeResponse([], '<https://evil.example/x>; rel="next"'))
    with pytest.raises(BCoursesUnavailable):
        client.courses()


@pytest.mark.parametrize("status,code", [(401, "bcourses_token_rejected"), (403, "bcourses_forbidden"), (500, "bcourses_unavailable")])
def test_client_errors_are_actionable_and_never_contain_the_token(monkeypatch, status, code):
    client = BCoursesClient(token="secret-token")

    def fail(request, timeout):
        raise urllib.error.HTTPError(request.full_url, status, "x", {}, None)
    monkeypatch.setattr(client._opener, "open", fail)
    with pytest.raises(BCoursesUnavailable) as raised:
        client.courses()
    assert raised.value.code == code and "secret-token" not in raised.value.message


def test_client_without_token_explains_where_to_put_it():
    with pytest.raises(BCoursesUnavailable, match="BCOURSES_TOKEN"):
        BCoursesClient().courses()


def test_migration_0016_is_last_and_isolated():
    assert [m.name for m in load_migrations()][-1] == "bcourses"
    assert platform.BASE == "https://bcourses.berkeley.edu"
    assert os.environ["BEARPLANS_SECRETS_FILE"].endswith("none.env")
