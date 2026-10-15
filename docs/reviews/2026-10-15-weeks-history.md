# Weeks, closed history and reviewed carryover — daily build review

Date: 2026-10-15 (America/Los_Angeles); pulled forward from the Oct 17 roadmap row.
Baseline: `a21cb49`. Reviewed application build: `7155bc2`.
Implementation review: **Pass**. Overall operator acceptance: **Pass** (2026-10-15).
Broader M1 milestone review remains separate and pending. No push and no next feature.

## Acceptance scenario and design

End Week first previews the displayed task details, dates and unique leaf completion
totals. Confirmation freezes those values and archives the original placements in
one transaction. A closed week remains reproducible after later project/task edits,
completion, scheduling, permitted subtask removal and process restart. Historical
cards are read-only and distinguish **At closure** from **Current task** status.
Empty weeks close with 0 of 0 complete (0%).

Migration `0005_closed_weeks.sql` adds:

- `closed_weeks`: unique Monday, Sunday, UTC closure instant, application timezone,
  versioned JSON containing complete displayed task fields, frozen project/parent
  context, original placements, and completed/total unique-leaf counts.
- `closed_placements`: original placement IDs and every original field, plus the
  closed source week. Task IDs remain historical references without a live-task FK,
  so permitted deletion of a current subtask cannot erase history.
- `carryover_operations`: operation ID, normalized source/selections hash, and the
  saved result. Receipts are committed with destination placements.

Applied migrations 1–4 are unchanged. Closing transfers source placements from
active storage into immutable historical storage without changing task records.
SQLite triggers prevent updates/deletion of snapshots, archived placements and
carryover receipts. Existing active unique-task and task/day constraints remain.

The previous one-day decision now applies to **active plans across open weeks**;
historical records do not consume that allowance. This permits carrying the same
unfinished task forward while preserving its original week. Multi-day work within
active planning still requires explicit subtasks. Counts defensively deduplicate
task IDs and exclude parent containers, even with repeated historical references.

Carryover flow: close source → select unfinished-at-closure work → choose dates in
the immediately following Monday–Sunday week → review current details/destination
dates → Apply. Only existing, currently incomplete leaves are eligible. Currently
complete, deleted, new-parent and already-planned work is explained; closed
destinations are rejected. Task IDs, deadlines, notes, project, completion and any
future session references remain on the original task. No task copying, automatic
bulk carryover or source-history mutation occurs.

Shared Python functions in `backend/domain/weeks.py` implement previews, closure
and carryover. Preview hashes bind the reviewed details. Apply revalidates inside
`Database.write()`; changed state or failure leaves no partial changes. Repeated
closure returns the original snapshot. Retrying the same carryover operation returns
its original receipt, including after later task changes/destination closure. Reusing
the key with different work/dates conflicts. Failed UI saves retain the selections,
date, token and operation ID for retry. Reopening is unavailable; the closure preview
states this explicitly. Past/current/future closure is allowed because no date
restriction was requested.

## Checks actually performed

Detected **macOS 26.6.2 (25G83)**, Python **3.13.15**, Node **24.21.0**, installed
Chrome. All failure/migration/corruption/browser fixtures used disposable data.
No Windows run or new Mac sleep/wake test is claimed. No timer implementation.

| Command/check | Actual outcome |
| --- | --- |
| Baseline `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q` | **242 passed**, 20.43 s; previous weekly build verified |
| Baseline `npm --prefix frontend test` and `npm --prefix frontend run typecheck` | **32 tests passed**, 2.71 s; typecheck passed |
| New `.venv/bin/python -m pytest -q tests/test_weeks.py tests/test_weeks_restart.py` (loopback permitted) | **83 passed**, 3.53 s |
| Final `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q` | **326 passed, zero failed/skipped**, 27.71 s |
| Final `npm --prefix frontend test` | **40 passed**, 2.84 s |
| Final `npm --prefix frontend run typecheck` | Pass |
| Final `npm --prefix frontend run build` | Pass |
| `BEARPLANS_EVIDENCE_DIR=docs/reviews/evidence/weeks BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q tests/test_weeks_browser.py` | **1 passed**, 3.28 s; strengthened keyboard-activation rerun **1 passed**, 3.26 s; synthetic screenshots |
| Migration compatibility | v1/v2/v3 foundation regressions plus genuine v4→v5 upgrade preserve all task/project/placement fields; failed v5 rolls back to usable v4 and retry succeeds |
| Snapshot preservation | Complete JSON/archive tuples remain identical through project/parent/task edits, completion/reopening, new active scheduling, permitted subtask deletion, and launcher/service restarts |
| Counts and empty weeks | Duplicate references count leaves once; parent context excluded; empty snapshot and interface show 0/0 and 0% |
| Closed scheduling | Domain/API reject new assignments into closed dates, moves into/from closed history, same-date archived moves and removal; structured 409 errors retain all rows |
| Carryover | Identity/field preservation, following-week/year boundaries, invalid/missing input, current completion/deletion/parent changes, active-plan conflicts and closed destination cases pass |
| Replays/concurrency | Repeated/concurrent close and carryover create one result; order-normalized retry returns original receipt; changed key payload conflicts |
| Atomic failure/retry | Injected failure after snapshot insertion/archive copy, after one destination insert, and before receipt insertion rolls back everything; locked SQLite saves return useful 503 and retry succeeds |
| Browser recovery | Lost response after real committed carryover retains reviewed payload and reuses the same operation ID; retry produces exactly one placement |
| Local protection | New routes retain loopback Host and same-origin mutation checks |
| Source review | Separate backend/frontend/test review found no blocking defect; minor active-plan wording clarified |
| Documentation/diff | Scoped whitespace and local links pass; pre-existing planning edits and their staged state preserved; CLAUDE.md remains intact |

