-- Countdown results retain the task/project identity and display context at start.
-- These are historical references, deliberately not cascading foreign keys to live
-- tasks: permitted subtask removal must never erase recorded work.
CREATE TABLE timer_sessions (
    id TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    start_operation_id TEXT UNIQUE NOT NULL CHECK (length(start_operation_id) = 36),
    task_id TEXT NOT NULL,
    task_title TEXT NOT NULL,
    project_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    parent_title TEXT,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes BETWEEN 1 AND 180),
    state TEXT NOT NULL CHECK (state IN ('running', 'paused', 'needs_review', 'finished')),
    active_microseconds INTEGER NOT NULL DEFAULT 0
        CHECK (active_microseconds >= 0 AND active_microseconds <= duration_minutes * 60000000),
    started_at TEXT NOT NULL,
    checkpoint_at TEXT NOT NULL,
    finished_at TEXT,
    outcome TEXT CHECK (outcome IN ('completed', 'finished_early', 'interrupted')),
    review_reason TEXT,
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    CHECK ((state = 'finished' AND finished_at IS NOT NULL AND outcome IS NOT NULL)
        OR (state <> 'finished' AND finished_at IS NULL AND outcome IS NULL))
);

-- Needs review also occupies the allowance until explicitly resolved. This index
-- is the final atomic barrier even when requests arrive concurrently.
CREATE UNIQUE INDEX timer_one_unfinished ON timer_sessions ((1))
    WHERE state <> 'finished';
CREATE INDEX timer_task_history ON timer_sessions (task_id, started_at);

CREATE TABLE timer_intervals (
    id TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    session_id TEXT NOT NULL REFERENCES timer_sessions(id),
    started_at TEXT NOT NULL,
    checkpoint_at TEXT NOT NULL,
    ended_at TEXT,
    active_microseconds INTEGER NOT NULL DEFAULT 0 CHECK (active_microseconds >= 0)
);
CREATE INDEX timer_interval_session ON timer_intervals (session_id, started_at);
CREATE UNIQUE INDEX timer_one_open_interval ON timer_intervals (session_id) WHERE ended_at IS NULL;

CREATE TABLE timer_operations (
    operation_id TEXT PRIMARY KEY NOT NULL CHECK (length(operation_id) = 36),
    session_id TEXT NOT NULL REFERENCES timer_sessions(id),
    action TEXT NOT NULL CHECK (action IN ('start', 'pause', 'resume', 'finish')),
    fingerprint TEXT NOT NULL
);
