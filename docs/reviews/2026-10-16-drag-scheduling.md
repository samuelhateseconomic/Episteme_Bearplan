# Weekly board — drag Move and Option/Alt Add

Later October 16 interface follow-up: modifier Add, Add-another-day forms, the board
instructions and visible Drag label are superseded by the
[move-only refinement](2026-10-16-drag-simplification.md). This record retains the
original build's evidence. Existing saved placements and schema 7 remain intact.

October 16, 2026, America/Los_Angeles. Baseline **`bbe6059`**, with the existing
reviewed disabled-tracking-button copy follow-up preserved. Countdown baseline
**`c4b7dd3`** is an ancestor. The local commit containing this record identifies
this build. Schema **6 → 7**; no dependency or timer/recovery changes.

## Decision and scope

**Implementation review: Pass.** The preceding tracking
interface and its copy follow-up were independently rechecked before drag edits:
63 frontend tests passed (3.06 s), typecheck passed, and the real Chrome eligibility
journey passed (1 test, 2.11 s). Synthetic 1440/375 px views were inspected. No
tracking prerequisite defect was confirmed.

**Overall M2 gate remains Fail / not passed, pending recovery acceptance.** This
build does not certify sleep/wake, crash or clock-change recovery. No new operator
acceptance is claimed, and no recovery build or push is authorized by this review.

The explicit Option/Alt-add request supersedes October 15's one-active-date rule:
a leaf can now have several active planned dates, with **one placement per
task/date**. Each card references the same task; completion is shared and weekly
completion counts unique scheduled leaves. The earlier refinement review remains
historical evidence, with a supersession note. AGENTS and README record the current
rule. User-staged review-plan/roadmap edits and unstaged roadmap checkmarks remain
outside this build commit, with their exact original diff hashes preserved.

Read AGENTS, CLAUDE, progress, build/review plans, roadmap, README and current reviews;
inspected recent commits, staged/unstaged changes and untracked work. No nested
AGENTS applies. Before editing, stated Move/Add transitions, the multi-date rule,
schema upgrade, affected records, cancellation/failure behavior and acceptance
cases. The earlier copy removal is retained; no disabled-button explanation returns.

## Implemented behavior and records

- Drag the dedicated card handle to **Move** the existing placement. Its ID and
  creation instant stay fixed; only that placement's date/update/revision change.
  Hold **Option on macOS / Alt on Windows while dropping** to **Add** a destination
  placement for the same task, retaining the source and all other placements.
- A floating, bounded **Move/Add** status shows the task and hovered date. Valid
  destinations have dashed green outlines; the hovered destination is solid.
  Occupied dates are visibly marked as conflicts. Gesture guidance sits near the
  board. Narrow layouts accept drops on the seven day buttons without selecting
  another day or switching weeks.
- Same-day drops in either mode, Escape, outside drops and drag-end cancellation
  save nothing. Task/date conflicts preserve all existing placements and explain
  choosing another day. Failed saves keep the last saved board, show a structured
  error and offer **Refresh weekly plan** before retrying. There is no optimistic
  removal to undo after a rejected save. A lost response can have saved successfully;
  refresh checks the persisted state before another attempt.
- Existing **Move or remove** date controls remain. **Add another planned day** on
  cards and in task planning offers a labeled date input and **Add to day**, usable
  with a keyboard and for dates outside the shown week. Reverse a saved move by
  moving back; reverse an addition by removing that placement. No one-click Undo,
  task cloning, recurrence or automatic week switching was added.
- Only the handle is draggable. Checkbox, tracking button, summaries, date inputs
  and other card interactions retain their existing functions. Closed history has
  no drag handles, completion controls or scheduling forms.
- Existing shared `move_placement` and `create_placement` functions remain the
  mutation path. Both validate destination open-week/leaf/duplicate eligibility
  inside `Database.write()`. Modifier Add supplies optional `source_placement_id`;
  that same transaction also requires an existing active source, open source week
  and matching task. A source archived by another tab is rejected. Ordinary date
  assignment still requires an existing leaf and open destination. Concurrent
  requests serialize, with SQL task/date uniqueness as the final barrier.
- Scheduling never writes task, timer or closed-history rows. Task ID, project,
  parent, title, notes, date-only deadline, completion and completion instant stay
  attached to the task; session intervals remain attached to when work happened.
  Completing one of several cards completes their shared task. Starting/finishing
  tracking still never changes completion. Carryover's existing policy remains:
  a leaf with any active placement is explained as already planned and excluded.

## Storage and saved-data safety

`0007_multiple_planned_days.sql` only removes the superseded
`planned_items_one_per_task` index. Original `UNIQUE(task_id, planned_date)`, foreign
keys, WAL and all row fields remain. Applied migration files were not edited.

