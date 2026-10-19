-- Preserve the existing sessions, intervals and request receipts unchanged.
-- Every interruption retains the last confirmed credit, the observed reason and
-- the explicit resolution. Wall timestamps describe observations, never credit.
CREATE TABLE timer_interruptions (
    id TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    session_id TEXT NOT NULL REFERENCES timer_sessions(id),
    kind TEXT NOT NULL CHECK (kind IN ('service_restart', 'sleep', 'clock_change', 'checkpoint_gap')),
    reason TEXT NOT NULL,
    checkpoint_at TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    confirmed_active_microseconds INTEGER NOT NULL CHECK (confirmed_active_microseconds >= 0),
    measured_sleep_microseconds INTEGER CHECK (measured_sleep_microseconds >= 0),
    resolved_at TEXT,
    resolution TEXT CHECK (resolution IN ('resume', 'finish')),
    CHECK ((resolved_at IS NULL AND resolution IS NULL)
        OR (resolved_at IS NOT NULL AND resolution IS NOT NULL))
);
CREATE INDEX timer_interruption_session ON timer_interruptions (session_id);
CREATE UNIQUE INDEX timer_one_unresolved_interruption ON timer_interruptions (session_id)
    WHERE resolved_at IS NULL;
