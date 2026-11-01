# Ten-minute target-Mac timing observation — October 30, 2026

Revision `d9b5f90e10579d8687c4ffbd8e132a7121573ac1`; runtime source unchanged.
User selected **Ready for ten-minute stopwatch check**. This follows the completed
[one-minute workflow scenario](2026-10-30-mac-workflow.md); it uses separate
synthetic data and no personal records. The combined hardware gate remains open.

Expected: an uninterrupted awake ten-minute countdown saves exactly 600,000,000
confirmed microseconds, one mature Pine and ten coins, leaving its task incomplete.
Compare against the operator's separate stopwatch with start/stop uncertainty;
the proposed tolerance is two seconds. Same-host clocks cannot substitute for
that independent reading. No system power or clock setting is changed.

## Setup and collection

Disposable root: `/private/tmp/bearplans-mac-precision-20261030-nee19kfv/`.
A `.venv/bin/python -u -` heredoc imports `OwnedService`, `source_digests`,
`clock_sample` and `sleep_delta` from the existing `tools/m2_probe.py`. It starts
one owned service against `root/data`, creates one synthetic task through the
domain-backed API, and then only reads SQLite in short snapshots every 0.2 seconds.
The first setup was stopped before any countdown to retain the service after
expiry for operator inspection; its incomplete report remains separate.
The active collector uses port **50695**, backend PID **32516**, and writes
`precision-observation.json`. Its reference captures the last no-session sample,
first observed running sample, last unfinished sample and first finished sample.
The monotonic elapsed bounds account for polling uncertainty. Both Mac clock
samples are retained to detect measured sleep; service source hashes bracket the
run. The collector retains the service after completion until deliberately stopped.

The agent opened the in-app browser visibly, selected the synthetic task and set
duration to ten minutes without activating Start. The operator was instructed to
click Start countdown and start a separate phone stopwatch as close together as
possible, keep the Mac awake, leave timer controls untouched and stop the stopwatch
when Countdown completed appears. A final reading and approximate start separation
were requested. UI starts use normal domain functions; no saved time is seeded.

Actual session start: **07:45:20.374124 PDT** (14:45:20.374124Z), October 30.
The read-only observer detected the new running session. No agent pause, resume,
finish or sleep action was performed.

## Saved result

Finished **07:55:20.372645 PDT**. One completed session
`140e0f1d-d613-423b-9824-0ef8a4fccfc2`, one closed interval, exactly
**600,000,000 microseconds**, one mature Pine and one **10-coin** initial award.
Task remains incomplete; Stats and daily progress show ten saved minutes and
wallet balance is ten. No interruption rows; observed sleep **0 seconds**.
The collector retained **2915** session samples. Same-host monotonic elapsed bounds
from observed start/finish polling were **599.944399625–600.357575208 seconds**;
these bounds support the local observation only. Wall endpoints span
599.998521 seconds and are not substituted for active monotonic credit.

Source hashes match before/after; SQLite integrity `ok`, foreign-key check empty.
The visible UI showed Countdown completed, 10:00, ten coins and Mature Pine.
After the database-only collector observed completion, read-only API views of
timer, tasks, shop, forest, streaks and statistics confirmed the saved outcome.
The UI remained open during this run, so its normal polling was present; this
does not independently demonstrate expiry without API activity. The earlier
one-minute browser-closed scenario supplies that separate evidence.

## Operator observation and decision

The operator replied **"Started and I found that count down complete and no
different"**, and answered the stopwatch-reading question **"same"**. Record this
as a reported independent match to ten minutes. No numeric reading, display
resolution, start/stop offset or explicit awake confirmation was supplied. The
observer measured no sleep, but cannot replace those operator timing details.

**Pass with follow-ups for this observation:** saved-work behavior passed and the
operator reported a stopwatch match. The exact proposed **two-second tolerance
remains unquantified**, so formal independent precision certification is pending.
Do not convert "same" into an invented decimal reading or zero-error measurement.
Battery/other supported power states and the real long-duration observation also
remain pending. No normal data, application code or power configuration changed.

Stopped only the owned collector/service with Ctrl+C after recording the result;
closed its test tab. Durable ignored evidence, operator's verbatim answers,
environment, clock/record samples and SHA-256 manifest:
`.evidence/mac-verification-20261030/precision-600/`. No database copied into the
checkout. [Completed outcome screenshot](../../.evidence/mac-verification-20261030/precision-600/completed-outcome.png).
The earlier setup report is retained as incomplete, never counted as a second run.
Final checks: scoped whitespace/local Markdown links and all retained evidence
hashes passed; runtime source diff empty. `lsof -nP -iTCP:58618 -iTCP:50695
-sTCP:LISTEN` returned no listeners (expected no-match exit 1), confirming both
owned workflow/timing services stopped. No application-suite rerun was needed
for these documentation/evidence-only changes.
