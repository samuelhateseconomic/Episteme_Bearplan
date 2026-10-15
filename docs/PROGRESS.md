# BearPlans — shared progress and handoff

Read [AGENTS.md](../AGENTS.md) first; Claude also reads [CLAUDE.md](../CLAUDE.md).
This is the single mutable work/handoff record. Detailed reviews retain the evidence.

## Current state

**Weeks, closed history and reviewed carryover: implementation review Pass;
operator acceptance Pass.** User accepted build `7155bc2` on 2026-10-15:
“Looks good to me.” This records overall feature acceptance, not itemized confirmation
of every demonstration step. Broader M1 milestone review remains separately pending.
Implemented 2026-10-15, pulled forward
from the Oct 17 roadmap row. Schema **5**. Baseline `a21cb49` (one-day refinement),
original weekly build `801cbc3`; reviewed application build `7155bc2`.
Previous projects/tasks: `a9ba50b`, operator acceptance `d2174a6`.
Relevant local commit authorized; no push.

Current implementation work and overall operator acceptance are complete. The
[current review](reviews/2026-10-15-weeks-history.md) preserves the demonstration
checklist and exact evidence; individual manual steps were not reported separately.
**Countdown is the next roadmap build, not started and not authorized by this
request.** Broader M1 operator acceptance is not certified by automated checks alone.
Reopening, recurring tasks, automatic bulk carryover, advanced reports, timers,
rewards, AI and integrations remain deferred.

Pre-existing staged user edits to `BearPlans_Build_Review_Plan.md` and
`BearPlans_Dated_Roadmap.md` are unchanged and remain staged outside the build
commit. `CLAUDE.md` remains substantive and available, referencing shared guidance
and this handoff record.

## Completed builds

| Build | State | Evidence |
| --- | --- | --- |
| M0 / foundation | Implementation and Mac/operator gate passed | [M0 review](reviews/2026-10-14-local-foundation.md); `36f6e48`, `f4c59dd` |
| Projects/tasks/subtasks | Implementation and all six operator checks passed | [M1 takeover review](reviews/2026-10-13-m1-takeover.md); `a9ba50b`, `d2174a6` |
| Weekly planning + one-day refinement | Implementation Pass; previous operator checklist remains pending | [Prior review](reviews/2026-10-15-single-planned-day.md), `a21cb49`; [original weekly evidence](reviews/2026-10-15-weekly-planning.md), `801cbc3` |
| Weeks/history/carryover | Implementation Pass; overall operator acceptance Pass; broader M1 review separate | [Current review](reviews/2026-10-15-weeks-history.md), `7155bc2` |
| Countdown and later builds | **Not started** | [Daily roadmap](../BearPlans_Dated_Roadmap.md) and [review gates](../BearPlans_Build_Review_Plan.md) |

Weekly planning retains the project/task editor beside a Monday–Sunday board,
Previous/Next/Today, selected-day laptop layout, existing-leaf assignment,
individual placement moves across weeks, and unscheduling without deleting tasks.
**Latest user decisions:** each leaf task or subtask has at most one active planned
date across open weeks, including completed work. Closed history does not consume
that allowance. Split multi-day work into smaller
subtasks, schedule them separately, and finish every child to complete the parent.
A second assignment is an atomic conflict with the existing date and guidance to
Move or split work. Scheduled leaves show Move/remove controls without an Add form.
Task identity, deadline, notes, project and completion are not copied or changed by
planning. Parents remain context, with completion derived from children. Unscheduled
work and dates outside the visible week remain accessible in the task list.

`planned_items` references tasks with a unique task ID (migration 4); migration 3's
SQL remains unchanged. Moving preserves placement identity; different tasks can
share a day. Unscheduling keeps the task and allows a new assignment. Legacy
databases with multiple dates per task fail the upgrade safely with instructions
to remove extra planned dates using the previous build, then retry. No dates are
silently chosen or discarded. Scheduling rules live
in `backend/domain/planning.py`; reads share one consistent task/placement snapshot,
and writes use `Database.write()`. A scheduled standalone task must be unscheduled
before gaining children; a scheduled subtask must be unscheduled before deletion.
No silent removal or transfer of placements.

End Week previews complete displayed task/parent/project fields, placements and
unique-leaf totals before confirmation. Closure atomically stores a versioned frozen
JSON snapshot and archives original placement IDs/fields in `closed_placements`;
tasks remain unchanged. SQLite triggers protect history from update/deletion.
Closed cards have no mutation controls and separate At closure from Current task
status. Backend rejects closed-date scheduling and archived-ID moves/removal.
Empty weeks show 0/0 (0%). Closure can be past/current/future; reopening is deferred.

Carryover selects only unfinished-at-closure work still existing as incomplete
leaves. Choose dates in the immediately following Monday–Sunday week, Review, then
Apply. Completed/deleted/new-parent/already-planned tasks and closed destinations
are explained and rejected. Revalidate preview hashes inside `Database.write()`;
conflicts/failures are atomic. Persistent operation receipts return the original
result on retries and reject reused IDs with different source/work/dates. The same
task IDs, fields, completion and future session references remain; source history
is untouched. A current subtask may still be removed once its active plan is removed,
without erasing its historical details.

