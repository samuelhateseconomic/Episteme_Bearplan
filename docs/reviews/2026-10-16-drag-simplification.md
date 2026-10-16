# Weekly board — move-only drag interface

The later [card-context follow-up](#card-context-and-due-date-follow-up) moves the
grip beside the project/parent line and removes redundant Planned metadata from
weekly cards. Earlier title-row placement checks below remain historical evidence.

October 16, 2026, America/Los_Angeles. Baseline **`a7de8bf`**, verified in Git.
Follow-up to the user's three interface refinements, included in the local commit
containing this record after the user's subsequent commit request. **Implementation
review: Pass.** Schema remains **7**, with no backend, migration, dependency or timer
changes. Overall M2 recovery acceptance stays pending; recovery is not started.

Read AGENTS, CLAUDE, shared progress, build/review plans, roadmap, README and the
latest drag review. Inspected recent commits and complete staged/unstaged diffs;
only unrelated user review-plan/roadmap edits were present at entry. Their exact
staged/unstaged diff hashes are preserved. No nested AGENTS applies.

Before editing, stated that dragging will only move, modifier Add and all
Add-another-day choices disappear, board instructions are removed, and the grip
icon goes before the task name. Existing placements and all saved data remain.
This is an interface simplification: it does not reinstate the old one-active-date
database constraint. Initial scheduling remains for unscheduled tasks. Existing
multiple placements stay visible/movable/removable; no records are removed to
make the interface simpler.

## Changes and acceptance

- Dragging with or without Option/Alt invokes only the shared Move endpoint for
  the existing placement. Move status/highlights, duplicate errors, failure/refresh,
  Escape/outside cancellation and same-day no-op remain.
- Removed Add-another-day forms from cards and task planning, and removed their
  modifier handling, optional frontend source ID plumbing and unused styles.
  Unscheduled task assignment and keyboard Move/remove date controls remain.
- Removed the entire open-board instructional paragraph. Historical snapshot
  information remains available in closed weeks.
- Replaced the visible Drag word with a compact grip icon before the checkbox/task
  name in the same title row. The handle retains an accessible name and tooltip;
  date controls provide the keyboard alternative. Card controls do not start drag.
- Existing task/placement identity, deadlines, completion, saved timer intervals,
  historical snapshots and multi-date records remain. Reverse a saved move with
  Move placement; failed saves keep the saved board and offer refresh. No database
  or session-recovery changes. The running normal service can serve the rebuilt
  interface on refresh without a service restart.

## Checks actually performed

Actual host: **macOS 26.6.2 (25G83), Darwin arm64**. Mutation/failure/browser data is
synthetic and disposable. No physical Windows or new sleep/recovery acceptance.

| Command/check | Actual outcome |
| --- | --- |
| `npm --prefix frontend test` | **74 passed**, **3.31 s**. Includes initial scheduling, no extra-date choices, preserved existing dates, shared completion, move-only modifier behavior, controls and error cases. |
| `npm --prefix frontend run typecheck` | **Pass**. |
| `npm --prefix frontend run build` | **Pass**, Vite **82 ms**. |
| `BEARPLANS_EVIDENCE_DIR=/private/tmp/bearplans-drag-move-only BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -x -s tests/test_drag_browser.py`, with loopback/Chrome permission | **2 passed**, **7.24 s**, no diagnostic CSS or dispatched-drag substitutes. |
| `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q tests/test_weekly_browser.py tests/test_weeks_browser.py tests/test_m1_journey_browser.py tests/test_timer_eligibility_browser.py tests/test_timer_browser.py::test_countdown_navigation_tabs_pause_retry_and_history tests/test_e2e_browser.py`, with permission | **7 passed**, **23.04 s**, zero failed/skipped. Existing planner, M1, history, task/subtask and tracking journeys. |
| Running normal service | Read-only GET `/` exactly matches rebuilt `frontend/dist/index.html`. No service restart, database operation or personal-record mutation needed. Initial sandbox socket denial was rerun with permission; it was not an app failure. |
| Diff/doc checks | Scoped whitespace and local links pass; backend/storage/migrations unchanged. Original staged/unstaged user planning diff hashes preserved. |

Native Chrome verifies ordinary Move and actual Option/Alt Move of the same ID,
with all interface placement writes captured as **PATCH only**, never POST. Existing
extra placements seeded through the API are preserved through movement, conflicts,
shared completion, task reopening and restart. Also covered: same-day drops with
and without Option, Escape/outside cancellation, duplicate conflicts, failed PATCH
with and without Option plus successful retry, stale competing destination, source
closure mid-drag, keyboard date Move and Track entry, independent card controls,
narrow day-button drop without day/week switching, exact saved timer/session rows,
closed snapshots and unchanged task fields/deadline after restart.

Inspected seven fresh synthetic images at **1600 px** and **375 px**; no horizontal
overflow or page errors. The grip has no visible text, precedes the checkbox/task
name and overlaps the title's first line vertically at both widths. Native measured
wide grip x=446.19–463.78 and label x=493.36; grip y=519.66–543.66 and label
y=521.66–538.66. Narrow grip x=55–72.59 and label x=102.17; grip y=697.67–721.67
and label y=699.67–716.67. The open-board paragraph and extra-date controls are absent.

Evidence: [wide Move](evidence/drag-move-only/drag-01-move-wide.png),
[Option Move](evidence/drag-move-only/drag-02-alt-move-wide.png),
[narrow drop](evidence/drag-move-only/drag-03-move-narrow.png),
[saved narrow](evidence/drag-move-only/drag-04-saved-narrow.png),
[failed save](evidence/drag-move-only/drag-05-save-error-wide.png),
[closed wide](evidence/drag-move-only/drag-06-closed-wide.png),
[closed narrow](evidence/drag-move-only/drag-07-closed-narrow.png).

The preceding build's **400-test full-core** result remains historical, not a new
check. Backend domain/timer/storage code is unchanged, so no new full-core or
real-minute run was needed for this interface refinement. No confirmed product
defect or unresolved test failure arose in this follow-up.

## Decision and remaining checks

**Pass.** No confirmed interface blocker remains. Physical Windows gestures and
new hands-on operator acceptance are not claimed. The follow-up was initially left
uncommitted; the user subsequently requested a local commit, which includes this
record. No push. Overall M2 still requires recovery acceptance, which was not started.

Short demonstration: move a card using the icon before its title, repeat holding
Option/Alt and confirm the source moves, then use keyboard Move/remove. Confirm
there is no board instruction paragraph or Add-another-day option. Try Escape,
same-day/outside drops, narrow day-button targets and existing closed history.

## Card context and due-date follow-up

Later October 16 correction to the same interface refinement. **Implementation
review: Pass.** The user clarified that the grip belongs to the left of the
project/parent-task line, above the leaf/subtask title. Weekly cards need the due
date without repeating the planned date already represented by their day column.
Before editing, stated this placement and the scope of the date removal. Kept
planned dates in the task list, keyboard date controls, accessibility labels and
records. No clarification was needed for these concrete changes.

Moved the existing icon into a wrapping `.planned-card-heading` row beside project/
parent context. Checkbox/title retain their own row. Removed visible Planned-date
metadata from open and historical cards. Historical snapshot contents, task fields,
timers, placements and schema 7 are unchanged. Initial scheduling, move-only drag,
failure/cancel handling and keyboard alternatives remain. Existing uncommitted
work and unrelated staged/unstaged planning edits are preserved. The later local
commit request covers this correction too; no push or recovery build requested.

Actual checks: `npm --prefix frontend test` **74 passed**, **3.33 s**;
`npm --prefix frontend run typecheck` **Pass**; `npm --prefix frontend run build`
**Pass**, Vite **86 ms**. Existing assertions now check the header grip and due-only
card display, including historical cards. M1's browser helper waits for the moved
card's dated accessibility label instead of visible Planned metadata, retaining
the saved-state wait. Checks ran on the same **macOS 26.6.2 (25G83), Darwin arm64**
host, using disposable data:

- `BEARPLANS_EVIDENCE_DIR=/private/tmp/bearplans-card-context BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -x -s tests/test_drag_browser.py`, with permission:
  **2 passed**, **7.68 s**, no failures/skips. The first fixture now uses an actual
  parent and subtask. Native ordinary/Option Move, PATCH-only writes, existing dates,
  shared/derived completion, keyboard controls, cancellation/conflicts, failed-save
  retry, closed history, timer preservation and restart assertions all pass.
- `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q tests/test_weekly_browser.py tests/test_weeks_browser.py tests/test_m1_journey_browser.py tests/test_timer_eligibility_browser.py tests/test_timer_browser.py::test_countdown_navigation_tabs_pause_retry_and_history tests/test_e2e_browser.py`, with permission:
  **7 passed**, **23.14 s**, zero failed/skipped.
- Seven new synthetic wide/narrow images inspected at **1600/375 px**, with no
  overflow or page errors. The grip is left of context, above the leaf title, and
  absent from the title row. Measured wide grip x=446.19–463.78, context x=469.38,
  grip y=495.27–513.27, context first-line y=496.27–511.27. Narrow grip x=55–72.59,
  context x=78.19, grip y=673.28–691.28, context first-line y=674.28–689.28. Open and
  closed cards have no Planned metadata, retain Due, and task-list planned dates
  remain. Evidence: [wide](evidence/card-context/drag-01-move-wide.png),
  [Option Move](evidence/card-context/drag-02-alt-move-wide.png),
  [narrow drop](evidence/card-context/drag-03-move-narrow.png),
  [saved narrow](evidence/card-context/drag-04-saved-narrow.png),
  [failed save](evidence/card-context/drag-05-save-error-wide.png),
  [closed wide](evidence/card-context/drag-06-closed-wide.png),
  [closed narrow](evidence/card-context/drag-07-closed-narrow.png).
- Read-only GET of the normal service's interface matches the rebuilt HTML. No
  restart, personal-data access/mutation, schema change or timer interruption.
  Scoped whitespace, local document links and original staged/unstaged user
  planning hashes pass. No full-core/timer-domain repeat for these render-only
  changes; earlier core evidence remains historical. No unresolved failure.

No confirmed blocker remains. This follow-up and the preceding move-only changes
are included in the user-requested local commit containing this record. No push,
new operator/Windows hardware acceptance or M2 recovery
acceptance is claimed. Recovery remains not started. Demonstration: inspect the
project/parent grip with its subtask below, confirm Due without Planned metadata,
drag/move with the icon, use keyboard Move, and revisit the same due-only closed
card layout without changing historical data.
