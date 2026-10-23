# Statistics — October 23, 2026

Baseline: `d20eddf`; user authorized executing the next M3 work under AGENTS.md.
First scoped ticket: read-only all-time statistics. User subsequently requested
a local commit including the roadmap status refresh; no push requested.

## Acceptance and policy

Stats shows current leaf completion counts/percentages, saved time by local date,
project and task, and current leaf estimates versus all-time saved actual time.
Parents and repeated placements do not duplicate completion or estimates. No
estimate means unspecified. Daily completion reflects currently complete leaves
on their saved completion dates, not an immutable event log. Reopening/removing
work can change these counts; closed-week snapshots retain their own frozen totals.

Finalized closed intervals, including legacy/early/interrupted work, contribute
exact integer microseconds. Unfinished sessions and unresolved interruptions do
not contribute; missing intervals never fall back to a session aggregate. The
existing streak allocator handles midnight/DST/drift without creating credit.
Historical project IDs and removed-task time remain; current names/estimates are
used for current leaves. Historical rows add no current completion or estimates.
The task project filter only filters task details; all-time summaries stay explicit.

All report queries share one SQLite read snapshot. No report counters, schema
changes or personal-data access. Visiting Stats can settle a genuinely expired
timer via the existing service, once, just like Forest/Streak. Request generations
and aborts discard stale navigation responses. Failed refreshes retain and label
the last report; keyboard retry, focus refresh and service-restart guidance work.
This read-only ticket needs no Undo. Session correction is a separate next ticket.

## Windows prerequisites discovered during verification

Actual environment: Windows 11 `10.0.26300`, Python 3.14.5, Node 24.16.0,
Chrome 155.0.8059.85. This evidence does not certify Mac sleep or long sessions.

The installed Windows environment lacked IANA timezone data. Added a Windows-only
`tzdata` dependency in pyproject and regenerated both uv lockfiles (2026.5), with
all existing package pins retained. Installed the development lock in existing venv.

The real service then failed because `kernel32` did not export QueryInterruptTime.
A local ctypes probe found both clock symbols in the realtime API contract. Load
`api-ms-win-core-realtime-l1-1-1` for the existing awake/continuous 100 ns clocks.
Clock policy and Mac/Linux clocks are unchanged. The real Windows sampling
regression and disposable service restart now pass. Mock Linux/Mac clock fixtures
create platform-only attributes with `raising=False` so they run on Windows.
See [Microsoft interrupt-time documentation](https://learn.microsoft.com/en-us/windows/win32/sysinfo/interrupt-time).

## Verification

- `.venv\Scripts\python.exe -m pytest -xq tests/test_statistics.py tests/test_statistics_api.py tests/test_streaks.py tests/test_streaks_api.py`
  — **64 passed, 2 skipped**, 36.19 s. The skips require Unix `tzset`; configured
  IANA-zone cases pass on Windows. Exact fixtures: 40 + 20 min = 60; one saved
  session with two intervals counts once; one of three leaves = 33.33%; parent
  estimate 999 excluded; removed child/container time preserved; fractional
  midnight credit 2 + 3 microseconds; DST fall-back and zero wall-span preserved.
- `npm --prefix frontend test` — **127 passed**, 9 files, 26.04 s.
- `npm --prefix frontend run typecheck` and `npm --prefix frontend run build` — pass.
- `.venv\Scripts\python.exe -m pytest -xq tests/test_statistics_browser.py tests/test_timer_clock.py`
  with `BEARPLANS_EVIDENCE_DIR=docs/reviews/evidence/statistics` — **7 passed**, 10.87 s.
  Real browser, disposable service, API totals and all saved rows survive restart;
  no page errors or overflow at 1440/375 px. Keyboard retry, failed read, project
  filter, direct hash/reload/navigation and browser/service timezone mismatch pass.
  Wide/narrow screenshots were inspected; dark/error captures also retained.
- `.venv\Scripts\python.exe -m pytest -xq tests/test_tasks.py tests/test_projects.py tests/test_planning.py tests/test_weeks.py tests/test_rewards.py tests/test_forest.py tests/test_timer.py tests/test_streaks_restart.py`
  — **291 passed**, 146.00 s. Task identity/completion, planning/history, reward
  replay, forest, timer credit and three real process restarts pass.
- `.venv\Scripts\python.exe -m pytest -xq tests/test_instance_build.py tests/test_launch_compatibility.py tests/test_startup_errors.py tests/test_schema_validation.py tests/test_migration_fingerprints.py tests/test_migrations.py tests/test_timer_recovery.py`
  — **154 passed**, 42.57 s. Instance reuse/build identity, legacy schema upgrades,
  startup failures, schema validation, fingerprint rejection, migration rollback
  and timer recovery remain intact. The first run stopped after 31 passes on the
  frozen legacy fixture hash: Windows Git checkout had converted 19 LF lines to
  CRLF. Normalizing back to LF reproduced the exact Git blob SHA-256
  `d7b41e9e962e0fcde2fb8e5c2160f2317c3e322d8225ec93ee018009e090d743`.
  `.gitattributes` now preserves LF for frozen SQL fixtures; the fixture has no
  content diff and no applied migration was changed.
- Final selected backend/browser total: **516 passed, 2 skipped**. Full core not
  rerun for this scoped ticket; M3 and Mac hardware gates are not certified.
- `git diff --check` and local Markdown-link checks pass. Local commit authorized
  after implementation and roadmap review; no push requested.

Initial attempts: sandbox denied pytest temp directories and uv cache writes;
rerun with granted access. The first fixture used timer.start arguments in the
wrong order; corrected before the passing run. Missing Windows tzdata and the
native clock loader blocked initial existing/browser checks; fixed as above.
An older frontend run completed 122 tests before the five new Stats tests existed;
the final 127-test result includes them. No setup failure is counted as a pass.
The Windows-only mocked clock attribute failure was corrected with `raising=False`
before the final 7-test browser/native-clock pass. An earlier affected-suite run
was interrupted after the native loader caused setup errors; 291 is the clean run.

Implementation review: **Pass on Windows** for the scoped report and launch fixes.
M3 remains incomplete until session corrections and combined target-Mac acceptance.

Evidence: [wide](evidence/statistics/stats-01-wide.png),
[narrow](evidence/statistics/stats-02-narrow.png),
[dark](evidence/statistics/stats-03-dark.png),
[read error](evidence/statistics/stats-04-read-error.png).
