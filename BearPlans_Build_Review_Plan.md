# BearPlans — Review Plan for Every Build

Prepared October 13, 2026. Companion to the local laptop implementation plan. This defines proposed review and release gates; it does not report tests of an existing application.

## 1. Review at three levels

| Review | When | Scope | Suggested time |
| --- | --- | --- | --- |
| Change review | Every small ticket/build | Requirement, changed code, relevant checks, one user demonstration | 10–20 minutes |
| Milestone gate | Before advancing M0–M7 | Acceptance scenarios, regression risks, recovery and usability | 30–60 minutes; hardware tests may take longer |
| Personal release trial | Before declaring a daily-use release | Seven days of real coursework and recovery checks | Brief daily notes plus a closing review |

Avoid rerunning the full matrix for a cosmetic change. Changes to shared session, date, storage or reward code require its affected regression suite. Run the full core suite at milestone and release boundaries. Fake clocks cover timer boundaries without waiting three hours; validate a real long session and actual Mac sleep behavior before the core release.

## 2. Change-review contract

Before coding, put four things in the ticket: user-visible change; acceptance scenario; affected records; recovery/Undo behavior when relevant. Distinguish established requirements from proposed product defaults. Updating a rule requires updating its acceptance scenario, not silently changing the expected result to match the implementation.

After implementation:

1. **Requirement review:** Does the build do what the ticket says? Are accidental behaviors or scope additions present?
2. **Code review:** Is logic in the shared Python application layer? Are database writes bounded? Is validation present? Are errors visible and actionable? Check simpler implementation choices.
3. **Behavior review:** Run meaningful checks on the changed behavior. For persistent or timing changes, include failure/retry cases. Cosmetic changes usually need visual inspection rather than new unit tests.
4. **UX review:** Demonstrate the normal user journey on a representative laptop window and a narrower window. Check keyboard use, readable labels, disabled/loading states and user recovery.
5. **Evidence and decision:** Save build/commit ID, checks and outcomes, one screenshot or short recording when visual behavior matters, open issues and Pass/Pass with follow-ups/Fail.

A fresh review pass should inspect the diff and evidence without treating the implementation's explanation as proof. AI can assist review, but passing tests and the real laptop demonstration remain the evidence. The user judges workflow usefulness; the engineering review verifies correctness.

## 3. Milestone-specific gates

### M0 — Foundation and timer/sleep experiment

Review: launch instructions, persistence, migration path, local-only binding, frontend/backend boundary, and actual Mac power behavior.

Scenarios: start from a fresh directory; create/read a task; restart and read the same task; attempt a second application instance; exercise sleep/wake and distinguish it from a hidden tab.

Pass: reproducible startup, durable task identity, duplicate-instance handling and documented sleep behavior. If native sleep events are unreliable, explicitly select the Needs review fallback. Unknown gaps cannot silently earn time.

Evidence: startup transcript with secrets omitted, schema/migration version, saved record, and a short sleep/wake observation. Repeat on the Mac; the development environment cannot certify Mac power-event behavior.

### M1 — Weekly planner (gate pending)

The daily roadmap splits this gate across Oct 15 projects/tasks, Oct 16 weekly
planning, and Oct 17 history. Passing the projects/tasks implementation alone does
not certify the complete planner gate. The Oct 15 projects/tasks build has passed
implementation and operator review; Oct 16/17 remain pending. Current build evidence is in
[the M1 takeover review](docs/reviews/2026-10-13-m1-takeover.md).

Review: projects, parent/subtasks, completion semantics, date assignment versus deadlines, previous-week snapshots and movement of unfinished work.

Scenarios: plan a real week; complete a subtask; assign another day; move unfinished work forward; close the week; revisit it; restart; edit a task already referenced by a session fixture. Verify that an unscheduled task can still be selected for tracking.

