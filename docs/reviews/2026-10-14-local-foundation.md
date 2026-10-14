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
| `npm test` (8 component tests) | Pass | Node 24.21.0 installed mid-review; vitest 5.0.4, 8/8 |
| `npm run build` (`tsc --noEmit && vite build`) | Pass | vite 8.3.4, 17 modules, 223.27 kB (70.02 kB gzip) |
| `pytest` re-run with the interface built | **74 passed, 0 skipped** | The Playwright journey ran against real Chrome on macOS; nothing skips any more |
| `python3 launch.py` end to end on macOS | Pass | Transcript below; first run built the interface itself |
| Restart and task identity through the real launcher | Pass | Same UUID and byte-identical fields across a stop/restart; see below |

**Launcher transcript** (run 1 created the task, run 2 re-read it after a full restart,
both against a scratch `BEARPLANS_DATA_DIR`, both stopped on SIGTERM):

```
Building the interface ...
  $ /opt/homebrew/bin/npm run build
  ✓ built in 78ms
BearPlans 0.1.0
  data:   .../scratchpad/launch-data
  schema: version 1
  open:   http://127.0.0.1:18766/  (Ctrl+C to stop)
BearPlans stopped.
```

```
run 1 POST /api/tasks -> {"id":"1104110f-3146-449b-8f91-147852faf11c",
                          "title":"Read Math 55 notes",
                          "created_at":"2026-10-14T04:59:48.958350Z","revision":1}
run 2 GET  /api/tasks -> exactly one task, id 1104110f-3146-449b-8f91-147852faf11c,
                          every field identical to run 1
```

Before Node was installed, a Node binary bundled inside another application was borrowed to attempt the
frontend build. Typecheck succeeded, but `vite build` failed when loading
`@rolldown/binding-darwin-arm64`: *"code signature ... not valid for use in process:
mapping process and mapped file (non-platform) have different Team IDs"*. That is macOS
refusing to let a hardened, Team-ID-signed runtime `dlopen` a third-party native module.
It was an artefact of the borrowed interpreter, **not a defect in this project** — the real
Node 24.21.0 builds cleanly, as the rows above show. Recorded only so the dead end is not
re-investigated later.

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

### What the diagnostic was designed to settle

Three questions, each answered below by a recorded run rather than by argument:

1. Is a bounded suspend of known duration **measured** by the service, at a magnitude that
   matches an independent record of the sleep? (Run 2.)
2. Does a throttled browser produce a *different* signature from a suspend, so the two
   cannot be confused? (Run 1 supplies the throttle; run 2 the suspend.)
3. Does the service process survive a suspend and resume serving afterwards? (Run 2.)

The limits of the method are stated after the runs, in "What this still does not prove".

### Manual run 1 (2026-10-13 21:39–21:44 PDT) — no sleep occurred

260 service samples over 260.1 s, 255 browser samples. The operator marked a lid close at
04:42:15 UTC and a return at 04:43:59 UTC.

| Observation | Value |
| --- | --- |
| Largest service-side interval in the entire run | **1.01 s** (nominal 1.0 s) |
| Largest awake-clock loss (`Δcont − Δawake`) | **0.0 s** |
| Browser-side gap | **39.69 s**, tab reported `hidden` |

**The machine never suspended.** Cause: clamshell mode. An external display (Samsung
Odyssey G5) on AC power with a USB keyboard/receiver attached means closing the lid blanks
the internal display and keeps running. macOS's own power log confirms it independently:

```
21:42:29 -0700  Sleep  Entering DarkWake state due to 'Software Sleep pid=167' ... 9 secs
21:42:38 -0700  Wake   DarkWake to FullWake from Deep Idle ... due to HID Activity
```

A 9-second DarkWake, not a suspend — the CPU kept running, which is exactly why the sampler
shows no gap. `pmset -g assertions` also showed `PreventUserIdleSystemSleep 1`, held by
`powerd` ("Prevent sleep while display is on") and by `coreaudiod` for audio playback.

**What run 1 does establish**, on real hardware: the browser stream gapped 39.69 s while the
service stream stayed continuous and neither clock lost time. A browser-side gap therefore
does **not** imply sleep. This is the hidden-tab/sleep confusion the Build Plan warns about,
observed and resolved rather than argued. Run 1 is retained as the control case.

**What run 1 does not establish:** any measurement of an actual suspend.

