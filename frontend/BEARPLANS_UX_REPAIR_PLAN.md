# BearPlans — UX repair plan

Prepared November 1, 2026 from the [77/100 expert evaluation](../docs/reviews/2026-11-01-ux-expert-evaluation.md).

This defines a focused repair sequence for the existing editable Figma prototype.
The user requested a plan in this turn. No repair execution, application
implementation, API/schema work or saved-data change begins by saving this file.
The [canonical brief](BEARPLANS_UX_PLAN.md) retains the original UX-01–36 definitions;
these repair tickets supply evidence for its still-open acceptance gates.

Current status and each next action live only in [PROGRESS.md](../docs/PROGRESS.md).
Finished work is logged in [COMPLETED.md](../docs/COMPLETED.md). This document
contains stable tasks, dependencies, proposed design treatments and acceptance,
not a second mutable tracker.

## 1. Outcome

Make the existing minimal design support five real moments well:

1. Open Today and choose work from eight or more tasks.
2. Plan next week and compare days during a Wednesday/Thursday review.
3. Reorder or move one clearly identified task without losing its context.
4. Complete/reopen a child, inspect Done/history and carry unfinished work forward.
5. Focus, recover from interruption and review progress without dense explanations.

Preserve Today-first navigation, compact task name/project context/Start, prominent
streaks, on-demand rewards, gray struck-through completed rows and the free
two-dimensional editing canvas. Improve working space through layout and hierarchy;
do not add automatic priorities, extra task fields or a new dashboard.

## 2. Baseline, ownership and scope

- Existing file: [BearPlans — Local UX Refresh](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=50-4633).
- First editing page: Canvas · Flows, page 2:5; 75 screens in nine native Sections.
  Main overview section: 50:4633. Keep the open canvas and existing frame identities.
- Separate Screens page 2:4: 17 responsive/theme references. References are not
  independently working responsive applications.
- Exact IDs/components/tokens/session identity: [node ledger](design/figma-node-ledger.json).
  Resolve screen roots by ledger ID; a frame's top-level ancestor may be a Section.
- Design sizes: 640×800 compact, 800×900 split, 1440×900 wide. Check the proposed
  1279/1280 layout transition separately. Sizes are defaults, not Mac hardware evidence.
- One active ticket and one Figma writer: Codex. Independent reviewers inspect
  the active ticket's product rules, visual layout and verification evidence.
- Work on the current checkout, preserving concurrent application changes.
  Do not touch the core-trial copy, services, databases, dependencies or Git commits.

Most tickets should fit a 30–90 minute focused session. R03, R20–24 may require
up to 120 minutes; split a larger discovered batch into numbered children in
progress. These are scope-sizing limits, not a delivery-date promise.

## 3. Reconcile newer decisions first

These confirmed November 1 decisions postdate the original prototype and must be
reflected during repair. See [current rules](../AGENTS.md) and the
[End Week / Missed review](../docs/reviews/2026-11-01-end-week-carryover.md).

| Area | Contract for the repaired design |
| --- | --- |
| End Week | Preview explains frozen history and Missed; confirmation closes the week and immediately opens carryover choices. |
| Carryover defaults | Every eligible leaf starts checked. Suggested date is its last planned date in the frozen source plus seven calendar days. Several source placements produce one candidate. |
| Carryover control | User may uncheck/redate, then Review → Apply. Preselection saves nothing. Cancel leaves the week closed and creates no carryover placements. |
| Eligibility | Source was unfinished at closure; current task still exists as an incomplete leaf. Explain exclusions, occupied dates, closed destinations and stale review. |
| Missed | Overall label “Missed: N”; per task “Missed: N×”. Count planned leaves unfinished at closure once per closed week; open weeks excluded. The same leaf may contribute again in another closed week. Later completion/carryover does not erase a miss. |
| Done versus history | Done is current completion grouped by saved planned weeks; its overall total is unique current leaves. Closed snapshots retain original labels, details and completion. |
| Assistant | Current app has M5 Apply/Undo. The Figma sample is deliberately a read-only layout subset. Preserve this distinction; Assistant carryover is implemented in the app with Apply/Undo; hands-on acceptance remains pending and it is outside this read-only layout sample. |

