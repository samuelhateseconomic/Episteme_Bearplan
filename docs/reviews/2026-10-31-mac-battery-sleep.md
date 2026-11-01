# Target-Mac battery clamshell sleep — October 31, 2026

**Pass for the observed battery sleep/pause and explicit recovery scenarios.**
The completed follow-up below supplies Resume/Finish/reward/restart evidence;
the first observation's historical limits are retained. Actual Mac15,9,
macOS 26.6.2 (25G83), Darwin arm64, Python 3.13.15; revision
`d9b5f90e10579d8687c4ffbd8e132a7121573ac1`. Combined M2/M3 acceptance remains
**not passed**. This is operator evidence, not a new implementation review.

User confirmed **"Battery power confirmed"**, then **"Lid reopened; timer
untouched"**. Before launch, `pmset -g batt` reported **Battery Power, 80%,
discharging**; filtered `ioreg -r -c AppleSmartBattery -l` fields independently
showed `ExternalConnected = No`, `IsCharging = No`, `CurrentCapacity = 80`.
Post-reply power remained battery, 79%, discharging. No power/clock settings changed.

Expected: closing the browser while awake keeps tracking. Real sleep pauses at
the trusted checkpoint; wake does not resume automatically. Confirmed credit stays
frozen. Explicit Resume/Finish, if performed, must preserve session/tree and exclude
the gap. Only fresh synthetic records are affected; no rule/default changes.

## Command and evidence

```sh
set -o pipefail
.venv/bin/python -u tools/m2_probe.py sleep --seconds 300 --output /var/folders/wk/3yfnwgrx2qdbvr75y1kcqrx00000gn/T/bearplans-mac-battery-20261031-ng64tsz6/sleep-battery.json | tee /var/folders/wk/3yfnwgrx2qdbvr75y1kcqrx00000gn/T/bearplans-mac-battery-20261031-ng64tsz6/probe.log
```

Exit **0**, report `pass`, failures empty. Owned disposable service at
`http://127.0.0.1:56967/#track`; collection **15:24:32.780781–15:29:33.340240 PDT**.
The 300 seconds are an observation window, not five saved countdown minutes. The
probe starts a synthetic 180-minute countdown, observes it, stops only its own
backend and removes its temporary database when collection ends.

Durable ignored evidence:
`.evidence/mac-verification-20261031/sleep-battery/` contains the sanitized probe
report/log, exact probe source, preflight power, initial API views, awake closure
control, before-sleep screenshot, summary, filtered OS power events and SHA-256
manifest. No database included. Runtime source digest maps at start/end match.

## Observed behavior

- Closed the disposable tab while awake. Across the three-second API control the
  same running session gained **3.011637 seconds**. Reopened it before the lid test.
- Session `9b0f608f-ffe3-42c2-b706-a3f7a1c47f7c` started at **15:24:33.016707 PDT**.
  Last trusted checkpoint **15:25:26.220162** closed its single interval with
  **53,203,405 microseconds**. No further active credit was awarded.
- `pmset -g log` corroborates **Clamshell Sleep** at **15:25:24**, **Using Batt,
  Charge 80%**, coarse duration 68 seconds; **Wake from Deep Idle** at **15:26:32**,
  lid/HID activity, **Using BATT, Charge 80%**. Only matching Sleep/Wake event lines
  inside the test/reply window were retained.
- Probe clocks measured **66.267150375 seconds** of sleep. Persisted sleep record
  measured **66,267,156 microseconds**, detected at **15:26:32.818931**. OS log
  seconds include entry/wake latency and do not replace clock measurements.
- **179 paused samples**, **15:26:33.102127–15:29:33.022916**, all retained exactly
  **53.203405 active seconds**, same session, revision 2. No automatic wake resume.
  Final session remained paused; interruption remained unresolved; one closed
  interval summed exactly to confirmed session credit. No finished outcome claimed.

## Limits and follow-ups

The operator reply arrived after the five-minute window had ended. The normal
probe cleanup had stopped the owned service and removed its temporary database.
A subsequent read of its API therefore returned connection refused. This is the
test lifecycle, not evidence of a product crash. The final probe JSON already
retained the paused session, interval and interruption evidence above.

No post-wake UI inspection, separate tree/wallet/streak freeze comparison, explicit
Resume or Finish was performed in this battery run. Those behaviors have separate
AC/long-run/restart evidence; they are not relabeled as battery evidence. This
single clamshell/Deep Idle observation does not certify standby/hibernate or all
maintenance-wake/power configurations. A repeat needing post-wake UI work should
retain its disposable service until operator review completes.

Initial preflight under the restricted shell failed its assertion before service
launch because battery-registry fields were unavailable there. Rechecked with
host access, saved only the three required battery fields and passed preflight;
no application failure or power transition was inferred from the restricted read.

No application code, normal service, personal data, index, stash, commit or remote
change. No application-suite rerun. Evidence manifest, scoped Markdown links and
whitespace checks passed. Remaining gates: supported standby/hibernate/repeated
conditions, quantified ten-minute and uninterrupted long-run precision; battery
Resume/Finish/reward comparison is a follow-up. M1 operator acceptance remains
separate; M4 has not started.

## Recovery follow-up preparation

User requested **"continue"**. Current `pmset -g batt` and filtered battery registry
reported **AC Power, 80%, ExternalConnected = Yes, IsCharging = No**. Asked for
actual battery-power confirmation, keeping lid open; AC is an explicit alternative
but cannot count as battery evidence. No new service/countdown started.

