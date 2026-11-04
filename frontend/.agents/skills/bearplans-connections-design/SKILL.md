---
name: bearplans-connections-design
description: Plan, create or review BearPlans Settings and bCourses/Google connection UX in Figma. Use for connection design work, not ordinary frontend changes or runtime integration implementation.
---

# BearPlans connection design

Deliver the requested connection UX plan, review or Figma change. A saved plan
never starts application implementation or a live provider connection.

## Establish scope and current evidence

Resolve the Git root, then read [root guidance](../../../../AGENTS.md),
[frontend guidance](../../../AGENTS.md) and
[shared progress](../../../../docs/PROGRESS.md). Inspect Git status, recent commits,
relevant complete diffs and untracked work; reconcile concurrent source before
calling a setting implemented or missing.

Start at the [feature entry point](../../../plans/settings-connections/README.md).
Use [SPEC](../../../plans/settings-connections/SPEC.md) for the current product
contract and confirmed/proposed distinctions. Read the relevant design ticket in
[EXECUTION_PLAN](../../../plans/settings-connections/EXECUTION_PLAN.md) and its
checks in [TEST_PLAN](../../../plans/settings-connections/TEST_PLAN.md). Keep status
in shared progress rather than copying it into this skill or those definitions.

## Apply the existing design workflow

Use the existing [BearPlans design skill](../../../../.agents/skills/bearplans-design/SKILL.md)
for Figma procedure and handoff. Load the installed Figma skills applicable to the
actual operation, including `figma-use` before its tool and the composition or
library workflow when needed. Do not recreate these manuals here.

Keep one design ticket active and one Figma writer; independent agents may review.
Reuse the existing editable system and flow canvas. Record exact returned IDs in
the existing ledger. Inspect the live canvas before retrying uncertain mutations;
do not replay archived executed scripts as a shortcut to resuming work.

Reconcile each proposed control and displayed state against current source and the
SPEC. Document unsupported behavior as future engineering work. Use synthetic
connection data; keep credential values and real provider operations out of a
prototype. Match recovery, cancellation, navigation and local-runtime behavior to
the contract without inventing account identity or successful access.

Render the scoped width/theme/state examples and verify relevant prototype paths.
A written specification, successful write call or simulated transition is not
runtime verification or user acceptance. Follow TEST_PLAN for the evidence boundary.

## Handoff

Record node/evidence links, actual checks and unresolved requirements in a dated
review. Update shared progress and completed records with the next concrete step.
Keep original prototype acceptance and release gates distinct. Application work
uses the [build skill](../bearplans-connections-build/SKILL.md) only when separately
authorized; do not start it on a design handoff.