Do not normalize intentionally historical task/session facts to current facts.
Keep deadlines separate from planned dates, completion separate from timers,
and confirmed saved time separate from paused or uncertain gaps.

## 4. Order and checkpoints

| Phase | Tickets | Purpose | Checkpoint |
| --- | --- | --- | --- |
| A | R01–R03 | Baseline, decisions and consistent sample content | Current task facts agree; historical differences documented |
| B | R04, R19, R05 | Compact bounds, early contrast repair, scrolling and Today density | Eight-task Today usable at compact/split sizes |
| C | R06–R09 | Week navigation, contextual moves and readable planning | Next week and Wednesday review work clearly |
| D | R10–R12 | Manual order, crowded Projects and Done | Selection/order and live/frozen completion understandable |
| E | R13–R15 | Latest closure, carryover and Stats Missed | Explicit reviewed transfer; reliable counting/scopes |
| F | R16–R18 | Track, recovery and Assistant | Clear controls without repeated explanations |
| G | R20–R21 | Responsive/state coverage and native links | Affected components and journeys ready for independent QA |
| H | R22–R24 | Independent review, user walkthrough and handoff | Evidence-backed acceptance and separate engineering scope |

Default to this order, including the early R19 shared-token repair after R04.
Dependencies below determine whether a ticket is eligible;
independent reviewers may work in parallel on that same active ticket.
Checkpoints review concrete results. Do not ask permission again for an equivalent
routine fix once execution is authorized. Review a genuinely new behavior through
a concrete proposal rather than silently adding it.

## 5. Scorecard coverage

| Evaluation category | Baseline / 100 | Primary repair evidence |
| --- | --- | --- |
| Daily workflow fit | 84 | R05, R10–R11, R16, R23 |
| Prioritization / next action | 68 | R07, R10, R23 |
| Task density / scanning | 76 | R04–R05, R08–R09, R11 |
| Weekly planning / review | 62 | R06–R09, R13–R14, R23 |
| Projects / subtasks / Done | 78 | R11–R12 |
| Track / focus | 84 | R16–R17 |
| Streak / motivation | 90 | R05, R16, R19–R20 preserve strengths |
| Statistics | 82 | R15 |
| Assistant | 84 | R18 |
| Visual hierarchy / minimalism | 88 | R05, R08, R11, R16, R19–R20 |
| Cross-view consistency / trust | 64 | R01–R03, R12–R15, R21 |
| Compact / accessibility | 70 | R04, R19–R23 |
| Feedback / recovery | 86 | R07, R11, R14, R17–R18, R21 |

### Repair tickets

### UX-R01 — reconcile the baseline and current product decisions

Depends: none. Maps: UX-05/21/23/29/31/32.

1. Inspect live file/ledger, current Git changes and latest shared guidance before writes.
2. Record owned frame IDs, bindings, modes, reactions, named starts and affected
   component instances for the first repair batch.
3. Create a discrepancy list for newer carryover/Missed rules, Assistant subset,
   historical context and still-proposed design defaults.

Pass: every requirement is classified as confirmed, proposed or deferred;
baseline and recovery data exist outside Figma. Unknown/user-owned objects are
preserved. No application rule is inferred from an old screen.

### UX-R02 — define one synthetic task and session fixture

Depends: R01. Maps: UX-08/14/15/18/29/34.

1. Define stable synthetic identities with title, project/parent, deadline, estimate,
   planned dates, completion and relevant session state.
2. Include duplicate titles in different projects, a multi-date leaf, a partial
   parent, an unscheduled leaf, and a task changed after closure.
3. Record current Outline as Nov 4 / 20 min unless baseline reconciliation establishes
   a deliberate replacement; create separately labeled historical snapshot facts.

Pass: each current task has one fact set. Day placements reference that task;
they are not separate tasks. Closed/session context has explicit intentional
differences and expected leaf/count totals.

### UX-R03 — correct repeated task facts throughout the existing draft

Depends: R02. Maps: UX-13/15/18/24/29/31/32.

1. Audit repeated current task text across all 75 screens and 17 references,
   including move previews, task details, Track and Assistant examples.
2. Replace contradictory deadlines/estimates/context through component properties.
3. Update related counts and reset examples; preserve immutable historical/session
   context from the fixture.