Today is server-authoritative. `BEARPLANS_TIMEZONE` optionally names an installed
IANA timezone; otherwise the OS local timezone at the current instant is the
application default. The interface displays it. No timezone settings UI exists.
Dates are calendar dates; planned dates are distinct from deadlines. Today metadata
refreshes on navigation/save/reload; Today explicitly asks the server for the current
date, rather than relying on the browser timezone or a cached date.

## Checks actually performed

Detected **macOS 26.6.2 (25G83)**, Python **3.13.15**, Node **24.21.0**, installed Chrome.

- Verified baseline: **242 Python/browser tests**, 20.43 s; **32 frontend tests**,
  2.71 s; TypeScript passed before this build.
- Current full suite: **326 passed, zero failed/skipped**, 27.71 s. Includes
  migration v1/v2/v3 preservation, legacy duplicate rollback/retry, concurrency and
  global duplicate prevention, cross-week movement, unscheduling/reassignment,
  independent child completion/derived parent progress, invalid input, leaf guards,
  timezone/week boundaries, real-service/launcher restart and foundation regressions.
- New history domain/API/migration/restart cases: **83 passed**, 3.53 s, including
  exact frozen/archive preservation, distinct-leaf counts, empty closure, stale
  previews, closed-date guards, following-week boundaries, concurrent/retried close
  and carryover, receipt replay, current-state eligibility, injected partial-write
  rollback and genuine v4→v5 migration rollback/retry.
- Frontend: **40 tests passed**, 2.84 s; typecheck and production build passed. Cases cover
  one-date controls and stale-tab conflicts, plus
  saved-but-refresh-failed messaging, retrying the requested week/Today, and stale
  responses during concurrent navigation/mutation.
- Inspected current synthetic Chrome history evidence at **1600**, **1024**, **375** px.
  Earlier weekly dark-mode evidence remains linked in the prior review.
  Weekly browser journey covers separately scheduled children, parent 1/2 to 2/2,
  rejected second date, cross-week movement, unscheduling, restart, selected-day
  navigation, service-down failed save with retained date, and successful retry.
- Real Chrome history journey passed (3.28 s): preview/cancel/close, frozen history
  after later edits/restart, current completion exclusion, reviewed carryover and
  lost-response retry with identical operation ID and exactly one destination plan.
  Strengthened keyboard activation of End Week/Cancel/Close also passed (3.26 s).
- Separate read-only backend/frontend/test source review: **Pass**, no blocking defect.
- Initial new browser helper raced refreshed choices; waiting for enabled controls
  fixed test synchronization. Targeted and full journeys pass. Initial frontend
  test typing issue was corrected before the final passing checks.
- Scoped diff/whitespace, local document links and preservation of the two existing
  planning-file edits are checked before committing. A global whitespace warning
  in the user-edited review-plan heading is pre-existing and is retained.

Historical pre-weekly baseline (149 Python/browser, 18 frontend) and original weekly
results (228 Python/browser, 31 frontend) remain in the original review. The original
multi-day acceptance scenario was superseded by the user's explicit refinement.

Exact current commands, outcomes and screenshots are in the current review. All automated
failure/migration/corruption tests use disposable data. No Windows run or new Mac
sleep experiment is claimed. M0's measured sleep decision is historical design
evidence, not a timer implementation pass.

## Normal running instance and data preservation

The identified schema-4 launcher/service at `http://127.0.0.1:8765/` was stopped
gracefully. SQLite backup: `bearplans-pre-weeks-20261015T155840Z.sqlite3` in the normal
data folder, outside Git. Rehearsed schema 5 on a disposable copy with every original
task/project/placement SQL field unchanged and clean integrity/FK checks. The current
launcher then upgraded the normal database: **six saved tasks and three active
placements** retained, all original fields matching exactly. No real weeks were
closed, no personal carryover applied, and all history/receipt tables remain empty.
Chrome preview/Cancel checks on the updated normal app left its complete planning
response unchanged; no personal screenshot was taken.
The running app serves schema 5 with system-local timezone (PDT); refresh the
browser. Previous upgrade/backup evidence remains in the prior reviews.

No database, personal content or personal screenshot belongs in Git. Screenshot
artifacts included in the review are synthetic browser-test data only.

## Pending evidence and next steps

- **Operator acceptance:** user approved build `7155bc2` with “Looks good to me.”
  No new runtime checks were performed to record this approval. Specific weekly/
  history demonstration steps were not individually confirmed; the broader M1
  milestone gate remains separately pending. Retain the checklist for that review.
  The prior projects/tasks checklist remains passed; do not reopen it without a
  regression. No known blocking implementation defect remains in the current build.
- When the user authorizes another build, plan
  Countdown with its own acceptance scenario. Do not implement it now.
- Future timer gates still require their own sleep/restart/clock-change/midnight/DST
  checks and battery/standby/hibernate evidence. Unknown gaps must not earn work time.

## Guidance discrepancies retained for future agents

- Original weekly guidance/review allowed several dates for one task. The user's
  2026-10-15 refinement supersedes that rule: one planned day per leaf task/subtask.
  With closed history, that means one **active** date across open weeks; historical
  placements are preserved independently. Current rules are in AGENTS.
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
