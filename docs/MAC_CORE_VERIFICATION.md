# Combined M2/M3 target-Mac verification

Prepared October 26, 2026 against `635e1e7`. This is an operator runbook, not
completed acceptance evidence. Run it on the user's MacBook. Record the actual
revision, macOS/hardware, power source, Python/Node/browser versions and service
timezone. Keep the checkout fixed during a run; record any dirty diff.

The [shared progress record](PROGRESS.md) remains authoritative. Read the
[M0 measured sleep decision](reviews/2026-10-14-local-foundation.md#timer-policy-decision),
[M2 recovery review](reviews/2026-10-18-m2-recovery.md) and
[correction review](reviews/2026-10-23-session-corrections.md) first.
The [review plan](../BearPlans_Build_Review_Plan.md) defines the acceptance gates.

## Prepare and retain evidence

From the repository root in a Mac terminal, with dependencies already installed:

```sh
git status --short --branch
git rev-parse HEAD
sw_vers
uname -m
.venv/bin/python --version
node --version
```

Create a fresh evidence directory outside the checkout. Use the same terminal
for the remaining commands so these variables remain available:

```sh
verification_dir="$(mktemp -d "${TMPDIR:-/tmp}/bearplans-mac-review.XXXXXX")"
export BEARPLANS_EVIDENCE_DIR="$verification_dir/screenshots"
printf '%s\n' "$verification_dir"
npm --prefix frontend run build
npm --prefix frontend test -- --maxWorkers=2
```

Preserve command outputs and exit codes in that directory or the review record.
The build includes TypeScript checking. The backend suite below is a milestone
run; run it once after setup/build, then rerun only failures or changed areas.
The tests use disposable data; browser cases require installed Chrome or Edge.
Skipped required cases are missing evidence, not successful checks.

```sh
.venv/bin/python -m pytest -q
```

Retain evidence somewhere durable before the operating system clears temporary
files. Include only synthetic content in repository screenshots and review logs.
Keep normal personal data and its running service untouched.

## Observe real sleep and awake timing

Each probe starts its own temporary service and synthetic countdown, prints its
URL, and stops only its own service. It does not change power settings or initiate
sleep. Open the printed URL for its UI controls. Do not use the normal app URL.

```sh
.venv/bin/python tools/m2_probe.py sleep --seconds 300 --output "$verification_dir/sleep-ac.json"
```

First hide or close the browser while the Mac stays awake: work must continue.
Then initiate actual sleep using the lid or macOS controls. After wake, record:

- The same session/tree remains Paused or explicitly Needs review, and never
  resumes because the service woke. Unobserved checkpoint time stays excluded.
- Waiting while paused/reviewing adds no time, coins or streak progress.
- Explicit Resume/continue keeps that session and tree. Saving confirmed time
  finishes once. Refresh and another tab show the same result.

Repeat using new output filenames for battery sleep and each supported
standby/hibernate condition. Record actual conditions and repeated sleep/maintenance
wakes. Leave unsupported or untested conditions unverified; AC sleep alone does
not certify them. Do not change system power or clock configuration just to make
a probe pass. A 300-second run is a collection window, not a claim that standby
occurred; use a longer supported window when necessary.

Use an independent stopwatch for the ten-minute and real long-duration runs.
Start it with the observed countdown start, record start/stop uncertainty and the
external elapsed time, and keep the Mac awake throughout precision collection:

```sh
.venv/bin/python tools/m2_probe.py precision --seconds 600 --output "$verification_dir/precision-600.json"
.venv/bin/python tools/m2_probe.py precision --seconds 10800 --output "$verification_dir/precision-10800.json"
```

The proposed ten-minute precision tolerance is two seconds. Record the long-run
difference separately. Both should expire once with no extra timer API request
needed for expiry and no task completion change. The JSON reference uses the
same host clock; its result cannot replace the external stopwatch observation.

Exit 0 means that probe's scenario passed; 1 means failure; 2 means incomplete
observation, including no measured sleep or interrupted collection. Even exit 0
does not certify the complete hardware/operator gate.

## Join recovery, rewards, corrections and reports

The full suite includes `tests/test_corrections_browser.py`: a synthetic 60-minute
saved session earns 60 coins, buys Birch for 60, then is corrected to 30 minutes.
Expected: one -30 adjustment, balance -30, Birch retained, same tree unfinished,
daily qualification lost, reports reduced. Reviewed reversal restores 60 minutes,
adds +30, restores the same mature tree/qualification and leaves balance zero.
Lost-response reload/retry and restart must not duplicate adjustments or awards.
This fixture checks the joined workflow; it does not measure an hour of real work.

For the operator demonstration, use a separate terminal and an unused port:

```sh
operator_data="$(mktemp -d "${TMPDIR:-/tmp}/bearplans-mac-operator.XXXXXX")"
BEARPLANS_DATA_DIR="$operator_data" .venv/bin/python -m backend --no-browser --port 8876
```

Open the printed URL. A busy port must fail; choose another unused port rather
than stopping an unknown process. Create synthetic tasks and demonstrate Plan
and Track entry, an unscheduled leaf, pause/resume, refresh, hidden/closed browser,
two-tab one-session enforcement, early finish and a normal completed countdown.
Task completion stays separate. Compare saved forest, wallet, Stats and daily
progress; review a reduction and reversal in Stats. Check a narrow window,
keyboard actions, loading controls and preservation of input after a failed save.

Stop this terminal's service with Ctrl+C, then repeat the same launch command to
verify that the same records persist. For crash/restart, use the existing
disposable process-recovery tests, or explicitly identify and stop only this
synthetic service. A saved running session must reopen in Needs review without
gap credit; a saved paused session stays paused. Never force-quit an unidentified
service or run recovery experiments against personal data.

## Record the decision

Create a dated review under `docs/reviews/` with the tested revision and exact
commands/results, failures/skips, hardware and power observations, external timing,
screenshots and remaining cases. Distinguish automated fixture results from actual
hardware and operator evidence. If source changes during fixes, rerun affected
checks and identify the final reviewed revision.

Update `PROGRESS.md` with the decision and next concrete step. Missing required
hardware evidence keeps the combined gate **Fail / not passed**, even when all
automated checks pass. M1's broader operator certification is separate. Backup/
restore development, a core candidate freeze and the seven-day trial retain their
own scope and gates; none is certified by this runbook.