Pass: current Outline no longer changes from Nov 4 / 20 min to Nov 3 / 30 min
between Projects 5:4924 and Week 6:1868. No unexplained current fact mismatch remains.
Check collapsed/hidden variants as well as visible rows.

### UX-R04 — fix compact bounds and scrolling

Depends: R03. Maps: UX-07/09/10/16/33.

1. Repair 11:40 and 11:41: replace fixed 752px disclosure widths with available
   compact width, 592px at x24–616 inside the 640px frame.
2. Audit sibling buttons, hit areas and long labels for the same fixed-width defect.
3. Give Today one clear vertical scroll owner for working content; remove competing
   outer/inner scrolling for the same task list.
4. Keep Completed, Earlier unfinished and active timer controls reachable when expanded.

Pass: no unintended horizontal overflow, clipped action or unreachable last row.
At 640/800 widths, both disclosures and their expanded content remain within
the content bounds. Metadata passes are followed by an actual scroll check when supported.

### UX-R05 — improve Today density without crowding tasks

Depends: R04. Maps: UX-08/11/16/17.

1. Tighten title/date/view-switch/streak spacing before shrinking task text or targets.
2. Preserve 15px titles, readable context, full long-title wrapping and clear Start.
3. Show task count or a restrained continuation cue so hidden work is discoverable.
4. Review eight-task and twenty-task fixtures, both completed/earlier sections expanded,
   and a compact active timer.

Pass: the eighth task is discoverable and reachable at 640×800 and 800×900.
Proposed density target: eight ordinary two-line rows at split size, five at
compact size where content allows. These are review targets, not fixed-height
requirements; long names/error feedback must expand without clipping.

### UX-R06 — make Week navigation consistent

Depends: R04. Maps: UX-18/22/23.

1. Add visible Previous / Today / Next navigation to compact Week 6:1802.
2. Use the same meanings in 640, 800 and 1440 layouts; distinguish week navigation
   from Today/Week view switching.
3. Today returns to the service's current date/week. Previous/Next move calendar weeks;
   preserve selected weekday where meaningful and label selected versus Today.
4. Include empty, closed and year/month-boundary examples.

Pass: next week is reachable without History or End Week, then Today is reachable
again. Navigation creates no tasks/placements, carries nothing automatically,
and cannot expose editing in a closed week.

### UX-R07 — make Move and Reorder identify their placement

Depends: R03, R06. Maps: UX-19/20.

1. Choose a visible selected-placement action area or row menu; identify task,
   project/parent and source day before an action.
2. Retain the grip in its agreed position above/left of the title context; no
   visible Drag instructions or modifier Add behavior.
3. Provide keyboard/date alternatives and first/last-item ordering states.
4. Show result, cancellation, occupied task/date conflict, archived/read-only state,
   saving, failed and unconfirmed-response examples.

Pass: every movement action has an obvious target. Move preserves the placement
identity and other dates; same-position/cancel/outside drop do nothing. A failed
or uncertain save retains context and a useful recovery path.

### UX-R08 — strengthen compact Week overview and completion

Depends: R05–R07. Maps: UX-18/23.

1. Reclaim vertical space from repeated headings and global controls.
2. Give “2 of 11 complete · 18%” clear hierarchy and a restrained progress indicator.
3. Explore a compact day-count strip for cross-day comparison while retaining the
   readable selected-day list.
4. Keep unfinished work first, compact completed rows accessible, and End Week
   in the bottom-right footer with its preview.

Pass: week/day/task context remains visible; the user can compare Wednesday with
another day and identify unfinished work. Empty weeks show 0/0 and 0%.
Week completion counts unique leaves once; per-day counts may show the same leaf
on several days and must be labeled accordingly.

### UX-R09 — make the wide weekly board readable

Depends: R06–R08. Maps: UX-10/18/33.

1. Review 13:710 with real long task/project/parent names and a crowded Sunday.
2. Provide a collapsible project pane so cards can gain width.
3. Compare seven-column readability against the selected-day fallback near the
   proposed 1280px transition; do not force seven squeezed columns.
4. Keep all weekdays, due dates, movement cues and footer reachable.

