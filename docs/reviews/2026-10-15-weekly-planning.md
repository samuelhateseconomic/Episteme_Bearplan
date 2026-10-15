# Weekly planning — daily build review

Date: 2026-10-15 (America/Los_Angeles), pulled forward from the Oct 16 roadmap row.
Baseline: `d2174a6`; prior application implementation `a9ba50b`.
Status: **implementation review Pass; operator demonstration pending**. The local
weekly-planning commit containing this record is the reviewed build.

## Acceptance scenario and data model

Project/task list beside a Monday–Sunday board; previous/next week and Today;
selected-day layout at narrow widths. Existing leaf tasks can be planned for
multiple dates, moved one placement at a time across days/weeks, or unscheduled
without deleting the task. Planned dates are distinct from deadlines.

Migration `0003_planning.sql` adds `planned_items`: UUID, existing task FK, date-only
planned date, UTC creation/update timestamps and revision. A UNIQUE(task_id,
planned_date) constraint prevents duplicates. Completion remains solely on tasks.
No task copies, week snapshots or historical reports are created.

Acceptance checks:

- Foundation/v2 tasks and all fields survive migration; failed migration rolls
  back and can retry. Existing identities, metadata and history are not rewritten.
- Multiple dates per leaf are allowed; duplicate assignments/moves fail atomically
  with an explanation. Moving preserves placement identity and affects only that
  placement; same-date movement is a no-op.
- Unscheduling removes a placement, retaining its task. Completion changes remain
  consistent on every placement and preserve derived parent completion.
- Parents are context, not scheduled work. A scheduled standalone task must first
  be unscheduled before gaining children. A scheduled subtask must be unscheduled
  before deletion; no implicit deletion/reassignment of planned dates.
- Monday/Sunday, month/year and DST boundaries use calendar dates. Today comes
  from `BEARPLANS_TIMEZONE` when configured as an available IANA timezone; otherwise
  from the operating system's local timezone at the current instant. No timezone
  settings UI/record exists yet. Invalid configuration produces an actionable error.
- Restart persistence, invalid inputs, local request protection, failed saves and
  retries, and usable wide/narrow keyboard flows have actual evidence.

Affected functions: shared `backend/domain/planning.py`, task relationship guards,
planning routes, frontend planning view. All scheduling writes use `Database.write()`.
Recovery: correct a failed date or conflict and retry; unschedule only the intended
placement. No bulk move, carryover, timer, rewards, AI or integrations in this build.

## Baseline actually checked

Detected macOS/Darwin. Before implementation, **149 backend/browser tests passed**
with no skips; **18 frontend tests** and TypeScript checks passed. Previous operator
acceptance remains recorded in `d2174a6` and the M1 takeover review. Final build results, screenshots, decisions and the demonstration checklist follow.

## Implemented behavior and review fixes

The existing project/task editor is retained beside the board. Seven columns are
visible above 1300 px; at 1300 px and below a selected-day view keeps cards readable.
At 760 px and below, the board sits above the task list. Unscheduled tasks remain
accessible. Date pickers/buttons implement assignment, moves and removal; no new
frontend or Python dependency was needed.

The planning snapshot reads tasks and all placements in one SQLite read transaction.
The board filters the visible week; the task list exposes all of a task's planned
dates, including other weeks. Task edits/completion are read from the original task
row and refreshed across list/cards. Parent context includes the project and title.

Source review identified two frontend recovery issues during implementation, both
corrected with regression cases: a successful write followed by failed readback now
says it was saved and offers a refresh retry; pending/failed week navigation retains
its requested destination across retries and mutation refreshes. Completion controls
are locked during write/readback errors, and board completion is locked while its
snapshot loads. Old M1 browser selectors were made exact to distinguish task labels
from the new date-control labels; their behavioral assertions remain intact.

## Checks actually performed

Environment detected directly: **macOS 26.6.2**, build 25G83, Python **3.13.15**,
Node **24.21.0**, installed Chrome driven by Playwright. Windows was not tested in
this build. No new Mac sleep experiment or timer correctness claim is involved.

