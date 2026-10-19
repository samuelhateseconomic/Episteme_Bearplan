# BearPlans — shared progress and handoff

Read [AGENTS.md](../AGENTS.md) first; Claude also reads [CLAUDE.md](../CLAUDE.md).
This is the single mutable work/handoff record. Detailed reviews retain evidence.

## Current state

**M2 recovery implementation review: Pass on Linux; Mac gate pending.** The user explicitly
requested finishing M2 on October 18, 2026. Baseline is GitHub `main` at `a10c788`;
the clean cloud checkout was fast-forwarded from `801cbc3`. Recovery is committed
as `580b017` (`M2: add checkpoint-based countdown recovery`). The user subsequently
authorized pushing it to GitHub `main` for the Mac to pull. No next milestone was
requested; target-Mac acceptance remains pending.

Schema **8** adds durable interruption/resolution records. Measured sleep pauses
at the last trusted checkpoint and requires explicit Resume, including across
maintenance wakes. Running restarts, clock changes and unexplained gaps require
review; Continue with confirmed time resumes the same session while excluding the
entire gap. Save confirmed time and finish saves it once. Paused restarts stay
paused. Tasks, completion, placements and closed history retain their identity.

Full core **473 passed**, zero failed/skipped, 162.96 s. Frontend **81 passed**,
typecheck/build passed. New process/browser checks **3 passed**; targeted recovery/
API/clock checks **120 passed**. Final probe-only reporting regression checks
**16 passed** after the full-core run. Real ten-minute awake precision passed:
**600.000000 s** saved versus **600.160698 s** same-host reference (−0.160698 s).
No timer API requests ran during that observation; the monitor finalized it.
Source hashes match. Evidence, exact commands,
fixture corrections and the target-Mac checklist are in the
[M2 recovery review](reviews/2026-10-18-m2-recovery.md).

Actual current host: **Linux**. M2 target-Mac sleep/DarkWake, battery/standby/
hibernate and external timing/operator evidence remain pending. The overall M2
gate is **not passed** until those results are reviewed. Same-host precision or
fake-clock tests must never be presented as physical Mac evidence. Rewards,
statistics, AI and integrations have not started.

The prepared cloud launcher now serves schema 8 using the existing onboarding data
folder outside source. A SQLite backup was verified before upgrade; every original
schema-3 data row and migration record was preserved, with clean integrity/FKs.
No personal planner or timer action was performed. The older Mac instance/data
verification below is historical evidence from `a10c788`, not a claim about the
current cloud process or the user's current Mac.

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
| M2 recovery | Implementation Pass on Linux; Mac/operator gate pending | [Recovery review](reviews/2026-10-18-m2-recovery.md), `580b017` against `a10c788` |
| Rewards and later builds | **Not started** | Separate authorized scope and acceptance required |

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
- Checkpoints are attempted every second. Measured sleep pauses at the last saved
  checkpoint; neither wake nor maintenance activity resumes tracking. Running
  restarts, unexplained gaps over five seconds and clock divergence over two seconds
  require review. Explicit continue or finish excludes the gap and retains a durable
  schema-8 interruption/resolution record. Review still occupies the timer slot;
  paused restarts remain paused. Manual time correction is deferred. Actual Mac
  acceptance is pending; see the current recovery review.

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

## Move-only refinement checks (historical, before `a10c788`)

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

## Historical Mac instance and preserved data at `a10c788`

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

- Full-core and ten-minute Linux precision verification are complete and recorded
  in the recovery review. No further automated setup work is blocked.
- Review and run the target-Mac checklist in the recovery review. The disposable
  `tools/m2_probe.py` utility collects sanitized evidence without touching normal
  planner data or changing OS power/clock settings. No sleep observation is a pass
  if the machine did not actually suspend. Unsupported battery/hibernate conditions
  remain explicitly unverified until demonstrated.
- Preserve the earlier projects/tasks and overall history operator acceptances.
  Broader M1 real-coursework/operator evidence and the latest drag/card refinement
  demonstration were not newly certified in this Linux task.
- After the required M2 hardware/operator checks pass, record milestone sign-off.
  Rewards and later builds require a new request. Do not infer authorization to
  start M3 from this recovery task. Commit `580b017` and its push to GitHub `main`
  were explicitly authorized in subsequent requests.

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