Pass: card labels wrap without colliding with checkbox/Start; the task meaning
remains readable at normal size. Collapsing the pane does not lose selection,
change plans or hide the way back to Projects.

### UX-R10 — distinguish selection from manual priority order

Depends: R05, R07–R08. Maps: UX-08/16/19.

1. Reserve selected-row styling for selection; do not present it as an automatic recommendation.
2. Make deliberate manual order understandable in Today and the corresponding day in Week.
3. Demonstrate reorder, then navigation and return without losing the illustrated order.
4. Compare a quiet “first in your order” cue against order alone using a concrete frame.

Pass: selecting/opening a task never silently reorders it. Manual order is a future
persisted capability until separately implemented. No new priority field, due-date
sort, AI ranking or automatic scheduling is introduced.

### UX-R11 — support crowded Projects and compact task entry

Depends: R04, R10. Maps: UX-12/13/14/17.

1. Tighten Rename/Add project spacing while preserving their agreed order.
2. Establish a scrollable task body with project selection and Add task reachable.
3. Keep active/completed children in their parent grouping above the footer;
   preserve the repaired Read rows.
4. Inspect 15 mixed tasks/subtasks, several expanded parents, long names and unscheduled work.
5. Recheck the one-Save task editor, input retention and validation at compact width.

Pass: every leaf is reachable; parent rows show progress without completion/Start.
Expanded children never appear beneath footer actions. Task creation keeps deadline,
estimate and planned day clear; errors retain input.

### UX-R12 — clarify Done totals and frozen history

Depends: R02–R03, R11. Maps: UX-14/15/22.

1. Keep Done → year → month → planned week and No planned week.
2. Use “unique completed tasks” or equally clear overall scope; explain repeated
   week membership on demand.
3. Add a multi-week completed leaf and a renamed task with older frozen history.
4. Show reopen restoration, parent progress changes, pending/error focus and return.

Pass: Done counts each current leaf once overall and once within each relevant
week. Parents are context, not extra work items. Reopening updates current views
without changing frozen labels/completion/placements or an existing timer.

### UX-R13 — update End Week and immediate carryover choices

Depends: R01–R03, R06, R12. Maps: UX-21/22/23.

1. Update closure preview to explain freezing, Missed and the following choices.
2. On confirmed closure, open carryover choices immediately.
3. Preselect every eligible leaf at its last frozen planned date plus seven
   calendar days; show one candidate for several source dates.
4. Include empty/all-complete source and ineligible-task examples.

Pass: closure preview cancellation changes nothing. Confirming closes only the
source; preselection does not save destination placements. Deadlines do not move.
The closed source remains available and immutable.

### UX-R14 — complete the reviewed carryover flow

Depends: R07, R13. Maps: UX-23/32.

1. Let users uncheck, recheck or redate candidates in the immediately following week.
   Rechecking restores the suggested same-weekday date.
2. Review exact selections/dates before Apply; show exclusions and no-selection state.
3. Add occupied/closed destination, existing-active-placement exclusions,
   completed/removed/container task, stale review,
   failed Apply and lost-response/retry examples.
4. Preserve one/two/no-transfer examples without implying they cover every combination.
5. Provide a clear return to the closed week after Cancel and a way to reopen its
   carryover choices, revalidating current eligibility without closing the source again.

Pass: only Apply demonstrates new destination placements, retaining task identity.
Cancel leaves the source closed and saves no carryover. Retry/stale behavior is
described truthfully; no silent overwrite, duplicate task or automatic transfer.

### UX-R15 — clarify Stats scopes and add Missed

Depends: R12–R14. Maps: UX-29/30.

1. Separate all-time saved focus/session measures from current task completion.
2. Add exact “Missed: N” overall and per closed week, and “Missed: N×” per task.
3. Show one multi-date leaf counted once in one closed week and again in a second
   closed week; later complete it without erasing its historical misses.
4. Keep By week/project/estimates detail optional and give weekday charts clear date context.

Pass: fixture totals count planned leaves unfinished at closure in frozen snapshots;
open weeks contribute no Missed.
Done's unique-current total is not confused with Missed across weeks. Saved-time
corrections do not rewrite closure history or task completion.

### UX-R16 — simplify Track and make task selection discoverable

