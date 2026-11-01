# Target-Mac extended natural sleep observation — October 31, 2026

**Pass for observed extended battery clamshell/Deep Idle maintenance-wake and
explicit recovery behavior. Separately named standby/hibernate remains unverified.**
User explicitly requested longer sleep/
power-mode checks. Actual macOS 26.6.2 (25G83), arm64, revision
`d9b5f90e10579d8687c4ffbd8e132a7121573ac1`. Existing local work preserved.

Preflight `pmset -g batt` showed **Battery Power, 80%, discharging**; limited battery
registry fields independently showed **ExternalConnected = No, IsCharging = No**.
Read-only `pmset -g custom` showed standby 1, hibernatemode 3 and powernap 1.
`pmset -g cap` listed standby/hibernatemode-related capabilities. These are recorded
configuration/capability statements, not proof of entry into a deeper power state.
No power/clock configuration, sleep command or system assertion was changed.

Expected: actual sleep pauses at the last trusted checkpoint; maintenance wakes,
repeated sleeps and full wake never resume automatically. Same session/tree and
confirmed credit remain frozen until explicit recovery. After operator return,
compare timer/tree/wallet/streak during a paused wait, then explicitly Resume and
Finish, auditing confirmed intervals, one original unfinished tree, captured-rate
award and unchanged task. Only synthetic data is affected; no rule/default change.

## Instrument and operator procedure

