# UX-R23 continuation — spacing acceptance and task-save recovery

Date: November 3, 2026 (America/Los_Angeles). Environment: macOS 26.6.2,
Darwin arm64. Owner/writer/reviewer for this bounded continuation: Codex.
No independent agent review in this continuation. File:
[BearPlans](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=2-5).
Resumed from design commit `23faa2d`; R23 remains Active and R24 has not started.

**Outcome: Pass with follow-ups for the scoped rendered checks and recovery repair.**
Required remaining user journeys are not certified by the model checks.

## User feedback

The user replied **“Looks right now”** to revisiting weekday views and completing
Read to inspect Outline. This accepts those visual repairs only. The earlier
“nothing stuck” report still applies to its original separate examples; neither
report establishes combined completion during an active timer or final acceptance.

## Rendered spacing checks

Inspected static Today references [640×800 Light](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=11-2)
and [800×900 Dark](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=11-457).
Both show consecutive compact Read/Outline rows without a large white gap.
Temporarily rendered the actual [completed-Read frame](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-4109)
at 640×800 Light and 800×900 Dark, seeding Read completion, expanded completed work
and the four derived layout heights. Outline starts at y1 within its list; its
row remains 59px high. Inter Regular/Medium/Semi Bold were read back and loaded,
matching the existing Figma fallback (the fallback choice remains unconfirmed).

The seed checked layout, not complete total derivation: labels were not fully
recomputed for that isolated render. The installed-reaction model checks completion
totals separately. The compact frame's lower completed rows extend below the
visible crop; the single Main content viewport (5:4123) has VERTICAL overflow and
clips content. Actual scroll discoverability/reachability remains a user gate.
Every temporary variable, dimension and explicit theme override was restored in
finally, then read back: 800×900, no explicit color-mode override, original eight
seeded values. No responsive reference was converted into an interactive screen.

## Acceptance and affected objects for recovery repair

A failed save must retain its sample details; Retry must use the same closed-week
check and representative task identity as Save. A closed-day error must offer a
route to review details, never a false saved result. Clicking outside any of the
four task forms must match Cancel's current session/Today return context. No real
records are affected and no domain/default rules changed. Dismissal creates no
task; the existing representative retry is replay safe. No new Undo behavior.

Inspection found inherited clickable Feedback instances leading directly to
Task saved (5:4403), bypassing guarded Save. Repaired:

- Failed-save Feedback 9:6086: cleared ancestor reactions; its button
  I9:6086;3:349 now copies guarded Retry Save 9:6095.
- Closed-day Feedback 124:7107: cleared ancestor reactions; its button
  I124:7107;3:349 now returns to task details and reads “Review day.”
- Backdrops 5:5532, 5:5608, 9:6064, 124:7095 now copy their corresponding
  timer/context-preserving Cancel reactions.
- Bottom label I124:7112;3:197 shortened from “Back to task details” to
  “Task details”: 75px text fits the 96px available inside its 112px button.

Ten exact affected node IDs are in the execution evidence; no new nodes/variables.
The post-fix 800×900 Light closed-day composition has readable, unclipped actions
and keeps the error/details visible. Validation/error screens use fixed example
fields; arbitrary text editing or changing to a new planned date is not demonstrated.

## Checks and limits

Executed the read-only installed-reaction model: **60 Pass / 0 Fail**. This includes
the previous 23 cases plus 37 focused cases: inline Retry success/replay and
closed-day rejection, Review day, four modal dismissals across idle/running/paused/
review/sleep, and both non-reactive feedback ancestors. Reset still initializes
206 prototype variables. These checks interpret the actual installed reactions in
JS Maps; they do not click Figma presentation controls or exercise real storage.
Prior 44 time and 601 navigation cases were not rerun for this repair.

One diagnostic attempted to return full reaction trees (2,374,517 bytes) and was
rejected by the 48,000-byte output limit, without canvas mutation. Retried with
bounded control summaries. All subsequent writes succeeded; no uncertain mutation.
No browser/computer-control tool is available. Actual clicking, scrolling, keyboard/
focus, arbitrary drag smoothness and assistive technology remain unverified here.
No application tests/service/database operations, commit or push in this continuation.
Concurrent application/Google work and duplicate files were preserved.

