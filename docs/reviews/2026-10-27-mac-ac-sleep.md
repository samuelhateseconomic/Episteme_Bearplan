# Target-Mac AC sleep observation — October 27, 2026

Revision: `d9b5f90e10579d8687c4ffbd8e132a7121573ac1`. User selected starting the
five-minute sleep check. Existing staged/unstaged review-plan edits, progress/
status records and test-only date-fixture repair were inspected and preserved.
Runtime application source still matches HEAD; no implementation/default change.

Host: Mac15,9, macOS 26.6.2 (25G83), Darwin arm64; Python 3.13.15, Node 24.21.0.
AC attached, battery 80%, not charging before/after. Read-only power configuration:
standby 1, hibernatemode 3, powernap 1. Configuration does not prove those power
states occurred. Interface inspected in Codex's in-app browser; physical sleep
was initiated by the operator, not UI automation or a power-setting change.

Expected: awake browser closure keeps tracking; actual sleep pauses at the saved
checkpoint; maintenance/full wakes never resume automatically. Paused confirmed
time/tree/wallet/streak stay frozen. Explicit Resume retains the same session/tree
and excludes the gap; Finish saves confirmed work and an unfinished tree.

## Command and evidence

```sh
.venv/bin/python tools/m2_probe.py sleep --seconds 300 --output /private/tmp/bearplans-mac-sleep-20261027-i9ebndvr/sleep-ac.json
```

Ran with loopback access granted; stdout retained via `tee .../probe.log` and
shell pipefail. Exit **0**, report **pass**, failures empty. Probe used its own
temporary synthetic task/database/service at `http://127.0.0.1:57818/#track`.
No normal planner data was opened or migrated. Collection ran **285.351843 s**
(08:21:21.958964–08:26:07.310807 PDT), ending when the synthetic session finished;
300 s was its maximum collection window, not a completed five-minute countdown.
The synthetic countdown requested 180 minutes and was deliberately finished early.

Read-only commands: `sw_vers`, `uname -m`, `pmset -g batt`, `pmset -g custom`,
`sysctl -n hw.model`, and `pmset -g log`. Retained only log lines in the probe's
time window; no power, clock or wake configuration changed. Probe source SHA-256
maps at start/end match. User reported **"Lid reopened; timer untouched."**

Durable ignored evidence directory:
`.evidence/mac-verification-20261027/sleep-ac/` (sanitized JSON, environment,
filtered OS power events, summary, probe log, awake/paused/resumed snapshots and
screenshots). Temporary originals remain at the command's output directory.
The probe cleaned up its synthetic service/database; `lsof` afterward found no
listener on its port (normal no-match exit 1).

## Observations

- Closed the test page while awake: same running session gained **3.012881 s**
  across the three-second control. Reopened it before asking for physical sleep.
- OS event at **08:22:51 PDT**: Entering Sleep due to **Software Sleep pid=167**,
  AC power; log duration 27 s. **08:23:18**: DarkWake from Deep Idle; **08:23:46**:
  DarkWake to FullWake due to UserActivity Assertion. The operator reported a lid
  cycle, but OS classification is retained rather than relabeled as Clamshell Sleep.
- Service measured **25.278537 s** sleep; independent probe clock pair measured
  **25.277513959 s**. OS log seconds include coarse entry/wake latency and are not
  substituted for either clock measurement.
- Same session `fdb40711-bdb9-4c91-8065-ece0d65328ed` paused at **90.672367 s**.
  Checkpoint 08:22:52.968102; detection 08:23:18.536187. Probe captured **116 paused
  samples**, 08:23:18.825994–08:25:15.297731, each with that exact credit. This
  includes the observed DarkWake/maintenance period and later user wake.
- Separate ten-second API comparison: unchanged paused credit, identical Pine
  progress/identity, identical shop state and identical streak view. UI visibly
  said "Paused after sleep. Sleep time is excluded" and offered Resume.
- Agent explicitly clicked Resume at **08:25:15.838813**. Same session and tree
  `8f9a907d-f14f-42bd-a571-c4be09da88c2`; recovery resolved as resume. The probe
  recorded explicit resume and same-session finish, not automatic wake resumption.
- Agent clicked Finish early at **08:26:06.441915**. Final records: one finished-
  early session, two closed intervals, one resolved sleep interruption. Confirmed
  interval credits **90,672,367 + 50,603,595 = 141,275,962 microseconds**. No interval
  spans the excluded sleep/paused gap. UI showed **02:21**, **2 coins**, one
  **Unfinished Pine**, wallet 2 and saved daily progress below the hour threshold.
  Saved task remained available to track, consistent with separate completion.
  This run did not repeat Finish/replay; retry coverage remains the earlier suite's
  evidence and is not claimed anew here.

Inspected and retained [paused screen](../../.evidence/mac-verification-20261027/sleep-ac/after-wake-paused.png)
and [saved outcome](../../.evidence/mac-verification-20261027/sleep-ac/finished-after-explicit-resume.png).

## Decision and remaining gates

**Pass for this single AC sleep/maintenance-wake scenario.** This supplies real Mac
hardware evidence for that condition only. Combined M2/M3 acceptance is still
**not passed**: battery sleep, repeated/other supported standby/hibernate conditions,
external ten-minute timing and the real long-duration observation remain pending.
Do not infer hibernate or general lid-closed acceptance from Deep Idle/Software
Sleep labels. The broader M1 operator gate is separate. Existing automated Mac
results remain in the [sync review](2026-10-27-mac-sync-and-verification.md).

Next: coordinate battery sleep or external-stopwatch precision using the runbook.
No application code, personal data, power setting, normal service, stash, index,
commit or remote repository was changed by this observation. Only progress/review
and ignored synthetic evidence were added.