Prepared `/private/tmp/bearplans-mac-battery-recovery-20261031-gi2z279y/observe.py`
from the previously verified long-run observer. It keeps collecting through paused/
review states with no unfinished-session timeout, and retains the disposable data.
The only adaptations are synthetic task title, scope/docstring and final result
label (`finished_pending_record_audit`), avoiding a three-hour precision claim.
`ast.parse` passed. Exact preparation metadata is retained beside the script.

Acceptance scenario: while confirmed on battery, actual sleep leaves the same
session/tree paused; an independent paused wait changes no credit, growth, wallet
or streak. Explicit Resume keeps that identity and excludes the gap; Finish saves
confirmed intervals, one unfinished tree and one captured-rate award, without task
completion. Replay/restart preserve the saved result. No new application rules,
defaults, schema or personal records; the disposable test can be stopped explicitly.
Awaiting operator power-source choice before launch; this is preparation only.

## Completed battery recovery follow-up

Operator again confirmed **"Battery power confirmed"**. Before start, host reads
showed **Battery Power, 80%, discharging, ExternalConnected = No, IsCharging = No**;
power remained battery after wake and the final audit. Same Mac/build as above.
No product rule/default/schema change. A fresh owned service at loopback port
**58657**, PID **16011**, used only the prepared disposable data directory.

Exact observer command:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-battery-recovery-20261031-gi2z279y/observe.py
```

The agent started synthetic task `acbc34a9-fa36-4b59-89d7-271462525e68` through
`POST /api/timer/start` with a fresh operation UUID and 180 minutes. This is an
early-finish sleep test, not a three-hour timing claim. Session
`519236f8-b80c-4939-a861-db6f7b1a36f1` started **16:27:23.021782 PDT**; original Pine
`16330f37-bbb3-4bf7-88b4-3d7d80538d35`. Operator was asked to close the lid briefly
and leave controls untouched, then reported **"Lid reopened; timer untouched"**.

OS `pmset -g log` records **Clamshell Sleep** at **16:27:50**, **Using Batt (80%)**,
coarse duration 139 seconds, then **Wake from Deep Idle**, lid/HID activity,
**Using BATT (80%)** at **16:30:09**. Probe measured **136.056643625 seconds** sleep;
persisted interruption measured **136,056,641 microseconds**. The coarse OS event
includes entry/wake latency and does not replace clock measurements. No separately
observed DarkWake/hibernate state is inferred.

Last trusted checkpoint **16:27:52.549552**, credit **29,526,489 microseconds**;
sleep detection **16:30:09.612587** left it paused, revision 2. **37 paused observer
samples** retained identical credit. At **16:30:25 UTC−07:00**, separate API views
and another comparison after ten seconds preserved the entire session/tree object,
forest, shop and streak view exactly. UI said **Paused after sleep. Sleep time is
excluded. Resume when you are ready.** Screenshot retained as `after-wake-paused.png`.

Agent explicitly clicked UI **Resume** at **16:30:46.534938 PDT**. Persisted Resume
operation resolved the same sleep interruption, retaining session/tree. The full
**173.985386-second** checkpoint-to-Resume gap earned no time. Agent then clicked
**Finish early**, saving at **16:31:25.882293**:

- Two closed interval credits **29,526,489 + 39,347,148 = 68,873,637 microseconds**.
- Same original Pine, outcome **unfinished**, finalized with the session.
- Exactly one `session_award` of **1 coin**, from whole confirmed minutes at the
  captured rate of 1; no pause/sleep/review award.
- Task remained incomplete, revision 1, with unchanged created/updated instants.
- Statistics and October 31 streak credit both exactly **68,873,637 microseconds**,
  **0/1** leaf tasks complete, zero-day streak and no qualified day.

UI showed **Finished early · 01:08**, **Earned 1 coin**, **Unfinished Pine**;
`finished.png` retains that outcome. No resumed or elapsed wall gap was credited.

Exact audit commands, both exit **0**:

```sh
.venv/bin/python /private/tmp/bearplans-mac-battery-recovery-20261031-gi2z279y/audit_saved.py
.venv/bin/python /private/tmp/bearplans-mac-battery-recovery-20261031-gi2z279y/audit_restart.py
```

Saved audit checked the interval sum, identity, explicit resolution/excluded gap,
captured-rate award, unchanged task, source digests, SQLite `integrity_check = ok`
and empty foreign-key check. Two identical Finish requests with one operation ID
preserved every substantive database row. Stopped owned observer exec **45649**
with Ctrl+C at **16:31:55.096189 PDT**; exact report/source persisted before cleanup.
Separate `OwnedService` restart used the same disposable database, PID **16219**,
port **58934**. Every database row and forest/shop/streak/statistics view matched
before/after restart, with every row still identical after graceful stop. Both
ports returned normal no-listener `lsof` exit 1. Normal service/data untouched.

Final evidence is under ignored
`.evidence/mac-verification-20261031/bearplans-mac-battery-recovery-20261031-gi2z279y/`:
exact observer/audit sources, start/wake/paused/resumed/saved/restart JSON, scoped OS
events and UI screenshots. Verified SHA-256 manifest covers **19 files**; no database
included. Runtime source unchanged, no application-suite rerun, commit or push.
Scoped documentation whitespace/local links passed.

**Pass for this actual battery clamshell sleep, freeze, explicit recovery, early
finish, rewards, replay and restart scenario.** This completes the battery
Resume/Finish/reward comparison follow-up for the observed condition. Combined
M2/M3 remains not passed: supported standby/hibernate/maintenance-wake conditions
and quantified external precision remain separate. No general power-mode or
uninterrupted precision certification follows from this observation.
