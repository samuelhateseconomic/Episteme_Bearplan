---
name: bearplans-design
description: Plan, create, revise, or review BearPlans Figma screens, components, and prototypes using its UX plan and application rules. Use for BearPlans design work, not ordinary app debugging or implementation.
---

# BearPlans design

Use this workflow for the existing local BearPlans app. The requested outcome may
be a plan, documentation, read-only review, or an authorized Figma change; complete
only that outcome. Saving a plan or creating agent guidance does not start Figma
work or authorize application changes.

## Establish the active work

Resolve the current repository root from the working checkout, using
`git rev-parse --show-toplevel` when available. If the working directory is stale
or outside the checkout, locate the root from this repo-local skill's location
and verify `AGENTS.md`, `frontend/package.json`, and `backend/`. Do not reuse a
machine-specific path from an earlier chat.

Read these paths relative to that root:

- `AGENTS.md` and applicable nested guidance: shared rules and preservation duties.
- `frontend/BEARPLANS_UX_PLAN.md`: canonical design brief, ticket definitions,
  confirmed decisions, defaults, and acceptance scenarios.
- `docs/PROGRESS.md`: current ticket, actual status, evidence, and next action.

Inspect the current Git changes and relevant source/evidence before relying on an
older handoff. Latest explicit user decisions govern; record contradictions in
progress rather than silently revising behavior. If the canonical plan is absent,
finish independent discovery and identify the missing brief before screen work.

Keep one ticket active. Independent agents may inspect or review that ticket;
assign one Figma writer and serialize canvas mutations. Use the review checkpoints
already agreed in the plan without seeking repeat approval for equivalent routine
steps inside the authorized scope.

## Select the Figma workflow

Use the installed Figma skills for their tool mechanics, loading only the relevant
ones rather than copying their manuals into this skill:

- `figma-create-new-file` before creating a Design file.
- `figma-use` before any `use_figma` call.
- `figma-generate-design` with `figma-use` for composed screens and views.
- `figma-generate-library` with `figma-use` for reusable components, variants,
  variables, and styles. Load both companion workflows when a ticket includes
  library assets and assembled screens.

Resolve the intended file and account through the supported tools when the
request reaches authorized Figma work. Follow the applicable skill's session,
library discovery, font, variable, and retry rules. If a required skill or tool is
unavailable, report the exact missing capability and continue independent work
that stays within scope.

## Create and verify the scoped result

Start from the ticket's acceptance scenario and target widths. Reuse compatible
components and tokens, assemble with auto-layout, and keep text, controls, and
hierarchy editable. Use screenshots as review evidence, not as flattened screen
deliverables. Use synthetic tasks and contexts for examples unless the user has
selected other content.

Keep a node ledger outside Figma containing the file key, applicable session ID,
exact returned page/component/variable/frame IDs, and deterministic names. Record
its location in progress. Before retrying or resuming after uncertain execution,
read the ledger and inspect the actual canvas; reconcile existing objects before
creating more. Modify or remove only objects whose identity and ownership are
established. Do not use the ledger as a competing task tracker.

Read [review-and-handoff.md](references/review-and-handoff.md) when reviewing a
composition, connecting prototype flows, or preparing handoff. Inspect the rendered
result after a coherent composition and again after a relevant repair. Validate
structural evidence and actual interactions where supported; a successful tool
call alone does not establish completion.

Distinguish simulated prototype behavior from implemented app capabilities.
Document the engineering implications of new interactions without implementing
APIs, storage, application code, or additional Assistant capabilities as a side
effect of design work.

Close the ticket with its reviewed node links, checks actually performed, findings,
and next step in `docs/PROGRESS.md`, and log the finished ticket at the top of
`docs/COMPLETED.md`. Put detailed evidence in the dated review
record and stable design definitions in the canonical plan. Preserve existing
release and hardware acceptance status; design evidence certifies design only.