## Evidence and next action

- [Execution index](../../frontend/design/refinement-execution.json), key
  r23Resume20261103; [node ledger](../../frontend/design/figma-node-ledger.json).
- [Durable read-only model](../../frontend/design/refinement-support/continued-20261103/installed-journey-model.js)
  and [results](../../frontend/design/refinement-support/continued-20261103/installed-journey-model.json).
- [Scoped render/write evidence](../../frontend/design/refinement-support/continued-20261103/evidence.json).
  Executed mutation source archives in the same folder must not be replayed.
- [Shared progress](../PROGRESS.md) holds the pending task-entry prompt and remaining
  journeys. User acceptance of the recovery repair is pending; R23 remains open.

## Documentation verification

JSON parsing, relative-link checks, status assertions, 60-case result assertions,
ten changed IDs and restored preview assertions passed. Scoped git diff --check
passed. Node 24.21.0's plain node --check rejects the Figma script bodies' top-level
return; these are async function bodies, not standalone modules. Rechecked all
three archives by constructing AsyncFunction without executing it: all pass.
Preserved existing JSON escape formatting to keep the artifact diff scoped.

## Task-entry user feedback

The user replied **“Clear and worked”** to this walkthrough prompt:

> Next walkthrough: reset Today, open Projects, and use “+ Add task” to save
> the sample “Draft seminar questions” with its shown deadline, estimate and
> planned day. Could you find the form, understand the fields, and find the saved
> task without confusion? The prototype uses fixed sample values.

**Outcome: Pass with follow-ups for the user-reported sample task-entry journey.**
The report covers finding the form, understanding the shown fields, one Save and
finding the resulting sample task. No direct observation, timing, viewport,
keyboard, arbitrary editing, error-recovery or real persistence evidence was
provided. This does not accept the remaining R23 journeys or complete R24. No
corrective design change follows from this feedback.

The next prompt links directly to the failed-save example (9:6023), asking whether
the user can understand the error, Retry and find one sample task. Recovery remains
pending until reported; the earlier successful Save does not certify it. This
feedback update changed documentation only; no Figma/application changes, tests,
commit or push. Prior model results remain evidence for the prior repair.

## Failed-save user feedback

The user replied **“Clear and recovered once”** to the failed-save example:
understand what happened, Retry and find Draft seminar questions once in the task
list, using fixed sample fields. **Pass with follow-ups for this user-reported
recovery example.** No corrective change was requested. This supports the repaired
failed-save Retry path; it does not establish repeated retries, closed-week
rejection, timer-context dismissal, real persistence or other error states. No
direct observation, timing, viewport or keyboard evidence was provided.

The next prompt links to the closed-week save example (124:7050): understand the
blocked-save explanation, use Review day and inspect retained details. It explicitly
states that date editing is not interactive. That is a navigation/content check,
not certification of guard enforcement from a directly opened frame. R23 remains
Active; R24 not started. Documentation-only update; no Figma/application changes,
new behavior tests, commit or push. Content/link/status checks and scoped diff
whitespace check passed. Prior review sections describe their original checkpoint.

## Closed-week recovery user feedback

The user replied **“Clear; details were retained”** to the closed-week save
example: understand why saving was blocked, use Review day and inspect the
retained sample task details. **Pass with follow-ups for this user-reported
explanation/recovery-navigation example.** No correction requested. Date editing
was explicitly outside this fixed example. Directly opening the error frame does
not prove enforcement of the closed-week guard; the prior installed-reaction model
covers that guard. No real records, direct observation, viewport, timing or keyboard
evidence were provided. Overall R23 acceptance and R24 handoff remain open.