### Manual run 2 (2026-10-13 21:48–21:55 PDT) — forced suspend — PASS

Method: `pmset sleepnow` (deterministic; `PreventSystemSleep` was 0, and a forced sleep
overrides the idle-sleep assertions that blocked run 1), held, then woken by key press.
243 service samples over a 391.1 s span; 520 browser ticks.

The Mac suspended **three** times, not once: the forced sleep, then two further
`Maintenance Sleep` cycles that it entered on its own after each DarkWake.

| # | `pmset -g log` Sleep | Wake | pmset duration | probe `slept_s` | browser `slept_s` |
| --- | --- | --- | --- | --- | --- |
| 1 | 21:50:29 `Software Sleep pid=65852` | 21:50:59 DarkWake | 30 s | **28.301 s** | **28.301 s** |
| 2 | 21:51:45 `Maintenance Sleep` | 21:53:39 DarkWake | 114 s | **111.972 s** | **111.972 s** |
| 3 | 21:54:24 `Maintenance Sleep` | 21:54:34 DarkWake | 10 s | **7.522 s** | **7.522 s** |

Sleep 1 is the operator's `pmset sleepnow`. The session ended 21:54:43 with
`Wake: DarkWake to FullWake ... due to UserActivity`, the key press.

**Three independent sources agree.** `pmset`'s figures are the durations it prints on entry
to sleep; the probe reads between its own 1 s samples, so it necessarily under-reads by up
to a second at each end, which is the entire discrepancy. Internal arithmetic is exact:

```
span (continuous clock) 391.1 s  -  awake clock advanced 243.3 s  =  147.79 s asleep
sum of the three measured slept_s                                 =  147.795 s
service samples 243 vs 243 s awake  ->  the sampler missed 0 s while awake
```

**Conclusion: `time.monotonic()` freezes across a real macOS suspend, `CLOCK_MONOTONIC`
does not, and their difference measures the suspend to within the sampling interval.**
The policy below is no longer inferred from accumulated boot-time divergence; it is
measured, three times, against the operating system's own record.

### Two findings that change the M2 design

**1. The browser's monotonic clock freezes too.** `performance.now()` advanced only
1.18 / 1.00 / 1.00 s across suspends of 28 / 112 / 7.5 s, while `Date.now()` advanced
29.48 / 112.97 / 8.52 s. So Chrome on macOS behaves exactly like Python: the same
two-clock comparison detects sleep in the page, and the browser's `slept_s` matched the
service's to the millisecond on all three events.

This also exposed a defect in the first version of this diagnostic, which differenced
`performance.now()` alone and therefore reported "browser gaps: none" for a run containing
three real suspends. Fixed, together with two related faults the data revealed:
`performance.now()` restarts at zero on each page load, so ticks now carry a page-session
id and are only differenced within one session; and negative intervals are discarded
rather than reported as nonsense gaps. Run 1 re-analysed under the fix still reads
correctly as a throttle — both of its browser clocks advanced 39.689 s *together*.

**2. One user-visible sleep can be several suspends, with the service briefly alive
between them.** The service was scheduled and sampling for ~46 s during each DarkWake, with
the lid still shut and the user absent. A timer must therefore sum sleep across multiple
intervals rather than assume a single gap, and must never treat "my process is running" as
"the user is present."

### What this still does not prove

- **Instantaneous** pause at the moment of sleep. Detection remains retroactive, on wake.
- Anything across a **service restart or crash** — `time.monotonic()` is only comparable
  within one process lifetime, so that gap stays unmeasurable and must go to review.
- Battery/standby/hibernate behavior. All three observations were on AC power.
- Timer correctness. No timer exists yet.

## Timer policy decision

Chosen on the measured evidence of run 2, not on inference:

1. **Credit elapsed time from `time.monotonic()` only.** It is now measured to freeze across
   a real macOS suspend, so suspended time cannot be credited as work.
2. **Measure sleep as `Δcont − Δawake`** using `CLOCK_MONOTONIC`. While the service stays up
   a suspend is not merely detected but quantified — to within the sampling interval, and
   agreeing with `pmset` on three separate events. The countdown can therefore be corrected
   exactly on wake instead of being sent to review. **No native power-event adapter, no
   IOKit, no added dependency.** This is a better outcome than the Build Plan's fallback,
   which assumed precise power events might be unavailable.
