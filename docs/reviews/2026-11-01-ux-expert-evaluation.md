# BearPlans — expert UX/UI evaluation

Date: November 1, 2026. Environment: macOS 26.6.2 / 25G83.
Scope: read-only formative evaluation of the current Figma review draft.
Ticket: UX-32.1. Design owner/review synthesis: Codex; three independent reviewers
covered daily/weekly planning, secondary experiences, and compact/accessibility
references. No Figma design, application, API, data or service changes.

**Overall: 77/100** (weighted expert judgment: 76.84).
This is a heuristic assessment, not a measured usability or satisfaction score.
It gives daily and weekly workflow fit the highest combined weight (30%).
90–100 means very strong design fit; 80–89 solid with refinements; 70–79
material friction; 60–69 a priority weakness. Lower scores require substantial
rework. Scores do not certify runtime behavior or accessibility conformance.

**Design acceptance: Fail for implementation approval at this revision — targeted
revision required.** The advisory evaluation is complete. Missing compact Week
navigation, responsive overflow, ambiguous planning controls and contradictory
task facts prevent full UX acceptance. Existing UX-32.1 remains In review.

## Weighted scorecard

| Category | Score / 100 | Weight | Evidence and implication |
| --- | --- | --- | --- |
| Daily workflow fit | 84 | 15% | Today opens directly to scheduled tasks, project context and Start. Capture-to-focus is coherent. |
| Prioritization and next action | 68 | 10% | The first row is selected, but the design does not explain priority or help the user compare the next task. |
| Task density and scanning | 76 | 8% | Today fits seven complete 67px rows at 800×900. Compact Week fits roughly four-and-a-half 89px rows; header chrome consumes working space. |
| Weekly planning and review | 62 | 15% | Compact Week lacks visible Next week navigation; global Move/Reorder lack a clear selected-task target; wide cards are cramped. |
| Projects, subtasks and Done | 78 | 8% | Parent progress, compact completed children and planned-week hierarchy match the brief. Administration consumes drawer space; crowded-project scrolling is unresolved. |
| Track and focus | 84 | 7% | Task, countdown and Start form a clear hierarchy. Change-task affordance is missing; duration wording and Forest entries repeat. |
| Streak and motivation | 90 | 4% | Streak and saved progress are prominent, with forest/shop largely on demand. The banner should remain compact at narrow sizes. |
| Statistics usefulness | 82 | 5% | Readable summaries, weekly bars and optional details. All-time and current-task scopes need clearer separation. |
| Assistant experience | 84 | 5% | Calm answer typography, bottom composer and collapsed sources fit the requested direction. Context/model selection cues need clarity. |
| Visual hierarchy and minimalism | 88 | 8% | Consistent warm neutrals, restrained green, type hierarchy and component treatments. Some headers/forms are too spacious for task-heavy use. |
| Cross-view consistency and trust | 64 | 5% | Outline the discussion has conflicting due dates and estimates in Projects and compact Week. |
| Compact layout and accessibility | 70 | 5% | Readable main typography; compact Today has nested scroll and overflowing disclosure widths. Dark streak text is just below the normal-text contrast threshold. |
| Feedback, errors and recovery | 86 | 5% | Explicit recovery choices and saved-time explanations are strong. Remaining time and continued task context could be clearer; actual interactions are unverified. |

Figma editor/canvas organization is separately **86/100**: nine native sections,
a main-workspace overview and explicit handoff limits improve navigation. This
editor score is not included in the product UX overall.

## Connection to the user's actual workday

- **Opening and starting work: strong (84).** Today-first, title/context/Start,
  collapsed completed/earlier work and a prominent streak reflect the user's
  stated routine. Task selection leads to explicit countdown setup.
- **Choosing what matters next: partial (68).** Uniform task rows support scanning
  but do little to explain ordering. The green first-row variant is Selected,
  not an explicit priority designation. Prefer clear manual order/next-up context
  and details on demand; do not fill each row with extra metadata the user did
  not ask for or silently add automatic prioritization.
- **Weekend planning and Wednesday/Thursday review: weak (62).** Compact Week
  shows one day, losing cross-day comparison. No visible Next week control exists
  on the primary compact frame. A small week summary of day counts/allocated
  time would support comparison while retaining the readable day list.
- **Completing, reopening and reviewing: good direction (78).** Compact completed
  rows and partial-parent progress match the brief. Done and frozen closed history
  need clear counting/scope, with crowded and multi-week examples tested.
- **Focus, motivation and reflection: strong design intent (82–90).** Timer,
  saved focus and streak are easy to locate. Secondary rewards stay mostly out
  of the main work area. Stats presents a manageable amount of information.

## Priority findings

### P1 — compact Week planning

[Week 6:1802](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=6-1802)
shows Previous week but no visible Next week control. Move date (6:1924) and
Reorder (6:1926) open representative states without a clear selected-task label
in the default frame. Restore consistent Previous / Today / Next navigation and
make movement actions visibly contextual. The existing grip remains the drag
affordance; no visible Drag instructions or modifier Add behavior is proposed.

