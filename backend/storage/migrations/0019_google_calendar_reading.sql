-- Reading the user's own Google calendars (user decisions 2026-11-02): the user picks
-- which calendars to follow; their events are shown beside each day and any event can
-- become a task. BearPlans never changes these calendars. Cached text is data only.
CREATE TABLE google_source_calendars (
    calendar_id TEXT PRIMARY KEY NOT NULL CHECK (length(calendar_id) BETWEEN 1 AND 300),
    summary     TEXT NOT NULL,
    color       TEXT NOT NULL DEFAULT '',
    is_primary  INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
    followed    INTEGER NOT NULL DEFAULT 0 CHECK (followed IN (0, 1)),
    in_source   INTEGER NOT NULL DEFAULT 1 CHECK (in_source IN (0, 1)),
    fetched_at  TEXT NOT NULL
);

-- Events of followed calendars in a window around today, replaced on each read.
CREATE TABLE google_source_events (
    calendar_id TEXT NOT NULL REFERENCES google_source_calendars(calendar_id) ON DELETE CASCADE,
    event_id    TEXT NOT NULL CHECK (length(event_id) BETWEEN 1 AND 300),
    summary     TEXT NOT NULL,
    location    TEXT NOT NULL DEFAULT '',
    html_link   TEXT NOT NULL DEFAULT '',
    all_day     INTEGER NOT NULL CHECK (all_day IN (0, 1)),
    start_at    TEXT,   -- timed events: aware ISO instant
    end_at      TEXT,
    first_day   TEXT NOT NULL CHECK (first_day GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    last_day    TEXT NOT NULL CHECK (last_day GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    PRIMARY KEY (calendar_id, event_id)
);
CREATE INDEX google_source_events_days ON google_source_events(first_day, last_day);

-- Events the user turned into tasks; kept when the event leaves the cached window.
CREATE TABLE google_event_tasks (
    calendar_id TEXT NOT NULL,
    event_id    TEXT NOT NULL,
    task_id     TEXT NOT NULL UNIQUE REFERENCES tasks(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    PRIMARY KEY (calendar_id, event_id)
);
