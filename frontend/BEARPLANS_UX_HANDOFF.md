# BearPlans — refined UX handoff

Recorded November 3, 2026, America/Los_Angeles. This is the scoped R24 design
handoff after the bounded R23 user walkthrough. It defines implementation intent;
it does not authorize or start application changes. Current work/gates belong only
in [PROGRESS](../docs/PROGRESS.md). Stable decisions remain in the
[UX plan](BEARPLANS_UX_PLAN.md) and [shared guidance](../AGENTS.md).

## Open and identify this version

- [Free editing canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=2-5).
- [Review launcher](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&starting-point-node-id=141%3A7346).
- [Canvas handoff annotations](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=22-85).
- [Exact asset/state inventory](design/handoff-inventory.json): 89 product/state
  frames, 46 static references, 38 component/set nodes, 10 text styles, 26 selected
  semantic/dimension tokens, property contracts, theme aliases and 11 named starts.
- [Node ledger](design/figma-node-ledger.json) and
  [execution evidence](design/refinement-execution.json). Latest repair keys are
  r23Resume20261103 and r23Cancel20261103; R24 reconciliation is recorded separately.

The baseline design commit is `23faa2d`; November 3 refinements/handoff are
uncommitted. Concurrent application commits are outside this design version.
The prototype's synthetic service date remains **November 1, 2026**. Do not use
its date literals in production. One Figma writer has been used; original frame
IDs and ten original named starts were preserved, with one added review launcher.
The canvas is a free two-dimensional workspace with flow Sections, not a vertical
slide deck or one enclosing page-sized frame.

## Reviewed direction and evidence

The user accepted the demonstrated minimal, Today-first direction through scoped
reports. R23 is a formative walkthrough with follow-ups, not a timed usability
study or full original UX-01–36 acceptance. The original 77/100 assessment rose to
88/100 in the independent R22 static review; this heuristic score is not measured
task success and was not rescored from the latest user reports.

| Journey area | Evidence and practical boundary |
| --- | --- |
| Find today's work and focus | Lower rows, Start/pause/return reported successful; compact eighth/lower tasks reachable in the 20-row reference. Reference task buttons are unwired. |
| Capture task | One fixed Draft seminar questions Save, failed-save Retry, retained blocked-day details and empty-name validation were reported clear. Arbitrary typing is not demonstrated. |
| Next week/Today | Weekly navigation reported without interaction trouble; original weekday/Outline spacing finding was repaired and accepted. |
| Order and date move | Representative Read reorder/Move/cancel/conflict reported without interaction trouble. Free arbitrary drag performance remains untested. |
| Project hierarchy | Read completion/reopen under Prepare seminar discussion and crowded project scrolling reported successful. Parent arithmetic is supported by domain/model review, not a separately measured user observation. |
| End Week/carryover | Initial preview-cancel finding retained. After bounded repairs, Keep week open returned to an open board; choices/redating, Review/Skip, re-entry/Apply and next-week result reported clear. |
| Frozen Missed | Later Read completion changed current status while historical Missed/closed history stayed, by user report. |
| Task completion during session | The same session and controls remained available after completing Read, pausing and reopening. |
| Interruption review | The 120-second confirmed / 300-second uncertain example and explicit continuation were reported clear. No real sleep or clock evidence. |
| Stats/Assistant | Scopes/detail, answer/Sources and question retention after Cancel/error reported clear. No live inference or persistent chat is demonstrated. |

Detailed user reports, findings and repairs:
[R23 November 2](../docs/reviews/2026-11-02-ux-r23-walkthrough.md),
[R23 November 3](../docs/reviews/2026-11-03-ux-r23-continuation.md).
Latest installed-reaction Map model: **111 pass / 0 fail**. The 44 time and 601
navigation-return checks are earlier evidence, not rerun for R24. These models
interpret actual native reactions; they do not click Figma presentation or test
storage. The agent had no working browser/computer-control interface. Actual user
window/zoom, timing and input method were not reported.

