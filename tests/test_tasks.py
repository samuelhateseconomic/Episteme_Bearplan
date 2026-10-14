import threading
from pathlib import Path
from uuid import UUID

import pytest

from backend.domain.errors import InvalidInput
from backend.domain.tasks import TITLE_MAX_LENGTH, create_task, list_tasks
from backend.storage.db import Database, open_database


def test_create_returns_stored_task(db: Database) -> None:
    task = create_task(db, "  Read chapter 4  ")
    assert task.title == "Read chapter 4"
    assert UUID(task.id).version == 4
    assert task.revision == 1
    assert task.created_at == task.updated_at
    assert task.created_at.utcoffset().total_seconds() == 0
    assert list_tasks(db) == [task]


def test_list_is_empty_initially(db: Database) -> None:
    assert list_tasks(db) == []


def test_list_keeps_creation_order(db: Database) -> None:
    titles = [f"Task {i}" for i in range(20)]
    for title in titles:
        create_task(db, title)
    assert [t.title for t in list_tasks(db)] == titles


@pytest.mark.parametrize("title", ["", "   ", "\n\t", "​", "﻿", " ​　  ", " "])
def test_rejects_blank_title(db: Database, title: str) -> None:
    with pytest.raises(InvalidInput) as excinfo:
        create_task(db, title)
    assert excinfo.value.field == "title"
    assert list_tasks(db) == []


def test_title_length_limit(db: Database) -> None:
    assert create_task(db, "x" * TITLE_MAX_LENGTH).title == "x" * TITLE_MAX_LENGTH
    with pytest.raises(InvalidInput):
        create_task(db, "x" * (TITLE_MAX_LENGTH + 1))
    assert len(list_tasks(db)) == 1


def test_trims_invisible_edges_but_keeps_inner_text(db: Database) -> None:
    assert create_task(db, "﻿​Essay​ draft​ ").title == "Essay​ draft"


def test_rejects_unencodable_lone_surrogate(db: Database) -> None:
    with pytest.raises(InvalidInput, match="cannot be saved"):
        create_task(db, "a\ud800b")
    assert list_tasks(db) == []


def test_rejects_non_text_title(db: Database) -> None:
    with pytest.raises(InvalidInput):
        create_task(db, 42)  # type: ignore[arg-type]


def test_unicode_and_sql_like_text_round_trip(db: Database) -> None:
    title = "Bài tập 📚 '); DROP TABLE tasks; --"
    create_task(db, title)
    assert [t.title for t in list_tasks(db)] == [title]


def test_tasks_persist_across_database_reopen(tmp_path: Path) -> None:
    path = tmp_path / "db.sqlite3"
    created = create_task(open_database(path), "Problem set 2")
    assert list_tasks(open_database(path)) == [created]


def test_concurrent_creates_are_all_saved_with_unique_ids(db: Database) -> None:
    errors: list[BaseException] = []

    def worker(n: int) -> None:
        try:
            for i in range(10):
                create_task(db, f"worker {n} task {i}")
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    tasks = list_tasks(db)
    assert len(tasks) == 80
    assert len({t.id for t in tasks}) == 80
