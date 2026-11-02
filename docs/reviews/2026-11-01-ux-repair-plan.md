# UX repair planning review

Date: November 1, 2026. Environment: macOS 26.6.2 / 25G83.
Scope: requested detailed plan only; no Figma/application execution.

**Pass for documentation delivery only.** The repair sequence has 24 small parent
tickets across eight phases, dependencies, original UX mapping, category coverage,
concrete subtasks, observable acceptance, affected frames, recovery and verification.
All repairs remain Not started. UX-32.1 remains In review; original acceptance and
application/release gates are unchanged.

## Inputs and decisions

Read current shared guidance/design skill, progress, canonical brief, Figma index/
ledger, 77/100 evaluation, and latest End Week/carryover/Missed evidence.
Inspected Git status, recent commits, diff summaries and relevant planning changes.
Preserved concurrent source/doc edits.

The plan incorporates immediate post-close choices, all eligible leaves checked,
last frozen source date plus seven calendar days, explicit Review/Apply, re-entry
after Cancel, no deadline changes, frozen Missed and distinct Done counts.
The current M5 app is distinguished from the read-only layout sample; unbuilt
Assistant carryover is excluded. Optional day-minute/priority treatments stay
proposals rather than unconfirmed data rules.

Three independent agents supplied planning/acceptance reviews. Two also reviewed
the actual draft. Necessary corrections were applied: exact per-task Missed wording,
at-closure scope, existing-active-placement exclusions/recheck default, confirmed
session versus finalized time, static readiness before user-executed checks,
carryover re-entry, enlarged-text/reflow coverage, and early contrast repair.
Existing AGENTS/design skill are reused; no new skill or blanket guidance rewrite.

## Files and tracking

- [Repair plan](../../frontend/BEARPLANS_UX_REPAIR_PLAN.md): stable 24-ticket definitions.
- [Canonical brief](../../frontend/BEARPLANS_UX_PLAN.md): repair link and current
  confirmed decisions/page organization; original 36 ticket IDs retained.
- [Progress](../PROGRESS.md): sole mutable repair register and next eligible R01.
- [Completed](../COMPLETED.md): planning completion only.
- [Prototype index](../../frontend/FIGMA_PROTOTYPE.md): evaluation/repair links and
  explicit drift note; existing prototype evidence remains historical.

## Verification

Checks completed:

- `git diff --check` scoped to the six planning/documentation files: Pass.
- Standard-library Python checks: Pass for 199 local links, 24 ticket definitions,
  24 Not-started register rows, valid dependency graph/execution order including
  early R19, original 36 UX ticket IDs, 13-category coverage, Markdown whitespace
  and final newlines.
- Draft reviews checked the actual plan file; necessary corrections are recorded
  above. Content preserves current-versus-historical facts, explicit Apply,
  proposed defaults and pending manual evidence.
No application tests, service launch, Figma write, database operation, dependency
installation, commit or push. Planned tests/frames are not represented as completed.
