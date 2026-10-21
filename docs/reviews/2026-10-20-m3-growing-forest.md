# M3 first session — growing trees and the forest

October 20, 2026, America/Los_Angeles. Baseline `809761d`, plus the preserved
uncommitted progress decision allowing M3 before Mac acceptance. User scope:
one free species, three growth stages, Track artwork, persistent mature/unfinished
tree outcomes; local commit after passing review, no push or next-ticket build.

## Implementation and eligibility

New countdowns enroll one free **Pine**. Confirmed active duration divided by the
selected duration determines growth: seedling below 50%, sapling from 50%, mature
only after finalized completed status with the exact planned integer microseconds
and no unresolved interruption. The 50% visual boundary is an implementation
choice, not a new timer-credit rule. No animation, wall time or rounded percentage
earns progress. Pause/review preserve growth; recovery resumes the same tree.

Schema **9** adds `trees`, a non-cascading session reference, a unique session ID
and paired outcome/finalization fields. Enrollment shares the start transaction.
`TimerService._finish` invokes shared `finalize_tree` in its existing transaction:
timer intervals, session result and tree outcome either commit together or roll
back. Explicit finish/recovery receipts share their mutation transaction; automatic
expiry needs no receipt and may finalize before a later control request's receipt.
Exact expiry creates a mature tree; early/interrupted finish
preserves confirmed time and creates an unfinished tree. Retry, refresh and
concurrent finish cannot create a second tree. No tree deletion or manual editing
is offered in this build; excluded time is never reintroduced by an Undo operation.

**Eligibility begins with successful new starts using this forest-aware build.**
The migration creates no trees. Already-finished and already-unfinished sessions
remain ineligible, including later recovery, old request replay and finalization.
Original rows, migration receipts, session IDs/context and task history are retained.

`backend/domain/forest.py` owns enrollment, validation, growth, finalization and
forest reads for API/future tools. `GET /api/forest` returns finalized outcomes;
timer responses include nullable `tree`. The forest remains inside Track, with
lightweight SVG Pine artwork, historical project/parent/task context, associated
session, dates and confirmed time. Task edits, moves, completion or permitted
subtask removal cannot rewrite the saved collection. Trees never complete tasks.
Loading, empty, failure/retry and old-session eligibility states are present.
Move-only dragging, existing multiple planned dates and closed history are preserved.
No dependencies, applied migrations, timer-credit arithmetic or power rules changed.

## Checks and evidence

Actual host: **Linux x86_64**, Python **3.12.14**, Node **24.19.0**, Chromium
**154.0.8037.57**. All mutation/failure/browser fixtures use disposable databases;
no personal database or normal app instance is upgraded or modified.

- `npm --prefix frontend test`: **90 passed**, 11.59 s; typecheck and production
  build passed. Coverage includes backend-only growth despite browser ticks,
  paused/review display, almost-full unfinished result, legacy sessions, forest
  context, failed refresh/retry and stale response exclusion.
- `PYTHONPATH=/workspace/bearplans-setup BEARPLANS_EVIDENCE_DIR=/workspace/work/m3/evidence .venv/bin/python -m pytest -p system_browser -q -s`:
  final full core **500 passed**, zero failed/skipped, **142.73 s**. Includes
  foundation/planner/history/Move-only dragging, timer, migration, recovery, real
  process/browser and final forest tests. Full log: `full-core-final.log` beside
  the evidence directory.
- New forest API: **2 passed**, 0.08 s. Initial forest browser journey:
  **1 passed**, 4.00 s. Real Chromium uses the built production interface and a
  real disposable service; only its initial mature/sapling fixture uses fake clocks.
- Domain coverage checks 50% and final-microsecond boundaries, normal expiry,
  pause/resume, early finish at zero and just below full duration, Needs review,
  recovery continuation/finish, simulated sleep/maintenance wakes, same tree after
  restart, repeated/concurrent finalization, injected failed enrollment/finalization
  and interrupted-resolution rollback/retry, exact legacy-row migration rollback/
  retry, old start-receipt replay and historical edits/removal preservation.