3. **Never difference `time.time()` for credit.** Store wall-clock timestamps for display
   and cross-restart recovery only; an NTP step must never move a balance. The probe reports
   `Δwall − Δcont` separately so such a step is visible rather than silently absorbed.
4. **Sum sleep over multiple intervals; never assume one gap.** Run 2 produced three
   suspends from a single user action, because macOS re-slept after each DarkWake.
5. **"My process is running" does not mean "the user is present."** The service was
   scheduled for ~46 s during each DarkWake with the lid shut and nobody there. Presence
   must come from user activity, not from the service being alive.
6. **Keep the "Needs review" fallback, scoped to restarts and crashes.** Across a process
   restart the monotonic clocks reset, so the gap is genuinely unmeasurable. That case gets
   checkpoint-based recovery and an explicit **Needs review** state, as the Build Plan
   requires. Unknown gaps still never silently earn time.
7. **Browser ticks stay non-authoritative — display only.** `performance.now()` freezes
   across suspend exactly as `time.monotonic()` does, so the page *can* run the same
   two-clock check and it agreed with the service to the millisecond. But it is throttled
   when hidden, resets its origin on reload, and can be open in several tabs. Use it to
   corroborate and to refresh the display promptly on wake; never to decide credit.

Rule changes: none. These are implementation commitments for M2, not changes to a product
default, so no acceptance scenario changes.

This decision covers policy selection only. **The M2 timer implementation still requires its
own sleep, restart, clock-change, midnight, DST and recovery tests.** Nothing here
substitutes for them, and battery/standby/hibernate behavior remains unobserved.

## Issues

| Severity | Issue | Next action |
| --- | --- | --- |
| Medium (fixed in this review) | The first version of `tools/sleep_probe.py` differenced `performance.now()` alone and reported "browser gaps: none" for a run containing three real suspends. Two related faults: `performance.now()` resets per page load, so two page sessions were differenced against each other; and negative intervals were reported as gaps. | Fixed: wall-minus-monotonic comparison, per-page-session grouping, negative intervals discarded. Re-verified against both recorded runs and six synthetic cases. |
| Low | Request protection allows requests with no `Origin` header (curl, local scripts). By design for local tools; the full request-protection pass is scheduled for Oct 24. | Revisit on Oct 24. |
| Low | Battery, standby and hibernate sleep behavior is unobserved; all three measurements were on AC power. | Cover in the M2 sleep tests. |
| Low | Sleep is detected retroactively on wake, not at the moment of suspend. No pre-sleep notification is available without native power events. | Acceptable: the countdown corrects itself on wake. Revisit only if a user-visible pause at the instant of sleep is required. |
| Informational | `tools/sleep_probe.py` is a temporary M0 instrument, not product code. | Delete once M2 timer recovery has its own tests. |

## Decision

Reported separately, because the two answer different questions.

### Change review — the requested foundation build: **Pass**

Every requested item is implemented and verified on the target platform. Re-verified
directly on the Mac rather than assumed: 74 passing tests with nothing skipped (including
the Playwright journey against real Chrome), `npm test` 8/8, a clean `tsc && vite build`,
migration rollback atomicity, `Z`-suffixed UTC timestamps in both storage and the API, and
task identity preserved byte-for-byte across a real stop/restart of the launcher process.

Code review of the storage, migration, domain, route, locking and request-protection layers
found **no defect in the product code**. The one defect found and fixed in this review was
in the diagnostic instrument written for it, not in BearPlans.

### M0 milestone gate: **Pass**

All required evidence now exists, on the target hardware:

1. Reproducible startup — `python3 launch.py` run end to end on macOS, transcript recorded.
2. Durable task identity — same UUID and identical fields across a full restart.
3. Duplicate-instance handling — covered by the suite, which passes here.
4. Documented sleep behavior — three suspends measured and agreeing with `pmset -g log`,
   with the hidden-tab control case recorded separately in run 1.
5. Unknown gaps cannot silently earn time — the policy above routes the one genuinely
   unmeasurable case (restart/crash) to **Needs review**.

The review plan's bar — *"If native sleep events are unreliable, explicitly select the
Needs review fallback"* — is met in a stronger form: native sleep events proved unnecessary,
and the fallback is retained precisely where measurement is impossible.

**Next eligible build: Oct 15 — M1, Projects and tasks.**
