-- 0002: projects, subtasks, notes, deadlines, estimates and completion.
--
-- Tasks gain a project, an optional parent task, and the planning fields from the
-- Build Plan's Task record. SQLite cannot ADD COLUMN a NOT NULL foreign key, so the
-- table is rebuilt: every 0001 task is carried over unchanged into a default project.
-- Identity (id, title, created_at, revision) is preserved exactly.

CREATE TABLE projects (
    id          TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    name        TEXT NOT NULL CHECK (length(trim(name)) > 0 AND length(name) <= 100),
    is_default  INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    revision    INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1)
);

-- At most one default project; the partial index makes a second one impossible.
CREATE UNIQUE INDEX projects_single_default ON projects (is_default) WHERE is_default = 1;

-- Tasks that existed before projects did need somewhere to live.
INSERT INTO projects (id, name, is_default, created_at, updated_at, revision)
VALUES (
    lower(
        hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' || substr(hex(randomblob(2)), 2)
        || '-' || substr('89ab', abs(random()) % 4 + 1, 1) || substr(hex(randomblob(2)), 2)
        || '-' || hex(randomblob(6))
    ),
    'Inbox',
    1,
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    strftime('%Y-%m-%dT%H:%M:%fZ', 'now'),
    1
);

CREATE TABLE tasks_new (
    id               TEXT PRIMARY KEY NOT NULL CHECK (length(id) = 36),
    project_id       TEXT NOT NULL REFERENCES projects(id),
    -- One level only: a subtask may not itself have subtasks. The domain layer enforces
    -- that, which also makes a parent cycle impossible.
    parent_id        TEXT REFERENCES tasks_new(id),
    title            TEXT NOT NULL CHECK (length(trim(title)) > 0 AND length(title) <= 200),
    notes            TEXT NOT NULL DEFAULT '' CHECK (length(notes) <= 2000),
    -- Date-only, never an instant: "date-only deadlines stay date-only".
    deadline         TEXT CHECK (deadline IS NULL OR deadline GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    estimate_minutes INTEGER CHECK (estimate_minutes IS NULL OR (estimate_minutes >= 1 AND estimate_minutes <= 10080)),
    -- Set only on tasks with no subtasks. A task with subtasks derives its completion
    -- from them, so this column stays NULL for parents.
    completed_at     TEXT,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    revision         INTEGER NOT NULL DEFAULT 1 CHECK (revision >= 1),
    CHECK (parent_id IS NULL OR parent_id <> id)
);

INSERT INTO tasks_new (id, project_id, parent_id, title, notes, deadline,
                       estimate_minutes, completed_at, created_at, updated_at, revision)
SELECT t.id,
       (SELECT id FROM projects WHERE is_default = 1),
       NULL, t.title, '', NULL, NULL, NULL, t.created_at, t.updated_at, t.revision
FROM tasks AS t;

DROP TABLE tasks;
ALTER TABLE tasks_new RENAME TO tasks;

CREATE INDEX tasks_created_at ON tasks (created_at);
CREATE INDEX tasks_project ON tasks (project_id, created_at);
CREATE INDEX tasks_parent ON tasks (parent_id);