Pass: no lost or duplicate tasks; correct completion denominator; moving work retains task identity and deadlines; closed-week comparisons stay reproducible. A narrow window remains usable. Parent and child work are not counted twice.

Evidence: before/after week views and relevant saved IDs/counts. Early versions may use assignment buttons before drag-and-drop.

### M2 — Countdown and recovery

Review: backend-authoritative timing, lifecycle transitions, interval records, one-session enforcement and restart recovery.

Scenarios: start from a task and from Track; pause/resume; finish early; expire normally; refresh; hide the tab; close the browser while the service runs; request a second timer from another tab; sleep/wake; restart the service; retry finish; change the clock; cross midnight and a daylight-saving boundary.

Pass: paused/sleep time is excluded or explicitly unresolved; remaining time is reconstructed; active duration never exceeds the configured maximum; session save occurs once; ambiguous interruptions are shown for review. UI controls remain responsive. Switching screens does not stop tracking.

Proposed beta precision target: a ten-minute uninterrupted awake session differs by no more than two seconds from an independent reference. Persist checkpoints on a defined cadence and display recovery precision honestly; a gap after a crash is not automatically trusted. Check countdown boundaries with a fake clock and one real long session before release.

Evidence: interval/state records, deterministic test outcomes and real Mac observations. Logs must omit private task contents where unnecessary.

### M3 — Forest, coins, streaks and statistics

Review: reward transaction boundaries, shop balance rules, derived statistics and date allocation.

Scenarios: finish twice/retry finish; end early; 59 active minutes versus 60; two 30-minute sessions; pauses; midnight split; edit a saved session; buy a species with sufficient/insufficient funds; correct a rewarded session after spending its coins.

Pass: each session contributes one initial award; completed trees reference unique completed sessions; thresholds use active seconds; statistics match known fixture totals; corrections create explicit adjustment entries; purchases cannot overspend an available balance. Follow the agreed negative-balance correction policy without silently minting coins or removing owned trees.

Evidence: an independently calculated fixture sheet or test data, resulting ledger entries, streak dates, report totals and shop screenshots. Expected results are specified before inspecting outputs.

### M4 — Personal core release

Review: clean startup, code/data separation, backup/restore, migrations, local request protection, offline operation and real usage.

Scenarios: launch with no internet and no running model; restore a backup into a clean directory; upgrade a copy of an earlier schema; interrupt a migration safely; exercise an unavailable/corrupt database without resetting it; use the application for seven days on real coursework.

Pass: normal core workflows work offline; backup preserves tasks, plans, sessions, trees and ledger; failed migration retains a recoverable original; a saved task does not disappear after update/restart; unrelated web origins cannot invoke mutation routes. No open severe timer, persistence or reward issue.

Evidence: build/version and migration IDs, restore comparison, essential regression results and seven-day notes. Each daily note records work performed, friction, errors and any time correction. Remaining cosmetic issues become follow-ups.

### M5 — Local AI assistant

Review: exact tool schemas, bounded execution, scope of actions, truthful reporting, local model path, contextual retrieval and usable latency.

Evaluation set: 30 fixed cases—10 read/statistics, 10 edits/replanning, 5 timer requests and 5 ambiguity or source-instruction cases. Include duplicate task names, nonexistent IDs, stale edit revisions, malformed arguments, repeated requests and an unavailable model.

Pass: exact statistical answers match Python results; zero unauthorized mutations in the set; at least 90% end-to-end scenario success; ambiguous target/action requests remain unresolved until clarified; broad replanning is previewed; tool rounds stop at the configured limit; the assistant claims success only after a successful tool result. These are gates on a bounded test set, not a guarantee for all future requests.

Concurrency check: run a slow generation while starting/pausing a timer through the interface. Proposed target: a timer command is acknowledged within one second on the target Mac; investigate if inference monopolizes the service. Report median and slowest measured request times instead of guessing from model size.