Depends: R03, R04, R10. Maps: UX-24/25/27/28.

1. Keep one Forest entry; remove repeated duration wording.
2. Add a clear Change task path in idle setup, including unscheduled incomplete leaves.
3. Keep species selection quiet and optional to open, with a visible default choice;
   the owned species must still be selected and locked at session start.
4. Check idle, invalid/completed task and an already-active session.

Pass: task, remaining time, session state and primary controls dominate.
Changing setup cannot replace an active/paused/review session or enroll a second
timer/tree. Starting or finishing a session never completes the task.

### UX-R17 — improve recovery consequences and retained controls

Depends: R16. Maps: UX-25/26/30.

1. Show confirmed session time, remaining countdown and excluded gap together.
   Distinguish these from finalized saved totals and streak/coin credit.
2. Preserve explicit Continue/Finish choices and measured-sleep paused behavior.
3. Review running/paused/review states across Plan navigation and leaf completion/reopen.
4. Include failed/unconfirmed save and return/retry examples.

Pass: a fixture with 120 trusted seconds and a 300-second uncertain gap shows
two confirmed session minutes, excluding the gap. An unfinished session does not
yet contribute streak/coin credit. No automatic resume or extra credit;
the existing session and its controls survive task completion.

### UX-R18 — refine Assistant affordances within its actual sample scope

Depends: R03, R04. Maps: UX-31.

1. Clarify which context/model controls are selectors; show editable context only
   where supported, otherwise label it as context.
2. Preserve the calm answer area, bottom composer, concise answer and collapsed sources.
3. Check question retention, cancel generation, unavailable model and error recovery.
4. Label the read-only layout sample in handoff, preserving the app's separate M5 capabilities.

Pass: visible controls have a meaningful supported result; examples use the correct
service Today/selected-week context and fixture facts. No fake chat persistence or newly designed mutation/Undo flow is implied.

### UX-R19 — repair contrast and control states

Depends: R03–R04. Maps: UX-06/07/08/09/33/34. Execute early in phase B;
R20 rechecks later repaired dependents.

1. Adjust the dark streak pairing from approximately 4.46:1 to at least 4.5:1 using
   unrounded colors; aim for margin rather than the exact threshold.
2. Inspect affected semantic tokens and selected/hover/focus/disabled/error variants
   in both modes, without applying active-text rules blindly to disabled controls.
3. Keep checked completed rows operable and readable; provide non-color state cues.
4. Review focus annotations, control names, checked/expanded semantics and logical order.
5. Include enlarged-text/reflow stress content with expanding rows and reachable
   controls. Figma canvas zoom is not evidence of text enlargement/reflow behavior.

