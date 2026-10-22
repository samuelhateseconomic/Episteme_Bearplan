# BearPlans — shared progress and handoff

Read [AGENTS.md](../AGENTS.md) first; Claude also reads [CLAUDE.md](../CLAUDE.md).
This is the single mutable work/handoff record. Detailed reviews retain evidence.

## Current state — October 21, 2026

**Daily streaks are implemented; implementation review Pass on Mac.** The user
requested checking the next session and proceeding. It derives daily progress
from finalized saved intervals, including legacy/early/resolved interrupted work;
uses the current service timezone and exact integer-microsecond allocation; and
retains yesterday's streak while today is unfinished. Schema, timer/reward writes
and normal user data remain unchanged. Verification results are recorded in
the [daily-streak review](reviews/2026-10-21-daily-streaks.md).
The user requested the **local commit containing this record against `05a976e`**.
It includes daily-streak code, tests and handoff records; unrelated planning edits
remain outside it. Final full core: **605 passed**,
zero failures/skips, **156.70 s**; frontend **122 passed**, **3.81 s**,
typecheck/build passed. The browser-closed real minute saved **60.000000 s** after
**60.514 s** independent elapsed time. These are awake automated observations,
not new hardware/operator acceptance.

Latest implementation: **M3 daily streaks**, in this user-requested local commit
against **`05a976e` — M3: add confirmed-time coins and persistent tree shop**.
Before this commit, local `main` was one commit ahead of the recorded `origin/main`;
this session did not fetch or push. **Daily-streak implementation review passes on
macOS; the overall M3 milestone remains incomplete.**
Existing planning edits, documentation handoffs and recovery stash remain
preserved. The normal app was not restarted and its data was not migrated.

Before streak development, the earlier status check on **macOS/Darwin** confirmed
application source and tests were unchanged from `05a976e`. It ran Git/source/doc
consistency and link/whitespace checks without an application test rerun or new
hardware/operator evidence. Today's implementation extends that baseline while
preserving the existing staged/unstaged planning edits and status handoff. See the
[October 21 status check](reviews/2026-10-21-project-status.md).

Configurable proposed defaults: **1 coin per whole confirmed active minute**;
Birch **30**, Oak **60**, Cherry **120** coins, with Pine free. These are chosen
implementation defaults, not newly confirmed product rules. Only countdowns
started with the coins-aware build enroll for earnings; all pre-upgrade sessions,
including unfinished sessions and existing trees, remain ineligible. Capture the
earning rate and owned species when starting; finishing saves confirmed earnings
once, atomically with its session/tree result. Purchases revalidate displayed price,
balance and ownership in the serialized transaction and retain replay receipts.
Failed saves keep the chosen item for retry; no refund/Undo or manual correction
surface is added in this ticket. See the
[coins/shop review](reviews/2026-10-20-coins-shop.md) for that ticket's acceptance and evidence.

Schema **10** preserves existing tree fields/order while adding coin enrollment,
ledger, ownership and purchase receipts. Track shows coins, recent activity,
four cosmetic species and owned-species selection. Purchase requests persist
through lost responses/reload and refresh the authoritative balance. Default Pine
starts remain compatible with the earlier service API; the shop explains when an
older running service needs restarting. No prior sessions or trees are backfilled.

Historical coins/shop implementation evidence (October 20) on
**macOS 26.6.2 (25G83), Darwin arm64**, Python
**3.13.15**, Node **24.21.0**, Chrome **155.0.8059.82**: full core **553 passed**
in **144.66 s**, zero failures/skips; final frontend **111 passed**, typecheck/build
passed. After the Pine/404 compatibility follow-up, final shop/timer/eligibility
Chrome journeys **3 passed**, **10.01 s**. The full-core browser-closed real minute
saved **60.000000 s**, one mature Pine and one coin, observed after **60.414 s**.
All mutation/migration/restart fixtures use disposable data. Actual sleep,
battery/standby/hibernate and external long-duration acceptance remain pending.

