# Compact completed-task design — November 1, 2026

**Pass for documentation refinement only.** No Figma or application change.

The user's late reply confirms planned-week Done and adds compact gray completed
rows containing a struck-through title and operable checked checkbox. Unchecking
reopens the same task and restores normal eligible metadata/actions. Updated the
[canonical plan](../../frontend/BEARPLANS_UX_PLAN.md), UX-08/UX-18 criteria and
walkthrough, [root guidance](../../AGENTS.md) and shared progress. Kept the
collapsed completed section; style applies to its expanded current-work rows.
Parent containers retain derived completion; historical cards stay read-only.

Independent review found no contradiction. Retain readable gray contrast and
accessible context; maintain focus and pending/error feedback through reopening;
preserve task/placement identity, parent progress and any active timer. The
reusable skill remains unchanged because it already reads the canonical brief.

Environment: actual Darwin/macOS. Base HEAD `57aaa8e`. Tree was clean at inspection.
No unrelated source, existing evidence, index or HEAD changed; no commit/push.

## Checks actually run

- `git diff --check -- AGENTS.md frontend/BEARPLANS_UX_PLAN.md docs/PROGRESS.md`:
  passed. New review text also checked for whitespace/final newline.
- Temporary standard-library checker at
  `/private/tmp/bearplans-completed-ux-20261101/check.py`: all local links in the
  four affected Markdown documents resolve; all 36 ordered ticket definitions
  remain; original progress is preserved after the inserted refinement; all
  other pre-existing file hashes and Git index/HEAD match the baseline.
- Read the exact scoped diff and received an independent read-only design sanity
  review: no actionable issue.

No application suite/build, Figma screenshot/prototype, real completion/reopen,
accessibility execution, timer or hardware test was run for this documentation
change. UX-05 onwards remain Not started; existing application and M5 acceptance
records are not re-certified or rewritten.
