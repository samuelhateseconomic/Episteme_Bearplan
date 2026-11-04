# Settings and Connections — agent start here

Organized November 3, 2026. The goal is coherent connection management for the
existing local BearPlans app: bCourses token setup and selected courses; Google
Desktop OAuth setup, calendar/Tasks behavior and Pause / Resume automatic sync.

This package was originally delivered as documentation, a test plan and agent
skills. Saving it did not start Figma or application work. Subsequent explicit
user requests select execution units; read current authorization and PROGRESS
rather than treating this historical scope as a continuing prohibition or the
plan itself as authorization. Live sign-in, provider writes and saved-data work
remain bounded by the user’s actual request.

## Read in this order

1. Root [AGENTS.md](../../../AGENTS.md), [frontend AGENTS.md](../../AGENTS.md) and
   [PROGRESS](../../../docs/PROGRESS.md); inspect Git and relevant unfinished work.
2. [SPEC.md](SPEC.md): stable requirements CON-01–CON-12, confirmed choices,
   proposed defaults, status model, lifecycle and data consequences.
3. [EXECUTION_PLAN.md](EXECUTION_PLAN.md): six design tickets UX-C01–C06 followed by
   a separately scoped application sequence APP-C01–APP-C09. Each unit has inputs,
   ordered actions, checks, deliverables and a completion condition.
4. [TEST_PLAN.md](TEST_PLAN.md): fixture setup, case IDs, expected behavior,
   commands, automation versus manual checks, evidence and failure rules.
5. Load the applicable skill below. Read implementation details only for authorized
   application work; planning a test never means that test has passed.

## Choose the workflow

| Request | Skill and outcome |
| --- | --- |
| Review/plan/draw Settings in Figma | [bearplans-connections-design](../../.agents/skills/bearplans-connections-design/SKILL.md), alongside the existing BearPlans/Figma skills. Deliver the requested design or review only. |
| Implement or verify the local Settings UI and integration contract | [bearplans-connections-build](../../.agents/skills/bearplans-connections-build/SKILL.md). Follow only the separately authorized application unit; preserve concurrent backend work. |
| Review this documentation package | Check scope, links, unique requirements/tickets, test coverage and skill behavior. Do not launch the app or connect an account to validate Markdown. |

Skills are stored inside frontend as requested. The explicit links in
[frontend AGENTS.md](../../AGENTS.md) are the reliable entrypoints; this package
does not claim the host skill catalog has already refreshed.

## Authority and evidence

- SPEC holds product meaning; EXECUTION_PLAN holds stable step definitions;
  TEST_PLAN holds verification scenarios. Do not copy these into a new status file.
- Only [PROGRESS](../../../docs/PROGRESS.md) holds mutable status and the next
  eligible unit. Log finished units in [COMPLETED](../../../docs/COMPLETED.md).
- Record actual checks, environment, commit/diff boundary and limitations under
  `docs/reviews/`. Existing [coherence review](../../../docs/reviews/2026-11-03-settings-connection-coherence.md)
  is source evidence, not runtime acceptance.
- Existing design baseline: [UX handoff](../../BEARPLANS_UX_HANDOFF.md),
  [inventory](../../design/handoff-inventory.json) and
  [node ledger](../../design/figma-node-ledger.json). Preserve IDs and flow layout.
- Source baseline for this package: f375f24 moved credentials; 674db93 committed
  credential setup routes. These are historical source observations; inspect
  current source/tests before resuming. Do not rebuild work already supplied by
  another agent or quote old test totals as fresh evidence.

No active implementation or Figma ticket is created by reading this entrypoint.
