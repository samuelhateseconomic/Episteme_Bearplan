"""M1 acceptance: projects group tasks, and renaming one does not disturb them."""

import pytest

from backend.domain.errors import InvalidInput
from backend.domain.projects import (
    NAME_MAX_LENGTH,
    create_project,
    list_projects,
    rename_project,
)
from backend.domain.tasks import create_task, list_tasks
from backend.storage.db import Database


def test_migration_leaves_exactly_one_default_project(db: Database) -> None:
    projects = list_projects(db)
    assert [p.name for p in projects] == ["Inbox"]
    assert projects[0].is_default is True


def test_create_returns_stored_project(db: Database) -> None:
    project = create_project(db, "  Math 55  ")
    assert project.name == "Math 55"
    assert project.is_default is False
    assert project.revision == 1
    assert project in list_projects(db)


def test_default_project_is_listed_first(db: Database) -> None:
    create_project(db, "Math 55")
    create_project(db, "CS 61A")
    assert [p.name for p in list_projects(db)] == ["Inbox", "Math 55", "CS 61A"]


def test_tasks_land_in_the_project_they_name(db: Database) -> None:
    math = create_project(db, "Math 55")
    cs = create_project(db, "CS 61A")
    write_up = create_task(db, "Write PS7", project_id=math.id)
    lab = create_task(db, "Lab 3", project_id=cs.id)

    assert [t.id for t in list_tasks(db, math.id)] == [write_up.id]
    assert [t.id for t in list_tasks(db, cs.id)] == [lab.id]


def test_task_without_a_project_goes_to_the_default(db: Database) -> None:
    default = next(p for p in list_projects(db) if p.is_default)
    assert create_task(db, "Loose end").project_id == default.id


def test_rename_keeps_tasks_and_bumps_revision(db: Database) -> None:
    project = create_project(db, "Math 55")
    task = create_task(db, "Write PS7", project_id=project.id)

    renamed = rename_project(db, project.id, "Math 55 - Honors")
    assert renamed.name == "Math 55 - Honors"
    assert renamed.revision == project.revision + 1
    assert [t.id for t in list_tasks(db, project.id)] == [task.id]


@pytest.mark.parametrize("name", ["", "   ", "​", "﻿"])
def test_rejects_blank_name(db: Database, name: str) -> None:
    with pytest.raises(InvalidInput) as excinfo:
        create_project(db, name)
    assert excinfo.value.field == "name"
    assert [p.name for p in list_projects(db)] == ["Inbox"]


def test_name_length_limit(db: Database) -> None:
    assert create_project(db, "x" * NAME_MAX_LENGTH).name == "x" * NAME_MAX_LENGTH
    with pytest.raises(InvalidInput):
        create_project(db, "x" * (NAME_MAX_LENGTH + 1))
    assert len(list_projects(db)) == 2  # Inbox plus the one that fit


def test_rejects_unknown_project(db: Database) -> None:
    with pytest.raises(InvalidInput) as excinfo:
        rename_project(db, "00000000-0000-4000-8000-000000000000", "Nope")
    assert excinfo.value.field == "project_id"

    with pytest.raises(InvalidInput):
        create_task(db, "Orphan", project_id="00000000-0000-4000-8000-000000000000")
    assert list_tasks(db) == []


def test_rejected_rename_changes_nothing(db: Database) -> None:
    project = create_project(db, "Math 55")
    with pytest.raises(InvalidInput):
        rename_project(db, project.id, "   ")
    assert next(p for p in list_projects(db) if p.id == project.id) == project
