# Target-Mac three-hour observation — October 31, 2026

**Pass for the final uninterrupted three-hour saved-time run and reported external
match; manual timing uncertainty retained.** Earlier incomplete/paused attempts
remain historical evidence below; combined M2/M3 is not signed off.
User selected **Three-hour stopwatch run**.
Revision `d9b5f90e10579d8687c4ffbd8e132a7121573ac1`, runtime source unchanged;
macOS 26.6.2 (25G83), Darwin arm64, AC attached at preparation. No personal data.

Expected: an uninterrupted real 180-minute countdown saves **10,800,000,000
microseconds**, one mature Pine and one 180-coin award, with task completion
unchanged. Record the independent stopwatch reading and approximate start/stop
uncertainty, then report the long-run difference separately. Sleep, pause, service
interruption, early finish or insufficient observation cannot certify this run.

## Instrument and setup

Fresh disposable data and observer source:
`/private/tmp/bearplans-mac-long-20261031-nhd_e5qq/`.
Command:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-long-20261031-nhd_e5qq/observe.py
```

Owned service **PID 53295**, `http://127.0.0.1:59851/#track`, data under `data/`.
Observer uses the existing `OwnedService`, clock samples and source hashes, creates
one synthetic task through the API, and observes SQLite read-only once per second.
It never starts, pauses, resumes or finishes the countdown and never changes power
or clock configuration. The agent selected the task and set **180 minutes** without
starting it. Operator is asked to click Start alongside a separate stopwatch,
report approximate start separation, keep the Mac awake and report the exact
reading when Countdown completed appears.

`observation.json` is replaced atomically about every ten seconds and at state
changes. Copies of sanitized JSON, the exact observer source and synthetic
screenshots are retained under ignored
`.evidence/mac-verification-20261031/long-10800-nhd_e5qq/`; databases are excluded.
The observer records awake/continuous clocks, sleep loss, saved intervals/rewards
and source digests; polling bounds remain same-host evidence. The UI's normal
polling is present. This does not newly certify expiry without API activity.

No start within 15 minutes ends setup as incomplete. A paused/review state ends
uninterrupted collection as incomplete. The collection limit is three hours plus
five minutes from detected start, using continuous time. After finish/incomplete
collection, the owned service remains available up to 30 minutes for operator UI
inspection, then stops itself. Ctrl+C on this owned observer also stops only its
service and retains evidence. No milestone pass is assigned automatically.

## Outcome of first attempt

Operator started at **09:00:30.288541 PDT**. A persisted Pause operation closed
the first interval at **09:00:38.236320**, credit **7,947,714 microseconds**.
A Resume operation opened a second interval at **09:00:52.542175**, excluding
the **14.305855-second** pause. This was a controlled pause/resume, not measured
hardware sleep or a restart interruption. The observer captured nine samples,
classified the paused state as `incomplete_interruption`, and left collection.

The original observer's 30-minute cleanup window then stopped its service at
**09:30:39.569732 PDT**, even though the timer had resumed. This was an instrument
design problem: cleanup must not stop an unfinished countdown after a transient
pause. Final synthetic database: session still running, no final outcome,
**1,794,953,213 microseconds** (29m 54.953213s), two intervals, unfinished/unfinalized
original tree, no coin award. No three-hour duration was completed. Saved intervals
sum exactly; SQLite integrity `ok`, foreign-key check empty. Source digests match.
Read-only listener check found no remaining service on port 59851.

Operator later reported **"they are both the same"**. Retained that report verbatim
in `followup-audit.json`; it does not override the missing completed records.
**This attempt cannot certify three-hour acceptance.** No evidence suggests a
BearPlans application failure here; the observer stopped its own backend.
Preserved the original instrument, records/operations, report and renewed evidence
hash manifest. Personal data/service and application source remain untouched.

## Corrected observer and retry

User explicitly requested **"let's redo it"**. New disposable root:
`/private/tmp/bearplans-mac-long-retry-20261031-yezcui29/`.
Its `observe.py` records pause/review and continues observing; neither state nor
an elapsed collection window automatically stops an unfinished countdown. Such
interruptions make uninterrupted eligibility false. Cleanup occurs only after a
finished/no-start observation, explicit collector cancellation or collection error.
A completed full-duration result still requires source/record and external
stopwatch review; no milestone pass is automatic.

