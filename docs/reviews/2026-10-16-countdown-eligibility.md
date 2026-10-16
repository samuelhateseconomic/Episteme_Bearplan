# Countdown refinement — incomplete leaves and weekly-card entry

Date: October 16, 2026, America/Los_Angeles. Verified baseline **`c4b7dd3`**.
Schema remains **6**; no migration, dependency, timer arithmetic or recovery change.
The local commit containing this record identifies the reviewed refinement.

## Decision and acceptance

**Refinement implementation review: Pass.** Only incomplete leaf tasks may start a
new countdown. Both scheduled and unscheduled work remain eligible across projects.
Eligible open weekly-board cards open Track with the same task selected and retain
the existing duration/Start countdown flow. Completed leaves in the project list
and weekly board have a disabled Start tracking control with visible, accessible
reopening guidance. Track explains how to add/reopen work when none is eligible.
There is no untasked tracking.

**Overall M2 recovery acceptance remains pending / not passed.** This refinement
does not certify sleep/crash/clock-change recovery or its outstanding hardware,
midnight/DST and longer-session gates. No recovery or drag-and-drop implementation
was started. No new operator/manual acceptance is claimed. Relevant local commit
authorized on a passing build; no push or automatic next build.

Read AGENTS.md, CLAUDE.md, shared progress, roadmap, build/review plans, README and
the prior countdown review; inspected status, recent commits, complete staged and
unstaged diff and relevant untracked files. No nested AGENTS.md exists. Before
editing, stated the incomplete-leaf rule, affected entry points, stale-request
acceptance, absence of schema/state changes, and existing-session preservation.

The user explicitly supersedes the first countdown build's completed-leaf
eligibility. Reopening through task completion controls restores new-session
eligibility. Starting and finishing still never change completion. No session is
silently stopped, deleted or reassigned when its task completes. Existing running,
paused and Needs review sessions retain their task identity, saved intervals and
controls even when their task leaves the new-session choices. The one-unfinished
session constraint remains in force. Closed-week snapshots stay read-only.

## Implementation

`TimerService.start` checks the leaf's persisted `completed_at` in its existing
serialized write transaction, before inserting a session, interval or receipt.
Completed leaves receive structured **422 invalid_input**, field `task_id`, with
guidance to reopen or choose incomplete work. Rejected starts leave timer records
unchanged. Acknowledged operation receipts replay before eligibility checks, so a
lost successful Start response can still be safely acknowledged after task
completion; it cannot create another session. New keys for completed work reject.

Track filters the complete current task snapshot by no children and incomplete
status, independent of placements. A shared entry control supplies the same visible
and `aria-describedby` explanation in the task list and open weekly cards. Weekly
entry passes the original task ID to the existing request-token navigation; it does
not start immediately or replace the active session. Existing active-session
rendering is independent of new-session eligibility. A rejected Start refreshes task
choices and retains duration and retry identity; stale requests cannot bypass the
backend guard. Empty choices disable the selector/Start while explaining next steps.

Existing session/checkpoint/interval/retry/review behavior is preserved. There is no
data migration, session correction, bulk completion, deletion, new scheduling rule or
recovery resolution change. Shared guidance and README now record the refined rule;
the original countdown review retains its historical evidence with a refinement link.

## Checks actually performed

Actual host: **macOS 26.6.2 (25G83), Darwin arm64**, Python **3.13.15**, Node
**24.21.0**, installed Chrome **155.0.8059.82** via Playwright. No Windows or new
hardware sleep/clock experiment. All mutation/failure/browser fixtures are synthetic
and disposable, outside the source tree.

