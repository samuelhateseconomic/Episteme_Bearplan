-- Pause / Resume automatic Google sync (user-confirmed 2026-11-03). While paused_at is
-- set, the background worker starts no sync; an explicit "Sync now" still runs once.
-- The pause survives restarts until the user chooses Resume.
ALTER TABLE google_sync ADD COLUMN paused_at TEXT;