| Milestone | Implementation status | Remaining acceptance or work |
| --- | --- | --- |
| M0 — Foundation | Implemented; recorded Mac/operator pass | Historical evidence retained |
| M1 — Planner and history | Implemented; technical review and recorded operator approvals passed | Broader coursework/week operator certification remains unverified |
| M2 — Countdown and recovery | Implemented; Linux implementation review and current Mac automated regressions passed | Target-Mac recovery/hardware acceptance pending |
| M3 — Forest and statistics | Pine/forest, coins/shop and daily streaks implemented; streak implementation review Pass on Mac | Statistics/session corrections not started; combined Mac acceptance pending |
| M4 — Personal core release | Release work not started | Backup/restore and seven-day trial pending |
| M5–M7 — Assistant and connections | Not started | Separate future scope and acceptance |

**Next concrete step:** statistics/session corrections below, **not started**;
define one small ticket and correction policy when authorized. Daily-streak
backend/domain/API/restart checks: **51 passed**, **3.40 s**; final full core and
frontend results are above. Full commands, initial failures, exact allocation
fixtures and visual/restart evidence are in the
[daily-streak review](reviews/2026-10-21-daily-streaks.md). The earlier
[progress review](reviews/2026-10-20-project-progress.md) remains documentation-only;
the latest implementation evidence is today's daily-streak review.

**M3 remains partially complete:** growing trees/forest (`e0ccf1b`) and coins/shop
(`05a976e`) are committed; daily streaks are included in this user-requested local commit.
Statistics and session corrections, including reward/report adjustments, remain
**not started**.

These belong to M3, not later milestones. The next session is statistics/session corrections.
M2 hardware/operator verification
remains pending, and combined M2/M3 Mac verification is required after M3
implementation, before milestone sign-off or release readiness.

**M3 first session — growing trees and forest collection: implementation review
Pass on Linux; actual Mac acceptance deferred.** Baseline `809761d` plus the previous uncommitted
sequencing note, which is preserved in this handoff. The user explicitly authorized
M3 implementation, deferring actual Mac testing until M3 is complete, and a local
commit after passing review. That implementation is committed as `e0ccf1b`,
`M3: add confirmed tree growth and persistent forest`. The implementation and the
status clarification (`138cd3a`) are already on GitHub `main` and were pulled into
this checkout. That prior push request is complete.

The first-session build introduced free Pine growth from backend-confirmed time:
seedling below 50%, sapling from 50%, mature only after finalized full-duration
completion without an unresolved interruption. Early/interrupted finishes preserve
confirmed work and save an unfinished tree. Pausing and Needs review preserve
confirmed growth; explicit recovery continues the same tree. The forest within
Track shows saved outcomes with historical session context, time and dates.

Schema **9** introduced `trees`, with unique `session_id`. Only successful countdown
starts from tree-aware builds enroll a tree, atomically with their interval and
receipt. All sessions present before that upgrade, including running/paused ones,
remain tree-ineligible. No reads, retries or historical finalizations backfill trees.
Session finalization and tree outcome share one serialized transaction. Task edits,
completion, scheduling and removal do not rewrite tree/session history; trees never
complete tasks. Existing Move-only dragging and schema-7 multi-date records remain.

**M2 recovery implementation: Pass on Linux; actual Mac verification pending.**
Recovery remains committed as `580b017`; its historical 473 core / 81 frontend
passes and Linux ten-minute precision observation are detailed in the
[M2 review](reviews/2026-10-18-m2-recovery.md). This M3 build does not certify Mac
power behavior or change M2's gate status. The explicit October 20 sequencing
choice permits development while preserving the outstanding acceptance scenarios.

Recorded M3 implementation-review environment: **Linux x86_64**, Python
**3.12.14**, Node **24.19.0**, installed Chromium **154.0.8037.57**. That review's
final full core: **500 passed**, zero failed/skipped, **142.73 s**. Frontend:
**90 passed**, typecheck/build passed. Its real one-minute
monitor expiry with browser closed saved exactly **60.000000 s**, observed after
**60.656 s**, with one mature tree and unchanged task completion. All mutation,
migration, failure and browser work used disposable data.
No personal planner/database or normal running service was used in that review. The
[M3 review](reviews/2026-10-20-m3-growing-forest.md) records implementation,
verification and the separate platform decision.

