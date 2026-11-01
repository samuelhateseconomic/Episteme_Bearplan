# Review and handoff

Read this reference for a screen/component review, a connected prototype, or the
final design handoff. Use the active ticket's inventory and acceptance criteria;
checks unrelated to that ticket remain later work.

## Establish what is being reviewed

Record the ticket ID, requested outcome, target file and exact node IDs, current
brief decisions, viewport dimensions, and theme. Use actual reviewed dimensions;
do not describe generic frame sizes as evidence from a particular MacBook.

For resumed work, compare the node ledger with the canvas before changing objects.
A useful ledger records file/session identity, object IDs and names, component or
variable relationships, and the last validated composition. Keep human task
status in `docs/PROGRESS.md` only.

## Verify the design

- Inspect normal-size rendered frames for readable titles/context, clipping,
  overflow, empty assets, crowding, alignment, and sufficient contrast.
- Check the ticket's wide/narrow layouts and theme modes. Expandable panels and
  task details must leave a clear way back to the work list.
- Check applicable default, hover, selected, keyboard-focus, disabled, saving,
  empty, and error states. Errors and recovery choices stay available when they
  affect the next action; secondary explanations may open on demand.
- Check editable text/hierarchy, auto-layout behavior, component instances,
  relevant properties/variants, and token/style bindings. Confirm the actual
  assets used rather than accepting a flattened visual approximation.
- Use the canonical brief and root guidance to verify completion, scheduling,
  time/recovery, rewards, corrections, and frozen-history behavior. Apply the
  latest agreed design decisions; do not infer new product rules from appearance.

Take one useful screenshot per coherent composition, plus a new screenshot after
an actual visual repair. Recheck affected dependents if a shared component changes.
Do not repeat unchanged audits or screenshots solely to accumulate evidence.

## Check prototype flows

For each in-scope journey, record its named start frame, intended action, resulting
state, and return/cancel route. Exercise the links in the supported preview rather
than only inspecting reaction metadata.

For drag/reorder examples, distinguish representative Figma transitions from free
arbitrary drag behavior in the future app. Show the source, destination/insertion
cue, resulting order/day, and cancellation or conflict state required by the
brief. Check the keyboard/date alternative in the design notes; a pointer-only
Figma preview does not prove keyboard or assistive-technology support.

Keep simulated task saves, timers, recovery, purchases, corrections, and Assistant
answers clearly bounded to prototype data. Preserve meaningful busy/error/retry
states in the design; do not claim real persistence, timing precision, model
reliability, or application regression coverage from a prototype walkthrough.

## Evidence and outcome

Use a dated record under `docs/reviews/` for the coherent review checkpoint. Keep
it proportional and include:

- Ticket(s), file/node links, reviewed viewport/theme, and actual checks.
- Screenshots or prototype flow links supporting the result.
- Findings with user impact, repairs made, and any remaining limitation.
- **Pass**, **Pass with follow-ups**, or **Fail** against the scoped design
  acceptance criteria. Missing required evidence is not a pass.

In progress, link this record and record the current ticket outcome and next
eligible step. Do not duplicate a full status table inside the skill or Figma.

## Implementation handoff

Deliver a screen/state inventory with exact Figma links, reusable component and
property inventory, semantic token/style mapping, responsive behavior, interaction
notes, content rules, and the reviewed journey checklist. Identify which behavior
already exists in the app and which needs a later engineering ticket.

Flag interface/data implications when the design introduces capabilities such as
manual ordering, combined task-and-planning save, or grouping across saved planned
weeks. Describe intended behavior and failure/recovery expectations; leave app
implementation to its separately scoped plan rather than inventing endpoint or
migration details during a design-only ticket.

The final handoff identifies remaining follow-ups and the reviewed design version.
It does not advance unrelated application, core-trial, model, or hardware gates.