Evidence: model/version/quantization, prompt and tool-schema versions, case inputs/expected outputs/results, action records and latency measurements. Repeat relevant evaluations after model, prompt or schema changes. Larger hardware alone is not a passing result.

### M6 — Google Calendar

Review: selected calendars, scope minimization, normalized event IDs, recurrence/timezones, cancellation, sync cursors and credential handling.

Scenarios: first sync; repeat sync; changed event; canceled event; recurring-event exception; all-day event; offline mode; expired/revoked authorization; failed request; stale/incomplete partial response; restart mid-sync.

Pass: no duplicates; times displayed correctly; stale data labeled; failures do not erase valid cache; read-only actions remain read-only; credentials stay out of database exports and logs; reconnect resumes safely. An incomplete fetch cannot be interpreted as every absent event being deleted.

Evidence: synthetic provider fixtures, normalized IDs, last-successful-sync display and a limited live-account demonstration after authorization. Use synthetic data for normal tests.

### M7 — Canvas and Gmail

Review: accessible sources, field ownership, uncertain extraction, source links, token protection, deletion/disconnection and instruction boundaries.

Scenarios: repeated assignment/message import; assignment deadline change; missing deadline; inconsistent date text; source temporarily unavailable; imported task edited by the user; revoked token; malicious text pretending to instruct the assistant; disconnect and separately delete cached source content.

Pass: uncertain tasks go to review; deadlines are not invented; provider changes preserve user subtasks and planned dates; revoked/failed sources are visible; imported text cannot authorize actions; repeat import avoids duplicates. External authorization availability is a prerequisite, not a code-quality pass.

Evidence: normalized source fixtures and IDs, import-inbox examples, sync status and redacted authorization-handling checks. Scope approval and access constraints are recorded separately from implementation defects.

## 4. Severity and release decisions

| Severity | Examples | Decision |
| --- | --- | --- |
| Critical | Private data/credentials exposed; data corruption or irreversible loss | Block build/release; fix and rerun affected checks. |
| High | Wrong task changed; timer records sleep as work; duplicate rewards; failed restore; AI reports a mutation that failed | Block the affected milestone and release. |
| Medium | Incorrect recoverable report; a secondary flow unusable; misleading error | Required acceptance failures block that milestone; otherwise document a workaround and owned follow-up. |
| Low | Spacing, cosmetic animation/growth polish, minor wording | May proceed with a tracked follow-up. |

**Pass:** required scenarios have evidence and no blocker remains. **Pass with follow-ups:** required scenarios pass; only explicitly acceptable issues remain. **Fail:** a required scenario fails, a critical/high issue remains, or required evidence is missing. Untested sleep/recovery is not a pass because normal timing worked.

## 5. Review record template

Build/commit:
Milestone and ticket:
Expected user-visible behavior:
Requirement/default changes:
Affected records/functions:
Environment and model version when relevant:
Checks run and outcomes:
Evidence links:
Issues with severity, owner and next action:
Decision: Pass / Pass with follow-ups / Fail
Next permitted step:

Keep the record brief for a small change. A milestone record links the accumulated evidence rather than copying every test log. Avoid a large report for a wording or spacing edit.

## 6. Operating rhythm

During development: one small ticket, implementation, fresh review, relevant checks, demonstration and decision. At a milestone boundary: run the named acceptance scenarios and core regression checks, then advance only when the gate passes.

Use separate test data and database copies for migrations, interruptions and restore exercises. Never test destructive recovery against the only copy of personal data. For AI and integration fixtures, synthetic data keeps reproducibility and privacy manageable.

During the seven-day trial, keep a two-minute daily note. At the weekly review, identify the single largest friction or risk, correct it, and update the relevant regression case if it represents a meaningful failure. Then select the next three small tickets.

Budget routine review inside each milestone's existing acceptance work. The earlier build estimates already include basic verification. Re-estimate if new defects, Mac sleep support or integration behavior require additional engineering; do not promise that thorough review has zero cost.
