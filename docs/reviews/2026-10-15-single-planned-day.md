# Weekly planning refinement — one planned day

Date: 2026-10-15 (America/Los_Angeles). Baseline: `801cbc3`.
Latest explicit user decision supersedes the original weekly build's multi-day rule.

## Acceptance scenario and data model

Each leaf task or subtask can have at most one planned date across all weeks,
including completed work. Work requiring several days is split into smaller
subtasks, each scheduled independently. Finishing one child leaves the others
unfinished; completing all children completes their parent. Task completion still
agrees between the project list and its board card.

Schema 4 adds a unique index on `planned_items(task_id)`; schema 3's applied SQL is
unchanged. Existing task and placement identities, task fields, completion/history,
and placement timestamps/revisions are preserved by the upgrade. Shared Python
domain functions reject a second assignment, returning 409 with the existing date
and instructions to Move or split work. Move updates the existing placement's date
and revision without creating work or changing task completion. Different tasks
may share a date; a same-date move remains a no-op. Unscheduling preserves the task
and permits scheduling it again.

Scheduled leaves expose Move/remove controls instead of another assignment form.
Unscheduled leaves retain their date picker. Parents remain context, and existing
scheduled-parent/subtask deletion guards remain in force. Planned dates remain
distinct from deadlines. Failed saves retain the attempted date and useful errors.

Recovery: a failed legacy upgrade never chooses/deletes planned dates. If schema 3
contains multiple dates for one task, the upgrade rolls back with instructions to
open the previous build, remove extra planned dates, then retry. Tests use disposable
databases; personal data is backed up with SQLite's backup API before upgrade.

## Checks and decisions

Detected **macOS 26.6.2 (25G83)**, Python **3.13.15**, Node **24.21.0**, installed
Chrome. No Windows or new Mac sleep/wake verification is claimed.

| Command/check | Actual result |
| --- | --- |
| `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q` | **242 passed, zero failures/skips**, 21.19 s |
| `npm --prefix frontend test` | **32 passed**, 2.94 s |
| `npm --prefix frontend run typecheck` | Pass |
| `npm --prefix frontend run build` | Pass |
| `BEARPLANS_EVIDENCE_DIR=docs/reviews/evidence/single-day BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q tests/test_weekly_browser.py` | **1 passed**, 4.04 s; synthetic screenshots below |
| Independent review: `.venv/bin/python -m pytest -q tests/test_planning.py tests/test_planning_api.py tests/test_migrations.py` | **103 passed**, 1.91 s; source review Pass |
| Domain/API/DB constraints | Reject second dates even for completed work or other weeks; concurrent different-day requests save once; direct SQL is constrained |
| Movement/removal/completion | Same-date no-op, cross-week identity-preserving move, different tasks on same date, unschedule/reassign, independent siblings and derived 1/2 → 2/2 → 1/2 parent pass |
| Migration/restart | v1/v2/v3 compatibility; all task/project/placement fields retained; legacy duplicates fail with unchanged schema-3 rows/structure and actionable error; explicit resolution/retry succeeds; startup/restart regressions pass |
| Failure handling | Locked SQLite POST/PATCH/DELETE and service-down browser save retain data/input, show useful errors and retry successfully |
| Layout | Inspected synthetic wide 1600 px, laptop 1024 px, narrow 375 px, failure and dark-mode evidence; no horizontal overflow |
| Documentation/diff | Local links and scoped whitespace pass; CLAUDE.md retained; pre-existing planning-file content and staged state preserved |

An initial test-agent service run was blocked by sandbox loopback restrictions,
causing 12 permission failures. The permitted rerun passed all 12 service tests
(8.41 s); the final full suite passed with no skips. All automated failure,
corruption and migration tests use disposable data.

Normal running instance update after passing checks:

1. Identified the old launcher/service (88787/88789), verified the normal data
   folder and zero multi-day duplicates, then stopped that launcher gracefully.
2. Created `bearplans-pre-single-day-20261015T153552Z.sqlite3` in the normal data
   folder using SQLite's backup API, outside Git.
3. Rehearsed migration 4 on a disposable backup copy. All original task/project/
   placement SQL fields matched; integrity and foreign-key checks were clean.
4. Restarted the current launcher, verified `/api/health` reports schema 4, and
   compared normal database rows before/after. **Five tasks and two placements**
   retained unchanged, with clean integrity/FK checks. No synthetic records or
   personal screenshots were created in the normal app.
5. Inspected the updated normal interface in Chrome using read-only checks. Both
   saved scheduled leaves show Move/remove without a second assignment form; the
   board displays the one-day rule. No personal data was changed or captured.

Synthetic evidence: [wide](evidence/single-day/single-day-01-wide.png),
[stale assignment conflict](evidence/single-day/single-day-02-conflict.png),
[laptop](evidence/single-day/single-day-03-laptop.png),
[save error](evidence/single-day/single-day-04-save-error.png),
[narrow](evidence/single-day/single-day-05-narrow.png),
[dark](evidence/single-day/single-day-06-dark-wide.png).

**Implementation review: Pass.** Shared Python logic, DB constraint, UI, migration
recovery and regressions match the new rule, with no blocking defect found by a
separate source review. Relevant local commit authorized by the ongoing weekly
build request; no push. Existing staged roadmap/review-plan edits remain untouched
outside that commit. CLAUDE.md remains available and references updated shared rules.

**Operator demonstration: pending.** The user should refresh the running app and
check the revised workflow below. The earlier projects/tasks operator acceptance
remains passed. The broader M1 milestone is not certified: weeks/history is still
not started; no next feature is included.

Known limitation: older databases containing multiple planned days cannot start
this build until extra dates are explicitly removed using the previous build.
This preserves all saved plans rather than selecting a date without permission.
The actual normal database had no such duplicates and upgraded successfully.

## Five-minute operator demonstration

1. Refresh BearPlans. Plan an unscheduled leaf for one day. Check Planned and Due
   are separate and its controls now say Move or remove plan, with no Add to day.
2. Move that plan into next week. Navigate Next/Previous: the old card disappears
   and only one card exists. Its notes, deadline and completion stay unchanged.
3. Create a two-part task with two subtasks; plan them on different days. Complete
   one: the other stays incomplete and the parent shows 1 of 2.
4. Complete the other child: the parent shows 2 of 2 and completes. Reopen one child:
   the parent reopens. Remove a child's plan: the child remains in the task list.
5. Reassign the unscheduled child, refresh, then narrow the window and select its
   day. Confirm one date per work item and readable Move/remove controls.
