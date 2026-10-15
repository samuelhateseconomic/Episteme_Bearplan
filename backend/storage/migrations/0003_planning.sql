-- Planned dates reference existing task identities. Completion and deadlines stay
-- on tasks; a placement carries neither copies nor independent completion state.
CREATE TABLE planned_items (
    id           TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    task_id      TEXT NOT NULL REFERENCES tasks(id) ON DELETE RESTRICT,
    planned_date TEXT NOT NULL CHECK (
        planned_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    ),
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    revision     INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    UNIQUE (task_id, planned_date)
);

CREATE INDEX planned_items_date ON planned_items (planned_date);
