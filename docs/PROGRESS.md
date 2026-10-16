# BearPlans — shared progress and handoff

Read [AGENTS.md](../AGENTS.md) first; Claude also reads [CLAUDE.md](../CLAUDE.md).
This is the single mutable work/handoff record. Detailed reviews retain evidence.

## Current state

**Card context/due-date follow-up: implementation review Pass.** The
grip is now to the left of the project/parent-task line, above the leaf/subtask
title. Redundant Planned-date metadata is removed from open and historical weekly
cards; due dates remain, and planned dates stay in task planning, Move controls,
accessibility labels and saved records. Frontend **74 passed**, 3.33 s; typecheck
and production build passed (86 ms). Native wide/narrow **2 passed**, 7.68 s;
affected planner/history/tracking Chrome regressions **7 passed**, 23.14 s. Actual
parent/subtask context, icon alignment, due-only open/closed cards, unchanged saved
dates, drag/retry/keyboard and restart/history/session behavior pass. Seven synthetic
images inspected at 1600/375 px. The running service serves the new interface on
refresh, with no restart or personal-data operation. See the
[review follow-up](reviews/2026-10-16-drag-simplification.md#card-context-and-due-date-follow-up).
The user subsequently requested the local commit; this follow-up and the preceding
move-only refinement are included in the commit containing this record. No push.

**Move-only drag interface refinement: implementation review Pass against `a7de8bf`.**
Removes Option/Alt Add, all Add-another-day controls, the open-board dragging paragraph
and the visible Drag label. The earlier grip placement by the leaf title is
superseded by the follow-up above. Initial scheduling, keyboard Move/remove, native Move feedback,
cancel/conflict/error handling and existing placements remain. Schema stays **7**;
no new one-active-date constraint or data migration. See the
[current review](reviews/2026-10-16-drag-simplification.md). Included in the local
commit containing this record at the user's request. No recovery work or push. The normal service
serves the rebuilt interface on refresh; no service restart or user-data writes.

**Preceding drag Move / Option–Alt Add build: implementation review Pass**, commit
`a7de8bf` against `bbe6059` (countdown ancestor `c4b7dd3`). Its Add interface is
superseded by this follow-up; saved multi-date records remain supported and intact.
The [original drag review](reviews/2026-10-16-drag-scheduling.md) retains its actual
400-test full-core evidence rather than claiming that result for this follow-up.

The preceding tracking interface and cosmetic follow-up were reverified **Pass**
before drag edits: frontend **63 passed**, typecheck passed, Chrome **1 passed**,
1440/375 px inspected. The already-present removal of explanation beneath disabled
Start tracking controls is preserved, with its tests/review/evidence included in
`a7de8bf`. See the
[cosmetic follow-up](reviews/2026-10-16-countdown-eligibility.md#cosmetic-follow-up--remove-disabled-button-explanation).
No timer eligibility or session behavior changed in this drag build.

**Countdown eligibility and weekly-card entry refinement: implementation review Pass.**
Committed build: `bbe6059`; its earlier explanation requirement is superseded by
the cosmetic follow-up above. That refinement was reviewed October 16, 2026 against
verified baseline **`c4b7dd3`**, then at schema **6** without migration. Its
[review](reviews/2026-10-16-countdown-eligibility.md) retains the original evidence.
The original normal countdown build remains passed; its
[review](reviews/2026-10-16-countdown.md) and full-suite results are historical
baseline evidence, not new checks for this refinement.

**Overall M2 countdown/recovery gate: Fail / not passed because required recovery
and hardware evidence is outstanding.** The recovery build is **not started**.
Normal countdown acceptance does not certify sleep/crash/clock-change recovery,
midnight/DST, long-session precision or battery/standby/hibernate behavior.
No new operator acceptance is claimed.

**M1 technical/prerequisite review: Pass.** Before countdown product edits, the
joined create-task/subtask → schedule → move → close → revisit after edit/restart →
carryover journey and full baseline passed. No confirmed planner prerequisite defect
needed correction. [M1 review](reviews/2026-10-16-m1-review.md) records exact saved
identities, date-only deadlines, derived completion/leaf denominators and immutable
snapshots. Session-linked movement/editing and unscheduled Track selection now pass
in countdown integration tests. Broader M1 operator/manual certification remains
unpassed; no real-coursework demonstration or itemized user evidence was invented.
Prior projects/tasks operator approval and October 15 overall history approval remain
valid; the latter was “Looks good to me,” not an itemized checklist report.

Pre-existing staged user edits to `BearPlans_Build_Review_Plan.md` and
`BearPlans_Dated_Roadmap.md`, plus the unstaged roadmap checkmarks, are preserved
outside application changes. Their staged/unstaged diff hashes remain unchanged.
`CLAUDE.md` remains substantive and points here.

## Completed builds

| Build | State | Evidence / relevant commits |
| --- | --- | --- |
| M0 / foundation | Implementation and Mac/operator gate passed | [M0 review](reviews/2026-10-14-local-foundation.md); `36f6e48`, `f4c59dd` |
| Projects/tasks/subtasks | Implementation and all six operator checks passed | [Takeover review](reviews/2026-10-13-m1-takeover.md); `a9ba50b`, `d2174a6` |
| Weekly planning + one-day refinement | Implementation Pass; original individual checklist not newly attested | [Refinement](reviews/2026-10-15-single-planned-day.md), `a21cb49`; [weekly evidence](reviews/2026-10-15-weekly-planning.md), `801cbc3` |
| Weeks/history/carryover | Implementation Pass; overall user acceptance Pass | [History review](reviews/2026-10-15-weeks-history.md), `7155bc2`; acceptance `69c6630` |
| Joined M1 technical review | Pass; broader operator gate not newly certified | [October 16 review](reviews/2026-10-16-m1-review.md) |
| M2 normal countdown | Implementation Pass; overall M2 gate not passed | [Countdown review](reviews/2026-10-16-countdown.md), `c4b7dd3` |
| Countdown eligibility/weekly-card refinement | Implementation Pass; overall M2 pending recovery acceptance | [Eligibility review](reviews/2026-10-16-countdown-eligibility.md), `bbe6059`; cosmetic follow-up in `a7de8bf` |
| Weekly drag Move / Option–Alt Add | Implementation Pass; Add interface superseded by later follow-up | [Drag review](reviews/2026-10-16-drag-scheduling.md), `a7de8bf` |
| Move-only drag interface refinement | Implementation Pass | [Current review](reviews/2026-10-16-drag-simplification.md), local commit containing this record against `a7de8bf` |
| Card context/due-only refinement | Implementation Pass | [Follow-up](reviews/2026-10-16-drag-simplification.md#card-context-and-due-date-follow-up), same local commit |
| Recovery and later builds | **Not started** | Future work requires its own authorized scope and acceptance evidence |

## Implemented countdown behavior

- Direct Plan/Track navigation (`/#track`), Start tracking from a leaf/subtask,
  existing leaves across projects including unscheduled tasks, whole minutes **1–180**.
  The form suggests 25 minutes as a changeable UI convenience, not a newly confirmed
  product default. Only **incomplete leaves** are eligible, scheduled or unscheduled.
  Completed tasks and containers are excluded; the backend revalidates atomically.
  Completed Plan entries disable new starts without an explanation beneath them.
  Eligible open weekly-board cards open Track with the same task and existing duration/start flow.
  Empty choices explain adding/reopening work; stale rejection refreshes choices
  and retains duration. Completing an actively tracked task leaves its same running,
  paused or Needs review session visible and controllable. Receipt replay remains safe
  after completion; starting/finishing never changes completion.
- Backend-owned running/paused state, remaining time, pause/resume/finish early,
  compact timer while planning, and saved completed/early/interrupted outcome.
  Browser polling/interpolation is display-only. Navigation, refresh, visibility
  changes and closing the browser do not pause the service's monitor.
- Shared `backend/domain/timer.py` application functions, schema-6 sessions/active
  intervals/persistent request receipts, monotonic credit, UTC microsecond timestamps,
  atomic one-unfinished-session constraint and retry-safe finish. Active duration is
  capped at the chosen duration/three hours. Pauses do not earn time. Expiry resolves
  without browser callbacks. Finishing never changes task completion.
- Historical task/project context and interval dates persist after task move/edit/
  permitted removal. An unfinished tracked leaf must be finished before adding
  children; an unfinished tracked subtask must be finished before removal. Normal
  editing, completion and scheduling remain responsive.
- Checkpoints attempted every second. Restart, unexplained service gaps over five
  seconds, backwards clocks and clock divergence over two seconds conservatively
  enter Needs review at the last trusted checkpoint. Review occupies the timer slot;
  explicit Save confirmed time and finish excludes the uncertain gap. Full recovery,
  automatic sleep reconciliation and time correction are unavailable.

Core planning rules remain in AGENTS: stored dates are unique per task/date; existing
multiple placements for a leaf stay intact. The latest interface only schedules
unscheduled tasks or moves/removes saved placements; Option/Alt is no longer an Add
gesture. Move preserves placement identity and other placements. Closed snapshots/archive rows are immutable.
Reviewed carryover creates a new placement for the same current incomplete leaf,
and still excludes leaves with any active placement. Parent completion derives
from children, and totals count leaves once. Today is
service-authoritative, using `BEARPLANS_TIMEZONE` or the OS local timezone. Reopening,
recurring work, automatic bulk carryover, rewards, trees, coins, streaks, AI,
integrations and advanced statistics are not in this build.

Relevant implementation: `backend/domain/timer.py`, `backend/routes/timer.py`,
`backend/storage/migrations/0006_countdown.sql`, app lifecycle and task structure
guards; `frontend/src/Countdown.tsx`, App navigation, `WeeklyPlanner.tsx`, typed API
and styles.
Relevant tests: `tests/test_m1_journey_browser.py`, `tests/test_timer.py`,
`tests/test_timer_api.py`, `tests/test_timer_restart.py`, `tests/test_timer_browser.py`,
`tests/test_timer_eligibility_browser.py`, `frontend/src/Countdown.test.tsx` and
updated App mocks. Shared guidance/README carry the refined eligibility rule.

## Move-only refinement checks actually performed

Same **macOS 26.6.2 (25G83), Darwin arm64** host. Backend, schema, timer arithmetic
and recovery code unchanged. All mutation/browser fixtures use disposable data.

- Frontend **74 passed**, **3.31 s**; typecheck and production build passed (82 ms).
  Initial scheduling remains, extra-date forms disappear, and existing multiple
  placements stay editable with shared completion and unique-leaf totals.
- Native Chrome **2 passed**, **7.24 s**: ordinary/Option Move use the same placement
  ID and PATCH only, no new-placement requests. Conflicts, same-day/Escape/outside,
  failed Move/retry, stale/closed sources, existing other dates, timer history and
  exact rows after restart pass. Keyboard Move and normal card controls work.
- Existing affected planner/M1/history/tracking/project-task Chrome regressions:
  **7 passed**, **23.04 s**, zero failed/skipped. No full-core/timer-domain repeat
  for this UI-only refinement; earlier 400-test evidence remains historical below.
- Inspected seven new synthetic wide/narrow screenshots at **1600/375 px**. Grip
  icon precedes the title on the same line with no Drag word; no open-board help
  paragraph or extra-date controls, no page errors or overflow. Native geometry
  confirms alignment. See [evidence/commands](reviews/2026-10-16-drag-simplification.md).
- Normal service's read-only HTML response matches the rebuilt interface. Initial
  sandbox socket denial was rerun with permission. No restart or normal database
  operation was needed. Scoped whitespace/doc links and original user-file diff
  hashes pass. No unresolved implementation issue found.

## Drag scheduling checks (historical, a7de8bf)

Actual environment: **macOS 26.6.2 (25G83), Darwin arm64**, Python **3.13.15**,
Node **24.21.0**, Chrome **155.0.8059.82**. All mutation/failure/restart fixtures
use disposable data. The [drag review](reviews/2026-10-16-drag-scheduling.md) records
commands, failures, exact scope, screenshots and the demonstration checklist.

- Planning/API/migration/weeks/timer targeted regressions: **227 passed**, 6.46 s;
  independent reviewer also 227 passed, 6.33 s. Restart regressions: **13 passed**,
  10.13 s. Multiple dates, duplicate/concurrent conflicts, stale/archived sources,
  closed destinations, no-op identity, unique-leaf snapshots and upgrade rollback/
  retry are covered. Legacy schema-3 multi-date rows survive an atomic exact-known
  4–7 compatibility upgrade; applied SQL files were not changed.
- Frontend **74 passed**, 3.33 s after the native correction; typecheck and production
  build passed. Existing date controls remain; new keyboard Add and narrow day-button
  targets are tested. No task cloning, dependency additions or timer logic changes.
- Actual native Chrome mouse/Option journeys: **2 passed**, 7.76 s. Move/Add,
  duplicates, same-day/Escape/outside, failed POST/PATCH plus retries, stale-tab
  server conflict, closure during drag, card controls, keyboard, 375 px layout and
  exact saved task/session/snapshot records after restart all pass. Seven synthetic
  screenshots inspected at 1600/375 px; no page errors or horizontal overflow.
- Native tests found a real layout defect: in-flow feedback moved the source at
  drag start and stalled Chrome dragging. Fixed with a floating indicator and
  retaining old error feedback until drop; repeated conflict/error drags now pass.
- Initial full existing core: **397 passed, 1 helper failure**, 116.69 s. M1's date
  locator matched both Move and Add inputs. Scoped it to Move; focused M1 rerun
  **1 passed**, 3.55 s. Final full core including new native cases:
  **400 passed**, **118.99 s**, zero failed/skipped. This includes the real-minute
  countdown/expiry and relevant timer, completion, persistence and browser regressions.
- Independent backend/UI review found no remaining blocker. Initial sandbox setup,
  obsolete one-day test expectations and keyboard date-segment helper corrections
  are disclosed in the review. No skipped/setup-failed attempt is counted as a pass.

## Countdown eligibility checks (historical, bbe6059)

Actual environment remains **macOS 26.6.2 (25G83), Darwin arm64**, Python
**3.13.15**, Node **24.21.0**, installed Chrome **155.0.8059.82**. Disposable data
only for mutation/failure/browser tests; no new hardware recovery evidence.

- Affected domain/API/planner/history tests:
  `.venv/bin/python -m pytest -q tests/test_timer.py tests/test_timer_api.py tests/test_tasks.py tests/test_planning.py tests/test_planning_api.py tests/test_weeks.py`
  → **280 passed**, **6.66 s**, zero failed/skipped. Backend agent's earlier subset
  was 113 passed, 4.13 s. Completed leaves reject without partial rows; scheduled/
  unscheduled and subtasks are covered, along with stale clients, reopening/retry,
  unchanged active state/identity through completion and acknowledged receipt replay.
- Frontend: **63 passed**, **3.07 s**; typecheck and production build passed. Tests
  include incomplete choices across projects, disabled visible/accessibly explained
  Plan/weekly controls, keyboard weekly entry/duration retention, two empty states,
  stale choice refresh and running/paused/Needs review preservation through completion.
- New Chrome journey: **1 passed**, **2.30 s**. Inspected 1440/375 px screenshots,
  keyboard weekly Start + Resume, active completed-task session, stale rejection,
  retained 17-minute duration, stored empty state and completed weekly-card guidance.
- Existing timer/restart/weekly/history Chrome regressions: **6 passed**, **20.97 s**.
  Short real timer saved **2.556639 s** excluding pause; API task writes median
  **0.002924 s**, maximum **0.014481 s**; browser task creation **0.068 s**.
- Independent source review: **Pass**, no remaining blocker. Initial new Chrome
  checkbox helper raced the server-controlled state; waiting for the saved state
  corrected the test. A frontend table-test setup error was also fixed. No confirmed
  product defect or data loss arose from either. Exact commands and evidence are in
  the [current review](reviews/2026-10-16-countdown-eligibility.md).
- Scoped diff/whitespace, local links, unchanged schema and existing user-file diff
  hashes are checked before commit. These are **287 distinct affected Python/browser
  cases**, plus 63 frontend tests. The unaffected real one-minute/full-core baseline
  was not repeated or claimed as new evidence.

## Countdown baseline checks (historical, c4b7dd3)

Detected **macOS 26.6.2 (25G83), Darwin arm64**, Python **3.13.15**, Node **24.21.0**,
installed Chrome **155.0.8059.82**. No Windows or new hardware sleep run claimed.

- Pre-edit baseline including joined M1 journey: **327 passed, zero failed/skipped**,
  30.76 s; frontend **40 passed**, typecheck passed.
- Timer deterministic/domain/API: **51 passed**, 3.45 s. Existing task/API/migration
  targeted regressions: **117 passed**, 1.56 s. Real timer/restart tests: **2 passed**,
  6.18 s. Tests cover limits, pause arithmetic, exact expiry clipping, concurrent
  start/finish, persistent retry receipts, stale controls, rollback/retry, preserved
  history, graceful/abrupt restart and conservative review.
- Full core suite with loopback and Chrome permission:
  `BEARPLANS_EVIDENCE_DIR=docs/reviews/evidence/countdown BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s`
  → **382 passed, zero failed/skipped**, **107.43 s**.
- Full-suite real one-minute countdown with browser process closed: **60.000000 s**
  saved, monitor expiry after **60.149 s** independent elapsed time, original task
  still incomplete. No timer API calls resolved that expiry. Six normal API task
  writes during tracking: median **0.002977 s**, maximum **0.012065 s**.
- Final frontend: **53 passed**, 3.13 s; typecheck and production build passed.
  Final UI task-choice retry/copy changes were checked with the frontend suite and
  the focused Chrome countdown journey (**1 passed**, **4.42 s**), rather than
  repeating the unaffected long timing suite. Browser task creation during tracking
  took **0.067 s** on that run.
- Visually inspected synthetic active/compact/saved/review screens at **1440**,
  **1024**, **375** px, light/dark; keyboard controls, disabled/loading/failure retry,
  no horizontal overflow. Real Chrome tabs share the session and reject a second
  start; committed finish-response loss saves once; restart review requires explicit
  resolution. Visibility-hook tests refresh without pause; no physical sleep claim.
- Independent source review found/fixed backward UTC interval ordering and repeated
  task-to-Track selection. Final review found no source blocker. Initial test helper/
  typing issues were corrected. Initial socket/Chrome sandbox failures were rerun with
  permission, not counted as product passes. Exact evidence/failures are in reviews.

All failure, corruption, interruption and migration experiments use disposable data.
No personal data/screenshot/database is committed. Scoped whitespace/local document
links and original planning-file diff preservation are checked before commit.

## Normal running app and preserved user data

Before drag upgrade: **nine tasks, two projects, three active placements, two closed
weeks, four archived placements, three finished sessions, four saved intervals and
eight timer receipts**; carryover receipts empty. A live WAL-safe SQLite backup and
a disposable rehearsal of the schema-7 upgrade preserved every original field and
migration row; integrity/FKs passed.

Identified service **5897**, launcher **5874**, port 8765. Rechecked no running,
paused or Needs review session, gracefully stopped that launcher and confirmed port
release. Verified no saved rows had changed since rehearsal. Durable backup in the
normal data folder: **`bearplans-pre-drag-20261016T164423Z.sqlite3`**, matching the
baseline exactly. Restarted via `python3 launch.py --no-browser`; schema is now **7**.

Read-only Chrome inspected the already-closed current week, next open week's drag
controls, exact incomplete-leaf Track choices and 1440/375 px layouts. No personal
task, placement, completion, timer or history action and no personal screenshot.
**Every original SQL field** (including closed snapshots, sessions, intervals and
receipts), plus the original six migration rows, still equals the backup. Integrity/
FKs pass. The planning response stayed identical through navigation. The normal app
is running at `http://127.0.0.1:8765/`; refresh existing tabs. Earlier schema-6
backup evidence remains in the countdown/eligibility reviews.

## Pending evidence and next concrete action

- Context-row grip and due-only weekly-card refinement/review are complete, **Pass**.
  Changes are included in the user-requested local commit containing this record
  against `a7de8bf`, with unrelated staged/unstaged user planning changes intact
  outside that commit. No push or subsequent build.
- Hands-on drag demonstration: move using the grip icon before the project/parent line;
  Option/Alt still moves, and no Add-another-day option or instructional paragraph
  appears. Try same-day, Escape/outside and an existing duplicate destination; use
  keyboard Move/remove. Inspect narrow day-button targets and existing closed history.
  Weekly cards show Due without a redundant Planned-date line; task-list dates stay.
  New operator/Windows hardware acceptance is not claimed.
- Hands-on refinement: select an incomplete weekly card, start/pause, complete its
  task in Plan, then return to the same timer and finish. Verify completed work is
  excluded from new choices and empty guidance appears when no eligible work remains.
  No new operator acceptance is claimed.
- Use the [five-minute countdown demonstration](reviews/2026-10-16-countdown.md#five-minute-demonstration)
  for hands-on operator review. Broader M1 real-coursework/week operator evidence is
  still not newly certified; no destructive real-week closure is required merely
  for a demo when reopening is unavailable.
- Recovery is the next eligible M2 build, **not started**. Only begin after an explicit
  request. Its acceptance must cover real Mac sleep/wake and multiple DarkWake gaps,
  restart/crash reconciliation, forward/backward clock changes, midnight/DST,
  battery/standby/hibernate and a longer independent timing reference. Unknown time
  must never silently earn credit; the current conservative fallback remains until
  that gate passes.
- No known normal-countdown implementation blocker remains. No push, recovery,
  reward, AI or integration implementation is authorized by this handoff alone.

## Guidance discrepancies retained

- The explicit October 16 Option/Alt Add request supersedes October 15's one-active
  date refinement. Multiple dates now reference the same leaf, unique per task/date,
  with shared completion, unique-leaf totals and immutable historical placements.
  The later October 16 simplification removes modifier Add and Add-another-day UI,
  without reinstating a storage constraint or deleting existing dates. Earlier
  reviews retain historical evidence and link to the new decision.
- User-edited roadmap says planned/not tested while checkmark rows say otherwise;
  its unstaged checkmarks now include weeks/history and countdown. The review-plan
  edit removes an older M1 status paragraph. Preserve these edits;
  use this record and linked evidence for actual decisions.
- Historical Claude projects/tasks draft and earlier next-build text are evidence,
  not current instructions. Review filenames may use target dates. Follow contents,
  explicit user decisions and commits.
- Original build plan suggested native sleep events. M0 measured two Mac clocks and
  selected monotonic credit plus a scoped Needs review fallback. That policy does
  not replace the new timer's hardware/recovery acceptance.
- Deadlines are date-only; the old due-date/time sketch does not add time-of-day.
  Proposed reward/price/streak defaults are separate from confirmed requirements.

Before either agent stops/transfers work, update this record with actual checks,
files/commits, pending evidence and the next concrete action; link detailed reviews.
