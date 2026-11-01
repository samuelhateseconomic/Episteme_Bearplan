# Target-Mac crash and paused restart — October 31, 2026

Revision `d9b5f90e10579d8687c4ffbd8e132a7121573ac1`. macOS 26.6.2 (25G83),
Darwin arm64; AC attached, 80%, not charging. Inspected guidance, progress, full
working/index diff, recent commits and current reviews/runbook. Preserved existing
planning edits, date-fixture repair, evidence and stashes. No runtime source change.

Expected: an actual process interruption preserves only checkpointed time and
requires explicit review. Continue retains the session/tree and excludes the gap.
A paused restart stays paused. Finish/retry saves confirmed intervals once, an
unfinished tree and one zero award for this subminute scenario; task completion
stays separate. No product/default changes or normal-data experiment.

## Execution and observations

Created fresh disposable data at
`/private/tmp/bearplans-mac-recovery-20261031-vptslyb3/data` using
`tools.m2_probe.OwnedService` from a `.venv/bin/python -u -` heredoc. Backend PID
**52961**, loopback port **59531**. Created a synthetic task through the API;
selected it in Track and started a real two-minute countdown through the UI.

Before interruption, `ps -p 52961 -o command=` matched the owned backend command
`-m backend --no-browser --port 59531`. Sent **SIGKILL only to that identified PID**
using `os.kill(pid, signal.SIGKILL)`. Read SQLite after termination using URI
`mode=ro` and one snapshot transaction. The original supervisor was then stopped
with Ctrl+C. It did not stop any other process.

- Session started **08:54:03.561928 PDT**. Last saved running checkpoint:
  **08:54:20.696752**, **17,134,672 microseconds**. Same synthetic task and enrolled
  Pine were durable; no coin award existed yet.
- Restart command:
  `BEARPLANS_DATA_DIR=/private/tmp/bearplans-mac-recovery-20261031-vptslyb3/data .venv/bin/python -m backend --no-browser --port 59531`.
  UI showed **Needs review**, 00:17 confirmed and only explicit continue/save
  decisions. Restart interruption detected **08:54:46.653220**. Two API views
  separated by five seconds preserved exact credit and tree progress/identity.
- Explicit UI **Continue with confirmed time**, **08:55:01.291350**, resolved that
  interruption as resume and retained session `d407a568-5499-4bac-80f8-978b6e65eabd`
  and tree `bb09a528-41e5-4a5c-b014-38d6319f4ac4`. No interval spans the unknown gap.
- Explicit UI Pause at **08:55:05.180059** saved **21,023,345 microseconds**.
  Stopped only this owned service using Ctrl+C and repeated the same restart
  command. The complete active-session object was identical before/after restart
  and another five-second comparison: still Paused, exact same time/tree/recovery.
- UI Finish early at **08:55:43.175783** saved exactly that paused credit. Two
  interval credits **17,134,672 + 3,888,673 = 21,023,345 microseconds**; both closed
  at their trusted checkpoints. One session, one resolved restart interruption,
  original unfinished Pine, one persistent **zero** coin award. Task rows unchanged.
- Sent two identical `POST /api/timer/<session>/finish` requests with saved revision
  and one fresh UUID key; both returned the same saved session. Counts remained
  one session/tree/award. SQLite integrity `ok`, foreign-key check empty. Service
  source SHA-256 map still matched initial setup. Stopped the owned service with
  Ctrl+C after verification; test tab closed.

Durable ignored evidence: `.evidence/mac-verification-20261031/recovery/`.
Sanitized snapshots, environment, process identity, screenshots and SHA-256 manifest
retained; no database copied into the checkout. Screens:
[Needs review](../../.evidence/mac-verification-20261031/recovery/needs-review.png),
[paused after restart](../../.evidence/mac-verification-20261031/recovery/paused-after-restart.png),
[confirmed outcome](../../.evidence/mac-verification-20261031/recovery/confirmed-outcome.png).

## Decision

**Pass for this actual Mac crash/explicit-continue/paused-restart scenario.** No
hardware sleep or external timing claim is made from it. Runtime source unchanged;
full suite not repeated for this evidence/documentation-only work. Combined M2/M3
gate remains not passed: battery/other supported power modes, quantified ten-minute
precision and a real long-duration result remain outstanding. M1's broader operator
certification is separate. The user selected a three-hour stopwatch run next.
No personal database/service, index, stash, commit or remote repository changed.
