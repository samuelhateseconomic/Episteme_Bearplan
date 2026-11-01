# Distinct sleep-mode test preparation — November 1, 2026

**Pass for actual controlled Hibernate recovery. Original power settings fully
restored and helper/service stopped. Separate Standby type 5 remains unverified.** User explicitly requested
"go ahead and test the distinct standby", resuming the previously deferred scope.
Initial preparation completed read-only inspection and a concrete controlled-
hibernation proposal without launching a countdown or changing settings. Approved
execution and its final outcome are recorded below; preparation was not a pass.

Actual Mac15,9, macOS 26.6.2 (25G83), arm64. Read `pmset -g batt`, `pmset -g cap`,
`pmset -g custom`, selected IOPMrootDomain registry keys, and exact-category
Sleep/Wake/DarkWake logs for November 1. At **16:57:38.892917Z / 08:57:38 PST**:
battery 77%, discharging; standby 1, hibernatemode 3 in both battery/AC profiles.
Registry **IOPMSystemSleepType = 7**; 62 wakes from Deep Idle, zero from Standby
or Hibernate, no distinct transition recorded. Retained only selected fields and
aggregate/named state evidence in ignored
`.evidence/mac-verification-20261101/distinct-standby-preflight/inspection.json`.

Apple's [sleep-type definitions](https://github.com/apple-oss-distributions/xnu/blob/main/iokit/IOKit/pwr_mgt/IOPMPrivate.h)
identify Hibernate 4, Standby 5 and Deep Idle 7 separately. Its
[pmset manual](https://github.com/apple-oss-distributions/PowerManagement/blob/main/pmset/pmset.1)
and the installed `man pmset` describe hibernatemode 25 as saving memory to disk,
removing memory power and restoring from the image, with slower sleep/wake.
This is a documented hibernation setting, not proof that this particular machine
will enter a desired state, and a Hibernate observation cannot certify Standby 5.

The [verification runbook](../MAC_CORE_VERIFICATION.md) says:

> Do not change system power or clock configuration just to make a probe pass.

Another unchanged lid cycle could repeat the already-passed Deep Idle scenario.
The alternative controlled-hibernation experiment would deliberately depart from
that runbook restriction, so explicit user approval of the power-setting change
is needed before proceeding. This is a scope interpretation, not a claim that the
runbook itself prescribes an approval dialog. Existing authorization covers the
read-only inspection and disposable preparation; no blanket permission for global
power changes is inferred.

## Prepared, reviewable procedure

Prepared observer:
`/private/tmp/bearplans-mac-controlled-hibernate-20261101-_wjz84hq/observe.py`.
Reuses the completed indefinite overnight observer; changes scenario labels and
captures only IOPMSystemSleepType on state changes/measured sleep gaps. Syntax
checked with `ast.parse`; digest, exact proposed commands and validation scope
are in `proposal.json`. **Not launched.** No normal database is involved.

Proposed actions, only if explicitly approved:

1. Recheck battery and snapshot complete current power settings. Prepare the
   disposable countdown/UI before changing policy; user saves work in other apps.
2. Temporarily set only battery hibernation policy, leaving AC policy and other
   preferences unchanged:
   `sudo /usr/bin/pmset -b hibernatemode 25`.
   Administrator authorization may need to be entered by the user locally.
3. Verify the actual setting, start the disposable countdown, then coordinate a
   brief user-initiated lid sleep and return. Classify actual registry and OS-event
   evidence. An ignored setting or Deep Idle result remains unverified.
4. Restore the original battery value with
   `sudo /usr/bin/pmset -b hibernatemode 3`, and compare settings to the original
   snapshot before ending the test. A restore failure is unfinished work, not
   successful cleanup. Keep the exact recovery command available to the operator.
5. Verify paused/review stability, explicit same-session/tree recovery and saved
   confirmed intervals/rewards once, then stop only owned test processes.

This is a hibernation candidate procedure. There is no verified deterministic
procedure here for entering the separate Standby 5 state on this Mac. No draining
the battery, Lockdown/FileVault change, reboot, provider download or setting of
unverified standby-delay keys is proposed.

Guidance/progress, planning/runbook, current reviews and working/index state were
inspected; application source and prior user edits/index/stashes preserved. No
application tests rerun for this external observer/preparation-only work; local
Markdown links/whitespace and observer syntax checked. No commit or push. Next
action is the explicit power-policy scope decision, before any setting mutation.

## Approval and local-authentication preparation

User explicitly selected **"Approve temporary hibernation test"**. This overrides
the runbook restriction for the scoped battery-only mode 3 → 25 → 3 experiment.
No further permission prompt is required for those authorized actions.

Rechecked Battery Power 77%, ExternalConnected No, IsCharging No, both profiles
mode 3. Full `pmset -g custom` snapshot and parsed per-profile values saved as
`settings-before.json` before any change. `sudo -n /usr/bin/true` returned exit 1,
**"sudo: a password is required"**. This is missing local administrator
authentication, not automatic approval rejection; no privileged command ran.
The operator must enter their password locally, never into chat.

Prepared `power_mode_guard.py` in the temporary root above. It uses only standard
Python modules and fixed `/usr/bin/pmset` commands. It revalidates battery power
and original mode 3, applies/verifies battery mode 25, then waits interactively.
Return after wake, Ctrl+C or handled termination runs `finally` to restore/verify
3. There is also a 900-second select timeout; while the Mac is suspended the helper
cannot execute, so timeout cleanup runs once it can execute. A force-kill/power
loss or failed restoration still needs the printed recovery command; do not
claim unconditional cleanup. The recovery command is
`sudo /usr/bin/pmset -b hibernatemode 3`.

Guard syntax passed. Injected-callback checks passed for operator Return, timeout,
interrupt, partial-setting failure and parsing the actual before snapshot.
**These checks did not call pmset or change real settings**; their printed mode
messages are simulated callback output. Results retained in `guard-checks.json`.

Launched only the disposable observer/service:
owned observer exec **55621**, backend PID **27826**, URL
**http://127.0.0.1:57136/#track**, prepared **2026-11-01T17:03:39.785011Z**.
Synthetic incomplete task selected, Pine and 180 minutes set in UI; **countdown
not started**. `ready.png` retained, tab marked for handoff. Observer continuously
retains synthetic JSON/source evidence under
`.evidence/mac-verification-20261101/bearplans-mac-controlled-hibernate-20261101-_wjz84hq/`.

Next operator action: open a new Terminal tab and run the guard with sudo using
the repository's Python. Keep the lid open and report **MODE 25 SET**. Agent then
verifies actual settings and starts the countdown before giving the lid-close
instruction. After the brief sleep, the operator presses Return in that same
Terminal to restore 3, and returns to chat. Verify the complete settings snapshot
matches afterward before declaring the experiment cleaned up. Normal data/service
and all application source remain untouched; no full-suite rerun, commit or push.

## Verified mode change and running countdown

User reported **MODE 25 SET** after running the interactive sudo helper locally.
Read-only verification at **2026-11-01T17:07:27.565106Z / 09:07:27 PST** compared
every parsed key/profile to `settings-before.json`. Exactly one difference:
**Battery Power / hibernatemode / 3 → 25**. AC remains mode 3; all other settings
match. Battery 76%, discharging. Exact settings/diff retained in
`mode25-verification.json`. The helper remains open for Return after wake and its
900-second fallback; do not treat restoration as complete until host verification.

An old browser handle could not read the page; a fresh tab on the same owned
service worked. Selected the synthetic incomplete task, Pine and 180 minutes;
UI Start countdown at **17:07:47.640410Z / 09:07:47.640410 PST**. SQLite confirms
Running, revision 1, session `0d5f2174-4a7d-41ad-b674-b35a47c3b05c`, original Pine
`7299af4a-cba5-4967-8c3a-40868bc662a0`. `start-verification.json` and `running.png`
saved; fresh test tab marked for handoff. Owned observer exec 55621/backend PID
27826/port 57136 remain running.

Operator instructed to close the lid **3–5 minutes**, remain unplugged, leave
timer controls untouched, then reopen and press Return in the same helper Terminal
to restore mode 3 before reporting here. Actual Hibernate/Standby still requires
OS/registry evidence; mode 25 configuration alone is not a pass. Next: verify
complete settings restoration first, inspect observed state and paused records,
then explicitly recover/save and clean up the owned test.

## Actual Hibernate observation and verified completion

Operator returned **"Lid reopened; MODE 3 RESTORED"**. Actual OS events establish
Clamshell Sleep **09:09:03 PST** and **Wake from Hibernate** at **10:47:49 PST**,
November 1: **5,926 seconds / 1h38m46s**, longer than the requested 3–5 minutes.
The collector stayed available throughout; the duration is taken from logs rather
than inferred from the requested window. At the first post-gap registry sample
and a separate host query, **IOPMSystemSleepType = 4**. Before sleep it was 7.
This is actual Hibernate evidence, distinct from the previous Deep Idle results.
One Sleep, one Wake and one HibernateStats event; recorded power source battery.
Source: `power-events.txt`, `power-summary.json`, observer power-state samples.

Independent observer measured **5,902.212179083 s** sleep; the service's first
persisted sleep interruption measured **5,902,193,511 µs**. OS event span includes
entry/wake latency and is not substituted for measured suspended time. The
service paused at trusted checkpoint **17:09:04.879987Z / 09:09:04.879987 PST**,
**77,248,820 µs**, and never resumed automatically. All **235** paused samples
retained that credit, **18:47:50.405102Z → 18:51:46.164875Z**. Full paused
session/tree, forest, shop and streak views also stayed identical over a separate
ten-second comparison; wallet and coin ledger stayed zero/empty.

### Restoration discrepancy and cleanup

Despite the initial operator report, host verification at **18:48:42.830357Z**
still showed battery mode 25. Saved the failed verification rather than claiming
cleanup. `sudo -n pmset -b hibernatemode 3` could not authenticate (password
required). No automatic approval review rejected that command; it lacked a local
sudo credential. Asked the operator to run the already-authorized restoration
command in Terminal. After **"Restore command finished"**, two host snapshots
five seconds apart matched **every original battery/AC key**, including mode 3.
The initial discrepancy's cause was not established; it is not attributed to a
BearPlans timer defect or represented as a successful first restoration.

Known helper processes were still present: sudo wrappers 27912/27914 and Python
27915. Computer-use access to Terminal was blocked for safety, so no UI bypass
was attempted. Operator closed the original helper with Control+C and reported
the normal prompt. At **18:52:16.463590Z / 10:52:16 PST**, host verification
confirmed **no matching helper process** and **all settings still identical to
the original snapshot**. `settings-restored-verification.json` retains the
initial failed check; `settings-restored-final.json` and `guard-cleanup-final.json`
retain successful correction and final cleanup. No temporary mode remains.

### Explicit recovery and saved records

After settings restoration, agent UI Resume at **18:51:46.692206Z / 10:51:46 PST**
kept the same session/Pine and excluded the complete **6,161.812219-second**
checkpoint gap, including the post-wake waiting period. UI Finish early at
**18:52:05.705199Z / 10:52:05 PST** saved exactly **96,262,134 µs** across two
closed intervals: **77,248,820 + 19,013,314 µs**. Same original unfinished Pine,
one initial **1-coin** award at captured rate 1, task unchanged/incomplete revision
1. Screens `after-hibernate-paused.png` and `finished.png` retained.

Audit command, exit 0:

```sh
.venv/bin/python /private/tmp/bearplans-mac-controlled-hibernate-20261101-_wjz84hq/audit_saved.py
```

All nine checks passed: original session/tree, exact closed interval sum, explicit
sleep-gap exclusion, one captured-rate award, unchanged task, unchanged runtime
digests, integrity `ok`/empty foreign-key check, and two identical Finish requests
preserving all substantive records. Separate checks confirmed exact statistics/
streak **96,262,134 µs**, wallet 1 and one forest tree. Original baseline is
`start-verification.json`; saved audit and `completion-summary.json` retain exact
rows and calculations. No new restart or precision test is claimed.

Stopped only observer exec **55621** with Ctrl+C; owned backend stopped at
**18:52:44.432906Z / 10:52:44 PST**. Fresh inspection tab closed. Exact observer,
guard/source checks, original/changed/restored settings, filtered OS events,
saved/replay audit and screenshots retained under the evidence folder above.
Verified **24-file SHA-256 manifest**; no database included. All data synthetic;
normal user service/data, existing edits/index/stashes preserved. No app source
change, full-suite rerun, commit or push. Scoped documentation links/whitespace
checked.

**Pass for actual hibernation sleep detection, paused credit/growth/rewards and
explicit recovery/save/replay on this target Mac.** The test used the specifically
approved temporary mode change, with the restoration follow-up resolved and
verified. It does not certify the separately named Standby type 5. No automatic
repeat of that unobserved condition is scheduled. Existing offline backup/restore
operator pass stands; next is the final planner/trial-readiness review. Candidate
freeze, seven-day trial and full release acceptance remain separate.