Verified with a separate real disposable service:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-long-retry-20261031-yezcui29/observe.py /private/tmp/bearplans-long-observer-check-20261031
```

Started a one-minute synthetic session through the API, paused after two seconds,
waited three seconds, resumed, waited three seconds, then explicitly finished.
Observer remained collecting and backend alive through **running → paused →
running → finished**; final `uninterrupted_eligible` was false. Stopped only that
check service with Ctrl+C. Exact snapshots/source/check result retained under
ignored `.evidence/mac-verification-20261031/bearplans-long-observer-check-20261031/`.
Initial helper startup failed before any service launch because the alternate
temporary parent directory did not exist; added parent creation, then the real
behavioral check passed. This is test instrumentation only, no product change.

Actual retry command:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-long-retry-20261031-yezcui29/observe.py
```

Next: start the fresh 180-minute countdown alongside the independent stopwatch,
record start offset and exact final reading, and preserve the result. Battery/
other supported power states and quantified ten-minute precision remain separate.

Fresh retry prepared **11:52:50 PDT**, backend **PID 74328**, loopback port
**49554**, observer exec session **16554**. The new visible in-app tab has the retry
task and 180 minutes selected; no agent start action. Operator received the fresh
URL and start/stopwatch instructions. Durable ignored retry evidence:
`.evidence/mac-verification-20261031/bearplans-mac-long-retry-20261031-yezcui29/`.
This remains **prepared / not accepted** until actual records and independent
timing are available. Application source, personal data, index and Git refs unchanged.

Retry actually started **11:53:27.792329 PDT** and paused at **11:53:40.452317**, with
**12,660,014 microseconds** credited. Persisted Pause receipt, no interruption row.
The operator confirmed **"I pressed Pause"**, then **"I just activate my own
countdown so no worries"**. This is deliberate control use, not spontaneous pause.
Controls left unchanged; explained that Resume is required to keep tracking.
Observer remains collecting through this pause, confirming the cleanup fix in the
actual retry. This session is not uninterrupted; external start alignment and
numeric final reading remain unrecorded. `operator-note.json` retains both answers.

Operator resumed at **11:54:09.281138 PDT**, after **28.828821 seconds** paused.
Read-only records and visible UI confirm Running. Expected finish approximately
**14:53:57 PDT** without further pauses/sleep. `resumed-note.json` and
`running-after-deliberate-pause.png` retain the state. The observer remains active
and saves evidence; next action is reviewing actual completion with the external
reference and its alignment. No acceptance decision yet. Scoped documentation
whitespace/links and source preservation are checked on handoff.

## Completed retry and final audit

On this actual macOS 26.6.2 (25G83), arm64 Mac, the retry completed at
**14:55:28.946196 PDT** (21:55:28.946196Z), from **11:53:27.792329 PDT**.
Session `7dbbdba6-84b1-4f47-9c35-562c75e18468` finished with outcome `completed`,
revision 6, exactly **10,800,000,000 microseconds**. Three closed intervals saved
**12,660,014 + 4,529,635,693 + 6,257,704,293 microseconds**, summing exactly.
Wall duration was **10,921.153867 seconds**; wall and confirmed monotonic duration
need not be identical. No wall-duration difference was awarded as extra credit.

The initial deliberate pause excluded **28.828821 seconds**. Later measured sleep
was **69,917,527 microseconds** in the persisted interruption; the independent
observer measured **69.917528125 seconds**. The last trusted checkpoint was
**13:09:39.020916 PDT**. Detection at **13:10:49.920787** left the session paused
with **4,542,295,707 microseconds**; 21 post-detection samples preserved this
credit until a persisted Resume at **13:11:11.217326** (expected revision 4).
The full **92.196410-second** checkpoint-to-Resume gap was excluded. No automatic
resume or unresolved interruption. This was observed sleep, not a coordinated
battery or standby/hibernate test; its power condition was not separately captured.

The same original Pine `0d634226-d8e4-4b92-8474-0e58ada9f873` became mature at
finalization. Exactly one `session_award` row awarded **180 coins** at captured
rate 1. Task `c7cc90f9-d34f-42a3-8a56-b84206f72167` remained incomplete, revision 1,
with identical created/updated instants. UI showed **Countdown completed · 3:00:00**,
Mature Pine and earned 180 coins. Screenshot: ignored retry evidence `completed.png`.
API forest/shop/streak/statistics agree: one mature tree, balance 180, October 31
qualified with one-day streak, one saved session and **0/1** leaf tasks completed.

Operator reported **"it’s good, everything is matched"**. Stored verbatim in
`completion-audit.json`. No numeric external reading or start/stop uncertainty was
given. Same-host awake elapsed bounds **10,849.683414875–10,851.695788583 seconds**
include awake pause/recovery time and cannot replace the separate stopwatch.
`uninterrupted_eligible = false`: pause, measured sleep, three intervals. Thus this
is a completed three-hour **active-time persistence and recovery pass**, with a
qualitative operator match; uninterrupted long-run precision remains unverified.
Normal UI polling was present, so this run does not newly certify autonomous expiry
without API activity. The earlier one-minute browser-closed expiry evidence remains
separate. Combined M2/M3 acceptance is still not passed.

