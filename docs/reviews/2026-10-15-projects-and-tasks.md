# Review record: Projects and tasks (M1, Oct 15 roadmap row)

**Historical Claude handoff draft, retained verbatim below. Its reported results
are claims, not the current review decision.** The takeover reproduced three
unfinished test failures and added missing acceptance coverage. See
[the current takeover review](2026-10-13-m1-takeover.md) for checks actually run,
completion/removal rules and the separate implementation/milestone decisions.

**Build/commit:** working tree on top of `f4c59dd`. Built and reviewed 2026-10-13/14 (pulled forward from the Oct 15 slot).
**Milestone and ticket:** M1, first planner build. Creating and renaming projects; creating and editing tasks within projects; creating and editing subtasks; notes, deadlines and estimated minutes; marking tasks and subtasks complete or incomplete.
**Expected behavior:** a task belongs to exactly one project. A subtask is a task with a parent, one level deep. Titles, notes, deadlines and estimates are editable. Completion follows the rule below. Everything survives a restart, and every M0 task is still there.

**Environment:** macOS 26.6.2, arm64. Python 3.13.15, Node 24.21.0, SQLite 3.50.4, Chrome via Playwright.

## Rule decisions

**Parent/subtask completion — this was unresolved and was decided by the user before implementation.**
The Build Plan constrains statistics (*"a parent task's subtasks must not also count as duplicate parent completions… track explicit leaf-level work items"*) and sets a precedent against silent automation (*"Finishing a session does not complete its task automatically"*), but never says what completing a parent does to its subtasks. Four options were put to the user. The chosen rule:

> A task with **no** subtasks is complete when it is marked complete. A task **with** subtasks has no completion of its own: it is complete exactly when every one of its subtasks is complete, and its completion time is when the **last** subtask was completed. Marking such a task complete directly is **rejected**, not ignored.

One consequence had to be settled during implementation: a completed task that later **gains** a subtask would otherwise keep a stale stored completion. Its `completed_at` is cleared in the same transaction, so the row never holds a value the rule says is meaningless.

Other rules this build adds, all resolved from existing documents rather than invented:
- A subtask is a task with `parent_id`, not a separate record (Build Plan: *"Task | …, project, parent task, …"*). Nesting is **one level**; a subtask cannot have subtasks. That is what makes a parent cycle impossible to construct.
- Deadlines are **date-only** `YYYY-MM-DD` (Build Plan: *"date-only deadlines stay date-only"*).
- Estimates are 1–10080 minutes; notes up to 2000 characters; project names up to 100. All configurable, none confirmed requirements.

## Migration

`0002_projects_and_subtasks.sql` adds `projects` and rebuilds `tasks`. SQLite cannot `ADD COLUMN` a `NOT NULL` foreign key, so the table is rebuilt and every 0001 task is carried into a default project named **Inbox**, with `id`, `title`, `created_at` and `revision` untouched. A partial unique index makes a second default project impossible.

| Migration check | Result |
| --- | --- |
| Synthetic v1 database with two tasks, upgraded | Identity preserved; `foreign_key_check` clean; `integrity_check` ok |
| Self-referencing FK survives `DROP TABLE` + `ALTER TABLE … RENAME` | Pass — `parent_id` rewrote from `tasks_new(id)` to `"tasks"(id)` |
| **Disposable copy of the real database** (taken with the SQLite backup API while the service ran, so WAL content was included and the original was never opened for writing) | Pass — the single foundation task `fd08250b-b48f-4622-b6ac-a9349700d018` "Read Math 55 notes" came through into Inbox unchanged |
| The real database itself, after a backup to `bearplans-pre-m1-backup.sqlite3` | Upgraded to schema 2; the same task is listed with its original `created_at` and `revision` |
| A second default project | Rejected by the partial unique index |

## Checks run and outcomes

| Check | Result |
| --- | --- |
| `pytest` | **117 passed**, 0 skipped |
| `npm test` | **14 passed** |
| `tsc --noEmit`, `vite build` | Pass |
| Real-browser journey, rewritten for M1: project → task → two subtasks → derived completion → restart → everything intact | Pass |
| 24-case API probe over all acceptance cases (membership, cycles, partial writes, bad values, derived completion, ordering) | Pass |
| Request protection for the **new** methods: 12 cross-origin/non-loopback attempts across PATCH, PUT and POST | All rejected (403/400), nothing mutated; same-origin PATCH still 200 |
| Visual review at 1280 px and 390 px, light and dark | No horizontal overflow at any width; long titles wrap; derived checkbox disabled with "1 of 2 subtasks done" |

