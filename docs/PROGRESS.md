# BearPlans — shared progress and handoff

Read [AGENTS.md](../AGENTS.md) first; Claude also reads [CLAUDE.md](../CLAUDE.md).
This is the single mutable work/handoff record. Detailed reviews retain the evidence.

## Current state

**Weekly planning: implementation review Pass; operator demonstration pending.**
Implemented 2026-10-15, pulled forward from the Oct 16 daily roadmap row.
Schema **3**. Baseline: `d2174a6`; previous application implementation `a9ba50b`.
The local weekly-planning commit containing this record is authorized; no push.

Current implementation work is complete. The next action is the five-minute
operator checklist in the [weekly review](reviews/2026-10-15-weekly-planning.md).
**Weeks/history is the next daily build, not started and not authorized by this
request.** The broader M1 planner milestone is not certified by this daily build.
Closed-week snapshots/reports/bulk carryover, timers, rewards, AI and integrations
remain deferred.

Pre-existing work was inspected: user edits to `BearPlans_Build_Review_Plan.md` and
`BearPlans_Dated_Roadmap.md`, plus the shared-guidance preparation in `AGENTS.md`,
`CLAUDE.md` and this file. The two planning-document edits are unchanged and remain
outside the build commit. Shared agent guidance and its Claude entrypoint are
preserved and included with the relevant progress/rule updates.

## Completed builds

| Build | State | Evidence |
| --- | --- | --- |
| M0 / foundation | Implementation and Mac/operator gate passed | [M0 review](reviews/2026-10-14-local-foundation.md); `36f6e48`, `f4c59dd` |
| Projects/tasks/subtasks | Implementation and all six operator checks passed | [M1 takeover review](reviews/2026-10-13-m1-takeover.md); `a9ba50b`, `d2174a6` |
| Weekly planning | Implementation Pass; operator check pending | [Current review](reviews/2026-10-15-weekly-planning.md) |
| Weeks/history and later builds | **Not started** | [Daily roadmap](../BearPlans_Dated_Roadmap.md) and [review gates](../BearPlans_Build_Review_Plan.md) |

Weekly planning retains the project/task editor beside a Monday–Sunday board,
Previous/Next/Today, selected-day laptop layout, existing-leaf assignment,
individual placement moves across weeks, and unscheduling without deleting tasks.
Multiple dates per task are allowed; a duplicate destination is an atomic conflict.
Task identity, deadline, notes, project and completion are not copied or changed by
planning. Parents remain context, with completion derived from children. Unscheduled
work and dates outside the visible week remain accessible in the task list.

`planned_items` references tasks with a unique task/day pair. Scheduling rules live
in `backend/domain/planning.py`; reads share one consistent task/placement snapshot,
and writes use `Database.write()`. A scheduled standalone task must be unscheduled
before gaining children; a scheduled subtask must be unscheduled before deletion.
No silent removal or transfer of placements.

Today is server-authoritative. `BEARPLANS_TIMEZONE` optionally names an installed
IANA timezone; otherwise the OS local timezone at the current instant is the
application default. The interface displays it. No timezone settings UI exists.
Dates are calendar dates; planned dates are distinct from deadlines. Today metadata
refreshes on navigation/save/reload; Today explicitly asks the server for the current
date, rather than relying on the browser timezone or a cached date.

## Checks actually performed

Detected **macOS 26.6.2 (25G83)**, Python **3.13.15**, Node **24.21.0**, installed Chrome.

- Baseline before changes: **149 backend/browser tests, 18 frontend tests and
  TypeScript checks passed**, confirming the previous build's actual state.
- Final full suite: **228 passed, zero failed/skipped**, including migration v1/v2
  preservation, rollback/retry, concurrency/duplicate conflicts, cross-week movement,
  unscheduling, shared completion, leaf guards, invalid input, timezone/week
  boundaries, real-service/launcher restart and foundation regressions.
- Frontend: **31 tests passed**; typecheck and production build passed. Cases cover
  saved-but-refresh-failed messaging, retrying the requested week/Today, and stale
  responses during concurrent navigation/mutation.
- Inspected synthetic Chrome evidence at **1600**, **1024**, **375** px and dark mode.
  Weekly browser journey includes conflict recovery, persistence, selected-day
  navigation, service-down failed save with retained date, and successful retry.
- Separate read-only source review found no remaining blocking defect after fixes.
- Scoped diff/whitespace, local document links and preservation of the two existing
  planning-file edits are checked before committing. A global whitespace warning
  in the user-edited review-plan heading is pre-existing and is retained.

Exact commands, outcomes and screenshots are in the current review. All automated
failure/migration/corruption tests use disposable data. No Windows run or new Mac
sleep experiment is claimed. M0's measured sleep decision is historical design
evidence, not a timer implementation pass.

## Normal running instance and data preservation

The stale schema-2 background instance at `http://127.0.0.1:8765/` was stopped
gracefully. A pre-upgrade SQLite backup was created in the normal data folder:
`bearplans-pre-weekly-20261015T071929Z.sqlite3`. A disposable copy upgraded to schema 3
with matching task/project SQL values and clean integrity/FK checks. The current
launcher then upgraded the normal database; all stored task/project fields matched
unchanged, retaining four saved tasks. No test placements were added to personal data.
The normal instance now serves weekly planning with system-local timezone (PDT).

No database, personal content or personal screenshot belongs in Git. Screenshot
artifacts included in the review are synthetic browser-test data only.

## Pending evidence and next steps

- **Operator:** complete the five-minute weekly-planning checklist in the review.
  The prior projects/tasks checklist remains passed; do not reopen it without a
  regression. No known blocking implementation defect remains in the current build.
- After this daily build is accepted and the user authorizes another build, plan
  Weeks/history with its own acceptance scenario. Do not implement it now.
- Future timer gates still require their own sleep/restart/clock-change/midnight/DST
  checks and battery/standby/hibernate evidence. Unknown gaps must not earn work time.

## Guidance discrepancies retained for future agents

- The user-edited roadmap says "planned, not implemented or tested" but marks its
  first two rows complete, with checkmarks outside the declared table columns.
  The user-edited review plan removes the broader-M1 status explanation. Preserve
  these edits; use this progress record and linked evidence for actual status.
- The [historical Claude M1 draft](reviews/2026-10-15-projects-and-tasks.md) is
  superseded by the takeover review. Its test totals, no-deletion statement,
  pending-operator status and "configurable" field limits are historical. Current
  code supports confirmed subtask removal; field limits are constants, not settings.
- Historical "next projects/tasks" or "next weekly planning" statements are not
  current instructions. Review filenames may use target dates; follow content and
  commit history, not filename sorting.
- The original build plan suggests a native sleep adapter; the measured M0 decision
  proposes two-clock measurement and a scoped Needs review fallback without it.
  Read that evidence before timer work; it does not lower M2 safety gates.
- The original task-detail sketch mentions due date/time; explicit decisions use
  date-only deadlines. Proposed reward/price/streak settings remain distinct from
  confirmed product requirements; no such settings feature is implemented here.

Before either agent stops or transfers work, update this record with exact state,
files/commits, checks/failures/skips, pending manual evidence and the next concrete
step. Keep one shared record rather than separate Codex/Claude trackers.