## Screen and state map

Every product and reference node has a direct URL and actual dimensions in the
inventory. The six main 800×900 workspaces remain editable text, vectors,
auto-layout and component instances; no complete-UI image fill was found in the
scoped main-workspace inspection. This is not a claim that all 135 frames were
re-rendered at handoff.

| Area | Main frames and state examples |
| --- | --- |
| Today | [5:3972](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-3972); completed 5:4109; Earlier 5:4258; running 5:4551; failed reopen 5:4694; session/completion combinations 14:3112–14:3471. |
| Projects/capture | [5:4847](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-4847); Rename 5:5166; Add project 5:5229; details 5:5491; validation 5:5567; failed Save 9:6023; blocked planned day 124:7050; child completion/reopen 5:5292/9:6097. |
| Done | [5:4951](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-4951); previous planned week 5:5369; no planned week 5:5430; reopened 5:5054. |
| Week | [6:1802](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=6-1802); Mon–Sat selectors; reorder 6:2004/6:2136, reverse 147:7536; Move 6:2420/6:2266/conflict 6:2481; saving/failure/uncertain 70:4678/70:4844/70:5009. |
| Closure/history | [6:2541](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=6-2541); completed preview 14:3649; frozen 6:2600/14:3706; History 14:3767. |
| Carryover | [6:2634](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=6-2634); review 6:2683; one-selection 17:4256/17:4308; date 91:5667; changed/failure/uncertain 91:5720/91:5773/91:5826; next week 6:2761/17:4359/23:4666. |
| Track | [7:2586](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=7-2586); picker 105:5618; running 7:2639; paused 7:2686; review 7:2733; sleep 7:2780; finish 7:2827; failure/uncertain 105:5656/105:5693. |
| Rewards | Forest 7:2879; Shop 7:2929; failure 7:2980. These open within Track. |
| Stats | [7:3036](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=7-3036); sessions/detail 7:3121; correction/review/saved 7:3210/7:3247/7:3282. |
| Assistant | [7:3316](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=7-3316); generating 7:3355; answer 7:3390; Sources 7:3434; unavailable 7:3482; retained draft 110:5638. |

## Components and foundations

Use the existing component sets and semantic variables before creating replacements.
Full variant IDs and dimensions are in the inventory. Source component default text
is placeholder content; supply task identity/title/context consistently. In
particular, Task row still exposes a legacy Project property alongside Context;
do not let its old placeholder override current project/parent context.

| Component set | Owner ID | Exposed contract |
| --- | --- | --- |
| [Button](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=3-241) | 3:241 | Tone: Primary/Secondary/Quiet; State: Default/Hover/Focus/Disabled/Loading; Label#3:54. |
| [Checkbox](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=3-258) | 3:258 | Checked and Focus: false/true. |
| [Input](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=3-280) | 3:280 | Default/Focus/Error/Disabled; Label#3:78 and Value#3:79. |
| [Task row](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=3-341) | 3:341 | Active/Selected/Completed/Parent/Long title/Weekly; Title#3:91, Context#3:92 and legacy Project#8:0. |

Supporting assets: Disclosure 3:346, expanded Disclosure 164:8311, Feedback 3:351,
Streak 3:381 and Weekly column card 12:33. Active/Selected/Weekly rows are 59px in
the draft; Completed is 40px, Parent 59px and long-title sample 80px. Long content
must grow rather than inherit a fixed sample height. Visible Figma button variants
are 36px and checkbox frames 32px; actual browser target size/focus behavior must
be verified during implementation. A component variant's existence does not prove
hover/focus/disabled semantics work in the app.

Semantic colors use Light/Dark aliases, not separate ad hoc screen palettes.
These are the live snapshot values, not a new production color API:

| Token | Light | Dark | Semantic variable |
| --- | --- | --- | --- |
| color/bg | #F6F4EF | #161917 | VariableID:2:32 |
| color/surface | #FFFFFF | #1F2421 | VariableID:2:33 |
| color/text | #1F2421 | #E8EBE8 | VariableID:2:34 |
| color/muted | #5D655F | #A3ABA5 | VariableID:2:35 |
| color/border | #DCD8CF | #353B37 | VariableID:2:36 |
| color/accent | #2F6B4F | #6CBB93 | VariableID:2:37 |
| color/onAccent | #FFFFFF | #0E1A13 | VariableID:2:38 |
| color/soft | #E8EEE7 | #263C2E | VariableID:2:39 |
| color/error | #A4262C | #FF8A8F | VariableID:2:40 |
| color/errorBg | #FBEDEB | #40252A | VariableID:2:41 |
| color/focus | #1A5FB4 | #8AB4F8 | VariableID:2:42 |

Collections: primitive palette VariableCollectionId:2:7; semantic colors
VariableCollectionId:2:8 (Light 2:1, Dark 2:2); dimensions VariableCollectionId:2:9.
Spacing tokens: 0, 4, 8, 12, 16, 24, 32, 40, 48, 64. Radius tokens: 4, 8, 12, 16,
999. Preserve semantic roles and error/focus distinctions when mapping to CSS.
The R19 historical dark-accent samples measured 5.18 on soft and 7.80 for onAccent;
this is not a complete accessibility audit.

Text styles use the Figma fallback **Inter**. Keep the app's system-font direction;
SF Pro returned missing-font errors and Helvetica Neue was unavailable in Figma.
Fallback selection and exact measurements remain proposed defaults.

| Text style | Size/line-height, px | Weight/style |
| --- | --- | --- |
| Display | 64/72 | Medium |
| Hero | 40/48 | Semi Bold |
| Title | 28/34 | Semi Bold |
| Heading | 20/26 | Semi Bold |
| Body | 15/21 | Regular |
| Body strong | 15/21 | Semi Bold |
| Context | 13/18 | Regular |
| Label | 13/18 | Medium |
| Caption | 11/15 | Medium |
| Completed task | 15/21 | Regular |

Completed task presentation also requires readable gray and strikethrough plus an
enabled checked checkbox; do not rely on font style or color alone for its state.

## Responsive and scrolling contract

640×800 is the compact reference, 800×900 the primary split-window reference and
1440×900 the wide reference. These are fixture sizes, not a measured MacBook display.
Below the proposed wide threshold, use the top navigation, Projects drawer and
selected-day Week list. The wide composition places projects alongside work and
uses readable day columns/available horizontal space. Do not squeeze seven tiny
columns to meet a numerical breakpoint.

Reference examples: compact Today 11:2; crowded Today 65:5554; crowded Projects
82:6877; wide Week 13:710; dark Today 11:457; compact/dark carryover
113:8566/113:8733; enlarged text 115:8987. The 46-reference inventory includes
other widths, empty, long, completed, failure and recovery fixtures. User scrolling
reports cover only the two crowded references. R22/R23 render checks are linked
in the review; no full width/theme matrix rerun was performed in R24.

Today has one main vertical content scroll owner. Projects includes a distinct
bounded task viewport and reachable Add task footer. Keep the last task and its
actions reachable above fixed footers. Header navigation, active timer controls
and actionable recovery/errors stay accessible during scrolling. Preserve the
compact/dark completed-Read repair: hidden restoration shells must not reserve
blank rows above Outline. Derive layout from real visible work; the prototype's
four height variables are only a presentation workaround.

### Defaults/discrepancies to settle before implementation

- The original plan proposes a 64px active-row minimum; reviewed normal Figma rows
  are 59px. This handoff records both rather than silently rewriting the plan.
- The plan proposes a 1280px transition; both 1279/1280 comparison references use
  selected-day fallback. Treat the threshold as unresolved until browser layout
  review establishes room for projects, columns, long titles and controls.
