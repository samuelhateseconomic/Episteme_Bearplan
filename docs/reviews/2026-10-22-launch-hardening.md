# Launch compatibility and startup hardening — October 22, 2026

User authorized the [diagnosis plan](2026-10-22-launch-diagnosis-plan.md), then
requested continuing. Scope is the existing launch failure and its durable repair;
no next feature, push, timer policy, reward policy or planner interaction change.
Baseline: `aaf9b67`. Existing staged/unstaged build-review and roadmap edits and
the recovery stash are preserved separately from the scoped local commit.

## Cause and implementation

The genuine preserved local migration 8 has the same version/name as current 8
but creates `timer_recovery_gaps` and `pause_reason`, rather than
`timer_interruptions`. The old runner trusted version/name alone. This reproduces
the reported schema-10 startup error without dropping or fabricating a table.
The normal database had already received repair 11 before this build.

- Keep applied migrations 8 and 11 byte-for-byte unchanged. Repair 11 creates the
  missing canonical interruption table/indexes without deleting legacy evidence.
  The compatibility fixture freezes the genuine earlier SQL from the saved stash.
- Validate the required schema after migrations, before constructing services:
  tables, column shapes/defaults/primary keys, foreign keys, uniqueness, named
  indexes including ordering/collation/predicates/expressions, CHECK constraints
  and immutable-history triggers. Expected objects are derived from shipped SQL
  in memory; validation reads one saved-schema snapshot. Compatible extra legacy
  tables/columns remain. Unknown required-object mismatches fail with object names
  and backup/repair guidance rather than resetting data.
- New migration 12 stores SHA-256 receipts for applied SQL from version 12 onward,
  atomically with each migration. Missing/changed receipts refuse further upgrades.
  No invented retrospective fingerprint is attached to legacy migrations 1–11.
- Claim the socket before timer initialization; a busy port cannot itself recover
  a saved running timer. Catch storage/SQLite/startup errors, close sockets and
  release locks. Announce readiness and write instance metadata only after the
  application lifespan and Uvicorn listener have started successfully.
- Share a standard-library build identity between launcher/backend. Before setup
  or rebuilding the interface, recognize a held same-build instance and reuse it.
  Different/unknown builds explain a deliberate restart, without rebuilding,
  opening, stopping or replacing that service. Identity covers application inputs,
  not personal records, docs, build outputs or environment values.

Legacy recovery audit rows remain raw and intact. They lack the historical
confirmed-credit snapshots required for lossless canonical conversion. Do not
fabricate those snapshots or replay legacy unresolved flags over a newer explicit
canonical Resume/Finish decision. Their old resolved history is not newly exposed
in the current recovery interface. Existing timer transitions remain authoritative;
there is no parallel recovery system and no uncertain-time/reward backfill.

This validator checks required structural compatibility, not arbitrary row-level
semantic corruption or the behavior of every additional legacy object. It is not a
backup substitute. Future repairs add a migration; editing applied SQL is rejected.

## Saved-data evidence

Before normal-data changes, SQLite's backup API created a durable backup beside
the saved database:
`bearplans-pre-launch-hardening-20261022T160957259474Z.sqlite3`.
The original was opened read-only within a transaction. Backup permissions are
0600; every original row across 17 tables matched, integrity was `ok`, and foreign
key violations were zero. Saved schema was 11. No task text/content was printed.

A private copy upgraded 11 → 12 with all existing table columns and rows unchanged
and existing migration receipts retained. App construction then performed only
the expected cold-start recovery: saved running → Needs review, close its open
interval at the confirmed checkpoint and append a canonical interruption. Existing
confirmed credit, task/history/snapshot/reward data and legacy gaps were unchanged.

A real `launch.py --no-browser` process against that private copy returned HTTP 200,
recorded matching build identity, reused a second same-build launch, stopped
gracefully and restarted successfully. All copy rows stayed unchanged across both
launcher lifetimes, and instance metadata was removed on stop. Schema was 12.

The normal port was not listening before launch. A second fresh private read-only
snapshot captured schema 11 immediately before the normal launch. Actual
`python3 launch.py --no-browser` started at **schema 12**, with HTTP 200 for both
health and the built interface. Every original field matched that snapshot except
the one expected cold-start recovery described above; the saved running session
became Needs review, its revision advanced once, and exactly one interruption was
added. All confirmed credit and legacy audit rows matched. Integrity was `ok` and
foreign-key issues were zero; saved instance identity matched current source.

