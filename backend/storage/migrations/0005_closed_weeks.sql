-- Frozen display payloads do not depend on later edits or even deletion of a
-- current subtask. Stable task IDs remain historical references, not live FKs.
CREATE TABLE closed_weeks (
    week_start TEXT PRIMARY KEY NOT NULL,
    week_end TEXT NOT NULL,
    closed_at TEXT NOT NULL,
    timezone TEXT NOT NULL,
    snapshot_json TEXT NOT NULL CHECK (json_valid(snapshot_json))
);

CREATE TABLE closed_placements (
    id TEXT PRIMARY KEY NOT NULL,
    task_id TEXT NOT NULL,
    planned_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    revision INTEGER NOT NULL,
    week_start TEXT NOT NULL REFERENCES closed_weeks(week_start) ON DELETE RESTRICT,
    UNIQUE (task_id, planned_date)
);
CREATE INDEX closed_placements_week ON closed_placements(week_start);

CREATE TABLE carryover_operations (
    operation_id TEXT PRIMARY KEY NOT NULL,
    week_start TEXT NOT NULL REFERENCES closed_weeks(week_start) ON DELETE RESTRICT,
    request_hash TEXT NOT NULL,
    result_json TEXT NOT NULL CHECK (json_valid(result_json))
);

CREATE TRIGGER closed_weeks_no_update BEFORE UPDATE ON closed_weeks
BEGIN SELECT RAISE(ABORT, 'Closed weeks are read-only.'); END;
CREATE TRIGGER closed_weeks_no_delete BEFORE DELETE ON closed_weeks
BEGIN SELECT RAISE(ABORT, 'Closed weeks are read-only.'); END;
CREATE TRIGGER closed_placements_no_update BEFORE UPDATE ON closed_placements
BEGIN SELECT RAISE(ABORT, 'Closed placements are read-only.'); END;
CREATE TRIGGER closed_placements_no_delete BEFORE DELETE ON closed_placements
BEGIN SELECT RAISE(ABORT, 'Closed placements are read-only.'); END;
CREATE TRIGGER carryover_operations_no_update BEFORE UPDATE ON carryover_operations
BEGIN SELECT RAISE(ABORT, 'Carryover receipts are read-only.'); END;
CREATE TRIGGER carryover_operations_no_delete BEFORE DELETE ON carryover_operations
BEGIN SELECT RAISE(ABORT, 'Carryover receipts are read-only.'); END;
