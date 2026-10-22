"""Read-only validation of the application's required SQLite schema.

Migration receipts identify upgrades; they do not prove the required objects exist.
Build the expected shape from shipped SQL in memory, allowing preserved legacy
tables/columns while checking constraints relied on by current application code.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import re
import sqlite3

from backend.storage.db import Database, StorageError
from backend.storage.migrations import load_migrations


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _sql_tokens(sql: str | None) -> tuple[str, ...]:
    """Ignore formatting/case outside string values, never change literal values."""
    tokens = re.findall(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|\[[^\]]*\]|`[^`]*`|--[^\n]*|/\*[\s\S]*?\*/|\w+|[^\s]", sql or "")
    return tuple(token if token.startswith("'") else token.lower() for token in tokens
                 if not token.startswith(("--", "/*")))


def _checks(sql: str) -> Counter:
    tokens = _sql_tokens(sql)
    checks = Counter()
    for index, token in enumerate(tokens[:-1]):
        if token != "check" or tokens[index + 1] != "(":
            continue
        depth, end = 1, index + 2
        while end < len(tokens) and depth:
            depth += (tokens[end] == "(") - (tokens[end] == ")")
            end += 1
        checks[tokens[index + 2:end - 1]] += 1
    return checks


def _index_shape(conn: sqlite3.Connection, row: sqlite3.Row) -> tuple:
    name = row[1]
    keys = tuple((item[2], item[3], (item[4] or "").lower())
                 for item in conn.execute(f"PRAGMA index_xinfo({_quote(name)})") if item[5])
    sql_row = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?", (name,)).fetchone()
    sql = sql_row[0] if sql_row else None
    tokens = _sql_tokens(sql)
    where = tokens.index("where") if "where" in tokens else None
    predicate = tokens[where + 1:] if where is not None else ()
    # Expression keys have no column name in index_xinfo. Compare their complete
    # key/predicate body too, so e.g. (1) cannot silently become length(task_id).
    expression = tokens[tokens.index("("):] if sql and any(key[0] is None for key in keys) else ()
    return bool(row[2]), keys, bool(row[4]), predicate, expression


def _shape(conn: sqlite3.Connection) -> dict:
    result = {}
    names = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")]
    for name in names:
        columns = {row[1]: (row[2].upper(), bool(row[3]), _sql_tokens(row[4]), row[5])
                   for row in conn.execute(f"PRAGMA table_info({_quote(name)})")}
        foreign_keys = Counter(tuple(row)[1:] for row in conn.execute(f"PRAGMA foreign_key_list({_quote(name)})"))
        indexes, unique_constraints, primary_indexes = {}, Counter(), Counter()
        for row in conn.execute(f"PRAGMA index_list({_quote(name)})"):
            shape = _index_shape(conn, row)
            if row[3] == "c":
                indexes[row[1]] = shape
            elif row[3] == "u":
                unique_constraints[shape] += 1
            elif row[3] == "pk":
                primary_indexes[shape] += 1
        table_sql = conn.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone()[0]
        result[name] = {"columns": columns, "foreign_keys": foreign_keys,
                        "indexes": indexes, "unique_constraints": unique_constraints,
                        "primary_indexes": primary_indexes, "checks": _checks(table_sql)}
    triggers = {}
    for name, sql in conn.execute("SELECT name, sql FROM sqlite_master WHERE type = 'trigger'"):
        tokens = _sql_tokens(sql)
        if tokens[:5] == ("create", "trigger", "if", "not", "exists"):
            tokens = tokens[:2] + tokens[5:]
        triggers[name] = tokens
    return {"tables": result, "triggers": triggers}


@lru_cache(maxsize=4)
def _expected(sql: tuple[str, ...]) -> dict:
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)")
        for statement in sql:
            conn.executescript(statement)
        return _shape(conn)
    finally:
        conn.close()


def validate_schema(db: Database) -> None:
    """Refuse incompatible required objects without resetting or rewriting data."""
    expected = _expected(tuple(migration.sql for migration in load_migrations()))
    with db.read() as conn:
        conn.execute("BEGIN")
        actual = _shape(conn)
    issues = []
    for table, required in expected["tables"].items():
        found = actual["tables"].get(table)
        if found is None:
            issues.append(f"missing table {table}")
            continue
        for column, shape in required["columns"].items():
            if column not in found["columns"]:
                issues.append(f"missing column {table}.{column}")
            elif found["columns"][column] != shape:
                issues.append(f"incompatible column {table}.{column}")
        expected_pk = {key: value[3] for key, value in required["columns"].items() if value[3]}
        actual_pk = {key: value[3] for key, value in found["columns"].items() if value[3]}
        if expected_pk != actual_pk:
            issues.append(f"incompatible primary key in {table}")
        if required["primary_indexes"] != found["primary_indexes"]:
            issues.append(f"incompatible primary key index in {table}")
        if required["checks"] - found["checks"]:
            issues.append(f"missing or incompatible CHECK constraint in {table}")
        if required["foreign_keys"] - found["foreign_keys"]:
            issues.append(f"missing or incompatible foreign key in {table}")
        if required["unique_constraints"] - found["unique_constraints"]:
            issues.append(f"missing unique constraint in {table}")
        for name, shape in required["indexes"].items():
            if name not in found["indexes"]:
                issues.append(f"missing index {name}")
            elif found["indexes"][name] != shape:
                issues.append(f"incompatible index {name}")
    for name, shape in expected["triggers"].items():
        if name not in actual["triggers"]:
            issues.append(f"missing trigger {name}")
        elif actual["triggers"][name] != shape:
            issues.append(f"incompatible trigger {name}")
    if issues:
        detail = "; ".join(issues[:8])
        raise StorageError(
            f"Saved database schema does not match this BearPlans build: {detail}. "
            "Keep this database and a backup; use the matching build or a reviewed repair migration. "
            "Your saved data was not reset.",
        )
