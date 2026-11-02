# Figma follow-up — discussion rows and free editing canvas

Date: November 1, 2026. Environment: macOS 26.6.2 / 25G83.
Ticket: UX-32.1 scoped user corrections. Sole Figma writer: Codex; independent
inventory reviewer confirmed orphan source locations and a complete screen
partition. App implementation and full UX acceptance remain separate.

**Outcome: Pass with follow-ups.** Rendered hierarchy and canvas layout checks
pass. Native reopen actions are wired and state visibility is checked; actual
browser click/keyboard/scroll execution remains unverified.

## User-visible acceptance

Completing Read keeps one compact gray, struck-through row beside its siblings
above the footer. Reopening restores its active details and Start in the same
view. Completion never starts or finishes a timer. The editor opens onto an
unbounded two-dimensional Design canvas: six main workspaces across the top,
related states in named flow areas below, with open space to pan and expand.

The user supplied [AI Usage Hub — Developer Console](https://www.figma.com/design/6Axot2OcYiKcSfGYcLh3Jh)
and confirmed this concerns the editing canvas, not app viewport behavior.
Read-only metadata/programmatic inspection found one Design page, native freely
positioned frames and components. No reference-file content was changed.

## Repairs

| Frame | Existing completed row | Repair |
| --- | --- | --- |
| [Prepare discussion](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=5-5292) | 18:5191 | Moved before footer spacer; reopened in place |
| [Reopened child](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=9-6097) | 23:6149 | Same correction; removed stale duplicate progress subtitle |
| [Saturday](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=9-5956) | 23:6142 | Same correction in planned-day list |

The first repair screenshot exposed an additional duplicate: earlier first-match
lookups had bound backdrop Read rows, missing the two foreground drawer rows.
Bound 5:5341 and 9:6160 to the existing readingIncomplete visibility variable.
Final completed-state screenshots show Read once and above the footer; active
state assertions show the normal row restored and the completed row hidden.

Hidden completed checkboxes had no reactions because the earlier traversal skipped
invisible instance children. Added the existing Read-reopen actions to all three,
excluding navigation so the current view stays open. They update completion,
counts and derived parent progress; no session variable is changed. Preserved
existing row IDs, component instances, visibility variables and task semantics.

## Editing canvas

[Open Canvas · Flows](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=50-4633).
Page 2:5 is renamed and moved first. Added nine native Section nodes 50:4633–50:4641:
main workspaces, Today, Projects, Week, close/carryover, Track, rewards, Stats,
Assistant. No enclosing app/page frame was added. The six main workspaces form
the initial horizontal overview; all 75 screens are original editable frames.

Reparenting changes only canvas coordinates/section membership. Per-screen
signatures of dimensions, explicit modes and complete native reaction JSON match
before/after for all 75 frames. Ten named flow starts remain. The 17 responsive/
theme references on Screens are unchanged. Future scripts must resolve screen
roots by ledger IDs, rather than assuming their immediate top-level ancestor is
a frame.

## Checks actually performed

- Live before/after hierarchy and native reaction inspection; metadata for 5:5292.
- Completed-state full-frame screenshots of the three affected views; two targeted
  post-fix drawer screenshots after fixing duplicate visibility. Read is at y237/
  y347 in the repaired drawers, above footer y836; Saturday y248 above footer y776.
- Temporary completion/parent-progress variable values were restored in finally.
  Active-state assertions passed for all three active/completed row pairs.
- Repaired frames retain editable layers and component instances, no image fills,
  and Inter, the previously documented Figma fallback.
- Full main-section screenshot (2400px) and page overview (1600px) reviewed:
  separate workspaces, open space, no overlapping sections or escaped frames.
- Final native audit: 9 sections, 75 unique frames, zero unsectioned/overflowing
  frames or section overlaps; 2,383 frames, 2,653 text layers, 1,849 instances,
  503 vectors, 217 ellipses and 229 rectangles across screen trees.
- 1,130 native reactions, 62 distinct destinations, zero missing destination
  nodes; 10 flow starts. Zero UI image fills; all text remains Inter.
- Used Figma's open-in-thread tool for the original file and then the new main
  section. Successful open request does not prove the user's viewport rendering.
- Computer control still fails: “failed to start Node runtime: No such file or
  directory (os error 2)”. No actual presentation click, keyboard or scroll test.
- Filesystem content/link/JSON/diff and frontend source-hash checks recorded below.

No API, application code, data, dependency, service, core-trial copy, commit or push
was changed by this correction. Concurrent application changes in the working tree belong
to other work and were preserved.

## Remaining review

User confirmation of the editing workspace and discussion hierarchy, then further
scoped prototype feedback. Native in-place completion/reopen needs actual browser
execution. Full UX roadmap acceptance, app refresh and release/hardware gates
remain open.

## Filesystem verification

- `git diff --check -- docs/PROGRESS.md frontend/FIGMA_PROTOTYPE.md frontend/design/figma-node-ledger.json docs/COMPLETED.md docs/reviews/2026-11-01-figma-discussion-and-canvas.md`: Pass.
- Standard-library Python: JSON/page inventory, exact 75-screen partition across
  nine sections, 17 separate references, ten starts and zero signature/destination/
  geometry mismatches: Pass. Markdown local links and whitespace: Pass.
- The first publication attempt failed on the ledger's dictionary-valued notes
  field before any repository write; fixed that format and published successfully.
- A frontend source-baseline equality assertion failed because concurrent work
  changed Statistics.test.tsx, Statistics.tsx, WeekActions.test.tsx,
  WeekActions.tsx, WeeklyPlanner.tsx and api.ts. A separate read-only check found
  no added/removed source files. Those files were not written by this Figma task;
  do not interpret the earlier draft's unchanged-source result as current-tree
  evidence. Concurrent backend/statistics/week changes were also left intact.
- No application tests/build were run for this Figma/documentation correction.
