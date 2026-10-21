-- Eligibility starts with countdowns created by the forest-aware application.
-- Do not backfill finished or in-progress sessions from earlier builds.
CREATE TABLE trees (
    id TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    session_id TEXT UNIQUE NOT NULL REFERENCES timer_sessions(id),
    species TEXT NOT NULL CHECK (species = 'pine'),
    created_at TEXT NOT NULL,
    outcome TEXT CHECK (outcome IN ('mature', 'unfinished')),
    finalized_at TEXT,
    CHECK ((outcome IS NULL AND finalized_at IS NULL)
        OR (outcome IS NOT NULL AND finalized_at IS NOT NULL))
);