- Cross-month planned weeks under the Monday's month and the detailed Earlier
  unfinished selection policy remain proposed defaults. Preserve planned-week
  grouping without pretending those defaults were explicitly confirmed.
- Inter is the documented Figma fallback, not permission to replace the Mac app's
  system typography. Larger-text fixtures are not actual browser 200% reflow tests.

## Observable behavior and recovery

| Interaction | Intended result and failure handling |
| --- | --- |
| Select/Start | Select the correct incomplete leaf by task/project/parent context, then Track. Parent containers cannot start or complete directly. Preserve an existing session when navigating. |
| Complete/reopen | Same task identity everywhere. Compact to checked checkbox plus gray struck-through title; hide row metadata/actions while retaining accessible context. Restore eligible controls only after confirmed reopen. Keep failed-save status, input and focus recoverable; preserve active session controls. |
| Parent/subtasks | One level; derived parent completion/progress from children; totals count unique leaves. No direct parent completion or bulk child mutation from a parent control. |
| One Save | Task details plus optional planning save together, or neither saves. Preserve fields on validation/failure; replay/lost-response handling must not duplicate the task. Cancel creates nothing. The fixed form does not prove atomic storage. |
| Week navigation | Service Today is distinct from a selected week's Monday. Prev/Today/Next and day selectors preserve the viewed context. Due date remains distinct from planned date. |
| Order and Move | Grip/date/keyboard alternatives; identify placement and source. Within-day order and destination position need real persisted ordering. Cancel/outside/unchanged-position are no-ops. Move keeps task identity and other dates; occupied task/date rejects without losing the source. |
| End Week preview | No closure until explicit End Week. Keep week open, outside dismissal and Escape leave an open week open and return to its board. Already-closed preview routes to existing frozen history. Never implement this by unclosing frozen history. |
| Carryover | After closure, one candidate per eligible leaf, checked by default at last frozen source date plus seven calendar days. Uncheck/recheck/redate, then Review/Apply. Skip carryover adds no dates and leaves the source closed. Re-entry revalidates eligibility; failed/uncertain Apply must not duplicate plans. Deadlines/frozen history stay unchanged. |
| Done versus Missed | Done is live current completion grouped by planned year/month/week; current overall leaf totals deduplicate multi-date membership. Missed comes only from immutable at-closure unfinished leaves, once per task/closed week. Later completion/carryover cannot erase a miss. |
| Focus/recovery | Complete task and finish session are separate. Pause excludes time; measured sleep remains paused; uncertain gaps require review. Continue the same session explicitly, excluding the gap. Failed/unknown finish preserves session and recovery choices. Saved credit/rewards/streak derive from confirmed intervals. |
| Stats/correction | Label saved-time scope separately from current work and frozen Missed. Corrections retain reason, preview/revalidation, audit/replay, confirmed ceilings and wallet/streak/tree effects. A representative correction is not a general ledger implementation. |
| Assistant | Central answer, bottom composer, context/model and Sources on demand. Preserve the question on Cancel/error. This file demonstrates independent read-only questions; existing app M5 Apply/Undo and connections remain separately scoped capabilities. |

The prototype resets **206** ephemeral variables through eight launcher controls.
Do not port those variables, the boolean task allowlist, fixed dates or mock counter
strings into production domain logic. Ordinary navigation does not reset work.

## Keyboard, focus and accessibility intent

This is implementation intent, not executed browser accessibility evidence:

- Use semantic buttons/inputs, named checkboxes and disclosures with checked,
  expanded, busy and error state exposed. Completed titles retain project/parent/
  planned-date context in accessible names even when metadata is visually hidden.
- Tab order follows top navigation → view/project controls → working rows →
  contextual actions. Parent rows expose progress/disclosure, never a completion
  checkbox. Ensure enabled controls remain identifiable without color alone.
- Enter/Space activate ordinary controls. Provide explicit Move up/Move down and
  Move date/remove-date controls, with useful first/last boundaries. Escape cancels
  a pending move/reorder or dismisses a scoped dialog without mutating records.
