-- Receipts for assistant changes the user explicitly applied. Each stores the
-- normalized request fingerprint and original result for replay, plus the
-- reviewed before/after state that Undo may restore. Receipts are immutable;
-- an Undo is a separate immutable record, at most one per applied action.
CREATE TABLE assistant_actions (
    operation_id TEXT PRIMARY KEY NOT NULL CHECK (length(operation_id) = 36),
    kind TEXT NOT NULL CHECK (kind IN ('create_task', 'update_task', 'assign_task_date', 'complete_task',
                                       'start_timer', 'pause_timer', 'finish_timer')),
    fingerprint TEXT NOT NULL,
    request_json TEXT NOT NULL CHECK (json_valid(request_json)),
    undo_json TEXT CHECK (undo_json IS NULL OR json_valid(undo_json)),
    result_json TEXT NOT NULL CHECK (json_valid(result_json)),
    created_at TEXT NOT NULL
);
CREATE TABLE assistant_action_undos (
    operation_id TEXT PRIMARY KEY NOT NULL CHECK (length(operation_id) = 36),
    action_operation_id TEXT UNIQUE NOT NULL REFERENCES assistant_actions(operation_id),
    result_json TEXT NOT NULL CHECK (json_valid(result_json)),
    created_at TEXT NOT NULL
);
CREATE TRIGGER assistant_action_no_update BEFORE UPDATE ON assistant_actions
BEGIN SELECT RAISE(ABORT, 'Assistant action receipts are immutable'); END;
CREATE TRIGGER assistant_action_no_delete BEFORE DELETE ON assistant_actions
BEGIN SELECT RAISE(ABORT, 'Assistant action receipts are immutable'); END;
CREATE TRIGGER assistant_undo_no_update BEFORE UPDATE ON assistant_action_undos
BEGIN SELECT RAISE(ABORT, 'Assistant Undo receipts are immutable'); END;
CREATE TRIGGER assistant_undo_no_delete BEFORE DELETE ON assistant_action_undos
BEGIN SELECT RAISE(ABORT, 'Assistant Undo receipts are immutable'); END;
