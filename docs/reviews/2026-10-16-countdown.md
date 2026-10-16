# M2 first build — normal countdown tracking

Date: October 16, 2026, America/Los_Angeles. Baseline `69c6630`, schema 5.
Reviewed source, tests and this record are included together in the local build commit.
Schema after upgrade: **6**. No dependency change.

## Decisions

**Normal countdown implementation review: Pass.** Required normal-flow, boundary,
retry, persistence and UI cases pass. This decision covers the user's first-build
scope with conservative interruption handling, not automatic recovery.

**Overall M2 countdown/recovery gate: Fail — required recovery evidence outstanding.**
Full sleep/crash/clock-change reconciliation, actual Mac power-state cases, midnight,
DST and longer-session acceptance have not passed. They are not waived by the
normal countdown result. The recovery build has not started. No new operator
acceptance is claimed. Local commit authorized by the user for a passing build;
no push and no automatic next build.

**M1 technical prerequisite review: Pass.** The complete joined planner journey
and baseline regressions passed before countdown implementation began; no confirmed
planner prerequisite defect needed fixing. [M1 review](2026-10-16-m1-review.md)
separates this from historical operator acceptance and the broader operator/manual
gate, which is not newly certified. The current integration tests now also prove
unscheduled selection and session-linked task edit/movement preservation.

## Acceptance, transitions and storage

Before editing product code, described the running/paused/finished/needs-review
transitions, persisted sessions/intervals/checkpoints/receipts, one-session allowance,
uncertain-gap policy and normal-flow acceptance cases in the user update.

Track is directly accessible at `/#track` and through navigation. A leaf task's
Start tracking button selects that task on Track; Start countdown confirms its
chosen duration. Any existing leaf from any project is eligible, including
unscheduled and completed tasks. Containers are excluded and rejected by the domain.
The form initially suggests **25 minutes**, a changeable UI convenience rather than
a newly confirmed product default. Whole minutes **1–180** are enforced in UI,
typed API and shared domain functions.

Transitions: running → paused → running; running/paused → finished early; expiry →
finished/completed; discontinuity → needs_review. Review occupies the active slot
until **Save confirmed time and finish** explicitly excludes the unverified gap
and saves an interrupted result. There is no automatic restart/resume or correction
workflow. Finish never changes task completion. Task completion remains independent,
and completing a task does not end its timer.

Migration `0006_countdown.sql` adds:

- `timer_sessions`: original task/project IDs and display context, duration/state,
  active microseconds, UTC start/checkpoint/finish timestamps, outcome/review reason,
  revision and start operation ID. Historical IDs have no cascading live-task FK.
- `timer_intervals`: one interval per continuous active segment, with UTC
  start/checkpoint/end and credited microseconds; pauses are gaps between intervals.
- `timer_operations`: persistent request fingerprints and session/action receipts.

A partial unique index allows only one unfinished session, including paused and
needs-review states. Another allows one open interval per session. The saved session
row is the result; finalization updates it once instead of appending duplicate results.
Receipts reject request-key reuse for different work. Stale control revisions cannot
pause/resume a later interval. Retried terminal finish is harmless, including after
restart. Existing migrations are unchanged.

`backend/domain/timer.py` owns every timer control through `TimerService` and short
serialized `Database.write()` transactions. Clock anchors advance only with committed
checkpoints and are restored on rollback. A service-owned one-second monitor resolves
expiry even without a browser. Monotonic nanoseconds determine credit, capped at the
chosen duration; UTC timestamps locate work in history. The interface polls every two
seconds and interpolates a display with `performance.now()`; it cannot earn time or
finalize a result. Old poll responses cannot overwrite a newer action.

Navigation, refresh, browser visibility changes and browser closure do not pause
tracking while the service continues running. Visibility only requests an authoritative
refresh; it is never classified as laptop sleep. The compact Plan timer remains
available across normal task work. Failed requests retain input and operation IDs;
Track also exposes loading errors and retry for unavailable task choices.

Actively tracked tasks cannot gain children, and actively tracked subtasks cannot be
removed until their session finishes. Normal edits, completion and scheduling remain
available. Later task moves/edits/permitted removal preserve the saved session and
interval fields, so work history cannot migrate with a planned date.

## Provisional interruption boundary

