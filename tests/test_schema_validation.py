"""Refuse schema drift without repairing or rewriting unrelated saved records."""

from pathlib import Path

import pytest

from backend.domain.tasks import create_task
from backend.domain.planning import create_placement
from backend.domain.weeks import close_week, preview_close
from backend.storage.db import Database, StorageError, open_database
from backend.storage.schema import validate_schema


def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _snapshot(db: Database) -> tuple:
    with db.read() as conn:
        structure = tuple(tuple(row) for row in conn.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name"
        ))
        content = tuple(
            (name, tuple(sorted((tuple(row) for row in conn.execute(f"SELECT * FROM {_quoted(name)}")), key=repr)))
            for name, in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").fetchall()
        )
    return structure, content


@pytest.fixture
def saved_db(tmp_path: Path) -> Database:
    db = open_database(tmp_path / "saved.sqlite3")
    create_task(db, "Preserve this saved task", deadline="2026-11-01", notes="Schema checks cannot replace user data")
    return db


def _assert_rejected_without_changes(db: Database, affected: str, *, reopen: bool = False) -> None:
    before = _snapshot(db)
    with pytest.raises(StorageError) as raised:
        open_database(db.path) if reopen else validate_schema(db)
    assert affected in str(raised.value)
    assert "backup" in str(raised.value).lower()
    assert _snapshot(db) == before


def _replace_empty_table_definition(db: Database, table: str, old: str, new: str) -> None:
    with db.write() as conn:
        assert conn.execute(f"SELECT COUNT(*) FROM {_quoted(table)}").fetchone()[0] == 0
        sql = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()[0]
        indexes = [row[0] for row in conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'index' AND tbl_name = ? AND sql IS NOT NULL", (table,),
        )]
        assert old in sql
        conn.execute(f"DROP TABLE {_quoted(table)}")
        conn.execute(sql.replace(old, new))
        for index in indexes:
            conn.execute(index)


def test_latest_schema_validation_is_read_only(saved_db: Database, monkeypatch) -> None:
    before = _snapshot(saved_db)
    connect = saved_db.connect

    def read_only_connection():
        conn = connect()
        conn.execute("PRAGMA query_only = ON")
        return conn

    monkeypatch.setattr(saved_db, "connect", read_only_connection)
    validate_schema(saved_db)
    assert _snapshot(saved_db) == before


def test_missing_table_after_recorded_repair_is_refused_without_recreating_it(saved_db: Database) -> None:
    with saved_db.write() as conn:
        assert conn.execute("SELECT 1 FROM schema_migrations WHERE version = 11").fetchone()
        conn.execute("DROP TABLE timer_interruptions")
    _assert_rejected_without_changes(saved_db, "timer_interruptions", reopen=True)
    with saved_db.read() as conn:
        assert conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'timer_interruptions'").fetchone() is None


def test_missing_required_column_is_refused_without_changing_rows(saved_db: Database) -> None:
    with saved_db.write() as conn:
        conn.execute("ALTER TABLE timer_interruptions DROP COLUMN measured_sleep_microseconds")
    _assert_rejected_without_changes(saved_db, "measured_sleep_microseconds")


def test_missing_required_index_is_refused_without_changing_rows(saved_db: Database) -> None:
    with saved_db.write() as conn:
        conn.execute("DROP INDEX timer_one_unresolved_interruption")
    _assert_rejected_without_changes(saved_db, "timer_one_unresolved_interruption")


@pytest.mark.parametrize("replacement", [
    "CREATE INDEX timer_one_unresolved_interruption ON timer_interruptions (session_id) WHERE resolved_at IS NULL",
    "CREATE UNIQUE INDEX timer_one_unresolved_interruption ON timer_interruptions (id) WHERE resolved_at IS NULL",
    "CREATE UNIQUE INDEX timer_one_unresolved_interruption ON timer_interruptions (session_id)",
    "CREATE UNIQUE INDEX timer_one_unresolved_interruption ON timer_interruptions (session_id) WHERE resolved_at IS NOT NULL",
    "CREATE UNIQUE INDEX timer_one_unresolved_interruption ON timer_interruptions (session_id DESC) WHERE resolved_at IS NULL",
    "CREATE UNIQUE INDEX timer_one_unresolved_interruption ON timer_interruptions (session_id COLLATE NOCASE) WHERE resolved_at IS NULL",
], ids=["not-unique", "wrong-column", "missing-predicate", "wrong-predicate", "wrong-order", "wrong-collation"])
def test_right_index_name_with_wrong_constraint_is_refused(saved_db: Database, replacement: str) -> None:
    with saved_db.write() as conn:
        conn.execute("DROP INDEX timer_one_unresolved_interruption")
        conn.execute(replacement)
    _assert_rejected_without_changes(saved_db, "timer_one_unresolved_interruption")


