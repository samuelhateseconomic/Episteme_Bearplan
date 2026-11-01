# Mac workflow continuation — October 30, 2026

Revision: `d9b5f90e10579d8687c4ffbd8e132a7121573ac1`. Resumed the interrupted
October 27 operator check. Inspected current status, complete working/index diff,
progress and runbook. Existing planning edits, date-fixture repair and evidence
remain preserved. Application source is unchanged. No commit or push authorized.

## Battery observation could not start

On October 27 the user reported "On battery", then "All power cables disconnected".
Repeated `pmset -g batt`, including outside the sandbox, still reported AC attached,
80%, not charging. A separate read-only `ioreg -r -c AppleSmartBattery -d 1`
confirmed `ExternalConnected = Yes`, `AppleRawExternalConnected = Yes` and
`IsCharging = No`. No battery probe or physical sleep instruction followed this
mismatch. The October 30 recheck still reports AC attached. This is missing battery
evidence, not a BearPlans timer failure or proof that the operator did not unplug.
No power setting was changed.

Sanitized preparation/mismatch records:
`/private/tmp/bearplans-mac-battery-20261027-wcb5b5hc/`.
Only selected battery fields are retained; no complete hardware registry dump.

## Disposable workflow scenario

Expected: a real one-minute countdown expires while its browser is closed, saving
exactly 60,000,000 confirmed microseconds, one mature Pine and one coin. The task
remains incomplete. Repeated finish requests, refresh and a deliberate restart of
this identified synthetic service preserve the same records and rewards.
This is an agent-operated workflow demonstration, not external stopwatch evidence.

The October 27 setup created a task through Plan and selected Start tracking, but
the turn was interrupted before starting any timer. On October 30, read-only
process/port checks identified the same owned backend PID 78398 on loopback port
58618. `/api/timer` returned no active or saved session. No elapsed session time
from the three-day interruption is credited.

Synthetic service/data:
`/private/tmp/bearplans-mac-operator-20261027-na8lq_wy/`, port 58618.
It was created with `tools.m2_probe.OwnedService` and a fresh temporary directory;
the normal personal data/service was never selected. Source hashes are retained
before setup and on continuation. Browser actions use Codex's in-app browser.

Host on continuation: macOS 26.6.2 (25G83), Darwin arm64, Python 3.13.15,
Node 24.21.0; service dates System local (PDT). Power remained AC attached at 80%.

### Results

- Selected the existing unscheduled task in Track, set one minute and activated
  Start countdown with Enter. Start: **07:37:55.001829 PDT**, October 30.
  Closed the test browser while running. No timer API request was made between
  closure and expiry verification; a read-only SQLite observer watched saved rows.
- Before reopening or requesting the timer API, SQLite showed **completed**, exactly
  **60,000,000 microseconds**, one closed interval, one mature Pine and one initial
  coin award of **1**. Finish: **07:38:55.001681 PDT**. The task's completion,
  timestamps and revision remained unchanged. Wall endpoints differ slightly from
  monotonic credit, as expected; this is not an independent precision measurement.
- Sent the same JSON body twice to `POST /api/timer/<session>/finish`, with revision
  2 and one UUID operation key. Both returned the same saved session. One receipt
  was added; session, interval, tree, award and task rows stayed byte-for-field
  equal. Replaying that key after restart also changed no saved row.
- Stopped only the owned supervisor using Ctrl+C. Restart command:
  `BEARPLANS_DATA_DIR=/private/tmp/bearplans-mac-operator-20261027-na8lq_wy/data .venv/bin/python -m backend --no-browser --port 58618`.
  Timer (apart from response `server_now`), tasks, shop, forest, streaks and
  statistics API views were identical before/after restart. Integrity check `ok`;
  foreign-key check empty. UI showed 01:00, one coin and the same mature Pine.
- Stats showed one minute, one saved session and **0/1** leaf tasks complete.
  Opened saved-session corrections. An over-ceiling input of **6061 seconds**
  was rejected with an actionable message and preserved inputs/reason. The initial
  typing action appended to the existing 60; this was automation input behavior,
  not a product save error. Replaced it with 30 using the set-value operation.
- Preview explicitly showed **60 → 30 seconds**, **-1 coin**, balance **1 → 0**,
  mature → unfinished and the unchanged October 30 attribution. Applied it.
  API/SQLite confirmed 30 seconds, the same unfinished tree and zero balance.
- Entered a second reason and reviewed **30 → 60 seconds**, **+1 coin**, balance
  **0 → 1**, unfinished → mature. Applied it and expanded correction history.
  Both audit entries remained; the original award row was unchanged. One session,
  one interval and the original tree identity remained. Adjustments were **-1/+1**;
  task rows stayed identical. Stats/daily progress returned to one saved minute.
- Stopped/restarted that same synthetic service again with the command above.
  All six API views and all nine saved record sets (including both corrections,
  baseline and adjustments) were identical. Integrity/FKs passed again. Service
  source hashes matched the original October 27 setup throughout. Stopped the
  owned service gracefully after the comparison.

Session: `3b9e23d3-6d1a-411d-b459-e63b2c246eb0`.
Tree: `d1086c67-ae08-45d3-8b24-bfe7f13e87f2`.
Durable ignored evidence: `.evidence/mac-verification-20261030/operator/`;
power mismatch: `.evidence/mac-verification-20261030/power-mismatch/`.
JSON snapshots and screenshots retained; no database copied into the checkout.

Screens: [completion after restart](../../.evidence/mac-verification-20261030/operator/completed-after-restart.png),
[saved reduction](../../.evidence/mac-verification-20261030/operator/reduction-saved.png),
[restoration and audit](../../.evidence/mac-verification-20261030/operator/restored-audit.png).

**Pass for this agent-operated workflow scenario.** No application code changed;
the full core suite was not repeated after documentation/evidence-only work.
The earlier full Mac suite remains separate evidence. No normal data/service,
stash, index, commit or remote repository changed. A browser helper method was
unavailable while positioning a screenshot; ordinary scrolling succeeded.

Combined M2/M3 acceptance remains **not passed**. Battery and other supported
power conditions, external ten-minute precision, real long-duration timing and
broader M1 operator acceptance retain their separate gates. The user is ready for
a ten-minute external stopwatch observation; a fresh synthetic service has been
prepared separately, with no automatic start or power-setting changes.
