# M3 daily streaks — October 21, 2026

Baseline: `05a976e`, plus preserved planning and status-document edits.
Authorization: the user asked to check the next session, then proceed.
Status: **implementation review Pass on Mac; overall M3 incomplete**.
Included in the subsequently user-requested local commit against `05a976e`;
no push or normal-app rollout performed.

## Acceptance and chosen rules

Track shows saved daily confirmed progress toward one hour and consecutive
qualifying days. Two saved 30-minute sessions qualify once; 59:59.999999 does not.
The threshold is the established one-hour requirement. The following eligibility
and presentation choices are implementation defaults within that scope:

- All finalized outcomes contribute their confirmed closed intervals, including
  early finishes, resolved interruptions and legacy sessions. Unfinished sessions
  and any session with an unresolved interruption do not contribute. Tree/coin
  cutovers do not restrict streak eligibility. Missing intervals have no aggregate
  fallback and never acquire manufactured credit.
- The current service timezone governs Today and all historical date attribution.
  Changing the configured or OS timezone recomputes dates without altering saved
  data. Earlier intervals lack original timezone metadata despite the build plan's
  aspirational source-zone preservation rule; this ticket does not invent it.
- Today extends the streak when qualified. Before qualification, yesterday's run
  remains until today's end. Missing/unqualified earlier days break the run.
  Future-dated work cannot extend today's streak.
- Integer saved active microseconds remain the only earned duration. Each closed
  interval is split across local dates using UTC overlap lengths and cumulative
  integer floors, conserving every microsecond when observed wall and monotonic
  durations differ. No pause/review gap between intervals is included. A positive
  credit with zero wall span belongs to its starting local date; malformed or
  reversed spans produce a useful storage error rather than estimating work.

Affected records: reads of timer sessions, closed intervals and interruption
resolutions. No schema change, mutable streak counter, rewritten interval,
new award, purchase change or correction/Undo action. Existing timer expiry can
still finalize through the same application functions when Track is refreshed.
Read failures retain the prior display with refresh/retry feedback.

Reports, estimates versus actuals, session corrections, adjustment ledger actions,
AI and integrations remain outside this ticket. Combined M2/M3 actual Mac hardware
and operator acceptance remains pending. No normal data/service rollout, commit or
push was performed.

## Environment and verification

Actual host: macOS 26.6.2 (25G83), Darwin 25.6.0 arm64, Python 3.13.15,
Node 24.21.0. All mutation/browser/restart checks use disposable data.
Chrome reports 155.0.8059.82. No Windows or new hardware sleep run is claimed.

Implementation:

- `backend/domain/calendar.py` shares per-instant calendar rules with planning;
  `streaks.py` derives the last seven days and the full current consecutive run.
  Splitting on offset transitions as well as midnight handles historical date
  rollbacks, midnight gaps and skipped dates. Malformed saved dates return a
  structured `streak_data_invalid` 503 and preserve records.
- `GET /api/streaks` returns service Today/timezone, the integer threshold,
  current streak/streak-through date and daily integer totals. Existing timer
  application functions settle actual expiry before reading; no new mutation
  route or independent SQL write is introduced.
- `DailyStreak.tsx` shows progress, qualified days and timezone in Track. Date-only
  labels remain stable with a different browser timezone. Finish/navigation,
  focus/visibility, visible minute checks and manual refresh update the display.
  Aborted or superseded responses cannot replace a newer result. Loading disables
  refresh; errors identify a retained older display. An old service's 404 explains
  that the service needs restarting.

Independent expected fixtures include:

| Saved work | Expected result |
| --- | --- |
| Two 1,800,000,000 µs saved sessions on one date | 3,600,000,000 µs; qualifies once |
| 3,599,999,999 µs | Below the threshold |
| LA spring `2026-03-08T07:30Z`–`10:30Z`, three hours | March 7: 30 min; March 8: 150 min |
| LA fall `2026-11-01T06:30Z`–`09:30Z`, three hours | October 31: 30 min; November 1: 150 min |
| Six wall microseconds spanning UTC midnight, five saved µs | Prior date: 2 µs; next date: 3 µs |
| Goose Bay `2009-11-01T02:00Z`–`05:00Z`, three hours | October 31: 119 min; November 1: 61 min |