One initial browser test attempt timed out because its helper reused an already
checked control while Refresh carryover choices was still loading. The helper now
waits for enabled controls; the targeted and full journeys pass. This was a test
synchronization issue, with no dropped user data. An initial frontend test typing
issue was also corrected before the passing checks above.

Inspected synthetic screenshots at 1600 px, 1024 px and 375 px. Closed history,
preview, reviewed destination dates and current status are readable; no horizontal
overflow. Keyboard/focus/disabled controls remain covered by existing and new UI
checks. No personal screenshot is committed.

Evidence: [close preview](evidence/weeks/history-01-close-preview.png),
[frozen wide history](evidence/weeks/history-02-frozen-wide.png),
[carryover preview](evidence/weeks/history-03-carryover-preview.png),
[destination laptop](evidence/weeks/history-04-destination-laptop.png),
[closed narrow](evidence/weeks/history-05-closed-narrow.png).

## Normal running instance and saved data

After the checks passed, identified the schema-4 launcher/service (92840/92842)
at `http://127.0.0.1:8765/`, stopped that launcher gracefully and created
`bearplans-pre-weeks-20261015T155840Z.sqlite3` in the normal data folder using
SQLite's backup API. A disposable copy upgraded to schema 5 with matching original
task/project/placement SQL rows and clean integrity/FK checks. Restarted the current
launcher and verified schema 5, all **six tasks and three active placements**
unchanged, and clean integrity/FK checks. All history/receipt tables remain empty:
**no real week was closed and no personal carryover was applied**.

Read-only Chrome checks of the updated normal interface opened End Week preview
and Cancel. The complete planning response remained identical before/after; no
normal task/history changes or personal screenshots were made.

## Review decisions and remaining evidence

**Implementation review: Pass.** Requested behavior, persistence, migration,
failure recovery and regressions pass; no known blocking implementation defect.
Relevant local commit authorized, no push. Pre-existing staged edits to the roadmap
and review-plan files are preserved outside this commit. Shared guidance and progress
are updated; CLAUDE.md remains intact and points to them.

**Operator acceptance: Pass.** After receiving the implementation report and
demonstration checklist for `7155bc2`, the user said “Looks good to me” on 2026-10-15.
This records overall feature acceptance; it does not attest that each manual step
was individually performed. No application tests were rerun for this documentation
update; content, links and scoped diff were checked instead.

**Broader M1 milestone review: pending.** The daily build's acceptance does not
individually certify every broader milestone scenario. Previous projects/tasks
operator acceptance remains passed; retain the checklist below as evidence guidance.
Reopening, recurring work,
advanced reports, timers, rewards, AI and integrations remain deferred. Countdown is
the next roadmap build, **not started and not authorized by this request**.

Accepted limits: no automatic carryover, no reopening, no historical editing; each
current leaf still has one active planned date. Legacy schema-3 multi-day data still
requires explicit extra-date removal with the previous build before migration 4;
this build does not silently select dates. Saved current data had no such conflict.

## Five-minute demonstration

1. **Minute 1:** Refresh BearPlans and use a sample week with a completed leaf and
   an unfinished leaf. Choose End Week; verify details/counts, then Cancel once.
2. **Minute 2:** Preview again and Close week. Confirm the read-only badge, fixed
   At closure statuses and absence of historical completion/move/remove controls.
3. **Minute 3:** Edit or complete a current task in the project list. Revisit the
   closed week: its original details/counts remain, with Current task status separate.
4. **Minute 4:** Carry unfinished work, select an eligible task and a date in the
   following week, Review, then Apply. Completed/already-planned tasks should explain
   why they cannot be selected. Confirm the source stays unchanged and one current
   destination plan exists with the same deadline.
5. **Minute 5:** Refresh, navigate between the source and destination using the
   history selector/Previous/Next, then narrow the window and choose a day. Verify
   readable open/closed distinction and persistence. Close an empty sample week only
   if desired; it should show 0 of 0 (0%).
