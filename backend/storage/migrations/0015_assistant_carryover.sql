-- Allow the assistant's reviewed week carryover ("move this week's unfinished to
-- next week") as an applied, undoable action. SQLite cannot alter a CHECK, so the
-- receipt tables are rebuilt with every existing row kept unchanged. The Undo
-- table references receipts, so it is copied aside and rebuilt after them.
-- Dropping a table drops its triggers; the immutability triggers are recreated.
CREATE TABLE assistant_action_undos_copy AS SELECT * FROM assistant_action_undos;
DROP TABLE assistant_action_undos;

CREATE TABLE assistant_actions_new (
    operation_id TEXT PRIMARY KEY NOT NULL CHECK (length(operation_id) = 36),
    kind TEXT NOT NULL CHECK (kind IN ('create_task', 'update_task', 'assign_task_date', 'complete_task',
                                       'start_timer', 'pause_timer', 'finish_timer', 'carry_over_week')),
    fingerprint TEXT NOT NULL,
    request_json TEXT NOT NULL CHECK (json_valid(request_json)),
    undo_json TEXT CHECK (undo_json IS NULL OR json_valid(undo_json)),
    result_json TEXT NOT NULL CHECK (json_valid(result_json)),
    created_at TEXT NOT NULL
);
INSERT INTO assistant_actions_new (operation_id, kind, fingerprint, request_json, undo_json, result_json, created_at)
    SELECT operation_id, kind, fingerprint, request_json, undo_json, result_json, created_at FROM assistant_actions;
DROP TABLE assistant_actions;
ALTER TABLE assistant_actions_new RENAME TO assistant_actions;

CREATE TABLE assistant_action_undos (
    operation_id TEXT PRIMARY KEY NOT NULL CHECK (length(operation_id) = 36),
    action_operation_id TEXT UNIQUE NOT NULL REFERENCES assistant_actions(operation_id),
    result_json TEXT NOT NULL CHECK (json_valid(result_json)),
    created_at TEXT NOT NULL
);
INSERT INTO assistant_action_undos (operation_id, action_operation_id, result_json, created_at)
    SELECT operation_id, action_operation_id, result_json, created_at FROM assistant_action_undos_copy;
DROP TABLE assistant_action_undos_copy;

CREATE TRIGGER assistant_action_no_update BEFORE UPDATE ON assistant_actions
BEGIN SELECT RAISE(ABORT, 'Assistant action receipts are immutable'); END;
CREATE TRIGGER assistant_action_no_delete BEFORE DELETE ON assistant_actions
BEGIN SELECT RAISE(ABORT, 'Assistant action receipts are immutable'); END;
CREATE TRIGGER assistant_undo_no_update BEFORE UPDATE ON assistant_action_undos
BEGIN SELECT RAISE(ABORT, 'Assistant Undo receipts are immutable'); END;
CREATE TRIGGER assistant_undo_no_delete BEFORE DELETE ON assistant_action_undos
BEGIN SELECT RAISE(ABORT, 'Assistant Undo receipts are immutable'); END;
