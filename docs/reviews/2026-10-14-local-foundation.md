# Review record: Local foundation (M0, Oct 14 roadmap row)

**Build/commit:** `ea04dcd` ("Pre M0 - Waiting for Confirmation for testing on Mac"), on top of `23786cf`. First reviewed 2026-10-13 on Windows; re-verified on the target Mac 2026-10-13/14 (see [macOS verification](#macos-verification-2026-1013-14)). The build was pulled forward from the Oct 14 slot.
**Milestone and ticket:** M0, first foundation build. Covers the React/TS interface, FastAPI service, SQLite migration 0001, shared `create_task`/`list_tasks`, task entry and saved-task list, data outside the repo, and one launch command.
**Expected behavior:** `python3 launch.py` starts a loopback-only service and opens the interface. You enter a task and it appears in the saved list. After you stop and relaunch, the same task (same ID) is still listed.
**Rule/default changes:** none. Proposed rules this build adds:
- Task titles are 1–200 characters after trimming whitespace and invisible characters.
- The default port is 8765.
- One running instance is allowed per data folder.
**Affected records/functions:** `tasks` and `schema_migrations` tables; `backend/domain/tasks.py` (`create_task`, `list_tasks`).
**Environment:**
- Windows 11, Python 3.14.5, Node 24.16.0, SQLite 3.50.4.
- Chrome or Edge, driven by Playwright 1.64.
- The target Mac was **not** available.

## Checks run and outcomes — development environment (Windows 11)

These are the original 2026-10-13 results. They are retained as history. They certify the code, **not** this project's target platform; see the macOS section below for what was re-run on the Mac.

| Check | Result |
| --- | --- |
| `pytest` (74 tests): paths, migrations, domain, API/local-only protection, real-process restart, second instance, busy port, corrupt DB, browser journey | Pass |
| `npm test` (8 component tests), `npm run typecheck`, `npm run build` | Pass |
| Restart through the real service process: graceful stop, and abrupt kill; task re-read with an identical record | Pass |
| Exact launch command `python launch.py --no-browser --port 18766` run twice against a scratch data folder. The task created in run 1 was listed in run 2. Both runs exited 0 and printed "BearPlans stopped." | Pass |
| A data folder inside the repository is refused, and no `.sqlite3` file appears in the source tree | Pass |
| Second instance on the same data folder points to the running one and leaves it unaffected | Pass |
| A cross-origin POST, a non-loopback Host, or `Sec-Fetch-Site: cross-site` is rejected and nothing is saved | Pass |
| A failed migration rolls back. A newer or unknown schema is refused. A corrupt DB gives a clear error and the file is left unchanged | Pass |
| Visual review at 1280 px and 375 px, dark mode, and with the service down (`evidence/`). No horizontal overflow, visible focus, the typed title is kept on error | Pass |
| Independent review: 5 reviewers plus adversarial verifiers. 12 findings upheld: 1 medium (corrupt-DB traceback), the rest low. All fixed and re-tested | Pass |

Startup transcript (path shortened):

```
BearPlans 0.1.0
  data:   ...\scratchpad\launch-data
  schema: version 1
  open:   http://127.0.0.1:18766/  (Ctrl+C to stop)
BearPlans stopped.
```

## macOS verification (2026-10-13/14)

Run on the actual target machine, which the first review could not reach.

**Environment:** macOS 26.6.2 (build 25G83), Darwin 25.6.0, arm64 (Apple Silicon).
Python 3.13.15 (system `python3`), SQLite via the stdlib `sqlite3` module.
Google Chrome is installed. **Node.js was not installed** at the time of this review.

| Check | Result | Evidence |
| --- | --- | --- |
| `.venv` created from system `python3` and `requirements-dev.lock` installed | Pass | `python3 -m venv .venv`, pip install exited 0, interpreter reports 3.13.15 |
| `pytest` on macOS | **73 passed, 1 skipped** | The skip is `test_e2e_browser.py` — "frontend not built", because Node was missing. 74 collected, matching the Windows count |
| Migration atomicity, re-tested directly on macOS | Pass | A 4-statement migration whose last statement is invalid left **no** partial tables (`alpha`/`beta` absent), schema stayed at version 1, `MigrationError` raised. `executescript` inside `BEGIN IMMEDIATE` is atomic here |
| Stored vs returned timestamp format | Pass | Both the stored row and the API response are `2026-10-14T04:13:55.676290Z` — UTC with `Z`, as the project rule requires |
| `npm run typecheck` | Pass | Ran under a borrowed Node 24.21.0; `tsc --noEmit` clean |
| `npm test`, `npm run build`, browser journey | **Not run** | Blocked: no Node on this Mac (see Issues) |
| `python3 launch.py` end to end on macOS | **Not run** | Blocked by the same missing Node; `ensure_frontend()` raises `SetupError` before the service starts |

A Node 24.21.0 binary bundled inside another application was borrowed to attempt the
frontend build. Typecheck succeeded, but `vite build` failed when loading
`@rolldown/binding-darwin-arm64`: *"code signature ... not valid for use in process:
mapping process and mapped file (non-platform) have different Team IDs"*. That is macOS
refusing to let a hardened, Team-ID-signed runtime `dlopen` a third-party native module.
It is an artefact of the borrowed interpreter, **not a defect in this project**, and it is
not evidence that the build is broken on macOS. The borrowed `node_modules` was deleted so
the next `npm ci` starts clean.

## Mac sleep/wake experiment

### Why the task-entry screen cannot answer this

The M0 gate asks for sleep behavior that is distinguishable from a hidden tab. The shipped
interface has no timer and no clock display, so watching it across a lid close proves
nothing. A `visibilitychange` event cannot answer it either: the browser fires the same
event when you switch tabs and when the machine wakes. A dedicated diagnostic was needed.

### The clock finding

macOS exposes two clocks that Python surfaces separately, and they disagree by design:

| Clock | Python call | Behavior across sleep |
| --- | --- | --- |
| `mach_absolute_time` | `time.monotonic()`, `time.perf_counter()`, `CLOCK_UPTIME_RAW` | **Stops** while suspended |
| continuous | `time.clock_gettime(time.CLOCK_MONOTONIC)` | **Keeps running** while suspended |
| real time | `time.time()`, `CLOCK_REALTIME` | Keeps running, but is adjustable (NTP, user) |

Measured on this Mac, booted 2026-09-16 05:33:12:

```
wall since boot (includes sleep) : 2,389,266 s = 27.65 d
CLOCK_MONOTONIC (6)              : 2,389,265 s = 27.65 d   <- matches boot time to the second
time.monotonic() / UPTIME_RAW    : 1,083,197 s = 12.54 d
implied accumulated sleep        : 1,306,068 s = 15.12 d
```

`CLOCK_MONOTONIC` tracks wall-time-since-boot exactly, while `time.monotonic()` has lost
15.12 days. So **sleep is measurable in pure Python**: over any interval,
`Δcont − Δawake` is the time the machine was suspended. No native power-event adapter,
no IOKit, no extra dependency.

### The diagnostic

`tools/sleep_probe.py` (stdlib only, ~2 h of M0 budget) samples all three clocks once a
second in the service process and serves a page whose 1 s browser ticks are buffered
locally and flushed on wake. One JSONL log holds both streams plus user-pressed markers.
Per interval it reports `slept = Δcont − Δawake`, `stalled = Δawake − 1 s`, and
`clock_shift = Δwall − Δcont`, then classifies the gap.

This is a temporary M0 instrument, not product code. Delete it once M2 timer recovery has
its own tests.

**Classifier verification** — four synthetic logs plus one real process freeze:

| Case | Expected | Reported |
| --- | --- | --- |
| Synthetic 120 s suspend | sleep | `gap 120.5 s, slept 120.0 s, stalled 0.0 s` → machine slept |
| Synthetic 10 s awake starvation | stall | `gap 11.0 s, slept 0.0 s, stalled 10.0 s` → process stalled while awake |
| Synthetic 60 s suspend + 300 s NTP step | sleep, shift reported separately | `slept 60.0 s, clock_shift 300.0 s` → machine slept |
| Synthetic hidden tab (browser gaps, service does not) | hidden tab, not sleep | service gaps: none; browser gap 60 s |
| **Real** `SIGSTOP` for 8 s on the live probe | stall, **not** sleep | `gap 8.958 s, slept 0.0 s, stalled 7.958 s` → process stalled while awake |

The `SIGSTOP` case is the important one: a genuinely frozen process is **not** misreported
as sleep, because both kernel clocks keep advancing while it is stopped.

### What this can and cannot prove

Can prove, once the manual run below is done:
- That a bounded, deliberate sleep of known duration is detected and **measured** by the
  service, with a magnitude matching the wall time the lid was shut.
- That hiding a tab produces a visibly different signature (browser ticks throttle; both
  service clocks stay continuous), so the two are not confusable.
- That the service process survives lid-close sleep and resumes serving afterwards.

Cannot prove, and must not be claimed from this run:
- **Instantaneous** pause at the moment of sleep. Detection is retroactive, on wake. There
  is no pre-sleep notification without native power events.
- Anything across a **service restart or crash**. `time.monotonic()` is only comparable
  within one process lifetime, so a gap spanning a restart is unmeasurable by this method.
- Coverage of every macOS low-power mode (Power Nap, standby, hibernate) — only the modes
  actually exercised.
- Anything about timer correctness itself. No timer exists yet.

### Manual run — NOT YET RUN

Results are deliberately absent. They will be filled in from the probe's own report.

```
PENDING — awaiting the operator's run. Do not mark this check passed until the
report output is pasted here.
```

## Timer policy decision

Chosen on the clock evidence above, and **provisional** until the manual run confirms it
for a single bounded sleep:

1. **Credit elapsed time from `time.monotonic()` only.** It excludes sleep by construction
   on macOS, so suspended time is never credited as work.
2. **Measure sleep as `Δcont − Δawake`** using `CLOCK_MONOTONIC`. While the service stays
   up, a sleep interval is not merely detected but quantified, so the countdown can be
   corrected exactly on wake instead of being sent to review. This is a better outcome than
   the Build Plan's fallback, and it needs no native power-event adapter.
3. **Never difference `time.time()` for credit.** Store wall-clock timestamps for display
   and for cross-restart recovery only; an NTP step must never move a balance.
4. **Keep the "Needs review" fallback, scoped to restarts and crashes.** Across a process
   restart the monotonic clocks reset, so the gap is genuinely unmeasurable. That case gets
   checkpoint-based recovery and an explicit **Needs review** state, exactly as the Build
   Plan requires. Unknown gaps still never silently earn time.
5. **Browser ticks are never authoritative** — display only.

This decision covers policy selection only. The M2 timer implementation still requires its
own sleep, restart, clock-change and recovery tests; nothing here substitutes for them.

## Issues

| Severity | Issue | Next action |
| --- | --- | --- |
| Gate blocker (environment) | **Node.js is not installed on the target Mac.** `python3 launch.py` fails in `ensure_frontend()` with "The interface needs building, but npm was not found", so the launcher has never completed on this machine and the interface has never been built here. | Owner: user. Install Node 24 LTS, then run `python3 launch.py` once and confirm first-run setup, the saved task, and the restart. |
| Gate blocker (evidence missing) | The Mac sleep/wake experiment has not been run. The diagnostic now exists and is verified against synthetic and real-freeze cases, but **no actual lid-close observation has been recorded**. | Owner: user. Run `python3 tools/sleep_probe.py`, follow the four steps on its page, paste the report into "Manual run" above. |
| Gate blocker (evidence missing) | `npm test`, `npm run build` and the Playwright browser journey have not run on macOS. Only `tsc --noEmit` did. | Owner: user. Re-run after installing Node; Chrome is already present, so the browser test will no longer skip. |
| Low | Request protection allows requests with no `Origin` header (curl, local scripts). By design for local tools; the full request-protection pass is scheduled for Oct 24. | Revisit on Oct 24. |
| Low (resolved on macOS) | The browser test skips when neither Chrome nor Edge is installed. | Chrome **is** installed on this Mac, so the skip here was caused only by the missing frontend build, not by a missing browser. |
| Informational | `tools/sleep_probe.py` is a temporary M0 instrument, not product code. | Delete once M2 timer recovery has its own tests. |

## Decision

Reported separately, because the two answer different questions.

### Change review — the requested foundation build: **Pass with follow-ups**

Every requested item is implemented, and the implementation holds up on macOS where it
could be exercised. Re-verified directly on the Mac rather than assumed: 73 passing tests
(1 skipped for the missing build), migration rollback atomicity, and `Z`-suffixed UTC
timestamps in both storage and the API. Code review of the storage, migration, domain,
route, locking and request-protection layers found no defect to fix. The follow-up is
evidence, not code: the frontend toolchain has never run on this machine.

### M0 milestone gate: **Fail — required evidence is missing**

Not a code judgement. Three required pieces of evidence do not exist yet:

1. No `python3 launch.py` run has ever completed on the target Mac (Node missing).
2. No sleep/wake observation has been recorded on the target Mac.
3. The frontend test, build and browser journey have not run on the target Mac.

Per the Build Review Plan, *"Untested sleep/recovery is not a pass because normal timing
worked"*, and missing required evidence is a Fail rather than a Pass with follow-ups. The
review plan also states the development environment cannot certify Mac power-event
behavior — which is precisely the gap that remains.

**Do not begin Oct 15 (M1, Projects and tasks) until these are recorded.** The timer policy
above is chosen and justified, so M2 is unblocked on design; it remains blocked on M0's
gate like everything else.