For the next layout walkthrough, inspected the existing 640×800 references:
Today 11:2, crowded Today 65:5554 (20 task rows) and Projects 82:6877. Today uses
one 640×740 clipped Main content scroll viewport. Projects has Main content plus
a 392×475 clipped Project task scroll. These are layout references with unwired
task/disclosure controls. The pending user prompt tests finding the eighth task
Prepare lab materials and scrolling to Check essay citations in Today, then
reaching the last task in Projects; it does not ask unsupported controls to run.
This inspection confirms configured scroll containers, not actual scroll behavior.
No mutations followed this read-only Figma inspection.

Updated feedback/progress/completed documentation only. Content/link/status and
scoped diff whitespace checks passed; no application tests, commit or push.
Concurrent application work and earlier design changes were preserved.

## Compact and crowded scrolling user feedback

The user replied **“Both clear and reachable”** to finding Prepare lab materials,
scrolling to Check essay citations in crowded Today (65:5554), and scrolling the
project list to its last task in Projects (82:6877). The prompt explicitly stated
that these are layout/scroll references with unwired task buttons.

**Pass with follow-ups for user-reported task visibility and scrolling in these
two references.** No clipping or scroll-area confusion was reported; no correction
requested. The reference frames are 640×800, but the user's actual window size,
zoom, input method and elapsed time were not reported or directly observed. This
does not certify Start/disclosure controls in those static references, keyboard,
assistive technology, other widths or arbitrary content combinations.

The next walkthrough covers Reset Plan week → preview/cancel End Week → close →
inspect the single Read carryover candidate/default day → uncheck/recheck/redate →
Review/cancel without Apply → return to closed week → reopen/review/Apply → inspect
next week. Those steps remain pending until reported. R23 remains Active and R24
not started. Updated documentation only; no Figma or application mutations, new
behavior tests, commit or push. Content/link/status and scoped diff whitespace
checks passed. Unrelated concurrent work was preserved.

## End Week and carryover unresolved user finding

The user selected **“Something unclear or unsuccessful”** for the combined
walkthrough: Reset Plan week, preview/cancel End Week, close, inspect Read's single
candidate/default day, uncheck/recheck/redate, Review/cancel, return to the closed
week, reopen/review/Apply and inspect next week.

**Outcome: Fail for this walkthrough checkpoint — unresolved user finding.**
This means the flow is not accepted; the response does not identify which step
failed, whether the issue was interaction or explanation, or what state appeared.
Do not infer successful preceding steps, a specific bug, a date mismatch or a
required redesign from the choice alone. Earlier 60-case model checks do not
overrule the user's report.

Asked for the step/button, expected result and actual result, including any wrong
date/task list. Awaiting that detail before targeted repair. Independent read-only
inspection located the existing controls/destinations in End Week preview 6:2541,
Closed week 6:2600, Carryover 6:2634, Review 6:2683, Change day 91:5667, Changed review
91:5720 and Next week 6:2761. Control presence is not proof that the user's route
worked. No canvas mutation or speculative fix was performed.

R23 remains Active with this open finding; R24 not started. Current next action
is clarification/localization, then repair and recheck that concrete route. Prior
successful scoped examples remain valid. Documentation content/link/status/diff
checks passed; no new behavior tests, application changes, commit or push. Concurrent
Google commits and working changes were preserved.

## Preview-cancellation repair and targeted user recheck

The user clarified the symptom: **“when I hit cancel, it does not cancel but
already end the week”**, then specifically **“Preview, before confirming End Week.”**
This localizes the report to pre-confirmation cancellation. The initial possibility
of post-close carryover confusion was not established as its cause.

Acceptance: entering/dismissing a closure preview must not close the source, change
frozen facts, create next-week plans or alter an active timer. Confirm End Week
alone closes; later Skip carryover stops only transfer, preserving the closed
source. If already closed, the preview must route to existing frozen history.
No saved records, core rules/defaults or Undo behavior changed; reopening remains
deferred. Synthetic Figma service date remains November 1.

Inspection covered actual Week entry buttons, both previews, ancestors, absolute
bounds and modern/legacy reaction fields. Only the confirmation actions wrote
weekClosed=true; no overlap or ancestor closure handler was found. Installed-
reaction checks did not reproduce early closure. A real related issue was found:
preview backdrops returned to Today rather than the source weekly board. Also,
a directly revisited preview could still show before confirmation when the demo's
week was already closed. Neither is proven to be the exact cause of the user's
original symptom; the report was not dismissed based on model results.

