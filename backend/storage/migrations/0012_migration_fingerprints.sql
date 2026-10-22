-- Protect new upgrade identities. Earlier SQL has known historical variants;
-- do not invent fingerprints for migrations 1-11 after they have already run.
CREATE TABLE migration_fingerprints (
    version INTEGER PRIMARY KEY NOT NULL REFERENCES schema_migrations(version),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64)
);