Checkpoints are attempted every **one second**. A service restart, unexplained awake
sampling gap over **five seconds**, backward clock movement, or disagreement over
**two seconds** between clocks stops credit at the last confirmed checkpoint and
marks the session Needs review. An expiry endpoint that would reverse a saved UTC
interval also requires review. Unfinished paused sessions likewise require review
after service restart. A healthy paused interval can last indefinitely without earning
time or being treated as an awake sampling gap.

This can conservatively discard a healthy interval after a long scheduling stall.
Checkpoint cadence is a normal target, not a guaranteed crash precision. This build
does not recover the uncertain gap, automatically subtract measured sleep, reconcile
DarkWake, or offer time editing. Its only review resolution explicitly saves confirmed
time and excludes the gap. Sub-tolerance clock drift is not a claim of clock-change
recovery. M0's measured Mac clock policy was read and followed for credit; its hardware
experiment is historical evidence, not a timer recovery pass.

No new hardware sleep/wake, battery/standby/hibernate, system-clock manipulation,
midnight/DST, ten-minute precision or real three-hour run was performed. Fake clocks
cover 1- and 180-minute expiry boundaries and conservative discontinuity behavior.
The real one-minute test is normal expiry evidence only.

## Checks actually performed

Actual environment: **macOS 26.6.2 (25G83), Darwin arm64**, Python **3.13.15**,
Node **24.21.0**, installed Chrome **155.0.8059.82**, Playwright. No Windows run.
All failure, interruption, browser and migration tests use synthetic/disposable data.

| Command/check | Actual result |
| --- | --- |
| Pre-edit loopback/Chrome-permitted `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q` with M1 evidence directory | **327 passed**, zero failed/skipped, 30.76 s. See M1 record for sandbox failures and permitted retry. |
| `.venv/bin/python -m pytest -q tests/test_timer.py tests/test_timer_api.py` | **51 passed**, 3.45 s. |
| `.venv/bin/python -m pytest -q tests/test_api.py tests/test_tasks.py tests/test_migrations.py` | **117 passed**, 1.56 s. |
| Loopback-permitted `.venv/bin/python -m pytest -q -s tests/test_timer_restart.py` | **2 passed**, 6.18 s. Real pause/resume, monitor checkpoints, normal task-write latency, abrupt kill, restart and durable replay. |
| Initial short Chrome countdown journey | **1 passed**, 4.14 s; ordinary task creation during tracking 0.067 s. |
| `BEARPLANS_EVIDENCE_DIR=docs/reviews/evidence/countdown BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s` (loopback/Chrome permitted) | **382 passed**, zero failed/skipped, **107.43 s**. Full foundation/planner/countdown suite. |
| Full-suite real one-minute countdown | Browser process closed; SQLite row observed read-only, with no timer API callbacks. Monitor independently saved **60.000000 s**, completed after **60.149 s** on independent monotonic reference. Reopened browser showed saved outcome; task remained byte-for-byte incomplete. |
| Full-suite responsiveness measurement | Six API task writes during tracking: median **0.002977 s**, max **0.012065 s**. Browser task creation **0.071 s**. Separate short real session saved **2.559341 s**, excluding pause. |
| Final `npm --prefix frontend test` | **53 passed**, 3.13 s, including final Track task-choice error/retry regression. |
| `npm --prefix frontend run typecheck` and `npm --prefix frontend run build` | **Pass** after final UI clarity/loading-error changes. |
| Final focused Chrome command with the same evidence/environment and `tests/test_timer_browser.py::test_countdown_navigation_tabs_pause_retry_and_history` | **1 passed**, **4.42 s**, task creation **0.067 s**. Final copy/task-choice retry changes affect UI only; unaffected long timing tests were not repeated. |
| `.venv/bin/python -m compileall -q backend/domain/timer.py backend/routes/timer.py` | **Pass**. |

Deterministic cases include invalid types/durations, nonexistent task/container,
paused arithmetic, exact selected/three-hour cap, expiry without browser, concurrent
starts and twelve competing finishes, replay/key conflicts, stale controls, rollback
after partial start/finalization and successful retry, task-completion separation,
normal task edits/structure guards, immutable historical time after movement/removal,
v5→v6 preservation and failed migration rollback/retry. API cases retain structured
actionable errors, loopback Host and same-origin mutation protection.

