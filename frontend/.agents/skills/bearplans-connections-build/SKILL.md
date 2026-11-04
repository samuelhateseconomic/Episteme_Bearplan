---
name: bearplans-connections-build
description: Implement or review separately authorized BearPlans Settings and bCourses/Google connection changes across React and the local API. Use for runtime connection settings work, not Figma-only planning or unrelated integrations.
---

# BearPlans connection build

Work only on the application change or runtime review authorized by the user.
Plans, skills and Figma handoffs do not themselves authorize implementation.

## Establish the build boundary

Resolve the Git root and read [root guidance](../../../../AGENTS.md),
[frontend guidance](../../../AGENTS.md) and
[shared progress](../../../../docs/PROGRESS.md). Inspect Git status, recent commits,
relevant complete diffs and untracked work. Reconcile concurrent source and checks
before treating an older design snapshot as the current application.

Start at the [feature entry point](../../../plans/settings-connections/README.md).
Use [SPEC](../../../plans/settings-connections/SPEC.md) for product rules and
confirmed/proposed distinctions, the authorized application ticket in
[EXECUTION_PLAN](../../../plans/settings-connections/EXECUTION_PLAN.md) for scope,
and [TEST_PLAN](../../../plans/settings-connections/TEST_PLAN.md) for acceptance.
Keep one small ticket active in shared progress. Do not invent a new tracker here.

Before implementation, state the observable acceptance scenario, affected records,
any default/rule changes and failure/recovery behavior. Inspect the relevant
`src/` view and [API client](../../../src/api.ts), then follow the existing routes,
platform adapters, sync service and domain functions under `backend/`. Do not
move validation or persistence policy into the interface to bypass shared rules.

## Implement and verify the scoped behavior

Extend the current React/API architecture and dependency setup. Preserve existing
connection capabilities, local task identity and unrelated in-progress changes.
Reconcile displayed setup, authorization, sync and recovery states with actual
backend support; a disabled mock control is not a completed feature.

Follow the root credential/data/request-safety rules rather than copying them
here. Use fake credentials and disposable data for ordinary verification; do not
inspect or expose saved credential values. Live provider calls need their own
existing authorization and are not granted by this skill or plan.

Use TEST_PLAN's relevant frontend, backend, persistence/restart, failure and race
scenarios. Run the existing frontend scripts from the repository root as required:
`npm --prefix frontend test`, `npm --prefix frontend run typecheck`, and
`npm --prefix frontend run build`. Backend/schema changes also need the root
checks and affected regression coverage. Do not claim old totals as fresh results.

## Review and handoff

Record actual commands/results, environment, evidence and limitations in a dated
review. Update shared progress and completed records before stopping. Distinguish
implementation verification, live/operator acceptance and Figma evidence; missing
required evidence stays explicit. Commit/push only under the user's authorization.

For a connection design task instead, use the
[design skill](../bearplans-connections-design/SKILL.md); do not load both skills
merely because the work is in `frontend/`.