A second normal launcher invocation returned success and reused the same build.
Ctrl+C stopped it gracefully with exit 0. The normal launcher then restarted at
schema 12, and the same complete invariant comparison passed again: no duplicate
interruption, interval, session result, credit or reward. The local service remains
available at `http://127.0.0.1:8765/`. No Resume/Finish action was chosen for the user.

## Verification

Host: macOS 26.6.2 (25G83), Darwin arm64; Python 3.13.15, Node 24.21.0.
Real browser journeys used Chrome 155.0.8059.85, loopback HTTP and disposable data.
Evidence screenshots are under ignored `.evidence/launch-hardening/`.

Commands:

```sh
BEARPLANS_E2E_CHANNEL=chrome BEARPLANS_EVIDENCE_DIR=.evidence/launch-hardening .venv/bin/python -m pytest -q -s
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Initial full core: **698 passed, 1 failed, 158.00 s**. The failure was the existing
shop lost-response browser journey: after GET reads were unblocked, an authoritative
wallet refresh could acknowledge the committed purchase before the explicit Retry
POST. UI/ownership/balance were correct, but the test expected two captured POSTs
and saw one. The unchanged test passed once in isolation, corroborating the race.
The test now keeps GET reads blocked until the retry POST arrives and explicitly
waits for that request, retaining payload equality, single debit/ownership and
restart assertions. No shop product code changed. The journey then passed **four
consecutive runs** (3.58/3.59/3.42/3.36 s); frontend Shop tests **11 passed**.

**Final full core: 699 passed, zero failures/skips, 158.03 s.** Independent focused
source/storage/startup/identity review: **93 passed, 1.55 s**, no blocking finding.
Its separate storage compatibility review passed **70 tests, 1.52 s**.

Frontend: **122 passed, 3.89 s**; typecheck and production build passed. Compileall,
updated documentation links and scoped whitespace checks passed. New coverage exercises the exact legacy-8
upgrade, current/rich saved data, canonical decisions over legacy flags, repeat
opens, failed repair/upgrade rollback and retry, missing/incompatible schema objects,
fingerprint failures, and launcher/startup/stale-instance cleanup.

The final run's awake browser-closed minute saved exactly **60.000000 s**, observed
after **60.225 s** against an independent elapsed reference. The 0.225 s is
observation latency past expiry, not automatically credited time. This repair does
not supply a new Mac ten-minute accuracy or maximum-duration acceptance result.

No real clock change, laptop sleep/wake, battery/standby/hibernate or 180-minute
acceptance was performed. Existing combined M2/M3 hardware gates remain pending.
Broader M1 hands-on planner certification remains a separate outstanding gate.

Inspected the synthetic restart-recovery screenshot
`timer-06-restart-review.png`: remaining countdown, confirmed active time, last
confirmed checkpoint, explicit Continue/Save-and-finish controls, and the statement
that time since the checkpoint is excluded are visible. Tree growth is frozen at
confirmed time; the interface explains that finishing does not complete the task.
Existing wide/narrow/keyboard planner and recovery browser regressions passed.

## Decision and demonstration

Launch-repair implementation decision: **Pass on Mac**, including normal launch,
preservation, restart and the clean final regression run. Recovery logic itself was
not rewritten by this ticket. Overall M2: **not newly passed**; hardware/long-duration evidence
is still required. M3 remains partial; statistics/session corrections are not
started. No next milestone or feature was begun.

Demonstration after verification:

1. Run `python3 launch.py` from the project; wait for the ready banner and open URL.
2. Inspect Track: the previously interrupted session retains confirmed time in
   Needs review. Choose Resume or save confirmed time and finish explicitly.
3. Run the launcher again: the same build reuses the existing service.
4. Finish or pause active work before deliberately stopping for a source update.
   An older/unknown held instance now explains the required restart.

Commit scope contains this repair, its tests, README/progress and the prior relevant
uncommitted launch-repair/diagnosis records. Applied 8/11 SHA-256 values matched
their pre-implementation values. The genuine legacy fixture SHA-256 is
`d7b41e9e962e0fcde2fb8e5c2160f2317c3e322d8225ec93ee018009e090d743`.
Both staged and unstaged patches for the build-review plan and roadmap matched
their starting hashes; stash `ed5e990c6c1fd649ed60083ec8e61b90bdf2153c` remains
unchanged. These planning files are excluded from the user-authorized local commit.
No database, personal content, push or next feature is included.