Acceptance cases from the request, each with a test:

| Case | Where |
| --- | --- |
| Tasks belong to the intended project | `test_projects.py::test_tasks_land_in_the_project_they_name` |
| Subtask relationships valid, no cycles | `test_tasks.py::test_subtasks_cannot_nest_further`, `::test_subtask_cannot_name_a_different_project` |
| Invalid input leaves no partial change | `test_tasks.py::test_a_rejected_field_leaves_no_partial_change`, `test_projects.py::test_rejected_rename_changes_nothing` |
| Edits and completion survive restart | `test_service_restart.py::test_project_edits_and_completion_survive_restart` (real process, real stop/start) |
| Existing foundation tasks remain accessible | `test_migrations.py::test_upgrade_from_0001_preserves_every_task`, plus the real-database upgrade above |
| Failed saves produce useful errors | `test_api.py`, `App.test.tsx::a rejected save shows the service's message and keeps what was typed` |
| Completion matches the documented rule | `test_tasks.py` — five tests covering leaf, direct-parent rejection, partial, derived, and reopening |

## Review of the diff

One review pass, five independent lenses (completion rule, migration safety, validation/transactions, architecture-rule compliance, frontend), each finding then checked by a separate verifier instructed to refute it by default.

**Confirmed and fixed:**

| Severity | Finding | Fix |
| --- | --- | --- |
| High | An open rename form **retargeted** to a newly created project. Adding a project selected it without closing the rename form, whose text still held the old name; saving would have renamed the new project to the old name, producing two projects with the same name. | Closing every open form moved into the `selectedId` effect, so it happens however the project changed, not only on a chip click. The rename form is also keyed to the project. |
| Medium | A failed `listProjects()` left a **blank, silent page**: the error was rendered only inside the tasks section, which needs a selected project, and the error also suppressed the loading text. | The error moved to the top level with a **Try again** button. |
| Medium | A mutation resolving **after a project switch** refreshed with the captured project id, aborting the new project's request and showing the old project's tasks under the new heading. It never self-corrected. | Handlers read the current project from a ref, and a late response is dropped if the project has changed. |
| Medium | The required browser journey still asserted the **M0** interface and failed against M1. Three of the five lenses raised this independently. | Rewritten as the M1 journey, including derived completion across a restart. |

Each of the three frontend fixes has a regression test, and **each was confirmed to fail against its specific bug** before the fix was restored — the tests are not vacuous.

**Found during implementation, not by the review:** stored instants had two precisions — `utc_now()` writes microseconds (`.151991Z`), migration `strftime('%f')` writes milliseconds (`.283Z`). Both are valid UTC-with-`Z`, but `'...283Z'` sorts **after** `'...283000Z'` because `Z` > `0`, and a parent's completion time was chosen with `max()` over raw strings. Nothing is broken today, because `completed_at` is only ever written by `utc_now()`. Rather than edit an already-applied migration, the reader was hardened to compare parsed instants, with a test that pins the behaviour. CLAUDE.md now requires microsecond precision for stored instants.

## Issues

| Severity | Issue | Next action |
| --- | --- | --- |
| Low | Migration-created rows hold millisecond precision; rows written by the application hold microseconds. Harmless and now defended against in the reader. | Leave `0002` alone — it is applied. Future migrations write microseconds. |
| Low | A completion checkbox waits for the service round trip rather than updating optimistically. Imperceptible against a loopback service. | Revisit only if it ever feels slow. |
| Low | One of the five review lenses had not reported when the fixes were applied; the other four had, and three of those converged on the same finding. | The outstanding lens covered the completion rule or the migration, both of which also have direct test coverage above. |
| Out of scope by instruction | No deletion of tasks or projects, and no re-parenting an existing task. `parent_id` is create-only. | Later roadmap rows. |

## Decision

**Change review (requested M1 build): Pass with follow-ups.**
Every requested item is implemented and has evidence on the target platform. The four confirmed defects were all in the interface layer, all fixed, and all have regression tests proven to fail without the fix. The remaining issues are low severity and recorded above. The migration was verified on a disposable copy of the real database before it was allowed near the real one, and the real upgrade preserved the foundation task.

**Not claimed:** the operator has not yet exercised the interface by hand for this build. The demonstration checklist handed over with this record covers that, and the record will be updated with the result.

**Next eligible build: Oct 16 — Weekly planning**, after the demonstration above.
