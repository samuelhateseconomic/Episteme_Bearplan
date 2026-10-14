"""Project application functions.

The interface, and later the assistant and connection adapters, all call these;
none of them write project rows directly.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from backend.domain.errors import InvalidInput
from backend.domain.text import clean_text
from backend.storage.db import Database, utc_now

NAME_MAX_LENGTH = 100


class Project(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    revision: int


class ProjectNotFound(InvalidInput):
    def __init__(self, project_id: str) -> None:
        super().__init__("project_id", f"No project with id {project_id}.")


def _clean_name(name: object) -> str:
    return clean_text(
        name,
        "name",
        max_length=NAME_MAX_LENGTH,
        required=True,
        empty_message="Enter a project name.",
        long_message=f"Keep the project name to {NAME_MAX_LENGTH} characters or fewer.",
    )


def _row_to_project(row: sqlite3.Row) -> Project:
    return Project(
        id=row["id"],
        name=row["name"],
        is_default=bool(row["is_default"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        revision=row["revision"],
    )


def default_project_id(conn: sqlite3.Connection) -> str:
    """The project that holds tasks created without one. Migration 0002 guarantees it exists."""
    row = conn.execute("SELECT id FROM projects WHERE is_default = 1").fetchone()
    if row is None:  # pragma: no cover - only reachable if the row were deleted by hand
        raise InvalidInput("project_id", "The default project is missing from this database.")
    return row["id"]


def require_project(conn: sqlite3.Connection, project_id: str) -> str:
    if not isinstance(project_id, str):
        raise InvalidInput("project_id", "Project id must be text.")
    if conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone() is None:
        raise ProjectNotFound(project_id)
    return project_id


def create_project(db: Database, name: str) -> Project:
    """Validate and save a new project; returns the stored record."""
    cleaned = _clean_name(name)
    project_id = str(uuid4())
    now = utc_now()
    with db.write() as conn:
        conn.execute(
            "INSERT INTO projects (id, name, is_default, created_at, updated_at, revision)"
            " VALUES (?, ?, 0, ?, ?, 1)",
            (project_id, cleaned, now, now),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return _row_to_project(row)


def rename_project(db: Database, project_id: str, name: str) -> Project:
    """Change a project's name. Task membership is untouched."""
    cleaned = _clean_name(name)
    with db.write() as conn:
        require_project(conn, project_id)
        conn.execute(
            "UPDATE projects SET name = ?, updated_at = ?, revision = revision + 1 WHERE id = ?",
            (cleaned, utc_now(), project_id),
        )
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return _row_to_project(row)


def list_projects(db: Database) -> list[Project]:
    """All projects, the default one first, then oldest first."""
    with db.read() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY is_default DESC, created_at, rowid").fetchall()
    return [_row_to_project(row) for row in rows]