- Browser evidence covers live restart review, keyboard-compatible controls,
  continuation, pause/reload, committed-but-lost finish response and retry, unique
  mature/unfinished session associations, exact forest equality after process
  restart, unchanged task completion, SQLite integrity and foreign keys. Inspected
  Track and forest at **1440/375 px**, light/dark; no page errors or horizontal
  overflow. Screenshots/log: `/workspace/work/m3/evidence`, `full-core.log` beside it.
- Existing real one-minute journey now checks that the monitor atomically creates
  one mature tree while the browser is closed, before any timer read can resolve
  expiry. Final run saved **60.000000 s**, independently observed after
  **60.656 s**, one mature tree and unchanged task completion. Six task writes
  during a separate short real timer had median **0.001679 s**, max **0.002916 s**;
  browser task creation during tracking took **0.145 s**. These are Linux
  observations, not target-Mac or external-stopwatch acceptance.
- Independent source review found no implementation blocker. Scoped diff and local
  documentation links are checked before the authorized local commit.

The first full run had **497 passed / 1 failed**, 177.04 s. The existing weekly
browser test opened date controls before week navigation finished: the old week
also had one checked card, so its count/completion assertions did not establish
the destination. Added an explicit wait for the destination heading; planner code
and Move behavior are unchanged. Final forest domain plus weekly/forest browser
checks passed together: **21 passed**, 8.10 s. The final full run above also covers
the two final domain guard/legacy-replay cases added after the first collection.
The forest browser fixture explicitly clears the deliberate lost-response feedback
via Refresh timer before capturing ordinary collection screenshots.

Initial setup/fixture issues: default sandbox sockets are denied, which stalled
TestClient and prevented loopback browser setup. The API/browser/full-core runs use
the permitted localhost execution context and installed Chromium via the existing
external `system_browser` helper. No assertions are bypassed. A schema-5 preservation
test initially classified the new empty trees table as old data; it now compares
all original tables and explicitly checks that trees starts empty. The schema-7
upgrade test now expects the latest version rather than hard-coded version 8,
retaining its original-row assertions. Failed/setup-stalled attempts are not passes.

## Implementation decision and platform checkpoint

**Implementation review: Pass on Linux.** No unresolved implementation blocker.
The implementation commit is `e0ccf1b`,
`M3: add confirmed tree growth and persistent forest`. The original request
authorized a local commit only; the user subsequently authorized documenting the
partial-M3 status and pushing this implementation plus the clarification to GitHub
`main`. Shared progress
and README document eligibility, pending platform evidence and the next session;
AGENTS records the current tree invariants. Local links and diff checks pass.

**M2 Mac acceptance remains pending; the overall M3 milestone is not complete.**
Only M3's first session is complete. Remaining M3 work is coins and the tree shop
(including three purchasable species), daily streaks, and statistics with session
corrections/reward adjustments. Those sessions have not started. AI, integrations
and deployment were also not implemented. Simulated recovery, Linux process
restart/stall and same-host timing do not establish actual Mac observations.

The user authorized proceeding without waiting for Mac testing. After M3
implementation is complete, combined **M2/M3 verification is required before
release readiness**: target-Mac sleep/wake, maintenance wakes and supported
battery/standby/hibernate, interruption recovery and retries, forward/backward clock
changes, midnight/DST and externally referenced real-duration acceptance. Confirm
uncertain/paused time never grows a tree or earns a later reward, recovery preserves
the original tree, early/interrupted finish stays unfinished and full confirmed
completion creates exactly one mature result. Preserve the detailed
[M2 checklist](2026-10-18-m2-recovery.md#target-mac-acceptance-still-required).

Next eligible session is **coins and the tree shop**, not started. Scope,
dependencies, relevant functions, acceptance cases, unresolved proposed defaults
and a continuation prompt are in [shared progress](../PROGRESS.md#next-m3-session--coins-and-tree-shop-not-started).
