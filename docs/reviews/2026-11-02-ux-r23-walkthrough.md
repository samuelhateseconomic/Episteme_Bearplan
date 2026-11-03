# UX-R23 — initial user walkthrough evidence

Date: November 2, 2026 (America/Los_Angeles). Environment for documentation:
macOS 26.6.2 / Darwin arm64. Scope: two previously presented Figma examples;
no Figma or application changes in this checkpoint.

**Outcome: Pass with follow-ups for these two user-reported examples.**
The user replied **“nothing stuck”** to this prompt:

> The Figma review launcher is open. For the first walkthrough, try choosing work
> from the lower Today rows, pausing it and returning to the same session; then
> complete and reopen “Read the primary source” under “Prepare seminar discussion.”
> What worked, and where did you hesitate or get stuck? Use Reset between the two
> examples.

## Evidence accepted

- Lower-row Today task selection, start/pause and return to the same session:
  user reported no obstacles.
- Read completion/reopening within Prepare seminar discussion: user reported
  no obstacles. The examples were separated by Reset.

This is the user's report, not direct observation by the agent. No specific
viewport, eighth-row discovery, elapsed time, keyboard route or scroll behavior
was reported. It does not establish completing a task during an active timer,
parent-total arithmetic, real persistence, arbitrary drag smoothness or overall
acceptance. No corrective design change follows from this feedback.

The evidence partially covers the repair plan's task-discovery and child-work
journeys, and supports its pause/navigation journey within the reported example.
R23 overall remains open. Remaining work and the next prompt belong only in
[PROGRESS](../PROGRESS.md), against [repair plan §8](../../frontend/BEARPLANS_UX_REPAIR_PLAN.md#8-required-validation-matrix-and-walkthrough).

## Verification and preservation

Inspected Git status, recent commits, working diff, current guidance and progress.
Re-read the applicable design review workflow and walkthrough matrix. Independent
reviewer walkthrough_scope_review confirmed the narrow evidence interpretation.
`sw_vers -productVersion` returned 26.6.2; `uname -m` returned arm64.
`python3` inline checks passed for scoped user evidence, unchanged ticket gates,
relative links and whitespace.
`git diff --check -- docs/PROGRESS.md docs/COMPLETED.md docs/reviews/2026-11-02-ux-r23-walkthrough.md` returned exit 0.
Application tests were not run for this documentation-only feedback record. Existing application work, CLAUDE.md
edits and untracked duplicate files are preserved. No commit or push.

## Weekly feedback and spacing repair — stop checkpoint

The user reported no weekly-flow confusion/failure, but said day designs looked
different and Outline had a large white gap. This does not accept the visuals.
The user then requested finishing the fix, documenting, committing and stopping.

Applied: aligned History/header, selected-day treatment and footer controls across
nine day/result views; removed the oversized Wednesday panel fill; corrected the
Saturday due caption and compact row, and Wednesday's 3-minute estimate. Four
layout-only float variables explicitly collapse inactive Read shells and manual
order groups so Outline has no reserved blank task slot. Applied binding updates
and height derivation across 42 affected roots in seven bounded groups. All eight
launcher Reset controls include the new values (206 variables total).

Verification: 800×900 Light renders of Wednesday and Saturday now have compact
59px rows with consistent History/End Week controls. A temporary completed-Read
Today render showed Outline at y1 in its list, with its preceding restoration
shell reduced to 1px. Temporary values were restored. The installed-reaction
journey model was rerun: **23 Pass / 0 Fail**, including completion, timers,
Move/closure and Reset. Earlier 44 time and 601 navigation cases are historical;
they were not rerun for this layout-only repair. No application tests were run.

A monolithic write timed out; a subsequent canvas read confirmed no new variables
or header change. Bounded visual and seven reaction batches then succeeded.
An invalid HEIGHT variable scope was rejected atomically and corrected to
WIDTH_HEIGHT. Exact IDs/outputs are in refinement-execution.json r23Spacing20261102
and the node ledger. Archived patch sources must not be replayed.

**Outcome: Pass with follow-ups for the scoped spacing repair.** User review of
this latest fix, remaining walkthrough journeys, compact/dark affected-state checks,
keyboard/scroll and final R24 handoff remain pending. No overall acceptance claim.
Work is paused at the user's request; current resumption details are in PROGRESS.
Concurrent Google/application work and duplicate files remain outside this commit.

Checkpoint documentation checks passed: JSON/link/whitespace assertions confirmed
seven successful batches, 23 passing cases, 1px spacing and restored preview.
The initial staged diff found four extra EOF blank lines in archived scripts;
these were removed before the final checkpoint amendment. Application changes
were excluded; no push was performed. Work remains paused by user request.