**Required checkpoint:** after M3 implementation is complete, run combined M2/M3
verification on the target Mac before release readiness or milestone sign-off.
Advanced statistics/session correction, AI and integrations remain unimplemented.

## Local Git update — October 20, 2026

User-authorized pull completed on **macOS/Darwin**: `main` fast-forwarded nine
commits from `861d851` to `138cd3a` and matches `origin/main`. The remote M2 recovery
and first M3 Pine/forest session are now checked out. The Linux test results above
remain historical evidence; this update did not perform target-Mac acceptance.

All prior local changes, including untracked recovery files, are preserved in
stash **`ed5e990c6c1fd649ed60083ec8e61b90bdf2153c`**, currently `stash@{0}`, named
`before-pull-2026-10-20-local-recovery-and-planning`. Every saved file was verified
against the pre-pull SHA-256 manifest. The two planning documents were restored
with exactly their original contents and staged/unstaged patches. The separate
snapshot remains at `/private/tmp/bearplans-before-pull-20261020-1k5inn3e/`.
Do not apply the whole stash over this build: it contains a different schema-8
recovery implementation. Its old progress/reviews describe that preserved branch
of local work, not the current checked-out build.

At completion of the pull, Git checks confirmed zero ahead/behind and no local
application-source changes. No application tests, service restart, database
migration, commit or push occurred during that pull or its documentation refresh.
See the [sync verification](reviews/2026-10-20-git-sync.md). The subsequent local
coins/shop implementation is described above. A future normal-app restart may
apply pending migrations through schema 10; it has not been performed here.

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
| Move-only drag interface refinement | Implementation Pass | [Current review](reviews/2026-10-16-drag-simplification.md), `861d851` against `a7de8bf` |
| Card context/due-only refinement | Implementation Pass | [Follow-up](reviews/2026-10-16-drag-simplification.md#card-context-and-due-date-follow-up), `861d851` |
| M2 recovery | Implementation Pass on Linux; Mac/operator gate pending | [Recovery review](reviews/2026-10-18-m2-recovery.md), `580b017` against `a10c788` |
| M3 growing trees / forest — first session only | Implementation Pass on Linux; Mac acceptance deferred | [M3 review](reviews/2026-10-20-m3-growing-forest.md); `e0ccf1b` |
| M3 coins/shop | Implementation review Pass on Mac; normal-app rollout and combined hardware/operator gate pending | [Coins/shop review](reviews/2026-10-20-coins-shop.md), `05a976e` against `138cd3a` |
| M3 daily streaks | Implementation review Pass on Mac; normal-app rollout and combined hardware/operator gate pending | [Daily-streak review](reviews/2026-10-21-daily-streaks.md), user-requested local commit against `05a976e` |
| Remaining M3: statistics/session corrections | **Not started; M3 incomplete** | Next session; separate acceptance required |
| M4 and later milestones | **Not started** | Separate authorized scope and acceptance required |

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
recurring work, automatic bulk carryover, AI, integrations
and advanced statistics remain deferred. Tree growth, saved forest, coins/shop and streaks
are included in the implemented M3 scope above.

Relevant implementation: `backend/domain/rewards.py`, `backend/routes/shop.py`,
`backend/storage/migrations/0010_coins_and_shop.sql`, `frontend/src/Shop.tsx`,
`backend/domain/timer.py`, `backend/routes/timer.py`,
`backend/storage/migrations/0006_countdown.sql`, app lifecycle and task structure
guards; `frontend/src/Countdown.tsx`, App navigation, `WeeklyPlanner.tsx`, typed API
and styles.
Relevant tests: `tests/test_rewards.py`, `tests/test_shop_api.py`,
`tests/test_shop_restart.py`, `tests/test_shop_browser.py`,
`frontend/src/Shop.test.tsx`, `frontend/src/api.test.ts`,
`tests/test_m1_journey_browser.py`, `tests/test_timer.py`,
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
baseline exactly. That restart via `python3 launch.py --no-browser` upgraded the
normal data to schema **7** at the time of that review.

Read-only Chrome inspected the already-closed current week, next open week's drag
controls, exact incomplete-leaf Track choices and 1440/375 px layouts. No personal
task, placement, completion, timer or history action and no personal screenshot.
**Every original SQL field** (including closed snapshots, sessions, intervals and
receipts), plus the original six migration rows, still equals the backup. Integrity/
FKs passed. The planning response stayed identical through navigation. At that
review, the normal app was running at `http://127.0.0.1:8765/`. Its current process,
schema and saved rows were not inspected by this documentation refresh; the old
PIDs and schema version are historical. Earlier schema-6 backup evidence remains
in the countdown/eligibility reviews.

## Pending evidence and next concrete action

- Coins/shop implementation and review pass in `05a976e` against `138cd3a`,
  with **553 core / 111 frontend** passes and final compatibility browser evidence
  above. The user explicitly requested this local commit after review; unrelated
  planning edits remain preserved. No push or normal-app rollout was performed. The earlier
  Pine/forest implementation and status clarification are already on GitHub `main`;
  that older push request is complete. The user subsequently authorized daily
  streaks; that implementation and its verification are now complete and
  included in this subsequently requested local commit against `05a976e`.
  No source/schema changes to timer recovery, coin/forest writes or dependency
  locks. The planning files' staged/unstaged edits and recovery stash remain
  preserved. No push, normal-app restart or personal database migration was
  performed. Next is the
  statistics/session-correction session below; do not begin it automatically.
- Actual target-Mac acceptance remains pending. After M3 implementation, run the
  combined checkpoint before release readiness: sleep/wake and maintenance wakes,
  battery/standby/hibernate where supported, process interruption/restart and
  explicit recovery, forward/backward clock changes, midnight/DST, external
  real-duration acceptance and no duplicate tree/reward outcomes. Preserve the
  exact commands and operator steps in the [M2 review](reviews/2026-10-18-m2-recovery.md#target-mac-acceptance-still-required).
- Use disposable data and the existing `tools/m2_probe.py`; never count missing
  sleep as a pass, estimate uncertain time or infer hardware behavior from fake
  clocks. Confirm resumed recovery continues its original tree, sleep/review never
  advances growth, interrupted/early finish stays unfinished and finalized full
  confirmed work creates one mature tree across refresh/retry/restart.
- Preserve earlier projects/tasks and history operator acceptance. Broader M1
  coursework/operator evidence and the latest drag/card demonstration are not newly
  certified by Linux tests. New forest/Track operator acceptance is also pending.

<a id="next-m3-session--coins-and-tree-shop-not-started"></a>

## Completed M3 session — coins and tree shop

The old continuation link is retained above for historical reviews. This ticket
was authorized by “continue” and is now implemented and reviewed; it is no longer
the next unstarted session. Its full rules, defaults, evidence, initial failures
and separate acceptance gates are in the [coins/shop review](reviews/2026-10-20-coins-shop.md).

New records: `coin_enrollments`, `coin_ledger`, `owned_species`, `shop_operations`;
schema 10 expands `trees` while preserving all original fields and row order.
The rate and Birch/Oak/Cherry prices are configured with `BEARPLANS_COINS_PER_MINUTE`,
`BEARPLANS_BIRCH_PRICE`, `BEARPLANS_OAK_PRICE`, `BEARPLANS_CHERRY_PRICE` before
launch. Old sessions stay coin-ineligible; new sessions capture their earning rate
and chosen owned species at start. No manual correction/refund interface was added.
The plan's future adjustment-ledger policy remains: retain purchases and block
new spending if a later correction makes the balance negative.

<a id="next-m3-session--daily-streaks-not-started"></a>

## Completed M3 session — daily streaks

Scope: daily qualifying-time progress and a consecutive-day streak derived from
saved confirmed work. The existing requirement is at least one active hour per
qualifying day. Reuse saved timer intervals and the application's timezone
(`BEARPLANS_TIMEZONE` or OS local timezone); browser dates are not authoritative.
Keep reports, estimates versus actuals, manual corrections, AI and integrations
out of this session.

Chosen implementation defaults: count finalized sessions of all outcomes and
legacy sessions with saved closed intervals; exclude unfinished sessions and
unresolved interruptions. Keep yesterday's streak while today is unfinished.
Reattribute historical dates when the current service timezone changes; earlier
records contain no original timezone metadata. Coin eligibility does not restrict
streak eligibility. Never manufacture or edit intervals to fill missing time.
Allocate confirmed integer microseconds
across local midnight and both DST transitions without losing or double-counting
time; paused/review/uncertain gaps remain excluded. Derive totals from saved
records, never an independently incremented mutable streak counter.

Acceptance: two saved 30-minute sessions qualify once; 59:59.999999 does not;
multiple projects/subtasks and early/interrupted confirmed work obey the chosen
eligibility rule; zero/subminute/paused/uncertain intervals do not inflate totals;
cross-midnight/DST and missing days produce exact dates/counts. Refresh, repeated
finish/recovery and restart preserve the same derived result. Existing coins,
ownership, tree outcomes, task completion and immutable weekly history stay intact.
Inspect daily-progress states at wide/narrow widths and with keyboard navigation.

Source: `backend/domain/calendar.py`, `backend/domain/streaks.py`,
`backend/routes/streaks.py`, `frontend/src/DailyStreak.tsx` and Track/API/styles.
No migration or separate counter is needed. Calendar localization is shared with
planning. UTC offset boundaries and local midnights both split allocation, including
historical rollbacks across midnight. Read failures retain data and allow retry.
Implementation review **Pass**: final full core **605 passed**, frontend **122
passed**, typecheck/build passed. The new Chrome journey covers saved partial and
qualified states, keyboard read retry, a lost finish response/exact retry, a
different browser timezone, reload, real process restart and unchanged task/week/
reward records. Inspected 1440/375 px light/dark previews; no overflow/page errors.
See the [daily-streak review](reviews/2026-10-21-daily-streaks.md) for commands,
initial failures, legacy compatibility and remaining hardware/operator gates.

## Next M3 session — statistics and session corrections (not started)

Scope remains the planned completion/confirmed-time totals by day, project and
task; estimates versus actuals; and explicit saved-session corrections with reward
adjustments. Keep one small ticket active and define correction semantics before
writing code: eligible historical sessions, exact interval/date attribution,
preview, revision/replay checks, audit/reversal behavior, and tree/coin cutovers.
Do not silently credit an uncertain gap. Derive streaks and reports from the same
corrected source; count leaf task completion once. Preserve closed snapshots and
historical task/project context. Corrections must use the planned adjustment
ledger, never repeat an initial award; retain purchases and prevent spending when
an adjustment makes the balance negative. These are future requirements, not
features available in the current interface.

Ready-to-use continuation prompt for a later authorized session:

> Continue BearPlans with M3's statistics/session-correction session. Read AGENTS.md,
> docs/PROGRESS.md, plans and latest reviews; inspect the complete working diff,
> preserve planning edits, the recovery stash and current coins/streak behavior.
> Define a small first ticket and the correction preview/audit/revision/replay
> policy before implementation. Reuse confirmed integer intervals, service dates
> and domain transactions; keep leaf totals, immutable weekly history, historical
> session context, coin/tree cutovers and configured captured rates. Reward changes
> use adjustments, retain purchases and block negative-balance spending. Verify
> known totals, correction rollback/retry/restart, midnight/DST and derived streak
> changes with disposable data. Keep combined M2/M3 hardware acceptance pending.
> Update progress/review. Do not commit or push without explicit authorization;
> do not start backup/restore, AI or integrations in this session.

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