@pytest.mark.parametrize("replacement", ["", " REFERENCES timer_sessions(id) ON DELETE CASCADE"], ids=["missing", "wrong-action"])
def test_missing_or_incompatible_foreign_key_is_refused_without_changing_rows(saved_db: Database, replacement: str) -> None:
    _replace_empty_table_definition(saved_db, "timer_interruptions", " REFERENCES timer_sessions(id)", replacement)
    _assert_rejected_without_changes(saved_db, "timer_interruptions")


@pytest.mark.parametrize("table,old,new,column", [
    ("timer_interruptions", "confirmed_active_microseconds INTEGER NOT NULL", "confirmed_active_microseconds TEXT NOT NULL", "confirmed_active_microseconds"),
    ("timer_interruptions", "reason TEXT NOT NULL", "reason TEXT", "reason"),
    ("timer_interruptions", "id TEXT PRIMARY KEY NOT NULL", "id TEXT NOT NULL", "id"),
    ("timer_sessions", "active_microseconds INTEGER NOT NULL DEFAULT 0", "active_microseconds INTEGER NOT NULL DEFAULT 1", "active_microseconds"),
], ids=["wrong-type", "nullable-required-field", "missing-primary-key", "wrong-default"])
def test_incompatible_required_column_definition_is_refused(saved_db: Database, table: str, old: str, new: str, column: str) -> None:
    _replace_empty_table_definition(saved_db, table, old, new)
    _assert_rejected_without_changes(saved_db, column)


def test_required_implicit_unique_constraint_is_not_just_an_index_name(saved_db: Database) -> None:
    _replace_empty_table_definition(saved_db, "trees", "session_id TEXT UNIQUE NOT NULL", "session_id TEXT NOT NULL")
    _assert_rejected_without_changes(saved_db, "trees")


def test_additional_legacy_unique_constraint_can_shift_automatic_index_names(saved_db: Database) -> None:
    _replace_empty_table_definition(
        saved_db, "trees", "id TEXT PRIMARY KEY NOT NULL", "legacy_marker TEXT UNIQUE, id TEXT PRIMARY KEY NOT NULL",
    )
    before = _snapshot(saved_db)
    validate_schema(saved_db)
    assert _snapshot(saved_db) == before


def test_required_expression_index_cannot_be_replaced_with_another_expression(saved_db: Database) -> None:
    with saved_db.write() as conn:
        conn.execute("DROP INDEX timer_one_unfinished")
        conn.execute("CREATE UNIQUE INDEX timer_one_unfinished ON timer_sessions ((length(task_id))) WHERE state <> 'finished'")
    _assert_rejected_without_changes(saved_db, "timer_one_unfinished")


@pytest.mark.parametrize("replacement", [
    "",
    " CHECK (kind IN ('service_restart', 'sleep', 'clock_change', 'checkpoint_gap', 'unverified_work'))",
], ids=["missing", "weakened"])
def test_required_interruption_kind_check_is_refused_if_missing_or_changed(saved_db: Database, replacement: str) -> None:
    _replace_empty_table_definition(
        saved_db, "timer_interruptions", " CHECK (kind IN ('service_restart', 'sleep', 'clock_change', 'checkpoint_gap'))", replacement,
    )
    _assert_rejected_without_changes(saved_db, "timer_interruptions")


def test_changed_maximum_duration_check_is_refused_without_rewriting_records(saved_db: Database) -> None:
    _replace_empty_table_definition(
        saved_db, "timer_sessions", "CHECK (duration_minutes BETWEEN 1 AND 180)", "CHECK (duration_minutes BETWEEN 1 AND 181)",
    )
    _assert_rejected_without_changes(saved_db, "timer_sessions")


def test_primary_key_collation_drift_is_refused(saved_db: Database) -> None:
    _replace_empty_table_definition(
        saved_db, "timer_interruptions", "id TEXT PRIMARY KEY NOT NULL", "id TEXT COLLATE NOCASE PRIMARY KEY NOT NULL",
    )
    _assert_rejected_without_changes(saved_db, "timer_interruptions")


@pytest.mark.parametrize("replace_with_noop", [False, True], ids=["missing", "no-op-body"])
def test_closed_history_update_trigger_drift_is_refused_without_changing_saved_history(saved_db: Database, replace_with_noop: bool) -> None:
    task = create_task(saved_db, "Frozen historical task", notes="Keep this frozen text")
    create_placement(saved_db, task.id, "2026-10-15")
    close_week(saved_db, "2026-10-12", preview_close(saved_db, "2026-10-12").preview_token)
    with saved_db.write() as conn:
        conn.execute("DROP TRIGGER closed_weeks_no_update")
        if replace_with_noop:
            conn.execute("CREATE TRIGGER closed_weeks_no_update BEFORE UPDATE ON closed_weeks BEGIN SELECT 1; END")
    _assert_rejected_without_changes(saved_db, "closed_weeks_no_update", reopen=True)