Disposable root:
`/private/tmp/bearplans-mac-extended-sleep-20261031-3_4ks6it/`.
Exact command:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-extended-sleep-20261031-3_4ks6it/observe.py
```

The previously behavior-checked observer was adapted only in title/scope/docstring
and removal of the pre-start timeout. `ast.parse` passed. It reads SQLite and
awake/continuous clocks once a second, records state changes, and atomically saves
synthetic evidence about every ten seconds. It does not initiate power transitions
or resume tracking. It retains unfinished/paused services until explicit stop;
after finish it retains the service for 30 minutes. No five-minute cleanup.

Owned backend **PID 17648**, loopback **http://127.0.0.1:59917/#track**, observer
exec **27174**. Agent started a fresh synthetic 180-minute countdown via the API
at **16:51:40.809194 PDT**. This duration supplies headroom for the sleep/recovery
exercise; it is not another three-hour precision run. Session
`c2494adb-cd51-479a-84d5-91c886406e7a`, Pine
`718ec299-fdbb-45aa-81dd-3a9a40be153b`. Initial API snapshots and power source saved
in `started.json`, preflight/configuration in `preflight.json`. UI confirmed Running;
`before-sleep.png` retained, tab marked for handoff.

Asked operator to close the lid for **at least 30 minutes**, or overnight if more
convenient, keep the Mac unplugged, leave controls untouched, then report reopening
and approximate closed duration. No final timer/reward action before inspecting
actual post-wake state. The 30 minutes are a proposed initial observation window,
not a guaranteed standby/hibernate transition time.

After return, collect only OS sleep/wake event lines inside the observation window.
Report exactly which states occurred, including maintenance wakes if recorded.
Do not label a missing hibernate event a product failure or a hibernate pass.
Unsupported or unobserved states remain explicitly unverified.

Live sanitized evidence:
`.evidence/mac-verification-20261031/bearplans-mac-extended-sleep-20261031-3_4ks6it/`.
No database copied into evidence/source. Runtime source hashes are retained at
start/current. Normal service/data untouched. No app change, suite rerun, commit or
push. Combined M2/M3 remains not passed; uninterrupted long-run precision and the
manual ten-minute timing uncertainty caveat remain separate. Next: inspect saved
observation and actual power events after operator return, then audit recovery.

## Completed observation and recovery

Operator reported **"It has been stayed close for few hours"**. Same actual Mac,
runtime revision unchanged. Initial battery 80%; after return 79%, still discharging.
OS logs identify first **Clamshell Sleep at 16:53:16 PDT** and final **lid/HID Wake
from Deep Idle at 19:45:25 PDT**, October 31: a **2h 52m 09s** observed window.
All retained event lines report battery power. The observer's cumulative measured
sleep was **9,659.759553245 seconds** (2h 40m 59.759553245s), across **49 sampled
sleep gaps over 0.1 seconds**. The remaining time includes maintenance wake work;
it is not user work or extra timer credit.

Scoped `pmset -g log` records contain **55 Sleep-category entries**, **51 DarkWake
events**, and **4 Wake-category entries**. Sleep entries include transitions into
DarkWake, so this is an event count, not 55 independently measured suspends.
DarkWake events report **Deep Idle**, with Sleep Service/maintenance/other wake
reasons. Three FullWake transitions due to notifications preceded the final
lid/HID user wake. Repeated maintenance sleeps/wakes and notification FullWakes
did not resume tracking. Exact scoped event lines are in `power-events.txt`.

An additional scan of **all timestamped** log categories inside the window found
**55 HibernateStats lines**, retained in `hibernate-standby-lines.txt`. They report
`hibmode=3 standbydelaylow=0 standbydelayhigh=0`. No separately named Sleep/Wake
standby or hibernate entry/resume was established. Preserve these configuration/
statistics rows without treating them as proof of deeper-state entry. This is not
a hibernate failure or a general hibernate acceptance pass.

First trusted interval ended **16:53:17.904528 PDT** with **97,094,856 microseconds**.
The first maintenance wake detected sleep at **17:09:20.114250**; persisted sleep
record measured **961,721,994 microseconds** for that first detection. It records
the initial interruption, not the cumulative multi-hour sleep reported by the
independent observer. All later sleep/awake gaps remained excluded because the
session stayed paused. **804 paused observer samples**, **17:09:20.700120–
19:47:50.545599**, retained the identical confirmed credit.

After operator return, API reads confirmed the original session/tree paused, wallet
zero, no award. A separate ten-second comparison preserved the **entire paused
session/tree object**, forest, shop and streak views exactly. UI visibly said
**Paused after sleep. Sleep time is excluded. Resume when you are ready.**
`after-wake-paused.png` retains that state. A stale browser handle was unavailable;
a fresh tab in the same in-app browser displayed the actual service state.

Agent explicitly clicked **Resume** at **19:47:50.603969 PDT**; persisted resolution
is `resume`, same session/Pine. Full checkpoint-to-Resume gap **10,472.699441 seconds**
excluded, including all maintenance/full wakes and post-return waiting. Agent then
clicked **Finish early**, saved at **19:48:14.414483 PDT**:

- Closed interval credits **97,094,856 + 23,810,264 = 120,905,120 microseconds**.
- Same original Pine, outcome **unfinished**, finalized with the session.
- One award **2 coins**, computed from two whole confirmed minutes at captured rate
  1; no sleep/paused/maintenance time awarded.
- Task remained incomplete, revision 1, unchanged created/updated instants.
- Statistics report exactly **120,905,120 microseconds**, **0/1** leaves complete;
  streak remains below the hour threshold.

UI shows **Finished early · 02:00**, **Earned 2 coins**, **Unfinished Pine**;
`finished.png` retains that outcome. Read-only views and saved records agree.

Exact final audit command, exit **0**:

```sh
.venv/bin/python /private/tmp/bearplans-mac-extended-sleep-20261031-3_4ks6it/audit_saved.py
```

The audit checked interval sums, identity, explicit resolution/gap exclusion,
captured-rate award, unchanged task, SQLite `integrity_check = ok`, empty FK check
and source digests matching observation start. Two identical Finish requests with
one operation ID preserved all substantive database rows. No new restart test in
this scenario; earlier battery/long-run restart evidence remains separate.

Stopped the identified observer exec **27174** with Ctrl+C; owned backend stopped
at **19:49:05.144214 PDT**. Listener check on port **59917** returned normal no-match
exit 1. Temporary synthetic data remains outside the checkout. Final sanitized
JSON, exact observer/audit source, both scoped OS-event files and screenshots are in
`.evidence/mac-verification-20261031/bearplans-mac-extended-sleep-20261031-3_4ks6it/`,
verified **18-file** SHA-256 manifest, no database included. No personal data/service,
application code, index, stash, commit or remote change. No app-suite rerun. Scoped
documentation whitespace/local links checked.

Auxiliary event-classification validation initially matched the word DarkWake
inside Sleep-category lines and failed its Deep Idle assertion. Narrowed the
helper to the actual DarkWake event category: all 51 such events report Deep Idle,
three notification FullWakes confirmed, exact streak total confirmed. Corrected
checks pass in `classification-check.json`; no product failure or count change.

**Pass for this observed extended sleep/maintenance-wake/recovery scenario.** It
provides actual multi-hour battery and repeated maintenance/notification-wake
evidence. Distinct standby/hibernate entry remains unverified; configuration alone
cannot certify it. Combined M2/M3 is still not passed: uninterrupted external
long-run precision remains open, with ten-minute manual timing uncertainty retained.
Next: coordinate that long-run timing observation and review any distinct supported
power-mode evidence still needed, without forcing settings or assuming a longer
lid interval guarantees a different state. M4/later work has not started.
