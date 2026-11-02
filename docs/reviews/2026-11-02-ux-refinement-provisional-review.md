# R22 independent UX/UI review — provisional

Reviewed November 2, 2026 (America/Los_Angeles). Reviewer: ux_inventory.
File: `jobFe4sXDot7BKsej0arNB`; session: `8ac12b29-2135-4b7a-8c4c-fd2b515b445b`.

**Static decision: Pass with follow-ups for the captured scope. No new static P1 found.**
This is a provisional formative review while the sole writer completes R21.
It is not final R22 acceptance, user acceptance or implementation approval.
Actual presentation clicks, scrolling, drag, keyboard/focus and assistive
technology remain unverified. The synthetic service day is November 1; it is
intentionally different from the review date.

## Evidence actually reviewed

Fresh full-frame screenshots:

- Today `5:3972`: eight complete active rows, explicit unfinished/completed count,
  compact streak, collapsed completed/earlier sections; no misleading selected
  first row in the resting state.
- Week `6:1802`: Previous/Today/Next, day counts, 2/11 and 18% progress,
  selected task/project/source-date toolbar, consistent Outline Nov 4 / 20 min.
- Projects `5:4847`: compact administration, parent progress without direct
  checkbox/Start, indented children and reachable Add task footer.
- Carryover `6:2634`: nine preselected candidates, explicit pre-Apply status,
  visible unchanged deadlines and Nov 8 suggestions; fixed Review/Cancel footer.
- Recovery `7:2733`: 12 confirmed minutes, 18:00 of 30:00 remaining, five excluded
  minutes, explicit Continue/Finish, locked species and separate saved-day streak.
- Assistant answer `7:3390`: explicit context, quiet local-model status, bottom
  composer, collapsed sources and New question. It remains a deliberate read-only
  design subset, not a claim that current M5 lacks Apply/Undo/carryover actions.

Fresh targeted metadata: compact carryover `113:8566`, dark compact Week
`113:9419`, crowded Projects `82:6877`, enlarged-text `115:8987`.
The long carryover candidate `113:8635` expands to 135 px; its planned date
`113:8643` moves to y90 rather than colliding with the wrapped title.
The crowded project viewport `82:6935` ends at y728; footer `82:6944` starts at
y736. Content `82:6936` retains its 1254 px extent. Metadata establishes geometry,
not actual scrolling or overflow-direction behavior.

Also considered the earlier independent renders within this same repair session:
compact/dark Today `11:2` / `11:457`, wide Week `13:710`, Stats `7:3036` / `11:328`,
dark Stats `113:9187`, compact carryover `113:8566`, dark editor `113:8392`, dark
Done `116:9264`, dark compact Week `113:9419`, and enlarged text `115:8987`.
These were not recaptured unchanged solely to accumulate evidence.

Read the canonical brief, repair plan, original expert evaluation and current
refinement execution/review records. No canvas/app/repository mutations were made.
Only this requested temporary report was saved.

## Provisional scorecard

Same 13 categories and weights as the original evaluation. Scores concern the
observable design, not measured task success or runtime conformance.

| Category | Score / 100 | Weight | Evidence for change or remaining limit |
| --- | ---: | ---: | --- |
| Daily workflow fit | 89 | 15% | Eight readable Today rows; scheduled work, project context and Start remain direct. |
| Prioritization and next action | 80 | 10% | Selected placement is explicit in Week and no automatic priority is implied; Today manual-order cue is currently missing after count rebinding. |
| Task density and scanning | 87 | 8% | 59 px ordinary rows, smaller chrome and natural long-title growth; crowded tasks require actual scroll validation. |
| Weekly planning and review | 86 | 15% | Visible calendar navigation, per-day counts, progress and movement target; selected-day comparison and horizontal-board use remain untested. |
| Projects, subtasks and Done | 87 | 8% | Parent/child hierarchy, bounded crowded task body, compact completion and unique planned-week scope are represented. |
| Track and focus | 89 | 7% | Change-task setup and recovery consequences are clearer; active-session safeguards are structurally modeled, not browser-tested. |
| Streak and motivation | 91 | 4% | Compact saved-progress cue, corrected dark pairing and on-demand rewards preserve the intended balance. |
| Statistics usefulness | 89 | 5% | All-time saved measures, current completion and frozen Missed are distinct; dated bars and optional detail are readable. |
| Assistant experience | 87 | 5% | Context/model status, sources, retained-question states and composer are clear within the bounded read-only sample. |
| Visual hierarchy and minimalism | 90 | 8% | Reduced chrome and repeated explanations; Week still repeats a range and History entry. |
| Cross-view consistency and trust | 87 | 5% | Fixture repairs resolve visible Outline mismatch and define historical differences; final R21 count/state rebinding remains in progress. |
| Compact layout and accessibility | 84 | 5% | Repaired widths, text-growth fixture, larger grip target and sampled contrast improve static readiness; runtime access remains untested. |
| Feedback, errors and recovery | 90 | 5% | Retained Notes, explicit pending/uncertain states, confirmed/remaining/excluded time and pre-Apply carryover are clear. |

**Weighted provisional score: 87.09/100 (87 rounded).** Original: 76.84/100.
The increase reflects observed repairs; it does not certify interaction success.

## Actionable findings

1. **P2 — preserve manual-order clarity after count rebinding.** Today `5:3972`
   currently says “8 unfinished · 2 complete”; the earlier “Your order” cue is gone.
   Retain a short manual-order cue beside the counts or equivalent context.
   Do not add automatic ranking, priority scores or metadata to every row.
   This may be a transient R21 integration change; reconcile before closing R21.
2. **P2 — optional Week chrome reduction.** Week `6:1802` repeats Oct 26–Nov 1
   beside navigation and repeats History at top and footer. One clear range and
   History entry could reclaim space without losing meaning. This is a density
   follow-up, not a new blocker or permission to change navigation behavior.

No new required static P1 was observed. The earlier missing Notes defect is
repaired; the long carryover card now grows instead of hiding its date.

## Timing and acceptance boundary

R21 is actively rebinding counts, created-task state and movement/closure routes.
This report describes the rendered default state at capture time. Final R21
metadata/model checks must finish, and any resulting visible changes need their
smallest affected recheck. This report does not certify those unfinished routes.

Required R23 user journeys remain pending: find task eight, navigate next week and
return, reorder/move/cancel/conflict, crowded Projects scroll, child completion/
reopen, reviewed carryover with re-entry, Missed after later completion, and return
to the same paused/review session. If tool-based preview remains unavailable,
record explicit manual user evidence rather than inferring success from reactions.

Application persistence, timers/rewards, actual accessibility/reflow, model quality,
core-trial and Mac hardware gates remain outside this review.