- Modal focus enters its heading/first meaningful field, stays inside while open,
  and returns to its invoking control. Preview cancellation returns to End Week;
  completion/reopen preserves focus on the same task's available representation
  or its completed disclosure when that row is collapsed.
- Associate field errors with the affected input; retain values; announce save
  outcome and keep Retry reachable. Do not hide actionable errors inside Help.
  Loading/disabled states prevent duplicate writes without losing context.
- Honor reduced motion while preserving the same state/focus outcomes. Exact
  animation timings remain proposals; arbitrary drag smoothness, screen-reader
  operation, real text enlargement/reflow and dark focus require later testing.

## Finite demonstration and remaining checks

Only Read, Choose the seminar theme and Summarize chapter 4 have enabled completion
examples; other checkboxes are intentionally disabled. One created Draft task,
representative Read order/Move, one synthetic 12-minute save and finite correction/
wallet combinations are supported. The fixed 120/300 interruption example is not
an OS event. Assistant answers and error states are fixed, with a two-second
simulated generation. Successful purchase/ownership, a general session ledger,
arbitrary fields/dates/dragging and persistent chat are not demonstrated.

User reports cover the core repair journeys, including cancel/error retention;
optional full reward/correction tours and the original 36-ticket checkpoint path
are not thereby accepted. Required later runtime checks include arbitrary input,
real scroll/focus at actual app widths, keyboard/accessibility, replay/stale-write/
restart/persistence, real timer recovery, integration preservation and hardware
acceptance. App implementation and its acceptance must be separately authorized.

## Candidate implementation units — not started by this handoff

| Unit | Concrete outcome and acceptance focus |
| --- | --- |
| UI shell/foundations | Map existing components/tokens to the current React interface; preserve existing integrations, navigation, timer state and errors at compact/wide sizes. Resolve sizing/default discrepancies above. |
| Task surfaces | Today-first compact rows, project drawer, partial parents and completed/reopen states with shared task identity and accessible focus/error recovery. |
| Atomic capture | Scope a real details/planning save through existing domain functions; verify all-or-nothing results, retained input and replay without duplication. Preserve newer placement fields already present in the app. |
| Persisted ordering | Scope within-day and destination order, Move identity, no-op cancellation/boundaries, conflicts/revisions and existing-plan/history compatibility. |
| Done/Earlier projections | Scope planned-week membership/deduplication and the approved Earlier policy without changing frozen history, deadlines or current task identity. |
| Focus/secondary screens and QA | Apply calm Track/Stats/Assistant surfaces while preserving confirmed-time, recovery, rewards, correction and existing M5/M6 behavior; execute real width/theme/keyboard/failure regression checks. |

These describe observable outcomes, not invented endpoints, migrations or a new
architecture. Freshly inspect current source, AGENTS.md, Git diff and domain tests
before scoping any build. The app advanced concurrently, including Google/calendar
work; absence from this prototype is never permission to remove those capabilities.
No core-trial copy, service, database, release, model or Mac hardware gate was
changed by the design/handoff work.

## Source evidence

- [R21 native wiring](../docs/reviews/2026-11-02-ux-r21-wiring.md).
- [Independent R22 static assessment](../docs/reviews/2026-11-02-ux-r22-static-review.md).
- [R23 reports and bounded repairs](../docs/reviews/2026-11-03-ux-r23-continuation.md).
- [R24 handoff reconciliation](../docs/reviews/2026-11-03-ux-r24-handoff.md).
- [Canonical UX plan](BEARPLANS_UX_PLAN.md),
  [repair plan](BEARPLANS_UX_REPAIR_PLAN.md),
  [shared agent guidance](../AGENTS.md) and
  [design skill](../.agents/skills/bearplans-design/SKILL.md).

The November 2 support handoff-draft.md remains historical evidence. This document
and the exact inventory supersede that draft as the scoped engineering handoff;
PROGRESS remains the single mutable work/acceptance record.
