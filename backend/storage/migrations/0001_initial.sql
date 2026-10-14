-- 0001: tasks with stable identity.
-- Projects, subtasks, deadlines, estimates and completion arrive in later migrations.

CREATE TABLE tasks (
    id          TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    title       TEXT NOT NULL CHECK (length(trim(title)) > 0 AND length(title) <= 200),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    revision    INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1)
);

CREATE INDEX tasks_created_at ON tasks (created_at);