Commands/results:

- `.venv/bin/python -m pytest -q tests/test_timer.py tests/test_timer_recovery.py tests/test_timer_clock.py tests/test_rewards.py tests/test_shop_api.py tests/test_forest.py tests/test_forest_api.py tests/test_planning.py tests/test_planning_api.py tests/test_weeks.py tests/test_tasks.py tests/test_migrations.py`
  → **394 passed**, **10.78 s**. Affected timer/reward/planning/history foundations
  pass; the later full-core result covers the final calendar correction.
- `.venv/bin/python -m pytest -q tests/test_streaks.py`
  → **43 passed**, **1.44 s**, after the midnight rollback correction, before the
  additional genuine schema-7 upgrade fixture.
- `.venv/bin/python -m pytest -q tests/test_streaks.py tests/test_streaks_api.py tests/test_streaks_restart.py`
  → **51 passed**, **3.40 s**, zero failures/skips, with loopback permission.
  Includes exact thresholds/fractions, all outcomes, legacy and unfinished work,
  multiple projects/subtasks, gaps, service-zone changes, OS-local/configured DST,
  invalid data, save/recovery replay and real process restarts. A disposable
  schema-7→10 upgrade preserves original rows: legacy 4.25 seconds count, and the
  total becomes 8.5 seconds only after the other session's explicit finalization, with no tree/coin
  backfill. Derived reads preserve all saved tables, task completion, ownership,
  rewards, frozen history and integrity/foreign keys.
- `npm --prefix frontend test` → **122 passed in 8 files**, **3.81 s**;
  `npm --prefix frontend run typecheck` and `npm --prefix frontend run build`
  passed (production build **173 ms**).
- `BEARPLANS_EVIDENCE_DIR=.evidence/daily-streaks BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q tests/test_streaks_browser.py`
  → **1 passed**, **6.23 s**. Real Chrome/loopback service, synthetic task data and
  observed fake-clock seed sessions. The browser timezone is Pacific/Auckland
  while the service uses LA. Two-day/yesterday streak plus 30 saved minutes becomes
  three days/60 minutes after an early finish. A committed lost response, exact
  retry, reload and process restart preserve the result and all unrelated records.
  Keyboard read-failure/retry, narrow layout, no page errors and four exact tree/
  reward outcomes pass. Section screenshots were added for the final core run.
- `.venv/bin/python -m compileall -q backend tests/test_streaks.py tests/test_streaks_api.py tests/test_streaks_restart.py tests/test_streaks_browser.py`
  and scoped `git diff --check` passed. Applied migrations, timer/reward/forest
  implementation and dependency locks have no diff.
- Independent source review initially found the Goose Bay midnight rollback issue.
  After correction, eight configured/OS-local cases (Goose Bay, St. John's, São
  Paulo and Apia) matched a separate second-by-second UTC reference and conserved
  credit. Final source review found no remaining blocker.

## Initial failures and corrections

- The first backend collection referenced the wrong existing week-preview helper;
  the fixture now imports `preview_close`. The first domain run was **41 passed,
  2 failed**: a fixture omitted the required pause revision, and the historical
  midnight rollback case exposed a real allocation defect. Offset-transition
  splitting and the repeated-midnight fallback fixed the defect; regressions pass.
- A backend subset had **7 passed, 1 failed** because sandbox rules denied the
  disposable service's socket bind. The loopback rerun reached the real restart
  checks and exposed a test assertion comparing the entire `TimerView`, including
  changing `server_now`. The corrected assertion compares HTTP status, exact saved
  session and all stored rows while allowing the clock to advance. Final 51 pass.