Pass: sampled applicable text/controls meet the stated contrast checks and focus
remains visible. Record colors, actual ratios and exact nodes. Visual annotations
do not certify keyboard or screen-reader execution.
Reference: [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

### UX-R20 — propagate repairs across responsive and theme references

Depends: R05–R19. Maps: UX-10/33.

1. Reuse repaired shared instances/tokens; update affected screens deliberately.
2. Review primary Today/Projects/Week/Track/Stats/Assistant compositions at 640,
   800 and 1440 widths, plus the layout transition and task-editor/recovery overlays.
3. Cover light/dark, empty, long-title, crowded, expanded, loading/error and active-timer cases.
   Include an enlarged-text fixture, with a proposed 200% text-size stress case;
   specify actual browser reflow/enlargement verification for later implementation.
4. Index any genuinely new reference frames instead of claiming the existing 17 cover everything.

Pass: no unintended overflow, clipped primary actions or inaccessible expanded
content. Preserve logical layout across widths and modes; all newly reviewed
compositions have exact IDs, dimensions and evidence.

### UX-R21 — rewire and audit the connected prototype

Depends: R13–R20. Maps: UX-32.

1. Recheck affected native links, selected task/context, completion/order and
   session-state variables; inspect hidden instance children explicitly.
2. Preserve the ten existing named starts; add a start only for a necessary new journey.
3. Check return/cancel/reset paths, current-versus-frozen routes and explicit Apply.
4. Keep fields/drag/timer/model demonstrations clearly marked as representative.

Pass: all destinations resolve; no dead-end actionable control, wrong task target,
unintended state reset, automatic timer resume or pre-Apply carryover exists in
the reviewed native routes. Execute supported preview journeys separately.

### UX-R22 — independent QA and consistent rescoring

Depends: R20–R21. Maps: UX-34.

1. Independent visual, product-rule and interaction reviewers inspect the repaired scope.
2. Close P1 findings against observable criteria; record any remaining issues with owner/next action.
3. Reuse the original 13-category weights to rescore, with specific evidence for each change.
4. Separate structural, rendered, executed interaction and later application evidence.

Pass for static readiness: no unresolved required static P1 in the reviewed scope.
Record required click/scroll execution still pending; R23 may proceed to obtain
that evidence through supported preview or manual user verification. Overall
acceptance requires those core interaction checks to pass. Scores do not increase
merely because more frames were created.
If a required check fails, record Fail and schedule the smallest repair.

### UX-R23 — user walkthrough and bounded corrections

Depends: R22 static readiness; pending execution checks are allowed. Maps: UX-35.

1. Run the journeys in section 8 with synthetic data and neutral task prompts.
2. Record wrong turns, overlooked actions, assistance needed and time to find;
   observe before explaining the intended path.
3. Show the smallest concrete correction for each material finding and recheck it.
4. Split substantial discoveries into R23.1/R23.2 rather than bundling an unlimited redesign.

Pass: required core click/scroll journeys have been exercised through supported
preview or manual user verification; the user can complete them with no unresolved
blocking confusion and accepts the direction. Other unsupported execution remains unverified;
one user's walkthrough is formative evidence, not a general usability study.

### UX-R24 — deliver the revised handoff

Depends: R22–R23. Maps: UX-36.

1. Update frontend index, ledger, component/token/state inventory and exact Figma links.
2. Document responsive rules, order/selection, counts, closure/carryover, failure recovery
   and accessibility/keyboard intent.
3. List demonstrated behavior, static references, pending runtime checks and engineering needs.
4. Update progress/completed/reviews without changing original evidence or release gates.

Pass: another contributor can scope implementation without guessing product
behavior. Future persistence/ordering/atomic Save/Done projection/accessibility
work remains separate; no API endpoints, migrations or app changes are invented here.

## 6. Review proposals that are not confirmed requirements

| Proposal | Default for the first concrete comparison | Decision/check |
| --- | --- | --- |
| Compact week summary | Day task counts, unique within each day | Compare during R08; distinguish placements from unique weekly leaf totals |
| Workload minutes | Omit initially | Add only after defining repeated-date and missing-estimate semantics; never invent per-day allocation or available capacity |
| First-task emphasis | Clear manual order without automatic recommendation | Compare a small order cue during R10; selection alone is not priority |
| Density targets | Reclaim chrome before reducing text/targets | R05/R08 review real long/crowded content; no arbitrary fixed row ceiling |
| Wide project pane | Collapsible, preserving selection | R09 compares readability and return access |
| Filing cross-month weeks/font fallback | Retain existing proposed Monday filing and documented Inter fallback | Remain proposed until the user reviews them |

Optional proposals must not block known width, navigation, factual or contrast
repairs. Do not add priority scores, automatic scheduling, arbitrary capacity
limits, new accounts/sync, native rewrites or persistent chat as a repair side effect.

## 7. Per-ticket execution and recovery

Use the existing [AGENTS.md](../AGENTS.md),
[BearPlans design skill](../.agents/skills/bearplans-design/SKILL.md) and
[review workflow](../.agents/skills/bearplans-design/references/review-and-handoff.md).
They already provide agent/skill guidance; no blanket rewrite or new skill is
needed. Change guidance only for an actual gap or a newly accepted rule.

Before each authorized Figma write: state the visible acceptance scenario,
affected owned nodes/dependents, rule/default changes and cancel/recovery behavior.
Load the relevant installed Figma skills; keep one writer and serialize mutations.
Checkpoint affected properties, reactions, bindings, modes and a useful current
render. Reuse exact component/variable IDs; no flattened UI screenshots.

After the coherent repair: inspect normal-size output, affected shared dependents,
and relevant alternate states. Take a new screenshot after a real visual repair,
not repeated unchanged shots. Record actual commands/operations, nodes, dimensions,
theme, failure/recovery and Pass / Pass with follow-ups / Fail in a dated review.

If execution fails, obey the tool's retry-safe flag and reconcile the live canvas
before uncertain retries. Restore only owned changes from the scoped baseline.
Do not globally Undo concurrent work, replace the file, blindly recreate IDs,
delete shared assets or overwrite historical evidence.

Status transitions and owner/reviewer/evidence/next action belong in progress.
Documentation completion is not screen completion. No app tests are required for
this plan; later Figma checks do not replace application persistence, accessibility,
drag-performance or Mac timer/hardware acceptance.

## 8. Required validation matrix and walkthrough

| Dimension | Minimum cases |
| --- | --- |
| Window/layout | 640×800, 800×900, 1440×900; proposed 1279/1280 transition |
| Theme | Both modes for repaired shared controls; primary compositions and dark error/recovery samples |
| Content | Empty, one, eight, twenty Today tasks; fifteen mixed project items; long titles/context; duplicate titles |
| Completion | Incomplete leaf, partial parent, completed leaf, reopen/pending/failure, multi-date shared completion |
| Week | Empty 0/0, open/closed, current/future, month/year boundary, occupied destination, archived placement |
| Carryover | All/one/none selected, recheck/redate, multi-date source, ineligible, stale/failed/unconfirmed Apply |
| Timer | Idle/running/paused/review/sleep/finished, completed selected task, no silent resume |
| Accessibility | Bounds, contrast, enlarged-text/reflow stress case, non-color cues, focus/tab annotations, names and expanded/checked intent |
| Evidence | Separate static structure, rendered composition, actual preview actions and later app tests |

Walkthrough prompts and expected outcomes:

1. **Find the eighth Today task at compact size.** Full name/context and Start
   are reachable; discoverability does not depend on guessing a hidden inner scroll.
2. **Create a task with deadline, estimate and planned day.** One Save and a
   useful validation/error state; no claim of real persistence in Figma.
3. **Plan next week, then return Today.** Visible navigation; no accidental closure
   or carryover, correct selected day and service Today.
4. **Rebalance Wednesday.** Identify one placement, reorder it, move it to another
   day, cancel a second move and inspect a conflict without changing other dates.
5. **Inspect a crowded project.** Expand completed children, find unscheduled work,
   complete/reopen one child; parent progress updates and no row falls below a footer.
6. **Close a week with a multi-date unfinished leaf.** Choices open with one checked
   candidate on its last source weekday next week; uncheck/recheck/redate, Review,
   cancel, return to the closed week, reopen carryover choices and review again,
   then Apply. Re-entry revalidates current eligibility; Cancel saves no carryover;
   deadlines/history remain unchanged.
7. **Inspect Missed and later complete that task.** Done/current completion changes;
   the historical miss remains. Repeated closed-week misses have explained totals.
8. **Start, pause, navigate and reopen the timer.** Same session remains paused.
   Completing the task preserves controls and does not finalize the session.
9. **Resolve a 120-second confirmed / 300-second uncertain gap.** Two trusted minutes,
   explicit choices, correct remaining duration and no automatic resume.
10. **Inspect Stats and ask Assistant.** Scope/model/context and sources are
    understandable; errors retain the question; no unsupported action is implied.

Attempt actual clicking, scroll, keyboard/focus and representative drag where the
supported preview allows. If tooling is unavailable, complete independent static
work and record the exact pending manual gate; do not mark executed interaction
Pass from reaction metadata. Arbitrary drag smoothness, screen-reader support,
real data/timing and actual Mac window behavior require later implementation tests.

## 9. Definition of completion

- Each repair has exact reviewed nodes, owner/reviewer and a dated evidence record.
- Required P1 issues have passed their acceptance; other findings are resolved or
  explicitly tracked with user impact and next action.
- The original checkpoints receive new evidence rather than being marked Done
  from this written plan.
- User workflow review passes the required representative click/scroll journeys;
  unsupported application/assistive-technology checks stay open as separate gates.
- Re-score with the same weights after review. No promised target score substitutes
  for successful task completion.
- Deliver the revised prototype/handoff, then scope implementation separately.
  App, model, core-trial and hardware/release gates remain independent.