def test_additional_legacy_check_with_nested_parentheses_and_quoted_check_text_is_preserved(saved_db: Database) -> None:
    _replace_empty_table_definition(
        saved_db, "timer_interruptions", "id TEXT PRIMARY KEY NOT NULL",
        "legacy_note TEXT CHECK (legacy_note IS NULL OR (instr(legacy_note, 'CHECK (') > 0)), id TEXT PRIMARY KEY NOT NULL",
    )
    before = _snapshot(saved_db)
    validate_schema(saved_db)
    assert _snapshot(saved_db) == before


def test_required_check_allows_formatting_changes_without_changing_literal_values(saved_db: Database) -> None:
    _replace_empty_table_definition(
        saved_db, "timer_interruptions",
        "CHECK (kind IN ('service_restart', 'sleep', 'clock_change', 'checkpoint_gap'))",
        "check ( kind in ( 'service_restart' , 'sleep' , 'clock_change' , 'checkpoint_gap' ) )",
    )
    before = _snapshot(saved_db)
    validate_schema(saved_db)
    assert _snapshot(saved_db) == before


def test_required_trigger_allows_equivalent_keyword_case_and_whitespace(saved_db: Database) -> None:
    with saved_db.write() as conn:
        conn.execute("DROP TRIGGER closed_weeks_no_update")
        conn.execute("create trigger closed_weeks_no_update before update on closed_weeks begin select raise ( abort , 'Closed weeks are read-only.' ); end")
    before = _snapshot(saved_db)
    validate_schema(saved_db)
    assert _snapshot(saved_db) == before


def test_where_inside_an_index_comment_does_not_change_its_predicate(saved_db: Database) -> None:
    with saved_db.write() as conn:
        conn.execute("DROP INDEX timer_one_unresolved_interruption")
        conn.execute(
            "CREATE UNIQUE INDEX timer_one_unresolved_interruption ON timer_interruptions (session_id) "
            "/* WHERE is only a formatting comment */ WHERE resolved_at IS NULL"
        )
    before = _snapshot(saved_db)
    validate_schema(saved_db)
    assert _snapshot(saved_db) == before


def test_if_not_exists_inside_a_trigger_literal_is_not_removed(saved_db: Database) -> None:
    with saved_db.write() as conn:
        conn.execute("DROP TRIGGER closed_weeks_no_update")
        conn.execute(
            "CREATE TRIGGER closed_weeks_no_update BEFORE UPDATE ON closed_weeks "
            "BEGIN SELECT RAISE(ABORT, 'Closed weeks are read-only.IF NOT EXISTS'); END"
        )
    _assert_rejected_without_changes(saved_db, "closed_weeks_no_update")


def test_integer_primary_key_cannot_gain_a_different_primary_index(saved_db: Database) -> None:
    with saved_db.write() as conn:
        sql = conn.execute("SELECT sql FROM sqlite_master WHERE name = 'migration_fingerprints'").fetchone()[0]
        assert "version INTEGER PRIMARY KEY NOT NULL" in sql
        receipts = [tuple(row) for row in conn.execute("SELECT * FROM migration_fingerprints ORDER BY version")]
        assert receipts
        conn.execute("DROP TABLE migration_fingerprints")
        conn.execute(sql.replace("version INTEGER PRIMARY KEY NOT NULL", "version INTEGER PRIMARY KEY DESC NOT NULL"))
        conn.executemany("INSERT INTO migration_fingerprints VALUES (?, ?)", receipts)
        assert any(row[3] == "pk" for row in conn.execute("PRAGMA index_list(migration_fingerprints)"))
    _assert_rejected_without_changes(saved_db, "migration_fingerprints")


def test_legacy_extra_tables_columns_and_indexes_are_preserved(saved_db: Database) -> None:
    with saved_db.write() as conn:
        conn.execute("ALTER TABLE timer_sessions ADD COLUMN pause_reason TEXT")
        conn.execute("CREATE TABLE timer_recovery_gaps (id TEXT PRIMARY KEY, saved_note TEXT)")
        conn.execute("INSERT INTO timer_recovery_gaps VALUES ('legacy-gap', 'Retain previous recovery evidence')")
        conn.execute("CREATE INDEX legacy_gap_note ON timer_recovery_gaps (saved_note)")
    before = _snapshot(saved_db)
    validate_schema(saved_db)
    reopened = open_database(saved_db.path)
    assert _snapshot(reopened) == before


def test_equivalent_index_whitespace_and_case_do_not_trigger_false_drift(saved_db: Database) -> None:
    with saved_db.write() as conn:
        conn.execute("DROP INDEX timer_one_unresolved_interruption")
        conn.execute('create unique index timer_one_unresolved_interruption on timer_interruptions ( session_id ) where resolved_at is null')
    before = _snapshot(saved_db)
    validate_schema(saved_db)
    assert _snapshot(saved_db) == before