A legacy schema-3 multi-date database would otherwise fail at historical migration
4 before reaching 7. A narrowly recognized **exact shipped 4–7 chain** is therefore
applied/recorded in one transaction, skipping only the transient index removed by
7. No intermediate version commits without its promised constraint. Custom chains
or old targets retain their fail-safe behavior. Tests deny timer-table creation
mid-upgrade and verify full schema/row/receipt rollback, then successful retry.
Schema-6 failure/retry tests preserve every original task, placement, closed snapshot,
timer/session interval and receipt. Legacy multiple dates survive intact.

All mutation, conflict, migration failure and crash/restart tests use disposable
databases. A live SQLite backup of the normal WAL database was made with SQLite's
backup API, then the schema-7 upgrade was rehearsed on another disposable copy.
Every original field and migration row matched; integrity and foreign keys passed.

Identified the normal service (PID 5897, launcher 5874, port 8765), rechecked no
running/paused/Needs review session, stopped that launcher gracefully and confirmed
the port released. Before restart, all saved rows still matched the rehearsal
baseline. Created durable backup **`bearplans-pre-drag-20261016T164423Z.sqlite3`**
beside the normal data in `~/Library/Application Support/BearPlans/`. Restarted with
`python3 launch.py --no-browser`; production build and startup passed at schema 7.

Read-only Chrome inspection of the normal app checked the already-closed current
week, the next open week's handles/guidance, Track's exact incomplete-leaf choices
and 1440/375 px overflow. No personal scheduling/timer/completion action or screenshot
was taken. After inspection, **every field in every original SQL table** and the
original six migration rows still matched the pre-upgrade backup. Counts remain
nine tasks, two projects, three active placements, two closed weeks, four archived
placements, three finished sessions, four intervals and eight timer receipts.
Integrity/FKs pass. The planning response was unchanged by read-only navigation.

## Checks actually performed

Host: **macOS 26.6.2 (25G83), Darwin arm64**; Python **3.13.15**, Node **24.21.0**,
Chrome **155.0.8059.82** via Playwright. No Windows hardware or new sleep evidence.

| Command/check | Actual result |
| --- | --- |
| `npm --prefix frontend test` before drag edits | **63 passed**, 3.06 s; preceding tracking interface and copy follow-up. |
| `BEARPLANS_EVIDENCE_DIR=/private/tmp/bearplans-drag-prereq BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s tests/test_timer_eligibility_browser.py` | **1 passed**, 2.11 s; permitted Chrome rerun of prerequisite. |
| `.venv/bin/python -m pytest -q tests/test_planning.py tests/test_planning_api.py tests/test_migrations.py tests/test_weeks.py tests/test_timer.py` | **227 passed**, 6.46 s; independent reviewer also 227 passed, 6.33 s. |
| `.venv/bin/python -m pytest -q tests/test_service_restart.py`, with loopback permission | **13 passed**, 10.13 s; persisted Move/Add and unchanged sessions/history after service restart. |
| `npm --prefix frontend test`, after native-drag geometry correction | **74 passed**, 3.33 s. |
| `npm --prefix frontend run typecheck` | **Pass**. |
| `npm --prefix frontend run build` | **Pass**, 83 ms Vite; launcher rebuild also passed. |
| `BEARPLANS_EVIDENCE_DIR=/private/tmp/bearplans-drag-native BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s tests/test_drag_browser.py`, with Chrome/loopback permission | **2 passed**, 7.76 s, using actual native mouse/key gestures and final production assets. |
| `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q --ignore=tests/test_drag_browser.py` | Initial full existing core: **397 passed, 1 failed**, 116.69 s. M1 helper matched both Move/Add date fields; scoped to Move form. |
| `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q tests/test_m1_journey_browser.py` | Corrected joined M1 regression **1 passed**, 3.55 s. |
| Final `BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q`, with Chrome/loopback permission | **400 passed**, **118.99 s**, zero failed/skipped, after all product/helper corrections. Includes the new native cases and real-minute countdown regression. |
| Independent backend/UI review; scoped diff/whitespace, document links, original planning-diff hashes | No remaining confirmed source blocker; final handoff checks recorded before commit. |

Domain/API cases cover multiple dates, same-date conflicts, missing/mismatched or
archived Add sources, closed destinations and archived Move IDs, no-op revisions,
concurrent Add/Move, shared completion/unique-leaf history, rollback/retry and schema
compatibility. Existing timer fake-clock limits, pause arithmetic, retries, one
unfinished session, expiry, restart review and task-completion separation remain
in the core suite. No timer business logic changed.

