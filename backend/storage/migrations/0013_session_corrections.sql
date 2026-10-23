-- Additive audit and adjustment records. Existing awards and raw identities stay.
CREATE TABLE session_correction_baselines (
    session_id TEXT PRIMARY KEY NOT NULL REFERENCES timer_sessions(id),
    intervals_json TEXT NOT NULL
);
CREATE TABLE session_corrections (
    operation_id TEXT PRIMARY KEY NOT NULL CHECK (length(operation_id) = 36),
    session_id TEXT NOT NULL REFERENCES timer_sessions(id),
    fingerprint TEXT NOT NULL,
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 500),
    before_json TEXT NOT NULL,
    after_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    result_json TEXT NOT NULL
);
CREATE INDEX correction_session_history ON session_corrections(session_id);
CREATE TABLE coin_adjustments (
    id TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    operation_id TEXT UNIQUE NOT NULL REFERENCES session_corrections(operation_id),
    session_id TEXT NOT NULL REFERENCES coin_enrollments(session_id),
    amount INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    ledger_position INTEGER NOT NULL CHECK (ledger_position >= 0)
);
CREATE INDEX coin_adjustment_session ON coin_adjustments(session_id);
CREATE TRIGGER correction_baseline_no_update BEFORE UPDATE ON session_correction_baselines
BEGIN SELECT RAISE(ABORT, 'Correction baselines are immutable'); END;
CREATE TRIGGER correction_baseline_no_delete BEFORE DELETE ON session_correction_baselines
BEGIN SELECT RAISE(ABORT, 'Correction baselines are immutable'); END;
CREATE TRIGGER correction_audit_no_update BEFORE UPDATE ON session_corrections
BEGIN SELECT RAISE(ABORT, 'Correction audit is immutable'); END;
CREATE TRIGGER correction_audit_no_delete BEFORE DELETE ON session_corrections
BEGIN SELECT RAISE(ABORT, 'Correction audit is immutable'); END;
CREATE TRIGGER coin_adjustment_no_update BEFORE UPDATE ON coin_adjustments
BEGIN SELECT RAISE(ABORT, 'Coin adjustments are immutable'); END;
CREATE TRIGGER coin_adjustment_no_delete BEFORE DELETE ON coin_adjustments
BEGIN SELECT RAISE(ABORT, 'Coin adjustments are immutable'); END;