The 408px list holds 89px rows: about four-and-a-half visible tasks. Completion
is a small gray line, 2 complete / 18%, while the user wants clearer completion
and weekly review. Give the summary stronger hierarchy; consider a restrained
progress bar and day counts/allocated time. This summary is a recommendation,
not a confirmed new product requirement.

[Wide Week 13:710](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=13-710)
does provide Next week. Its roughly 157px day columns wrap titles heavily beside
a 224px project pane. A collapsible pane would restore working width.

### P1 — conflicting task facts

The same Outline the discussion task is Due Nov 4 / 20 min in Projects row
5:4924, but Due Nov 3 / 30 min in compact Week row 6:1868. Make the synthetic
task facts consistent across every repeated view. This is a Figma content defect;
it is not evidence that the application changes saved task data.

### P1 — compact Today overflow and scrolling

[Compact Today 11:2](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=11-2)
shows the sixth row clipped; additional work has no visible remaining count/cue.
Both 11:12 and 11:23 are vertical scroll containers. Prefer one clear scroll
owner, reclaim header space and communicate hidden work.

Disclosure instances 11:40 and 11:41 remain fixed at 752px inside a 640px frame,
ending at x776. Fit them to the available 592px content width and inspect expanded
states and hit areas. Normal Today 5:3972 uses 67px rows within 474px, showing seven
complete rows of eight; a task count or continuation cue would help discovery.

### P2 — project hierarchy and crowded states

[Projects 5:4847](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-4847)
has useful parent progress, indentation and a completed-child disclosure.
Keep the agreed Rename/Add ordering, but tighten its vertical spacing. Provide
a scrollable task body with selection and Add task reachable; the current drawer
and Subtasks container do not establish a crowded-project scroll strategy.

[Done 5:4951](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-4951)
uses the right planned-week hierarchy. Clarify unique totals and multiple-week
membership on demand so group counts do not look contradictory.

### P2 — secondary experience refinements

- Track 7:2586: keep one Forest entry, reduce repeated duration wording, provide
  a discoverable Change task path including unscheduled tasks. Keep timer setup
  and task completion separate. Changing an active task must retain existing
  active-session safeguards.
- Stats 7:3036: distinguish all-time saved time/session measures from current
  task completion; use clearer dates for weekday initials when inspecting history.
- Assistant 7:3316 / 7:3390: preserve quiet typography and bottom composer.
  Clarify context/model selection affordances. This sample is a read-only layout
  subset; the current app's separate M5 Apply/Undo capabilities are not removed.
- Recovery 7:2733: explicit confirmed time and excluded gap are good; show remaining
  countdown duration with Continue so its consequence is easier to judge.
- Dark Today 11:457: 15px streak title I11:477;3:356 is approximately 4.46:1
  (#5fae86 on #263c2e), just below the 4.5:1 normal-text threshold.
  Increase it with margin. See [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
  Other sampled primary/secondary text pairs were approximately 5.05–15.76:1.
  This is sampled contrast evidence, not a full accessibility audit.

## Evidence and limits

Root inspected current full-frame renders of Today 5:3972, Projects 5:4847,
compact Week 6:1802, task editor 5:5491, Track 7:2586, Stats 7:3036, Assistant
answer 7:3390, wide Week 13:710 and compact Today 11:2. Independent reviews
also inspected Done 5:4951, Assistant empty 7:3316, recovery 7:2733,
compact Track 11:275 and dark Today 11:457. Primary reference sizes were
800×900, 640×800 and 1440×900; these are design sizes, not hardware measurements.

Targeted reads inspected title/context sizes, row/list geometry, scroll owners,
the Selected row component, native Move/Reorder actions, control bounds,
contrast and the existing node ledger. All canvas operations in this review were
read-only. Prior native schema/destination checks remain historical evidence.

No current presentation click-through, scrolling, free drag, keyboard/focus,
screen reader, text enlargement, persistence, timing or arbitrary state-combination
test was completed. Smooth drag quality and interaction success therefore remain
unscored rather than being inferred from screenshots. Previous CUA startup
failure remains recorded; it was not retried for this advisory review.

## Recommended next revision

Address the three P1 areas first: coherent compact Week navigation/action context,
consistent task facts, then compact overflow/scroll ownership. Next refine priority
communication and space allocation, followed by Track/Stats/Assistant affordances.
This review does not begin those changes or authorize application implementation.
Then run a short user walkthrough: choose a task from eight, plan next week,
rebalance Wednesday, complete/reopen a child, and return to an active timer.
Record observed errors and time-to-find before assigning a higher UX score.


## Repository verification

- `git diff --check -- docs/PROGRESS.md docs/COMPLETED.md docs/reviews/2026-11-01-ux-expert-evaluation.md`: Pass.
- Standard-library Python content/link checks: Pass for 165 local links, final
  newlines, whitespace, 13 score rows, 100% weights and weighted score76.84,
  rounded77. Source files were not edited or tested by this review.
- Git status/recent commits and staged/unstaged diff summaries inspected;
  concurrent source and documentation changes preserved. No commit/push.
