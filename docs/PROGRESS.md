# BearPlans — shared progress and handoff

Read [AGENTS.md](../AGENTS.md) first; Claude also reads [CLAUDE.md](../CLAUDE.md).
This is the single mutable work/handoff record. Detailed reviews retain evidence.

## Current state

**M2 first build, normal countdown tracking: implementation review Pass.**
Implemented and reviewed October 16, 2026 under the user's explicit request.
Baseline `69c6630`, schema **6**. The local build commit contains this record and
[the countdown review](reviews/2026-10-16-countdown.md); no push.

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
`BearPlans_Dated_Roadmap.md`, plus the extra unstaged roadmap checkmark, are preserved
outside this build commit. Their staged/unstaged diff hashes are checked before
commit. `CLAUDE.md` remains substantive and points here.

## Completed builds

| Build | State | Evidence / relevant commits |
| --- | --- | --- |
| M0 / foundation | Implementation and Mac/operator gate passed | [M0 review](reviews/2026-10-14-local-foundation.md); `36f6e48`, `f4c59dd` |
| Projects/tasks/subtasks | Implementation and all six operator checks passed | [Takeover review](reviews/2026-10-13-m1-takeover.md); `a9ba50b`, `d2174a6` |
| Weekly planning + one-day refinement | Implementation Pass; original individual checklist not newly attested | [Refinement](reviews/2026-10-15-single-planned-day.md), `a21cb49`; [weekly evidence](reviews/2026-10-15-weekly-planning.md), `801cbc3` |
| Weeks/history/carryover | Implementation Pass; overall user acceptance Pass | [History review](reviews/2026-10-15-weeks-history.md), `7155bc2`; acceptance `69c6630` |
| Joined M1 technical review | Pass; broader operator gate not newly certified | [October 16 review](reviews/2026-10-16-m1-review.md) |
| M2 normal countdown | Implementation Pass; overall M2 gate not passed | [Countdown review](reviews/2026-10-16-countdown.md), local commit containing this record |
| Recovery and later builds | **Not started** | Future work requires its own authorized scope and acceptance evidence |

## Implemented countdown behavior

- Direct Plan/Track navigation (`/#track`), Start tracking from a leaf/subtask,
  existing leaves across projects including unscheduled tasks, whole minutes **1–180**.
  The form suggests 25 minutes as a changeable UI convenience, not a newly confirmed
  product default. Completed leaves are selectable; containers are rejected.
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

Core planning rules remain in AGENTS: one active planned day per leaf across open
weeks, move preserves placement identity, closed snapshots/archive rows are immutable,
reviewed carryover creates a new placement for the same current incomplete leaf,
parent completion derives from children, and totals count leaves once. Today is
service-authoritative, using `BEARPLANS_TIMEZONE` or the OS local timezone. Reopening,
recurring work, automatic bulk carryover, rewards, trees, coins, streaks, AI,
integrations and advanced statistics are not in this build.

Relevant implementation: `backend/domain/timer.py`, `backend/routes/timer.py`,
`backend/storage/migrations/0006_countdown.sql`, app lifecycle and task structure
guards; `frontend/src/Countdown.tsx`, App navigation, typed API and styles.
Relevant tests: `tests/test_m1_journey_browser.py`, `tests/test_timer.py`,
`tests/test_timer_api.py`, `tests/test_timer_restart.py`, `tests/test_timer_browser.py`,
`frontend/src/Countdown.test.tsx` and updated App mocks.

## Checks actually performed

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

The identified old launcher/service on `http://127.0.0.1:8765/` (95317/95319) was
stopped gracefully. A live WAL-safe SQLite backup and schema-6 rehearsal used a
private temporary folder; every original SQL field matched and integrity/FKs passed.
A durable final backup is in the normal data folder:
`bearplans-pre-countdown-20261016T151846Z.sqlite3`.

Restarted using `python3 launch.py --no-browser`; the normal app now serves schema 6.
All **seven tasks, two projects, one active placement, two closed weeks and four
archived placements** match the pre-upgrade hashes exactly, including original
migration rows; carryover receipts remain empty. Integrity and foreign keys pass.
All timer tables remain empty: **no personal session was started**. Read-only Chrome
Track/Plan navigation and enabled task-choice checks passed, with the complete
planning response unchanged. No personal screenshot was taken. Refresh an existing
browser tab to load the updated interface.

## Pending evidence and next concrete action

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
- No known normal-countdown implementation blocker remains. No push and no recovery,
  reward, AI or integration implementation is authorized by this handoff alone.

## Guidance discrepancies retained

- User refinement on October 15 supersedes original multi-day planning: one active
  planned day per leaf, with closed historical placements preserved independently.
- User-edited roadmap says planned/not tested while checkmark rows say otherwise;
  the review-plan edit removes an older M1 status paragraph. Preserve these edits;
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
