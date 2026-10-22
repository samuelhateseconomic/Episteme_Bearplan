# Launch recovery-table repair — October 21, 2026

## Finding and acceptance

The reported `python3 launch.py` traceback failed while creating the app because
`TimerService` queried `timer_interruptions`, which was absent. The launcher had
printed schema version 10, while migration 8 is the migration that creates that
table. Therefore the saved database's recorded migration version and actual schema
did not agree. The traceback alone cannot identify how they diverged.

Acceptance: opening a disposable schema-10 database missing only
`timer_interruptions` applies a migration that recreates the table and its
indexes, preserves existing tasks/session checkpoint credit, and allows app
creation. An active legacy `Needs review` session receives a durable
`checkpoint_gap` record without crediting uncertain time.

Migration 11 uses `IF NOT EXISTS`, so existing tables, interruption records and
indexes remain unchanged. No user rule/default changed. The normal user database
was not opened, backed up, migrated or otherwise changed; no normal service was
restarted. The repair will apply when the user next launches this updated code.

## Implementation

- Added `backend/storage/migrations/0011_repair_timer_interruptions.sql` to
  restore the missing recovery table and indexes.
- Added a disposable schema-10 regression that drops the table, runs the normal
  `open_database` migration path, and constructs the app as the launcher does.
- Documented the repair and timer recovery behavior in `README.md`.

## Environment and verification

Actual host: **macOS (Darwin)**, Python **3.13.15**. All database mutation used
pytest disposable data under a temporary directory.

- `.venv/bin/python -m pytest -q tests/test_timer.py tests/test_timer_restart.py tests/test_timer_recovery.py tests/test_migrations.py tests/test_rewards.py tests/test_forest.py tests/test_streaks.py`
  → **201 passed in 14.28 s**.
- Scoped `git diff --check -- README.md tests/test_timer_recovery.py docs/PROGRESS.md`
  passed. The pre-existing modified planning documents were left untouched.

The first version of the new test dropped the table after applying the latest
migration, so reopening correctly did not rerun the already-recorded repair. The
fixture was corrected to reproduce the user's schema-10 state; the final
regression and combined test command passed.

## Decision

**Pass** for the migration and app-construction scenario. The normal database
launch was deliberately not attempted from this session. After pulling in the
source changes, run `python3 launch.py`; startup should apply migration 11 and
continue. If launch still fails, retain the full new traceback and do not delete
or replace `bearplans.sqlite3`.
