-- Optional start time on a planned day, and the Google Calendar events BearPlans
-- creates for them (user decisions 2026-11-02): a planned task with a time becomes an
-- event in a calendar BearPlans creates, with a popup reminder 30 minutes before.
-- Kept beside planned_items (not a new column) so placements and their archived
-- copies keep exactly their existing fields; removed with the placement.
CREATE TABLE placement_times (
    placement_id TEXT PRIMARY KEY NOT NULL REFERENCES planned_items(id) ON DELETE CASCADE,
    start_time   TEXT NOT NULL CHECK (start_time GLOB '[0-2][0-9]:[0-5][0-9]' AND start_time < '24:00')
);

-- The one calendar BearPlans created ("BearPlans"); it only ever writes there.
CREATE TABLE google_calendar (
    id          INTEGER PRIMARY KEY NOT NULL CHECK (id = 1),
    calendar_id TEXT NOT NULL CHECK (length(calendar_id) BETWEEN 1 AND 300),
    created_at  TEXT NOT NULL
);

-- No foreign key to planned_items: a removed placement's future event must still be
-- found and removed. start_at is the UTC instant last sent; past events are kept.
CREATE TABLE google_events (
    placement_id TEXT PRIMARY KEY NOT NULL CHECK (length(placement_id) = 36),
    event_id     TEXT NOT NULL UNIQUE CHECK (length(event_id) BETWEEN 1 AND 300),
    start_at     TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
