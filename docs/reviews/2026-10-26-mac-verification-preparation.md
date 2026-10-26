# Mac acceptance preparation — October 26, 2026

Baseline: `635e1e7`; user requested the next work. Actual host: Windows
`10.0.26300`. Clean `main` at inspection. This ticket prepares the recorded next
checkpoint, combined M2/M3 target-Mac acceptance; it does not execute that gate.

Expected behavior: an operator can follow one runbook using existing disposable
tools and tests, with separate records for real sleep, external timing and joined
recovery/rewards/corrections. No product/default change, database mutation,
service restart, migration or application Undo behavior is introduced.

Read repository guidance, shared progress, build/review/roadmap/README and current
M2/correction reviews. Checked the historical M0 timer policy and existing probe,
browser fixture and service commands. Added
[the runbook](../MAC_CORE_VERIFICATION.md), linked it from README and updated
shared progress. Existing reviews remain historical evidence.

Checks: `git status --short --branch`, recent commit log and complete working/
staged diffs inspected; documentation links, referenced paths/options and
`git diff --check` checked. No application suite rerun or new test: this is
documentation-only preparation. Full-core and frontend totals in the October 23
review are historical, not new results for this session.

Preparation decision: **Pass** for the runbook. Combined M2/M3 acceptance:
**Fail / not passed**, because required target-Mac hardware/operator observations
are absent. M1 operator certification is also pending. The user explicitly chose
to prepare the Mac verification handoff; run it on the target Mac and review its
evidence before advancing M4. Backup/restore remains not started. The user
subsequently authorized committing and pushing this documentation-only handoff
against `635e1e7`. No release readiness claimed.
