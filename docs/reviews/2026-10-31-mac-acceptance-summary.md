# Combined target-Mac evidence review — October 31, 2026

**Pass with follow-ups for the completed scenarios; combined M2/M3 gate remains
not passed because distinct supported standby/hibernate recovery is unverified.**
No observed product failure is identified by this evidence review. Missing state
evidence is not a failed timer calculation. This review consolidates evidence;
[PROGRESS.md](../PROGRESS.md) remains the work/handoff record.

Reviewed build `d9b5f90e10579d8687c4ffbd8e132a7121573ac1`, actual target
**Mac15,9, macOS 26.6.2 (25G83), Darwin 25.6.0 arm64**. Python 3.13.15,
Node 24.21.0 are recorded in the original execution reviews. Service timezone was
system local, America/Los_Angeles (PDT during these observations). Review performed
about 23:15–23:20 PDT October 31; UTC timestamps fall on November 1.

## Acceptance evidence

| Scenario | Result and evidence | Limit |
| --- | --- | --- |
| Fixed build, production interface and full Mac regression suite | [October 27 verification](2026-10-27-mac-sync-and-verification.md): 756 Python cases passed, one Windows-only skip; 136 frontend cases passed; build/TypeScript and dependency check passed. | Historical execution results, not a new suite run. Local test-only date-fixture repair is uncommitted; runtime source matches the reviewed build. |
| Awake browser closure and autonomous expiry | [October 30 workflow](2026-10-30-mac-workflow.md): browser closed, no timer API calls until SQLite independently showed completed; exactly 60,000,000 µs, original mature Pine, one coin, task unchanged. | One-minute autonomous-expiry case. Ten-minute and three-hour observations had normal UI polling; they do not independently prove expiry without API activity at those lengths. |
| AC sleep, maintenance wake, frozen credit and explicit recovery | [AC sleep](2026-10-27-mac-ac-sleep.md): 25.278537 s measured sleep; 116 unchanged paused samples; explicit Resume; 141.275962 s saved, unfinished Pine, two coins. | OS classified entry as Software Sleep. No separate standby/hibernate claim. |
| Battery clamshell sleep and recovery through restart | [Battery follow-up](2026-10-31-mac-battery-sleep.md#completed-battery-recovery-follow-up): actual battery power, Clamshell Sleep/Deep Idle wake, 136.056643625 s measured sleep, explicit Resume, 68.873637 s saved, one coin. Finish replay and graceful restart preserved saved records/views. | Battery source verified before/after; no inferred deeper state. Earlier collection with premature cleanup supplies only its narrower recorded evidence. |
| Extended battery sleep and repeated maintenance/notification wakes | [Extended sleep](2026-10-31-mac-extended-sleep.md#completed-observation-and-recovery): 2h52m09s lid window, 9,659.759553245 s measured sleep, 51 DarkWake and four Wake events; 804 unchanged paused samples. Explicit Resume excluded the full gap; 120.905120 s saved, original unfinished Pine, two coins. | Lid duration is not sleep-only time. HibernateStats configuration rows do not establish distinct hibernate/standby entry or restoration. |
| Crash, review, explicit continuation and paused restart | [Recovery](2026-10-31-mac-recovery.md): killed only the identified disposable backend; Needs review preserved 17.134672 s. Explicit continuation, pause and restart preserved identity/credit; final 21.023345 s, unfinished Pine, one zero award. | Actual process interruption; no claim of an OS-clock change. |
| Ten-minute independent stopwatch comparison | [Precision](2026-10-31-mac-precision.md#completed-run-and-external-comparison): exact 600,000,000 µs, original mature Pine, ten coins; operator explicitly clarified 600.20 s. Observed difference +0.20 s, within the proposed two-second target. | Start separation and stop reaction were not quantified. Retain this measurement uncertainty; do not invent a stricter new acceptance threshold or claim bounded subsecond accuracy. |
| Uninterrupted three-hour independent comparison | [Final long run](2026-10-31-mac-long-duration.md#final-uninterrupted-outcome): exact 10,800,000,000 µs, one interval, no sleep/interruption/pause; original mature Pine, one 180-coin award, task unchanged. Operator reported 3:00:00. | Zero observed difference at whole-second resolution. Manual offsets unquantified. Temporary keep-awake helper was released and owned service stopped. Earlier paused/interrupted attempts are not used as uninterrupted evidence. |
| Joined rewards, corrections, statistics and persistence | [Operator workflow](2026-10-30-mac-workflow.md): one-minute reduction/restoration, -1/+1 adjustments, same tree, unchanged initial award/task, exact reports, retry/restart persistence. [Full Mac suite](2026-10-27-mac-sync-and-verification.md) includes purchase, negative balance, retained ownership and reviewed reversal. | Automated fixture and agent-operated UI evidence are identified separately; this is not broader M1 real-coursework certification. |
| Forward/backward clock arithmetic, midnight/DST and duration boundaries | The final full Mac suite includes deterministic timer/calendar/reward cases, as described in the [implementation review](2026-10-18-m2-recovery.md#target-mac-acceptance-still-required). | No actual system-clock modification was performed or claimed. The checklist expressly permits automated evidence for these arithmetic cases; changing the Mac clock is not a new required hardware experiment. |

## Power-mode scope review

Read-only commands on this host:

```sh
sw_vers
uname -srm
/usr/sbin/sysctl -n hw.model
/usr/bin/pmset -g cap
/usr/bin/pmset -g custom
/usr/bin/man pmset
```

The capability query lists `standby`, `hibernatemode` and `hibernatefile`.
Battery and AC settings both show `standby 1`, `hibernatemode 3`. Therefore this
review cannot dismiss the remaining state check as unsupported. The installed
manual describes mode 3 as retaining powered memory while also saving a disk
image, with disk restoration if power loss requires it; standby is a separate
power-management transition. These documented settings describe capability and
policy, not proof of which restoration path the observed Mac took.

Apple's [safe-sleep explanation](https://support.apple.com/guide/mac-help/what-is-safe-sleep-mh10328/mac)
describes saved state protecting a sleeping laptop against complete power loss.
Apple's [pmset manual source](https://github.com/apple-oss-distributions/PowerManagement/blob/main/pmset/pmset.1)
distinguishes the hibernation modes and standby policy. Neither establishes an
event on this Mac from a `HibernateStats` configuration line. Inference: the
existing Deep Idle observations are sufficient evidence for their named scenarios,
but insufficient to certify a distinct standby/hibernate restore.

The remaining natural observation is a longer unplugged sleep, such as overnight,
using a fresh disposable session and the existing tested observer. It may still
produce only Deep Idle; no fixed duration guarantees a distinct mode. Capture
actual state/clock observations, verify frozen time/tree/wallet during absence,
then explicitly resume or finish and verify one outcome. Do not change power
settings, force hibernation or deplete the battery to produce a desired result.
Leave any unobserved condition unverified. No additional awake precision repeat
is requested by this review.

## Checks performed for this review

Inspected instructions, current progress, planning/runbook documents, recent
commits, complete working/index diff and relevant untracked reviews. Existing
user planning edits, test-fixture repair and stashes remain preserved. No runtime
code/default/schema change, personal-data operation, commit or push.

The first restricted host-read command stopped at `sysctl` with Operation not
permitted; the same read-only query outside that sandbox succeeded. All recorded
host capability/configuration/manual commands then exited 0. This was a read
permission limit, not an application failure. An initial review-file lookup used
an incorrect M0 filename; the runbook's correct local-foundation review was read.

Evidence check, exit 0:

```sh
.venv/bin/python .evidence/mac-verification-20261031/acceptance-review/verify_manifests.py
```

All **12** saved October 30/31 manifests, **155** entries, matched SHA-256;
neither evidence directory contains a `.db`, `.sqlite` or `.sqlite3` file.
This verifies retained bytes, not a new execution of the application scenarios.
Review source/results and read-only host observations are retained in
`.evidence/mac-verification-20261031/acceptance-review/`. Local Markdown links,
new-file whitespace and the scoped progress diff were checked. No application
suite rerun is necessary for this documentation/evidence-only change.

## Decision

Completed observations remain accepted at their documented scope. The ten-minute
manual uncertainty is a measurement caveat, not a newly invented failed gate.
Distinct standby/hibernate recovery remains unverified, keeping combined M2/M3
**not passed** under the current runbook. Broader M1 operator acceptance and M4's
backup/restore, candidate freeze and seven-day trial remain separate. No later
application build starts from this review. A text question asks the operator's
availability for overnight battery observation; elapsed time is not consent or
evidence that the Mac entered sleep.