Exact final audit commands (both exit 0):

```sh
.venv/bin/python /private/tmp/bearplans-mac-long-retry-20261031-yezcui29/audit_completion.py
.venv/bin/python /private/tmp/bearplans-mac-long-retry-20261031-yezcui29/audit_restart.py
```

Completion audit verified the interval sum, excluded gaps, unchanged paused credit,
explicit Resume, original tree, one award, unchanged task, SQLite `integrity_check`
(`ok`), empty `foreign_key_check` and runtime digests matching observation start.
Two identical Finish requests using one operation ID preserved every substantive
database row. Original completion evidence preceded those retries and is retained.

Stopped the identified observer using Ctrl+C on its owned exec session 16554;
it stopped only its disposable backend at **14:58:55.252855 PDT** and saved final
evidence. Restart audit used the same disposable data with `OwnedService`, PID
13596, port 56624: all database rows and derived forest/shop/streak/statistics views
were identical before/after restart. All rows remained identical after graceful
stop. Runtime source unchanged. Listener checks found neither test port listening.

Final sanitized JSON, exact observer/audit scripts and synthetic screenshots are in
`.evidence/mac-verification-20261031/bearplans-mac-long-retry-20261031-yezcui29/`,
with `sha256.json`; no database copied into source/evidence. Normal service and
personal database untouched. No product source change, full-suite rerun, commit or
push. Scoped documentation links/whitespace and evidence manifest checked.
Remaining hardware/operator gates: actual battery/supported power modes, quantified
ten-minute precision and uninterrupted external long-run collection. M1's broader
operator review is separate; no M4 implementation started.

Final evidence manifest verification passed for **16 files**, with no database in
the evidence folder. Scoped whitespace/local Markdown links and `git diff --check
-- docs/PROGRESS.md` passed. `git diff --name-only -- backend frontend/src tools
launch.py` was empty. Post-run `pmset -g batt` still showed **AC Power / AC attached,
80%, not charging**; asked for actual battery-power confirmation before starting
the next coordinated sleep scenario. No battery test started.

## Fresh uninterrupted awake run

User explicitly requested **"continue the next 3 hours session tests"** after the
extended battery sleep observation. This is a new, separate 180-minute precision
run; earlier paused/slept attempts above remain historical evidence, not replaced.
Actual macOS 26.6.2 (25G83), arm64, build `d9b5f90`; battery 77% at verified start.

Prepared `/private/tmp/bearplans-mac-awake-10800-20261031-hgapoh5c/observe.py` from
the successful ten-minute observer. Updated title/scope and exact completion check
to 180 minutes, retaining no pre-start/unfinished/paused cleanup timeout. Added a
bounded owned keep-awake helper only after the operator's session is detected.
`ast.parse` passed. Exact preparation source/changes/digest retained; no application
code, rule/default/schema or personal data changed.

