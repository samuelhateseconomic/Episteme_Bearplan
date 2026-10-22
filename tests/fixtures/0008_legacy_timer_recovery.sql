-- Extend the existing timer; old session/interval/receipt fields remain intact.
ALTER TABLE timer_sessions ADD COLUMN pause_reason TEXT
    CHECK (pause_reason IS NULL OR pause_reason IN ('manual', 'sleep'));

CREATE TABLE timer_recovery_gaps (
    id TEXT PRIMARY KEY NOT NULL,
    session_id TEXT NOT NULL REFERENCES timer_sessions(id),
    reason TEXT NOT NULL,
    started_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    excluded_microseconds INTEGER CHECK (excluded_microseconds IS NULL OR excluded_microseconds >= 0),
    clock_discontinuity INTEGER NOT NULL CHECK (clock_discontinuity IN (0, 1)),
    resolved_at TEXT,
    resolution TEXT CHECK (resolution IN ('resume', 'finish')),
    CHECK ((resolved_at IS NULL AND resolution IS NULL)
        OR (resolved_at IS NOT NULL AND resolution IS NOT NULL))
);
CREATE UNIQUE INDEX timer_one_unresolved_gap ON timer_recovery_gaps(session_id)
    WHERE resolved_at IS NULL;