Applied bounded repairs/clarifications across **32 unique existing nodes**, with
no new nodes or variables:

- Preview exit reads **Keep week open**. Copy states **Nothing changes until you
  choose End Week**, then explains frozen planning and optional carryover.
- Both preview backdrops now use the same source-Week-preserving exit reactions.
- Both preview timed entries guard already-closed sources, routing to their existing
  frozen view without reopening or altering closure/carryover facts.
- Later carryover/Review exits read **Skip carryover**, with explicit Week closed
  status and no-new-dates consequence. Buttons widened to 128px.
- Propagated copy/labels to compact Light, split Dark, empty and all-complete
  references. Internal layer action names remain stable for existing references.

Fonts read back as Inter. Keep week open measures 103px inside 108px available;
Skip carryover measures 90px inside 112px. Fresh final composition checks:
preview 6:2541 at 800×900 Light, carryover 113:8566 at 640×800 Light and review
113:8733 at 800×900 Dark. Text/actions are readable and unclipped; long candidate
lists remain inside their existing scroll viewports. An earlier preview render
was superseded after making the pre-confirmation wording explicit.

Final installed-reaction Map model: **111 Pass / 0 Fail**. The prior 60 checks
remain, plus 51 focused cases: preview cancellation in both completion states
and five session states, post-close skip/no-apply, outside dismissal, actual
Reset/Week-entry/preview/exit, reordered/complete source returns, Escape metadata
and eight stale-preview combinations. Earlier intermediate runs were 78, 88, 93
and 103 passes while narrowing/extending the checks. These are model checks,
not actual agent-driven clicks, keyboard execution, storage or Mac sleep evidence.
Reset remains 206 variables; 44 time and 601 navigation checks remain historical.

User recheck prompt: reload launcher → Reset demo · Plan week → open End Week →
Keep week open. The user replied **“Returned to the open week.”**
**Outcome: Pass with follow-ups for this targeted user-reported preview exit after
repair.** The full original cause is not reproduced independently; retain the
original report and repair evidence. Do not mark the entire End Week/carryover
walkthrough accepted from this narrow response. No viewport, timing or input-method
evidence was reported. A follow-up now covers choices/redating, Review/Skip,
closed-week re-entry and reviewed Apply into next week.

Evidence: refinement-execution.json key r23Cancel20261103 and
[cancellation support](../../frontend/design/refinement-support/continued-20261103/cancellation/evidence.json),
[model source](../../frontend/design/refinement-support/continued-20261103/cancellation/installed-cancellation-model.js)
and [results](../../frontend/design/refinement-support/continued-20261103/cancellation/installed-cancellation-model.json).
Executed mutation sources in that folder are archives and must not be replayed.
Documentation JSON/link/status/whitespace and async-body syntax checks passed.
No application changes/tests, new commit or push; concurrent Google work preserved.

## Remaining carryover sequence user feedback

The user replied **“Clear and completed correctly”** to confirming End Week,
unchecking/rechecking Read, choosing another available day, Review, Skip carryover
with no dates added, returning to the closed week, reopening Carry unfinished,
reviewing/Apply and inspecting next week. **Pass with follow-ups for the prompted
user-reported carryover sequence.** No further correction requested. Combined with
the successful targeted Keep week open recheck, this accepts the reviewed closure/
carryover direction in the finite example. The initial cancellation report and
its unproven root cause remain in the evidence rather than being rewritten.

This does not establish exact counts/dates beyond the user's general report,
actual persistence, arbitrary eligibility combinations, repeat/lost-response Apply,
keyboard or assistive technology. No direct observation, viewport, input method or
timing was provided. The current prompt now checks Stats Missed before/after later
Read completion and frozen source history without Reset. That report, remaining
recovery/Assistant journeys and overall R23 acceptance remain pending. Documentation
content/link/status/diff checks passed; no Figma/application changes, new behavior
tests, commit or push. Concurrent application work preserved.

