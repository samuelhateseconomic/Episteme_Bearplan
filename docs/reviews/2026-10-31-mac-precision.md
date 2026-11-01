# Target-Mac ten-minute precision retry — October 31, 2026

**Pass with follow-ups for the observed external comparison and saved-time
conditions.** Start/stop uncertainty remains unquantified; this is not full
M2/M3 acceptance. Build `d9b5f90`, actual macOS 26.6.2
(25G83), arm64. User requested continued verification after completed battery
recovery. Current power is Battery Power, 80%. Read-only `pmset -g custom` shows
standby enabled and hibernatemode 3; configuration does not prove those states
occurred. No power/clock setting changed.

The earlier [October 30 precision observation](2026-10-30-mac-precision.md) retained
a qualitative operator match, without numeric independent reading or start/stop
uncertainty. This retry targets that missing evidence, not a new application build.
Asked whether the operator can keep the Mac awake for ten minutes with a separate
stopwatch, or prefers a longer sleep observation. No new service/countdown started.

## Expected result and measurement

Operator starts a fresh ten-minute synthetic countdown and an independent stopwatch
as close together as possible, records approximate start separation/uncertainty,
leaves timer controls untouched and keeps the Mac awake. At **Countdown completed**,
stop the external stopwatch and report its numeric reading, decimals if available,
plus approximate stop reaction delay. Expected saved result: **600,000,000 integer
microseconds**, one original mature Pine, one ten-coin award at captured rate 1,
unchanged incomplete task, no sleep/pause/restart or unresolved interruption.

Compare external elapsed reading with 600 seconds and retain the reported start/
stop uncertainty. The proposed ten-minute tolerance is two seconds. Do not claim
zero error from "same" or certify that tolerance if uncertainty prevents a bounded
comparison. Same-host awake/continuous clock samples corroborate conditions but
cannot replace the separate stopwatch. Normal UI polling is expected during this
operator check; autonomous expiry evidence remains the earlier browser-closed test.

## Prepared instrument

Disposable source root:
`/private/tmp/bearplans-mac-precision-retry-20261031-76en1q6m/`.
`observe.py` reuses the previously behavior-checked long-run observer, changing its
synthetic title/scope and exact completed-duration check to ten minutes. It has no
pre-start or unfinished-session cleanup timeout. Pause/review stays observable and
invalidates uninterrupted eligibility. After finish the service is retained for
30 minutes; explicit stop retains evidence. No automatic timer/power controls.
`ast.parse` passed; preparation source/digest/changes retained beside it.

Ignored preparation evidence:
`.evidence/mac-verification-20261031/bearplans-mac-precision-retry-20261031-76en1q6m/`.
No application code/schema/default changes, personal data access, suite rerun,
commit or push. Combined M2/M3 remains not passed; supported power-mode and long-run
precision gates are separate. Next: launch only after operator readiness/choice,
open the ten-minute setup, then coordinate the paired start and numeric reading.

## Visible test setup

Operator selected **Ready for ten-minute stopwatch check**. Launched:

```sh
.venv/bin/python -u /private/tmp/bearplans-mac-precision-retry-20261031-76en1q6m/observe.py
```

Owned backend **PID 16519**, loopback **59117**, observer exec **9948**, prepared
**16:36:55.602670 PDT**. Opened the synthetic task in the in-app browser, selected
**10 minutes** and confirmed Start countdown enabled. Agent did not press Start.
`ready.png` preserves setup. Tab marked for handoff. Asked operator to click Start
with the separate stopwatch, report approximate start difference, keep Mac awake,
leave timer controls untouched, then report exact final reading plus stop delay.
No acceptance claim until actual records and numeric independent evidence exist.
Observer remains available before start and throughout unfinished collection.

Actual operator start **16:37:40.754115 PDT**, detected running at
**16:37:40.926403**. UI confirms Running, 10 minutes; `running.png` retained.
Expected uninterrupted expiry **16:47:40.754115 PDT**. External start offset has
not been supplied; do not infer synchronization from the UI start. Agent left all
timer controls unchanged and reiterated keeping Mac awake and retaining the exact
stopwatch reading at completion. Observer continues collecting synthetic records.