Exact observer command:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-awake-10800-20261031-hgapoh5c/observe.py
```

Owned backend **PID 18526**, loopback **61537**, observer exec **3621**. Visible UI
selected the synthetic task and **180 minutes**, Start enabled; agent did not start
it. Operator clicked Start and replied **"started"**. Saved start
**20:07:59.307065 PDT**, session `1a077402-516e-44d0-ba81-0c33d0aac525`;
expected uninterrupted finish **23:07:59.307065 PDT**. User asked to start a separate
stopwatch alongside it, report start separation, keep lid open and controls untouched,
then send exact final stopwatch reading/fractions and approximate stop delay.
External start offset is not yet quantified. No acceptance claim yet.

For this explicitly awake timing run, temporary helper **PID 18634** started at
**20:08:00.229426 PDT** using:

```sh
/usr/bin/caffeinate -i -d -t 11100 -w 18526
```

Local `man caffeinate` documents idle-system/display assertions, a timeout and
release when the waited-for process exits. `pmset -g assertions` confirmed both
**PreventUserIdleSystemSleep** and **PreventUserIdleDisplaySleep** for this owned
helper PID. Saved only its own rows in `start-verification.json`. The helper is
bounded to three hours plus five minutes and the owned backend lifetime; the
observer also terminates/waits for it during cleanup. No permanent power/clock
settings changed. These conditions are recorded as instrumentation; they do not
certify natural sleep behavior or guarantee uninterrupted eligibility. Actual sleep,
pause/review or restart still invalidates this precision observation.

Expected result: one closed interval **10,800,000,000 integer microseconds**, one
original mature Pine, one captured-rate **180-coin** award, unchanged incomplete
task; no sleep or unresolved interruption. Record external elapsed difference and
manual start/stop uncertainty separately. UI polling is present, so autonomous
expiry without API activity remains separate evidence. Same-host clock bounds
cannot replace the external stopwatch. No new long-run error tolerance invented.

Live sanitized evidence/source/setup/start verification:
`.evidence/mac-verification-20261031/bearplans-mac-awake-10800-20261031-hgapoh5c/`.
Tab marked for handoff. Normal service/data, existing edits/stashes/index untouched;
no app-suite rerun, commit or push. **Running / outcome pending.** Next: inspect
actual saved finish and external reading, stop only owned service/helper, verify
cleanup and final evidence manifest, then decide the observation result. Combined
M2/M3 remains not passed; separately unverified power states and manual timing
uncertainty remain explicit. M4/later not started.

## Final uninterrupted outcome

Operator reported **"it runs completely fine, 3:00:00s"**. The fresh run above
finished **23:07:59.270926 PDT**, October 31 (06:07:59.270926Z, November 1), from
**20:07:59.307065 PDT**. Session `1a077402-516e-44d0-ba81-0c33d0aac525`, outcome
`completed`, revision 2. One closed interval saved exactly **10,800,000,000 integer
microseconds**. No measured sleep, interruption or pause/recovery operations; the
only timer operation was Start. Observer `uninterrupted_eligible = true`.

The same original Pine `a720c929-347f-491d-a1ca-f8691be0756d` matured and finalized
with the session; one `session_award` credited **180 coins** at captured rate 1.
Task `55d34f9a-7719-4761-a1b5-df3b04c8ae0f` remains incomplete, revision 1,
unchanged created/updated instants. Statistics and October 31 streak credit both
exactly **10,800,000,000 microseconds**; **0/1** leaves complete, one qualifying day
and one-day streak. UI showed **Countdown completed · 3:00:00**, Mature Pine and
180 coins. `completed.png` retains that outcome. A stale browser handle was
unavailable; a fresh tab in the same in-app browser showed the saved service state.
No timer control was used during final inspection.

External reading reported **3:00:00**, or **10,800 seconds**, yielding raw observed
external-minus-saved difference **0 seconds at the reported whole-second
resolution**. Start offset and stop reaction delay were not separately quantified;
no subsecond accuracy, zero underlying clock error or reaction adjustment is
claimed. Same-host elapsed bounds **10,798.534890250–10,800.545390916 seconds**
corroborate the observation and do not replace the separate stopwatch. No new
long-run tolerance was invented. Wall timestamps span **10,799.963861 seconds**;
confirmed credit follows the awake clock rather than wall-clock subtraction.
Normal UI polling was present, so autonomous expiry without API activity remains
separate earlier evidence.

Read-only final audit command, exit **0**:

```sh
.venv/bin/python /private/tmp/bearplans-mac-awake-10800-20261031-hgapoh5c/audit_precision.py
```

All checks passed: exact completed duration/single interval, no observed sleep or
interruption, original mature tree, single captured-rate award, unchanged task,
exact statistics/streak totals, all database rows unchanged by API inspection,
SQLite `integrity_check = ok`, empty foreign-key check, source digests identical to
start. No new replay/restart test in this precision run; prior separate evidence
remains valid. Actual OS macOS 26.6.2 (25G83), arm64, runtime build `d9b5f90`.

Stopped only owned observer exec **3621** with Ctrl+C after review. Backend stopped
at **23:09:26.209590 PDT**, keep-awake helper released at **23:09:26.209554**.
Post-cleanup verification: no assertion rows for helper **18634**, no helper
process (`ps` no-match exit 1), no port **61537** listener (`lsof` no-match exit 1).
Battery was 77% at start; final review showed AC attached, 80%, not charging.
No permanent power/clock setting change. Exact cleanup verification retained.

Final sanitized report, exact observer/audit/preparation source, initial assertion
proof, operator reading, screenshots and cleanup JSON are retained under ignored
`.evidence/mac-verification-20261031/bearplans-mac-awake-10800-20261031-hgapoh5c/`.
Verified **12-file** SHA-256 manifest; no database included. Disposable data remains
outside the checkout. Normal service/data, existing edits/index/stashes unchanged.
No app implementation, app-suite rerun, commit or push. Scoped documentation
whitespace/local links checked.

**Pass for the observed uninterrupted three-hour match and saved-time behavior.**
This closes the actual long-run observation for the current build, with explicit
manual timing uncertainty. Combined M2/M3 remains not signed off: separately named
standby/hibernate entry is still unverified. Next: review the accumulated actual-Mac
evidence against the acceptance scope and resolve any supported/unverified mode
limits before milestone sign-off. M1's broader operator gate remains separate;
M4/later work has not started. No additional timer run automatically started.
