"""Task application functions.

The interface, and later the assistant and connection adapters, all call these
functions; none of them write task rows directly.
"""

from __future__ import annotations

import sqlite3
import unicodedata
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from backend.domain.errors import InvalidInput
from backend.storage.db import Database, utc_now

TITLE_MAX_LENGTH = 200


class Task(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    revision: int


def _is_invisible(char: str) -> bool:
    # Whitespace, separators, control and format characters such as U+200B and U+FEFF.
    return char.isspace() or unicodedata.category(char)[0] in "ZC"


def _normalize_title(title: object) -> str:
    if not isinstance(title, str):
        raise InvalidInput("title", "Title must be text.")
    start, end = 0, len(title)
    while start < end and _is_invisible(title[start]):
        start += 1
    while end > start and _is_invisible(title[end - 1]):
        end -= 1
    cleaned = title[start:end]
    if not cleaned:
        raise InvalidInput("title", "Enter a task title.")
    try:
        cleaned.encode("utf-8")
    except UnicodeEncodeError:
        raise InvalidInput("title", "The title contains characters that cannot be saved.") from None
    if len(cleaned) > TITLE_MAX_LENGTH:
        raise InvalidInput("title", f"Keep the title to {TITLE_MAX_LENGTH} characters or fewer.")
    return cleaned


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        revision=row["revision"],
    )


def create_task(db: Database, title: str) -> Task:
    """Validate and save a new task; returns the stored record."""
    cleaned = _normalize_title(title)
    task_id = str(uuid4())
    now = utc_now()
    with db.write() as conn:
        conn.execute(
            "INSERT INTO tasks (id, title, created_at, updated_at, revision) VALUES (?, ?, ?, ?, 1)",
            (task_id, cleaned, now, now),
        )
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_to_task(row)


def list_tasks(db: Database) -> list[Task]:
    """All saved tasks, oldest first."""
    with db.read() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at, rowid").fetchall()
    return [_row_to_task(row) for row in rows]