- The first frontend run had seven new test locator failures because nested
  strong/time elements split visible text; locators were corrected. An unused
  `waitFor` import caused an initial typecheck failure and was removed. The final
  suite, typecheck and build pass without weakening the product behavior.
- The first new Chrome run failed its synthetic seed pause because the test
  omitted the required revision (**1 failed, 7.99 s**); corrected fixture rerun
  passed. An initial full-page narrow screenshot showed repeated compositor tiles;
  direct section captures were added for visual inspection.
- The first full core had already collected the earlier restart assertion before
  its correction was saved. Command:
  `BEARPLANS_EVIDENCE_DIR=.evidence/daily-streaks/full-core BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s`
  → **604 passed, 1 failed**, **154.42 s**. The sole failure was that same
  advancing-`server_now` test assertion, not changed records or streak totals.
  The final files passed the focused 51-case run and the final full rerun below.
  This first full run observed a browser-closed countdown saving **60.000000 s**
  after **60.266 s** independent elapsed time. Short timer: **2.554286 s** saved;
  task-write median **0.003042 s**, max **0.011492 s**, browser create **0.069 s**.

No failed/setup-blocked attempt is counted as passing evidence.

## Final verification and decision

Final command:

```sh
BEARPLANS_EVIDENCE_DIR=.evidence/daily-streaks/final-core BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s
```

**605 passed**, **156.70 s**, zero failures/skips. This covers the final source and
test files, including the new Chrome journey and existing foundation, planner,
history, timer/recovery, forest, coin/shop, migration and restart regressions.
The browser-closed real minute saved **60.000000 s**, observed after **60.514 s**
independent same-host elapsed time. The short real timer saved **2.564542 s**;
task writes during tracking had median **0.003096 s**, max **0.012518 s**,
and browser task creation took **0.071 s**. No external stopwatch or physical
sleep claim follows from these observations.

Visually inspected synthetic wide **1440 px** partial progress, narrow **375 px**
qualified progress and dark mode. The seven-day grid, timezone/help text,
qualification and retry controls remain readable without horizontal overflow.
Native keyboard retry works and Chrome reports no page errors. Direct section
captures resolve the full-page compositor artifact noted above. Evidence stays
ignored under `.evidence/daily-streaks/`; final previews include
`final-core/streak-01-partial-section.png`,
`final-core/streak-04-qualified-section.png` and
`final-core/streak-05-dark-section.png`. No personal records or screenshots were
used or committed.

Scoped whitespace, local documentation links/anchors and compile checks pass.
SHA-256 checks preserve both planning files' complete contents and staged/unstaged
patches, the entire original index diff, all pre-existing review records, HEAD and
recovery stash. Preservation manifest:
`/var/folders/wk/3yfnwgrx2qdbvr75y1kcqrx00000gn/T/bearplans-streak-20261021-xvxjpzq7/preservation.json`.
No applied migration, dependency lock, timer recovery, reward/purchase write or
forest write changed. No normal app was restarted, no personal database was
migrated, and no commit/push occurred.

Decision: **implementation Pass**. Required actual target-Mac/operator acceptance
remains pending for combined M2/M3: sleep/lid/maintenance wakes, supported power
conditions, real interruption/recovery, clock changes and externally referenced
long-duration behavior. Automated date/retry checks do not certify those gates.
M3 still lacks statistics/session corrections; backup/restore and the seven-day
trial remain later release work. The next session is prepared in
[shared progress](../PROGRESS.md#next-m3-session--statistics-and-session-corrections-not-started)
and has not started.

## Local commit authorization

After the completed implementation review, the user explicitly requested committing
the work. This local commit includes daily-streak source, tests, guidance and both
October 21 handoff reviews against `05a976e`. The two unrelated planning files
retain their original staged/unstaged edits and remain outside the commit. No
application source changed after the recorded 605 core / 122 frontend passes;
only commit/handoff wording was updated. Scoped diff, documentation links and
planning/stash preservation are rechecked for the commit. No push is performed.