Operator then confirmed they are counting and will report the result; no numeric
reading or start offset supplied yet. Retained verbatim in `operator-note.json`.
Answered their remaining-test question as three acceptance items: this ten-minute
precision run, uninterrupted long-run precision and supported longer power/sleep
conditions. The power item may require multiple observed cycles; no fixed count
or unsupported-mode certification was promised. Timer controls remain untouched.

## Completed run and external comparison

Actual uninterrupted finish **16:47:40.756981 PDT** (23:47:40.756981Z), from
**16:37:40.754115 PDT**. Session `9ad4b43a-5b57-4e2b-80aa-9b501bc1bb7e` saved
outcome `completed`, revision 2, exactly **600,000,000 microseconds** in one closed
interval. No measured sleep or interruption; the only timer operation was Start.
Observer `uninterrupted_eligible = true`, source digest maps unchanged. Normal
UI polling was present; autonomous expiry without API activity is not claimed anew.

The original Pine `5c016b2c-c92e-4118-b0b2-a3be248c4bd0` became mature, finalized
with the session. Exactly one award **10 coins**, captured earning rate 1, wallet
10. Task `07c9fbd2-f394-4451-aa2c-da4bc35beb0a` remains incomplete, revision 1,
with unchanged created/updated instants. Statistics and October 31 streak credit
both exactly **600,000,000 microseconds**; **0/1** leaves complete, zero-day streak,
no qualified day. UI shows **Countdown completed · 10:00**, Mature Pine, 10 coins.
`completed.png` retains that outcome. A stale browser handle failed with an
unavailable browser API; a fresh tab in the same in-app browser showed the result.
No timer control was used during inspection.

Operator reports, retained verbatim in `completion-audit.json`:

- **"1. the ten minute stopwatch is matched"**.
- **"10:00:20 but it’s also my hand and reflection so no worries though"**.
- When asked to distinguish notation, **"10 minutes, 0.20 seconds"**.

Thus the external reading is **600.20 seconds**, raw external-minus-confirmed
difference **+0.20 seconds**, within the proposed two-second target at the reported
reading. Operator attributes the small difference to hand/reaction. No reaction
correction was applied and no zero error was inferred. Approximate start offset
and stop reaction delay were not separately quantified, so an uncertainty-bounded
absolute error is not established. Same-host elapsed bounds were
**599.506931750–601.520798208 seconds** and remain corroboration, not a substitute
for the separate stopwatch. A repeat was not automatically requested.

Read-only audit command, exit **0**:

```sh
.venv/bin/python /private/tmp/bearplans-mac-precision-retry-20261031-76en1q6m/audit_precision.py
```

Checks passed: exact interval/session duration; no sleep/pause/restart; original
mature Pine; one captured-rate award; unchanged task; exact statistics/streak
totals; all database rows unchanged by API reads; SQLite `integrity_check = ok`,
empty foreign-key check; runtime source identical to observation start. No repeat
Finish/restart test was run in this observation; those have separate prior evidence.

Stopped identified observer exec **9948** with Ctrl+C after evidence review;
it stopped only its owned backend at **16:49:15.710650 PDT**. Final sanitized report,
exact observer/audit source, screenshots and operator reading retained under
`.evidence/mac-verification-20261031/bearplans-mac-precision-retry-20261031-76en1q6m/`.
Verified SHA-256 manifest covers **11 files**; no database included. Original
disposable data is outside the checkout. Normal service/data untouched. Scoped
documentation whitespace/local links passed. No app-suite rerun, commit or push.

**Pass with follow-ups** for the observed +0.20-second external match and exact
saved-time behavior, with the manual uncertainty limitation above. The two main
remaining observation items are uninterrupted long-run precision and supported
longer power/sleep conditions. Combined M2/M3 remains **not passed**; M1 operator
acceptance is separate and M4/later work remains not started.
