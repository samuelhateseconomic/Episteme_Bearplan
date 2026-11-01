# Overnight battery sleep and recovery — November 1, 2026

**Pass for observed overnight battery Deep Idle/maintenance-wake and explicit
recovery behavior. Distinct standby/hibernate remains unverified.** User volunteered overnight testing
and unplugging the charger after previously deferring standby checks. This is
explicit authorization to resume this hardware observation; the earlier skipped
results remain historical. No other application ticket starts concurrently.

Actual Mac15,9, macOS 26.6.2 (25G83), arm64; Python 3.13.15, Node 24.21.0.
Base `d9b5f90` plus uncommitted reviewed M4 backup/restore code. Timer/reward
source unchanged; exact runtime digests retained at start/current collection.
Existing user edits/index/stashes preserved. No normal data/service, commit or push.

Expected: actual sleep/maintenance wakes pause at the trusted checkpoint, never
resume automatically, and add no uncertain work, tree growth, coins or streak
credit. On return, inspect paused/review state and actual OS events before using
controls. Explicit Resume/continue retains the original session/tree and excludes
the entire gap; Finish saves only confirmed intervals once. Distinct standby or
hibernate is certified only if actual event evidence establishes that state;
overnight duration and mode settings alone do not prove it.

Read-only host preflight verified **Battery Power, 80%, ExternalConnected = No,
IsCharging = No**. Recorded `pmset -g batt`, `pmset -g custom`, `pmset -g cap`,
selected battery registry fields, OS/architecture/Python/Node and HEAD. No power,
clock or sleep settings changed; no keep-awake assertions created.

