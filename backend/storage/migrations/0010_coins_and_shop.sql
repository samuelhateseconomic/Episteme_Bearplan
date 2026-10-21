-- Preserve every existing tree field while expanding the cosmetic species set.
CREATE TABLE trees_with_species (
    id TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    session_id TEXT UNIQUE NOT NULL REFERENCES timer_sessions(id),
    species TEXT NOT NULL CHECK (species IN ('pine', 'birch', 'oak', 'cherry')),
    created_at TEXT NOT NULL,
    outcome TEXT CHECK (outcome IN ('mature', 'unfinished')),
    finalized_at TEXT,
    CHECK ((outcome IS NULL AND finalized_at IS NULL)
        OR (outcome IS NOT NULL AND finalized_at IS NOT NULL))
);
INSERT INTO trees_with_species (rowid, id, session_id, species, created_at, outcome, finalized_at)
SELECT rowid, id, session_id, species, created_at, outcome, finalized_at FROM trees;
DROP TABLE trees;
ALTER TABLE trees_with_species RENAME TO trees;

-- Enrollment is explicit at new-session creation. Existing sessions, including
-- unfinished schema-9 tree sessions, never receive retroactive coin eligibility.
CREATE TABLE coin_enrollments (
    session_id TEXT PRIMARY KEY NOT NULL REFERENCES timer_sessions(id),
    coins_per_minute INTEGER NOT NULL CHECK (coins_per_minute BETWEEN 0 AND 1000000)
);
CREATE TABLE owned_species (
    species TEXT PRIMARY KEY NOT NULL CHECK (species IN ('birch', 'oak', 'cherry')),
    acquired_at TEXT NOT NULL
);
CREATE TABLE coin_ledger (
    id TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    kind TEXT NOT NULL CHECK (kind IN ('session_award', 'purchase')),
    amount INTEGER NOT NULL,
    session_id TEXT REFERENCES timer_sessions(id),
    species TEXT CHECK (species IN ('birch', 'oak', 'cherry')),
    created_at TEXT NOT NULL,
    CHECK ((kind = 'session_award' AND amount >= 0 AND session_id IS NOT NULL AND species IS NULL)
        OR (kind = 'purchase' AND amount <= 0 AND session_id IS NULL AND species IS NOT NULL))
);
CREATE UNIQUE INDEX coin_award_once ON coin_ledger(session_id) WHERE kind = 'session_award';
CREATE UNIQUE INDEX coin_species_purchase_once ON coin_ledger(species) WHERE kind = 'purchase';
CREATE TABLE shop_operations (
    operation_id TEXT PRIMARY KEY NOT NULL CHECK (length(operation_id) = 36),
    fingerprint TEXT NOT NULL,
    result_json TEXT NOT NULL
);