| Check | Actual result |
| --- | --- |
| `BEARPLANS_EVIDENCE_DIR=docs/reviews/evidence/weekly BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q` | **228 passed, 0 failed, 0 skipped**, 19.23 s |
| `npm --prefix frontend test` | **31 passed** (18 previous + 13 weekly cases) |
| `npm --prefix frontend run typecheck` | Pass |
| `npm --prefix frontend run build` | Pass |
| Schema 1 and schema 2 compatibility | Tasks/projects retain all stored fields, identities and completion; integrity/FK checks clean |
| Failed planning migration | Rolls back to usable schema 2, then retry succeeds without changing tasks/projects |
| Domain/API behavior | Multiple dates, concurrent duplicate prevention, atomic conflicting moves, selected cross-week moves, same-day no-op, unscheduling, invalid input/IDs, leaf guards and shared completion pass |
| Calendar/timezone | Monday/Sunday, year/month/leap-day, first/last representable full weeks, configured timezone midnight/DST and OS-local default pass |
| Save failure/retry | Real disposable SQLite writer locks POST/PATCH/DELETE; structured 503 leaves records unchanged; retry succeeds after unlock. UI retains attempted dates |
| Real processes | Placements/moves/removals/completion survive restart; foundation graceful/crash/duplicate-instance/launcher/corrupt-data regressions pass |
| Real-browser weekly journey | Add two dates, complete everywhere/derive parent, move one into next week, reject duplicate, unschedule, restart, navigate Today, recover service-down save and retry pass |
| Layout/UX | Inspected 1600 px board, 1024 px laptop, 375 px selected-day and dark-mode screenshots; no horizontal overflow; controls and planned/deadline labels readable |
| Source review | Separate read-only backend/frontend review found no remaining blocker after recovery fixes |
| Scoped whitespace and document checks | Pass; pre-existing planning-document edits left unchanged |

All automated migration, failure and corruption tests used disposable data. The
normal app was updated only after the suite and upgrade checks passed:

1. Identified the stale schema-2 instance at `127.0.0.1:8765`, stopped it gracefully.
2. Created a SQLite backup outside the repository:
   `bearplans-pre-weekly-20261015T071929Z.sqlite3` in the normal data folder.
3. Rehearsed schema 3 on a disposable copy of that backup; all task/project SQL
   values matched, with clean integrity and foreign-key checks.
4. Started the current launcher against the normal folder, verified schema 3 and
   compared all task/project stored fields unchanged after migration. Four saved
   tasks were retained, and no test placements were added to personal data.

The running normal instance now provides weekly planning with the system-local
application timezone (PDT in this session). No database or personal screenshot is
included in the commit.

Synthetic evidence:
[wide board](evidence/weekly/weekly-01-wide.png),
[conflict](evidence/weekly/weekly-02-conflict.png),
[laptop](evidence/weekly/weekly-03-laptop.png),
[failed save](evidence/weekly/weekly-04-save-error.png),
[narrow](evidence/weekly/weekly-05-narrow.png),
[dark](evidence/weekly/weekly-06-dark-wide.png).

## Decisions and remaining evidence

**Implementation/change review: Pass.** The requested daily scope is implemented,
verified and reviewed without a known blocking defect. The local commit containing
this record is authorized by the request; no push. Preserved shared-agent guidance
and this build's progress updates accompany the implementation. Separate pre-existing
roadmap/review-plan edits are retained outside the build commit.

**Operator/build demonstration: pending.** The real-course workflow should be checked
by the user using the checklist below. This does not invalidate the passing
engineering checks, nor certify the full M1 planner milestone: closed-week snapshots
and history are still a subsequent build. No next feature has started.

Accepted limitation: an idle page's Today metadata refreshes on navigation, save or
reload; the Today button always requests the current server date. An optional IANA
timezone requires an installed timezone database; the system-local default needs
no additional package. No new settings screen, historical report, frozen-week gate,
bulk carryover, timer, rewards, AI or integration work is included.

## Five-minute operator demonstration

1. **Minute 1:** Refresh BearPlans. In a test task or existing leaf, open Plan task;
   choose a day and Add to day. Check Planned and Due remain separate.
2. **Minute 2:** Add a second planned date for that same leaf. Complete it from one
   card; both cards/list must agree. For a child, verify its parent still derives
   completion. Unscheduled work must remain available in the project list.
3. **Minute 3:** Use Move or remove on one card to move it into next week. Navigate
   Next/Previous; the other placement stays where it was. Try moving onto its other
   planned date: a conflict should preserve both, with the attempted date retained.
4. **Minute 4:** Remove just one placement. The task, deadline, notes and other date
   must remain. Refresh and verify the placement state persists; automated checks
   already cover a full launcher/service restart.
5. **Minute 5:** Narrow the window, select a day and use keyboard navigation. Click
   Today, check the displayed application timezone, and report any confusing controls.
