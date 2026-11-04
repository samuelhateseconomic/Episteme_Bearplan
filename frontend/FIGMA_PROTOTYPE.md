# BearPlans — first Figma prototype

Built November 1 and refined through November 3, 2026. The bounded repair
walkthrough and scoped handoff are delivered; application implementation is separate.
Start with the [refined UX handoff](BEARPLANS_UX_HANDOFF.md) and
[exact asset/state inventory](design/handoff-inventory.json).

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
status is in [PROGRESS](../docs/PROGRESS.md). The bounded R23 walkthrough and R24
handoff are complete; full original checkpoint and production acceptance remain separate.

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

Structural and scoped visual checks passed, including repaired compact Track fields.
The user reported success for bounded core click/scroll journeys, with preview-
cancellation repaired and rechecked. The agent had no browser/computer-control
interface; keyboard/focus, arbitrary combinations and runtime data/timing remain
unverified. This is not full original roadmap or application acceptance.

The [November 3 continuation](../docs/reviews/2026-11-03-ux-r23-continuation.md)
records the user's acceptance of weekday/Outline spacing, completed-Read compact/
dark renders, and task-save recovery repairs. Its 60 installed-reaction Map checks
pass; actual preview execution is distinguished from those checks. The later
[preview-cancellation repair/recheck](../docs/reviews/2026-11-03-ux-r23-continuation.md#preview-cancellation-repair-and-targeted-user-recheck)
adds explicit Keep week open/Skip carryover labels, source-board dismissal and
stale-preview guards; its 111 model cases pass and the user reported returning
to the open week. The later user-reported carryover sequence is recorded in the
same review; overall acceptance remains in shared progress. Original review
records remain historical evidence. The [R24 reconciliation](../docs/reviews/2026-11-03-ux-r24-handoff.md)
and [frontend handoff](BEARPLANS_UX_HANDOFF.md) describe the delivered scope.

SF Pro was advertised but returned missing-font errors; Helvetica Neue was not
available. **Inter is the documented Figma fallback**, with the app's system-font
direction preserved for later implementation. Measurements and cross-month filing
remain proposed defaults until reviewed by the user.

Exact returned asset/frame/state IDs and structural evidence are in the
[node ledger](design/figma-node-ledger.json). Product rules and remaining acceptance
are in the [canonical UX plan](BEARPLANS_UX_PLAN.md), current status is in
[shared progress](../docs/PROGRESS.md), and actual checks/limitations are in the
[prototype review](../docs/reviews/2026-11-01-figma-prototype.md).

No application source, data, service or core-trial copy was changed by this Figma
work. The user authorized committing and pushing the November 3 design checkpoint;
Git records the result. Concurrent unfinished application changes remain separate.


## Settings and Connections extension

The [UX-C02 overview review](../docs/reviews/2026-11-03-settings-overview.md)
adds six 800×900 Light states in a separate
[free canvas flow section](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-5718).
[Open Settings](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=219-5719)
or use the gear on any of the 89 prototype workspace states, including Track,
Stats and Assistant. The UX-C02 audit covered 95 navigation headers
(89 open Settings; six Settings references close it); UX-C03 adds four review headers.
The earlier 89-product/46-reference handoff remains its original baseline;
the extension does not rewrite its acceptance evidence.

Working-state Manage/Hide and overlay close routes are installed. UX-C03 wires
bCourses setup and management below; UX-C04 adds the Google flow and UX-C05 the
Pause/removal effects. Responsive/user verification follows in UX-C06; other overview error/busy
commands remain references.
[Exact extension IDs](design/settings-connections/overview-inventory.json) and
[installed-structure/model checks](design/settings-connections/overview-audit.json)
distinguish checked metadata from unverified actual preview behavior.


### bCourses setup extension — UX-C03

[Flow review](../docs/reviews/2026-11-03-bcourses-settings-flow.md) ·
[exact inventory](design/settings-connections/bcourses-inventory.json) ·
[installed-action audit](design/settings-connections/bcourses-audit.json) ·
[31 scoped action models](design/settings-connections/bcourses-models.json).

- [Connect / Replace canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=234-6386)
- [Recovery examples and review starts](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=234-6387)
- [Course / assignment-review canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=234-6388)
- [Connect sample](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=234-6389&starting-point-node-id=234%3A6389&scaling=min-zoom)
- [Working Settings entry](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=5-3972&starting-point-node-id=5%3A3972&scaling=min-zoom): gear → Manage bCourses → Replace token / Choose courses / Review assignments.

21 540px dialogs and four 800×900 Light work views. Click an empty token field to
use the fixed masked sample; no real typing, token storage or bCourses access.
Direct reference starts lack the original invoking background. Main source Add
and deadline choices are finite interactions; disabled work actions, ordinary
review tabs and unsampled groups remain references for UX-C06. Actual preview,
keyboard/focus and broader widths/themes remain pending. New review views retain
Settings; current Navigation coverage is 99/99 headers. The earlier 95-header audit
is historical evidence before these four views were added.


### Google setup extension — UX-C04

[Flow review](../docs/reviews/2026-11-04-google-settings-flow.md) ·
[exact current inventory](design/settings-connections/google/inventory.json) ·
[installed-action audit](design/settings-connections/google/audit.json) ·
[59 aggregate models](design/settings-connections/google/models.json).

[Open the sample guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=255-6835&starting-point-node-id=255%3A6835&scaling=min-zoom)
or inspect the [file](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=251-6374),
[browser](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=251-6375) and
[calendar/account](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=251-6376)
flow groups. Working Google management → Sign-in & calendars is wired; setup
Connect uses the fixed sample-file flow. There are 47 540px references plus the
800×778 guide. No real file picker, credentials, browser authorization or provider
work. C04 guide starts reset five Google variables plus three Google policy/operation
variables added by C05; the eight full review resets include these too. Browser-return outcomes use explicit guide simulations;
waiting does not become connected by a timer. Actual preview/accessibility,
responsive/Dark and user acceptance remain pending. Pause/Disconnect effects are
provided by UX-C05 below. Earlier Settings-gear evidence remains 99/99 headers.


### Pause, offline and removal extension — UX-C05

[Flow review](../docs/reviews/2026-11-04-connection-recovery.md) ·
[exact inventory](design/settings-connections/recovery/inventory.json) ·
[installed actions](design/settings-connections/recovery/sources.json) ·
[58 action models](design/settings-connections/recovery/models.json).

[Open the recovery guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=270-6806&starting-point-node-id=270%3A6806&scaling=min-zoom).
36 540px Light states and a 19-start 800×738 guide. Working Manage Google →
Pause/Sync once and Sign-in & calendars → Sync & access enter the flow;
Manage bCourses → Remove token opens reviewed local removal. Explicit Cancel,
request/receipt, unknown-result recovery and local/provider removal results remain distinct.

Busy samples use fixed 2.5-second replies. No credentials, provider work, restart
or real timer runs. User reported the main Pause → Sync once → Resume clear;
saved Pause surviving restart and one-shot retaining Pause are confirmed intent.
Other error/removal walkthroughs, complete contexts/themes and accessibility remain
UX-C06 follow-ups. Source lock-timeout/automatic-reader gaps are recorded for later
app implementation. The historical C02–C04 audits remain their original evidence;
C05 contains the changed installed sources and current relevant bounds.

## Settings context/theme review — November 4

[Open the consolidated guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=293-8853&starting-point-node-id=293%3A8853&scaling=min-zoom)
or read the [connection implementation handoff](plans/settings-connections/HANDOFF.md).
Six flow sections add 54 editable window references at 640×800, 800×900 and
1440×900 in Light/Dark. The 800×1284 guide provides 18 isolated starts plus links
to original provider/recovery guides, with static focus/disabled/loading/error
specimens. Existing flow IDs and page organization remain.

Scoped navigation retains Today/Track origin and changes only isolated sample
state; other controls are disclosed visual references. The user reported compact
scroll/cancel/session return, Dark readability and selected provider recovery/scope
examples clear. This does not certify real session identity, keyboard/focus, browser
resizing/zoom, provider access or restart. [Review and evidence](../docs/reviews/2026-11-04-settings-context-handoff.md).
