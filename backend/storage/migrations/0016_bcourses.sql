-- bCourses (Berkeley's Canvas) read-only source cache. Refresh fetches outside any
-- transaction and then replaces source fields here; the user chooses which courses
-- to follow and which assignments become tasks. Source text is data only.
CREATE TABLE source_courses (
    course_id   TEXT PRIMARY KEY NOT NULL CHECK (length(course_id) BETWEEN 1 AND 40),
    name        TEXT NOT NULL,
    course_code TEXT NOT NULL DEFAULT '',
    term        TEXT NOT NULL DEFAULT '',
    followed    INTEGER NOT NULL DEFAULT 0 CHECK (followed IN (0, 1)),
    -- The BearPlans project its assignments go to; created on the first Add.
    project_id  TEXT REFERENCES projects(id) ON DELETE SET NULL,
    in_source   INTEGER NOT NULL DEFAULT 1 CHECK (in_source IN (0, 1)),
    fetched_at  TEXT NOT NULL
);

CREATE TABLE source_assignments (
    assignment_id     TEXT PRIMARY KEY NOT NULL CHECK (length(assignment_id) BETWEEN 1 AND 40),
    course_id         TEXT NOT NULL REFERENCES source_courses(course_id) ON DELETE RESTRICT,
    title             TEXT NOT NULL,
    due_at            TEXT,              -- UTC instant from bCourses, or NULL when none is published
    html_url          TEXT NOT NULL DEFAULT '',
    points_possible   REAL,
    source_updated_at TEXT,
    in_source         INTEGER NOT NULL DEFAULT 1 CHECK (in_source IN (0, 1)),
    fetched_at        TEXT NOT NULL,
    -- new: waiting for review; added: became task_id; dismissed: the user chose not to add it.
    status            TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'added', 'dismissed')),
    task_id           TEXT UNIQUE REFERENCES tasks(id) ON DELETE SET NULL,
    -- The bCourses due date the user last accepted, so a later change can be reviewed.
    accepted_due_at   TEXT,
    decided_at        TEXT,
    CHECK (status = 'added' OR task_id IS NULL)
);
CREATE INDEX source_assignments_course ON source_assignments(course_id);

CREATE TABLE source_sync (
    source          TEXT PRIMARY KEY NOT NULL CHECK (source IN ('bcourses')),
    last_attempt_at TEXT,
    last_success_at TEXT,
    last_error      TEXT
);