| Command/check | Actual outcome |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_timer.py tests/test_timer_api.py tests/test_tasks.py` | **113 passed**, 4.13 s; backend agent's initial targeted run. |
| `.venv/bin/python -m pytest -q tests/test_timer.py tests/test_timer_api.py tests/test_tasks.py tests/test_planning.py tests/test_planning_api.py tests/test_weeks.py` | **280 passed**, 6.66 s; zero failed/skipped. |
| `npm --prefix frontend test` | **63 passed**, 3.07 s in the final parent run (agent verification: 63 passed, 3.09 s). |
| `npm --prefix frontend run typecheck` | **Pass**. |
| `npm --prefix frontend run build` | **Pass**, 84 ms Vite build; launcher rebuild also passed. |
| `BEARPLANS_EVIDENCE_DIR=docs/reviews/evidence/countdown-eligibility BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s tests/test_timer_eligibility_browser.py` with Chrome/loopback permission | **1 passed**, 2.30 s; complete joined refinement journey. |
| `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s tests/test_timer_restart.py tests/test_timer_browser.py::test_countdown_navigation_tabs_pause_retry_and_history tests/test_weekly_browser.py tests/test_weeks_browser.py tests/test_m1_journey_browser.py` with Chrome/loopback permission | **6 passed**, 20.97 s; affected service/timer/planner/history regressions. |
| Short real timer and normal-operation responsiveness in that regression run | **2.556639 active seconds** saved, excluding pause. Six API task writes: median **0.002924 s**, max **0.014481 s**. Browser task creation during tracking: **0.068 s**. |
| Independent source review | **Pass**, no remaining blocker; reviewed atomic eligibility/replay ordering, UI/weekly wiring, empty/stale behavior, all existing active states and test additions. |

Backend additions cover completed standalone/subtask leaves, scheduled/unscheduled
work, exact timer-table preservation on rejection, explicit reopen/retry, stale API
clients, completion during running/paused/Needs review, unchanged session identity,
continued controls and safe acknowledged Start/Finish replay. Fake-clock timer
regressions retain 1/180-minute limits, paused arithmetic, capped expiry, one-session
concurrency, rollback/retry and conservative interruption handling. API protections
and actionable save errors remain covered.

Frontend additions cover scheduled/unscheduled/cross-project choices, completed
standalone/subtask/container exclusion, visible accessible disabled guidance,
weekly-card keyboard entry retaining duration, empty/no-task and all-completed
states, stale rejection/choice refresh, completion during all three unfinished
states, and absence of tracking controls in closed history.

Real Chrome verifies the same incomplete scheduled child selected from the board,
keyboard Start, task completion/derived parent completion with the same running
session still visible, pause/resume/finish after completion, exclusion after finish,
stale completion by a second context, direct rejected request, retained 17-minute
input, unchanged saved result, stored empty state after refresh and completed board
guidance. Inspected **1440 px** and **375 px**, focus/keyboard controls, readable
completed explanations, active completed-task session and disabled/empty/error
states; no horizontal overflow. No personal screenshot was made.

The first new Chrome attempt used Playwright `check()` on a server-controlled
completion checkbox; its immediate post-click assertion raced the service refresh.
Changed the helper to click and wait for the saved checked state; the complete
journey passed. An initial frontend table-test setup error was corrected before
the passing runs. Neither was a confirmed product defect or loss of user data.

Evidence:
[filtered choices](evidence/countdown-eligibility/eligibility-01-choices-wide.png),
[weekly entry and completed guidance](evidence/countdown-eligibility/eligibility-02-board-wide.png),
[completed task's active session, narrow](evidence/countdown-eligibility/eligibility-03-completed-active-narrow.png),
[stale rejection and empty state](evidence/countdown-eligibility/eligibility-04-stale-empty-narrow.png),
[completed board, narrow](evidence/countdown-eligibility/eligibility-05-board-narrow.png).

This is a focused refinement review, not a fresh overall M2 milestone review.
The prior full **382-test** run and real one-minute browser-closed expiry are
[historical baseline evidence](2026-10-16-countdown.md); they were not rerun or
represented as new results. The current affected Python/browser runs contain
**287 distinct tests** (280 + 6 + 1), plus the 63 frontend tests.

## Normal app and saved-data preservation

Identified service **3284**, launcher **3261**, normal data folder and port 8765.
The current data had grown since the baseline handoff: **nine tasks, two projects,
three active placements, two closed weeks, four archived placements, three finished
sessions, four saved intervals and eight timer receipts**. SQLite backup API and
integrity/FK checks passed; no personal contents were printed. No unfinished session
existed. Rechecked the backend before signaling the verified launcher with SIGINT,
so the refresh did not interrupt a running, paused or Needs review session.

Confirmed port 8765 released, built the interface, and saved a durable backup in
the normal data folder: `bearplans-pre-eligibility-20261016T161718Z.sqlite3`.
It matched the earlier live backup exactly. Restarted using
`python3 launch.py --no-browser`; schema remains **6**.

Read-only Chrome inspection of the normal app checked exact incomplete-leaf option
IDs, completed controls, navigation and narrow layout without a timer start, task
edit or personal screenshot. The complete planning response and **every original
SQL field/hash** across all tables, including all three saved sessions, intervals,
receipts and closed snapshots, matched the pre-restart backup. Integrity and foreign
keys passed. Existing browser tabs should refresh to load the refinement.

Pre-existing staged review-plan/roadmap edits and unstaged roadmap checkmarks are
preserved outside this build commit. Scoped whitespace/local links and staged/
unstaged diff preservation are checked before committing. No database, personal
content or personal screenshot is committed.

## Remaining work

No known blocking issue remains in the requested refinement. Hands-on operator
acceptance is not newly claimed. Overall M2 remains pending recovery acceptance:
real Mac sleep/wake and DarkWake, crash/restart reconciliation, forward/backward
clock changes, battery/standby/hibernate, midnight/DST and longer precision evidence.
Current conservative Needs review behavior remains. No full recovery or next build
was started; no drag-and-drop, untasked tracking or unrelated feature was added.