Real Chrome coverage joins task-to-Track and direct Track, unscheduled work, Plan
navigation, compact timer, responsive task creation, shared two-tab state, rejected
second start, keyboard Start/Pause, pause/reload/resume, lost committed finish response
and retry, saved result, restart Needs review and explicit resolution. Visibility hook
tests verify refresh without pause; no new physical hide-tab/sleep measurement is
claimed. Real browser-process closure is tested separately from sleep.

Independent source review found two defects before final checks: a short backwards
UTC step/clipped expiry could reverse interval endpoints, and repeated entry from the
same task could retain a different dropdown selection. Both were fixed and have
regressions. No remaining source-review blocker. Final UI inspection also corrected
review-state copy, singular minute wording, and actionable task-choice loading errors.
An early test helper used the wrong project rename function; two UI test assertions/
types were corrected. These were test setup issues. Initial restart tests could not
bind loopback in the sandbox; their permitted rerun passed. A resize/media screenshot
capture artifact is addressed by waiting for paint and checking one main element.

Inspected synthetic active/compact/saved/review views at **1440**, **1024**, and
**375** px, light/dark, keyboard focus and disabled/loading/error controls. No horizontal
overflow. Evidence:
[active wide](evidence/countdown/timer-07-active-wide.png),
[active narrow](evidence/countdown/timer-08-active-narrow.png),
[compact Plan](evidence/countdown/timer-01-plan-compact.png),
[compact narrow](evidence/countdown/timer-09-compact-narrow.png),
[saved outcome](evidence/countdown/timer-02-saved-wide.png),
[dark laptop](evidence/countdown/timer-04-dark-laptop.png),
[restart review](evidence/countdown/timer-06-restart-review.png),
[real expiry](evidence/countdown/timer-05-real-expiry.png).

The real-expiry capture predates the final singular-minute/task-choice-retry wording;
the final focused journey regenerated the other countdown captures. Duplicate synthetic
captures from historical tests were removed from the new countdown evidence folder.

## Normal app upgrade and saved-data preservation

Identified existing backend PID 95319, launcher PID 95317, loopback port 8765 and
normal data folder before stopping anything. SQLite's backup API produced a live
backup in a private temporary folder. A rehearsal on another SQLite backup copy
upgraded schema 5→6 and compared hashes of every original SQL field, including
closed snapshots/archive rows. Integrity and foreign keys passed, new timer tables
were empty. The first restricted attempt could not open SQLite's WAL bookkeeping;
the permitted retry used a fresh filename. The empty failed target was never used
as a backup. No original data was overwritten or reset.

Stopped the identified launcher gracefully with SIGINT and confirmed the service
released port 8765. Saved a durable backup beside the user's existing backups:
`bearplans-pre-countdown-20261016T151846Z.sqlite3` in the normal data folder. It
matched the rehearsed data exactly. Restarted with `python3 launch.py --no-browser`.

The normal service now runs schema 6. Every original field/hash is unchanged:
**seven tasks, two projects, one active placement, two closed weeks and four archived
placements**; carryover receipts are still empty. Integrity/FK checks passed, original
migration records were preserved and all three timer tables remain empty. Read-only
Chrome inspection of direct Track, task choices, Plan and back passed, with no
horizontal overflow and the complete planning response unchanged. **No personal
timer/task/history edit or screenshot was made.** Existing tabs should refresh.

Scoped diff/whitespace and local document links pass. The original staged and
unstaged roadmap/review-plan edits are preserved outside the local build commit.
No database, personal content or personal screenshot is included in Git.

## Five-minute demonstration

1. **Minute 1:** On a sample leaf/subtask choose Start tracking. Confirm the selected
   task, choose one minute and Start. After ten seconds Pause; wait five seconds and
   verify the remaining value holds, then Resume.
2. **Minute 2:** Open Plan and see the compact timer. Edit a normal task, refresh,
   and open a second tab: the same timer appears and another Start is unavailable.
   Finish early. Verify one saved outcome and an unchanged task completion checkbox.
3. **Minute 3:** Open Track directly. Select an unscheduled leaf, choose one minute,
   Start, and close the browser while leaving the local service running.
4. **Minute 4:** After at least one minute reopen Track. Verify Countdown completed
   and the saved active minute. Move the task's planned date, if scheduled: its saved
   session time stays where it occurred. Task completion remains a separate action.
5. **Minute 5:** Narrow the window and use keyboard controls. Confirm 0, 181 and
   fractional minutes cannot start. Read the provisional recovery note; use disposable
   data for later interruption demonstrations. Full hardware recovery is still pending.
