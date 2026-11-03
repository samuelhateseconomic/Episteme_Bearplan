# BearPlans — first Figma prototype

Built November 1, 2026 for the user's “build the prototype first” request.
This is an editable review draft; application implementation is separate.

[Open the prototype](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB/BearPlans?node-id=5-3972&starting-point-node-id=5%3A3972&page-id=2%3A5&scaling=scale-down)
or [open the free editing canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=50-4633).
Start with **Start here · Today** in Figma's flow list.

The [original 77/100 evaluation](../docs/reviews/2026-11-01-ux-expert-evaluation.md)
and [24-ticket repair plan](BEARPLANS_UX_REPAIR_PLAN.md) define the refinement.
The repaired native wiring now reflects planned-week Done, reviewed next-week
carryover defaults and frozen Stats Missed. Use the [review launcher](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB/BearPlans?node-id=141-7346&starting-point-node-id=141%3A7346&page-id=2%3A5&scaling=scale-down)
to reset between bounded examples. [R21 evidence](../docs/reviews/2026-11-02-ux-r21-wiring.md)
separates installed-action models/static renders from actual interaction.
[Independent static review](../docs/reviews/2026-11-02-ux-r22-static-review.md) scored
87.98/100 with no unresolved required static P1 in its reviewed scope. Current
status is in [PROGRESS](../docs/PROGRESS.md); actual walkthrough/user acceptance and
final implementation handoff remain separate gates.

## What to review

- Today's task density, prominent streak and collapsed earlier work.
- Compact gray, struck-through completed rows; reopen the reading task.
- Projects drawer: Rename, compact Add project, Active/Done and partial parents.
- Done → year → month → planned week, with current completion separate from history.
- Compact Week and the wide seven-column reference, including the footer.
- Calm Track, recovery, on-demand rewards, Stats and Assistant layouts.

## Useful starting points

| View | Editable frame |
| --- | --- |
| Today | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-3972) |
| Completed Today | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-4109) |
| Projects | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-4847) |
| Done by planned week | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-4951) |
| Week | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=6-1802) |
| Wide Week reference | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=13-710) |
| Track | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=7-2586) |
| Interrupted session | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=7-2733) |
| Stats | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=7-3036) |
| Assistant answer | [Open](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=7-3390) |

The six pages are Canvas · Flows, Brief, Foundations, Components, Screens, and
Review and Handoff. Canvas · Flows opens first and holds **89 product/state frames at
800 × 900 plus a separate review launcher** in native flow sections on a free two-dimensional canvas. The six
main workspaces run left to right; supporting flows occupy labeled areas below.
There is no enclosing page-sized frame. Existing prototype frame IDs and links
are preserved. Screens holds
**46 static responsive/theme/stress references**, last reviewed in R20, including
640px compact, 800px split, 1440px wide and enlarged-text fixtures. These
references are not separate fully wired responsive prototypes.

## November 1 review corrections

[Prepare discussion](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-5292)
keeps completed Read alongside its siblings above the footer, with only one
visible active/completed representation. The matching Reopened child and Saturday
states are repaired too; checked Read controls reopen in place. The canvas layout
follows the user's AI Usage Hub reference as an open editing workspace.
[Scoped evidence and remaining interaction checks](../docs/reviews/2026-11-01-figma-discussion-and-canvas.md).

## Representative journeys

1. Today → task Start → Track → Start countdown → Pause → Plan → Open timer.
2. Projects → + Add task → prefilled task details → one Save → Today.
3. Complete **Read the primary source** → inspect the compact row → Week → reopen.
4. Projects → Done → planned week → representative leaf reopen.
5. Week → selected Read reorder example or Move date → conflict/cancel/result.
6. End Week → review/cancel/close → frozen history → explicit carryover selection,
   review and Apply. Next week starts empty until the demonstration applies it.
7. Named interruption/sleep flows → explicit Continue/Resume or confirmed finish.
8. Forest/shop, Stats/correction, and Assistant answer/sources/error examples.

Use the reset launcher between independent examples. Read/Theme/Chapter have
shared completion demonstrations; other tasks and combinations have partial or
static coverage. Fields use prefilled states, and arbitrary typing, free dragging,
real timers, persistence, purchases and model generation are not implemented here.
The read-only Assistant layout is a deliberate design subset; the current app's
M5 Apply/Undo actions remain outside this sample.

## Review boundaries and handoff

Structural and scoped visual checks passed, including the repaired compact Track
fields. Browser presentation could not be launched by the computer-control tool,
so actual clicks, scrolling, keyboard execution, focus transfer and arbitrary
state combinations remain unverified. This is not full roadmap acceptance.

SF Pro was advertised but returned missing-font errors; Helvetica Neue was not
available. **Inter is the documented Figma fallback**, with the app's system-font
direction preserved for later implementation. Measurements and cross-month filing
remain proposed defaults until reviewed by the user.

Exact returned asset/frame/state IDs and structural evidence are in the
[node ledger](design/figma-node-ledger.json). Product rules and remaining acceptance
are in the [canonical UX plan](BEARPLANS_UX_PLAN.md), current status is in
[shared progress](../docs/PROGRESS.md), and actual checks/limitations are in the
[prototype review](../docs/reviews/2026-11-01-figma-prototype.md).

No application source, data, service, core-trial copy, commit or push was changed
by this Figma work. Concurrent application changes in the checkout remain separate.