The native journeys verify actual Mac Option (`Alt` event) Add and ordinary Move,
both indicators and target highlights, exact source IDs/revisions/creation times,
retained source/other cards, both same-day modes, Escape/outside cancellation,
both duplicate modes, failed POST/PATCH followed by exact successful retries,
server-side competing-tab 409, source closure while dragging, historical rows,
keyboard Add/date fields/Track entry, normal checkbox completion and reopening,
card-control drag attempts, 375 px day-button targets with unchanged selected day
and week, and complete task/session/snapshot persistence after restart. No page
errors or horizontal overflow. A genuine short timer result is saved before the
move and compared field-for-field afterward; the existing real-minute timer
regression runs separately in the full core suite.

### Failures and corrections

- Native Chrome exposed a **confirmed UI defect** missed by DOM-event tests:
  inserting an in-flow status or removing an old error during drag start moved the
  source and stalled native dragging. Exploratory runs were interrupted at 88.53 s
  and 46.99 s; they were not counted as passes. A temporary diagnostic overlay
  isolated the cause. Product feedback now uses a fixed, bounded overlay; existing
  in-flow errors stay put until drop. Final tests use no diagnostic CSS and cover
  repeated drags after conflicts/failures.
- Initial restricted loopback/Chrome attempts were denied by the sandbox (restart
  tests: 13 setup failures; prerequisite browser skipped). Reruns with permission
  supplied the actual results above. No sandbox skip is claimed as evidence.
- Initial permitted restart test: 12 passed, 1 failed because it expected the old
  cross-date conflict. Updated it to the retained same-task/date conflict; final
  13 passed. M1's ambiguous date selector was similarly updated without weakening
  the saved identity/history assertions.
- A native keyboard helper assumed one Tab left Chrome's segmented date input.
  It now traverses its actual date subfields to the Add button; final native tests
  pass. Early DOM drag tests supplied Alt via MouseEvent because jsdom lacks native
  DragEvent modifier support. Native Chrome evidence above verifies the real path.
- Normal-app read-only preflight initially used `status` rather than the actual
  timer `state` column, and a later UI check assumed the current week was open.
  Corrected the read query and inspected the existing closed week before navigating
  to the next open week. Both initial checks stopped without mutating personal data;
  corrected backup/schema/field/UI verification passed.

### Visual evidence

All images use synthetic disposable data. Reviewed wide **1600 px** and narrow
**375 px** layouts, feedback, failure copy, closed read-only cards and date controls:

- [Move/highlights](evidence/drag-scheduling/drag-01-move-wide.png),
  [Option Add](evidence/drag-scheduling/drag-02-add-wide.png).
- [Narrow day-button drop](evidence/drag-scheduling/drag-03-move-narrow.png),
  [saved narrow board](evidence/drag-scheduling/drag-04-saved-narrow.png).
- [Failed-save board](evidence/drag-scheduling/drag-05-save-error-wide.png).
- [Closed wide](evidence/drag-scheduling/drag-06-closed-wide.png),
  [closed narrow](evidence/drag-scheduling/drag-07-closed-narrow.png).

## Remaining checks and demonstration

No confirmed drag-build blocker remains after the native correction. Physical
Windows Alt-drag and hands-on operator acceptance are **not newly performed**;
Mac Chrome native Alt/Option behavior and shared event/unit paths are verified.
The overall M2 recovery/hardware gate remains pending. Current conservative Needs
review behavior persists; this build does not credit uncertain time or treat tab
visibility as laptop sleep. Recovery and all later builds remain not started.

Short demonstration, preferably using a disposable sample plan:

1. Schedule a leaf on Monday; drag its handle to Tuesday. Observe **Move**, target
   highlight, unchanged deadline/task identity and only Tuesday remaining.
2. Option/Alt-drag Tuesday to Wednesday. Observe **Add** and both cards; complete
   either card, see both agree and weekly totals count the task once, then reopen.
3. Drop onto Wednesday again, onto Tuesday itself, press Escape during a drag and
   drop outside. Conflicts explain themselves; no-op/canceled plans stay unchanged.
4. Use keyboard **Move or remove** and **Add another planned day**. Activate the
   checkbox and **Start tracking** independently; tracking opens the same task.
5. Narrow the window and drag onto a day button; refresh/restart and revisit the
   saved dates. View existing closed history and confirm it offers no drag controls.
   Failed-save/retry and mid-drag closure are covered by disposable automated
   fixtures; do not close a personal week merely to rehearse when reopening is absent.

The reviewed build passes and is included in the local commit containing this
record, along with the preserved, separately reviewed disabled-button copy
follow-up. Unrelated user planning edits stay outside that commit. No push or
automatic recovery build.
