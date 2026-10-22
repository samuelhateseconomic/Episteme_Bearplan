# Launch diagnosis and proposed repair — October 22, 2026

Scope: user requested reviewing progress and yesterday's launch failure/temporary
fix, then a plan. No application implementation, normal-data mutation, restart,
commit or push was performed. Current HEAD: `aaf9b67` (daily streaks), two commits
ahead of cached origin/main; no fetch. Host: macOS 26.6.2 (25G83), Darwin arm64.

Read AGENTS.md, CLAUDE.md, progress, relevant build/review/roadmap sections and latest
launch/recovery/sync records. Inspected complete staged/unstaged changes, untracked
repair SQL/review and the preserved schema-8 migration in the stash. Three independent
read-only audits covered migration compatibility, startup and project status.

## Findings and current saved state

The supplied traceback reports schema 10 with no `timer_interruptions`. Current
saved metadata is now **schema 11** with `repair_timer_interruptions` recorded;
`timer_interruptions` exists with the expected columns. The legacy
`timer_recovery_gaps` table and `timer_sessions.pause_reason` also remain. Each
recovery table has one row. Quick check is `ok`; foreign-key issues are zero.
No task text, names, notes or session content was printed.

There is one saved session whose state is running, but a read-only HTTP HEAD to
`http://127.0.0.1:8765/` returned connection refused. This does not establish a live
timer or a successful current launch. No timer control or service signal was sent.

A read-only SQLite source connection and SQLite's backup API created an automatically
cleaned-up private temporary copy. Running `open_database`, `create_app` and a timer
read on that copy passed at schema 11. The saved session entered Needs review on the
copy, legacy recovery rows remained, and integrity/foreign keys passed. The normal
database was not migrated or otherwise changed. This verifies initialization on a
copy of actual saved data, not a normal-service end-to-end launch.

The first restricted read-only database open failed with `unable to open database
file`; the approved read-only diagnostic succeeded. The approved HEAD probe reported
connection refused; the backup-copy initialization passed. No approval was rejected.

## Reproduced cause

Two different SQL definitions used migration **8**, name **timer_recovery**:

- Preserved local implementation: adds `pause_reason` and `timer_recovery_gaps`.
- Current committed implementation: creates `timer_interruptions`.

The migration runner validates version/name only, not SQL identity or required
schema objects. A disposable exact-path reproduction used schema 7, the genuine
stashed migration 8, then current 9/10. It recorded schema 10 without the current
table and `create_app` raised the user's exact missing-table error. No table had
to be dropped. The legacy structures in the actual saved database corroborate
this compatibility cause.

Applying repair 11 to the disposable reproduction restored app initialization and
preserved legacy rows/session credit exactly. However, it creates an empty current
table; it does not translate legacy recovery history. The constructor may create a
new checkpoint-gap record for a legacy unresolved session. Old resolved evidence
remains stored in the legacy table but is not exposed in the current recovery view.
Preserved data and complete semantic compatibility are separate findings.

## Existing repair and remaining weaknesses

Yesterday's fix is present as untracked
`backend/storage/migrations/0011_repair_timer_interruptions.sql`, with a modified
regression and documentation. It is not in a commit, but it **has applied to the
saved database**. Preserve this applied SQL unchanged. Yesterday's review accurately
said its author had not touched the normal database; that is historical evidence,
not today's deployment state.

The existing test simulates a dropped current table and passes. It does not cover
the actual incompatible migration-8 upgrade. `IF NOT EXISTS` also cannot validate
an existing wrong table/column/index definition, and an already-applied migration
will not run again if a table subsequently disappears.

A separate disposable schema-11 probe demonstrated that `open_database` still
accepts a missing interruptions table. Startup then prints its schema/open banner
before `create_app` raises an uncaught SQLite error. The bind socket lacks explicit
cleanup on that path. The instance lock does release. A printed open URL therefore
does not prove the service successfully started.

## Proposed next implementation ticket

1. Make a durable WAL-safe backup before any normal-data repair or upgrade. Rehearse
   on a fresh copy; compare all existing user, timer, snapshot, tree, coin and receipt
   fields, integrity and foreign keys. Never reset/delete the saved database or
   modify migration receipts to force old SQL to rerun.
2. Add an exact legacy-8 -> current-10 -> repair-11 compatibility fixture, healthy
   current-schema and repeated-open preservation, failed-repair rollback/retry,
   missing/wrong columns/indexes and current-schema missing-table cases. Retain
   timer, reward, streak and planner regressions. Existing legacy recovery evidence
   must stay intact; no duplicate credit, trees, coins or decisions.
3. Add explicit required-schema validation after migrations and before constructing
   domain services. Recognize documented compatible legacy shapes; unknown layouts
   should produce an actionable schema-mismatch error while leaving data recoverable.
   Protect future migration identities with fingerprints/known manifests. Do not
   retroactively edit applied migration 8 or 11. Use a new migration if further
   structural compatibility changes are necessary.
4. Harden startup: handle storage/schema errors from app construction, explicitly
   close any claimed socket, release the instance lock, and emit readiness only
   after successful initialization. Test stale-instance/version detection so a
   rebuilt interface is not silently paired with an older backend.
5. Preserve legacy recovery evidence without blindly replaying old unresolved flags.
   A current canonical interruption may already have been explicitly resumed or
   finished. Legacy resolved gaps lack their own confirmed-credit snapshots; do not
   fabricate those from today's session total. Define any linkage/conversion as an
   explicit, tested compatibility step rather than another empty-table workaround.
6. Verify cold launch and restart on disposable copies, then deliberately launch
   the normal saved database with its backup available. Confirm schema, persisted
   recovery, task/history/reward preservation and the absence of the original error.
   Record/commit the scoped repair when authorized. Resume statistics work afterward.

## Fresh verification and decision

`.venv/bin/python -m pytest -q tests/test_timer_recovery.py::test_missing_recovery_table_is_repaired_before_legacy_review_startup tests/test_migrations.py`
-> **22 passed, 0.49 s**, zero failures/skips. Independent repeat: 22 passed, 0.50 s.
Exact legacy-upgrade and startup-error probes also reproduced the findings above.
Documentation-only handoff checks use links/diff/whitespace; no frontend rerun or
new hardware/milestone acceptance is claimed.

**Immediate missing-table repair: applied and verified on an actual-data copy.**
**Normal launch end-to-end: not verified in this check.**
**Durable compatibility/startup hardening: planned, not implemented.**
M3 is partially complete (forest/coins/shop/streaks); statistics/corrections are not
started. Combined M2/M3 Mac acceptance and release gates remain outstanding.