Disposable root:
`/private/tmp/bearplans-mac-overnight-20261101-413bkmlx/`.
Copied the tested indefinite observer, changing evidence date and scenario labels
only; `ast.parse` passed, SHA-256 and exact replacements retained. Command:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-overnight-20261101-413bkmlx/observe.py /private/tmp/bearplans-mac-overnight-20261101-413bkmlx
```

Owned observer exec **5588**, backend PID **25271**, URL
**http://127.0.0.1:54617/#track**. No pre-start/unfinished/paused/post-completion
cleanup timeout. Observer remains available for inspection until explicit stop.
Fresh data startup also exercised the newly reviewed automatic backup path on
synthetic data; backups remain in that disposable data folder.

Agent selected the synthetic incomplete leaf, **180 minutes**, Pine, then started
through UI. Start **2026-11-01T07:20:20.088972Z**, **00:20:20.088972 PDT**.
Session `77d77865-619f-49ec-b557-687a90f63889`; original Pine
`5d9f60f6-f5be-44bd-b2a6-06cdc7526d2b`. SQLite and UI confirm Running, revision 1.
The duration is sleep-test headroom, not an external precision test or permission
to credit overnight absence. Screenshot `running.png`, initial record check and
preflight saved. User instructed to keep charger disconnected, close lid overnight,
leave controls untouched and report reopening/approximate closed duration.
Tab marked for handoff. No actual lid closure or sleep has yet been claimed.

Live sanitized source/preparation/host/state evidence is retained under ignored
`.evidence/mac-verification-20261101/bearplans-mac-overnight-20261101-413bkmlx/`;
no database copied into the checkout. No application source modification or suite
rerun for this operator-only setup. Local links/whitespace checked.

Planned return checks: inspect raw UTC intervals and measured sleep, scoped macOS
Sleep/Wake/DarkWake and relevant hibernation state events. Account for actual
timezone offsets when reporting the night; do not calculate elapsed duration by
subtracting repeated local clock labels across DST. Compare paused full session,
tree, wallet/streak/forest views before explicit recovery, then audit saved
interval/reward identity and clean up only the owned observer/service.

## Completed overnight observation

User returned with **"good morning, I just did"**. Before any timer control,
SQLite/API/UI all showed Paused at exactly **39,280,232 µs**, original Pine,
zero wallet/awards and no saved streak credit. Full timer/tree, forest, shop and
streak views stayed identical over a separate ten-second comparison. Final
observer retained **962 paused samples**, all with that exact credit, from
**07:22:25.984476Z** to **16:18:23.615564Z**. The only later transition back to
Running followed the agent's explicit Resume below; no maintenance auto-resume.

Scoped power logs establish first Clamshell Sleep **00:20:57 PDT (-0700)** and
lid/HID wake **08:15:52 PST (-0800)**, November 1. Convert the endpoints to UTC:
**07:20:57Z → 16:15:52Z**, **32,095 seconds / 8h54m55s**. The daylight-saving
rollback adds an elapsed hour beyond subtraction of local clock labels.
Observer measured cumulative sleep **31,272.306836835 s / about 8h41m12s**;
lid-window duration includes maintenance activity and is not sleep-only time.

Exact-category log counts: **62 Sleep, 61 DarkWake, one Wake, 62 HibernateStats**.
All 62 actual wake-category events report **Deep Idle**; all recorded event power
sources are battery. Post-return host reads still verify Battery Power, 80%,
ExternalConnected No, IsCharging No. No settings changed. HibernateStats rows
remain configuration/statistics evidence; no distinct standby/hibernate entry or
restore was established. A first prefix-category filter also included Wake
Requests; corrected to exact tab-delimited categories and replaced the generated
filtered files. The corrected counts above exclude requests; no application
failure resulted from this auxiliary classification correction.

Persisted sleep interruption detected at **07:22:25.941674Z** records the first
measured sleep **86,448,787 µs**. It is not a cumulative overnight sleep total.
Its trusted checkpoint is **07:20:59.374694Z**; the entire checkpoint-to-explicit-
Resume gap remains excluded, including all later maintenance activity.

## Explicit recovery, save and audit

Saved paused screenshot, then agent UI Resume at **16:18:23.729364Z / 08:18:23
PST** retained the original session/tree. Excluded gap **32,244.354670 seconds**.
UI Finish early at **16:19:08.880893Z / 08:19:08 PST** saved exactly
**84,431,660 µs**, two closed intervals **39,280,232 + 45,151,428 µs**. Original
Pine stayed unfinished; one initial award **1 coin** at captured rate 1. Task
remained incomplete, revision 1, unchanged creation/update instants.

Audit command, exit 0:

```sh
.venv/bin/python /private/tmp/bearplans-mac-overnight-20261101-413bkmlx/audit_saved.py
```

Adapted the prior completed extended-sleep audit only for this root's initial
record format; source/syntax check retained. All nine checks passed: same saved
session/tree, exact interval sum, gap exclusion and explicit resolution, one
whole-confirmed-minute award, unchanged task, unchanged runtime digests, integrity
`ok`/empty foreign-key check, and two identical Finish requests preserving every
substantive table. The replay adds only its first operation receipt. Separate
read-only checks confirmed exact statistics/streak **84,431,660 µs**, wallet 1 and
one forest tree. No new restart test or precision claim; prior evidence remains
separate. `saved-audit.json`, `completion-summary.json`, `after-wake.json` and
`overnight-analysis.json` preserve exact records/calculations.

Stopped only owned observer exec **5588** with Ctrl+C; owned backend stopped
**16:19:47.810665Z / 08:19:47 PST**. No keep-awake helper existed. Screens
`after-wake-paused.png` and `finished.png`, exact observer/audit/preflight source,
scoped OS events and JSON retained in the evidence folder above. Verified
**17-file SHA-256 manifest**; no database included. Normal user data/service and
existing work/index/stashes unchanged; no app change, app-suite rerun, commit or
push. Scoped document links/whitespace checked.

**Pass for this overnight battery sleep/maintenance-wake and explicit recovery
scenario, including a real DST-night absence.** This is not running-across-DST
precision evidence, and it does not certify distinct standby/hibernate. Preserve
the user's earlier choice to defer those unobserved modes; no repeat overnight
test requested automatically. M4 backup/restore implementation remains passed at
its recorded scope; trial-candidate and seven-day release gates remain separate.
