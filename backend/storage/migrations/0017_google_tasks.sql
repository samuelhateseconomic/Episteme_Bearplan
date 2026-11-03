-- Google Tasks sync (user decisions 2026-11-02): every project, task and subtask is
-- sent to Google Tasks (project -> task list, task -> task, subtask -> subtask);
-- a completion ticked in Google comes back. These tables only remember which Google
-- items BearPlans created. They deliberately have no foreign keys to projects/tasks,
-- so a task removed in BearPlans can still be found and removed from Google.
CREATE TABLE google_task_lists (
    project_id TEXT PRIMARY KEY NOT NULL CHECK (length(project_id) = 36),
    list_id    TEXT UNIQUE NOT NULL CHECK (length(list_id) BETWEEN 1 AND 200),
    created_at TEXT NOT NULL
);

CREATE TABLE google_tasks (
    task_id       TEXT PRIMARY KEY NOT NULL CHECK (length(task_id) = 36),
    list_id       TEXT NOT NULL CHECK (length(list_id) BETWEEN 1 AND 200),
    google_id     TEXT NOT NULL CHECK (length(google_id) BETWEEN 1 AND 200),
    -- The completion BearPlans last sent, so a tick made in Google can be told apart.
    pushed_status TEXT NOT NULL CHECK (pushed_status IN ('needsAction', 'completed')),
    updated_at    TEXT NOT NULL,
    UNIQUE (list_id, google_id)
);

CREATE TABLE google_sync (
    id              INTEGER PRIMARY KEY NOT NULL CHECK (id = 1),
    last_attempt_at TEXT,
    last_success_at TEXT,
    last_error      TEXT
);