## Missed and frozen-history user feedback

The user replied **“Clear; current status changed and history stayed”** to noting
Stats Missed, completing Read in Projects without Reset, and revisiting Stats
and the closed source week. **Pass with follow-ups for this user-reported live
completion versus frozen-history example.** No correction requested. This supports
understanding that later completion changes current status while historical Missed
and at-closure status stay unchanged. Exact totals, repeated misses across several
weeks, arbitrary task combinations and real saved data were not independently
observed or established by this report. No viewport, timing or keyboard evidence.

Next prompts are separate Reset examples: start Read's countdown, complete Read
through Plan, return to Track and pause/reopen the same session; then use Review
an interruption, inspect 120 seconds confirmed versus 300 uncertain and explicitly
continue. Those results are pending. Prior separate completion and pause reports
do not substitute for the combined active-timer check. R23 remains Active and R24
not started. Documentation content/link/status/diff checks passed. No Figma/app
changes, new behavior tests, commit or push; concurrent work preserved.

## Active-session completion and interruption user feedback

Two separate Reset examples were reported:

- **“Same session and controls stayed available”** after starting Read's countdown,
  completing Read through Plan, returning to Track, then pausing/reopening. This
  now supplies the previously missing combined task-completion/active-session
  user report; earlier separate examples were not substituted for it.
- **“Clear; only confirmed time counts”** for Review an interruption, inspecting
  120 seconds confirmed versus 300 uncertain and explicitly continuing.

**Pass with follow-ups for both prompted user-reported focus examples.** No
correction requested. The report supports preserved session controls and the
confirmed/uncertain-time distinction in the prototype. It does not certify real
elapsed-time accounting, durable session identity, operating-system interruption
or sleep/wake, reward accuracy, all recovery branches or hardware acceptance.
No direct observation, viewport, timing or keyboard evidence was provided.

Read-only inspection confirmed the next review's supported controls: Stats Recent
sessions; Assistant Ask, Sources and Cancel; missing-model retained-question state;
and the fixed empty-name validation reference with disabled Save. Generating has
a two-second transition, so the prompt explicitly asks the user to report Cancel
as untested if the answer arrives first. Current prompts cover Stats scopes,
Assistant context/model/sources/cancel/error and static validation clarity. Those
results and overall R23 acceptance remain pending. R24 not started. Documentation
content/link/status/diff checks passed. No Figma/app mutations, new behavior tests,
commit or push; concurrent application work preserved.

## Final Stats, Assistant and validation feedback

The user reported:

- **“Clear and easy to distinguish”** for Stats saved-focus/current-completion/
  historical-Missed scopes and Recent sessions detail.
- **“Clear; question remained after cancel/error”** for the Assistant sample answer,
  Sources used, generation cancellation and missing-model example. The prompt
  explicitly offered reporting Cancel as untested if the two-second response
  arrived first; the user instead reported retention after cancel/error. Record
  this as user-reported Cancel/error success, not direct observation or inference.
- **“Clear; other details remain visible”** for the fixed empty-name validation
  reference. Actual typing/correcting was explicitly outside the example.

**R23 outcome: Pass with follow-ups for the bounded formative prototype walkthrough.**
The ten repair-plan journey areas have user-reported coverage across the linked
November 2/3 records, with the cancellation finding repaired and successfully
rechecked. The aggregate reports accept the demonstrated direction; no additional
blocking confusion is reported. This closes the repair walkthrough ticket, not
all original UX-01–36 checkpoint acceptance or production readiness. Detailed task
timing, actual window/zoom, agent-observed clicks, keyboard/focus, arbitrary drag,
assistive technology and real data/timing remain outside the evidence. Unwalked
optional rewards/correction branches remain documented limits rather than implicit
user acceptance. R24 now prepares the revised handoff; no application work starts.
Documentation-only feedback closure; no Figma mutation, application tests, commit
or push. Content/link/status checks accompany the R24 handoff review.
