"""Session-owned trees; confirmed countdown records alone determine growth.

Enrollment and finalization accept an existing write transaction so timer state,
its one tree outcome and request receipts either all commit or all roll back.
No clock, browser animation or live task edit contributes tree progress here.
"""

from __future__ import annotations

import sqlite3
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from backend.storage.db import Database


class TreeProgress(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    species: Literal["pine"]
    stage: Literal["seedling", "sapling", "mature"]
    progress: float
    outcome: Literal["mature", "unfinished"] | None


class ForestTree(TreeProgress):
    session_id: str
    task_title: str
    project_name: str
    parent_title: str | None
    started_at: str
    finished_at: str
    duration_minutes: int
    active_seconds: float


def enroll_tree(conn: sqlite3.Connection, session_id: str, at: str) -> None:
    """Enroll only a newly created session, inside its start transaction."""
    conn.execute(
        "INSERT INTO trees (id, session_id, species, created_at) VALUES (?, ?, 'pine', ?)",
        (str(uuid4()), session_id, at),
    )


def finalize_tree(conn: sqlite3.Connection, session_id: str) -> None:
    """Finalize the enrolled tree without retroactively awarding old sessions.

    The caller must already have finalized this session in the same transaction.
    Integer microseconds and all unresolved interruptions are checked here; a
    rounded visual percentage can never qualify a mature outcome.
    """
    row = conn.execute("SELECT * FROM timer_sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None or row["state"] != "finished":
        raise ValueError("A tree outcome requires a finalized countdown.")
    unresolved = conn.execute(
        "SELECT 1 FROM timer_interruptions WHERE session_id = ? AND resolved_at IS NULL LIMIT 1",
        (session_id,),
    ).fetchone()
    mature = (
        row["outcome"] == "completed"
        and row["active_microseconds"] == row["duration_minutes"] * 60_000_000
        and unresolved is None
    )
    conn.execute(
        "UPDATE trees SET outcome = ?, finalized_at = ? WHERE session_id = ? AND outcome IS NULL",
        ("mature" if mature else "unfinished", row["finished_at"], session_id),
    )


def _progress(tree: sqlite3.Row, session: sqlite3.Row) -> TreeProgress:
    progress = session["active_microseconds"] / (session["duration_minutes"] * 60_000_000)
    stage = "mature" if tree["outcome"] == "mature" else "sapling" if progress >= 0.5 else "seedling"
    return TreeProgress(
        id=tree["id"], species=tree["species"], stage=stage,
        progress=progress, outcome=tree["outcome"],
    )


def session_tree(conn: sqlite3.Connection, session: sqlite3.Row) -> TreeProgress | None:
    tree = conn.execute("SELECT * FROM trees WHERE session_id = ?", (session["id"],)).fetchone()
    return None if tree is None else _progress(tree, session)


def list_forest(db: Database) -> list[ForestTree]:
    """Return saved outcomes with the immutable display context of their sessions."""
    with db.read() as conn:
        rows = conn.execute(
            "SELECT trees.*, timer_sessions.task_title, timer_sessions.project_name,"
            " timer_sessions.parent_title, timer_sessions.started_at, timer_sessions.finished_at,"
            " timer_sessions.duration_minutes, timer_sessions.active_microseconds"
            " FROM trees JOIN timer_sessions ON timer_sessions.id = trees.session_id"
            " WHERE trees.outcome IS NOT NULL ORDER BY trees.rowid DESC"
        ).fetchall()
        return [
            ForestTree(
                **_progress(row, row).model_dump(),
                **{key: row[key] for key in (
                    "session_id", "task_title", "project_name", "parent_title", "started_at",
                    "finished_at", "duration_minutes",
                )},
                active_seconds=row["active_microseconds"] / 1_000_000,
            )
            for row in rows
        ]
