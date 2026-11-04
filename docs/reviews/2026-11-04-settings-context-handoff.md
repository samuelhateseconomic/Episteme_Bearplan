# UX-C06 — Settings contexts, themes and handoff

November 4, 2026, America/Los_Angeles. User authorization: “go ahead” after the
planning-index status placed UX-C06 next. Base commit `01bb39c`; new work is
uncommitted. Scope: Figma design and documentation. No application, API, schema,
service, credential, provider or preserved core-trial copy changed. Unrelated
backend/account/CLAUDE changes and duplicate files remain untouched.

**Outcome: Pass with follow-ups for the scoped static/finite-prototype handoff
and bounded user design review.** This is not a complete runtime/accessibility
acceptance or an independent technical audit. Codex was the sole Figma writer and
technical reviewer. The user supplied the independent bounded design walkthrough;
no second agent was used. Full original UX checkpoint and release gates remain
unchanged.

## Delivered

- [Consolidated guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=293-8853&starting-point-node-id=293%3A8853&scaling=min-zoom),
  800×1284, 18 isolated starts plus links to the three existing flow guides.
- Six free-canvas sections, **54 full-window frames**: 640×800, 800×900 and
  1440×900 in Light/Dark, each with nine named work/Settings/provider/dialog states.
  Existing IDs/layouts retained; one named flow entry added. No page-sized wrapper.
- Long-course wrapping/scroll example, full-window Google scope and paused/offline
  dialogs, bCourses Keep token/removal receipt, Today/paused Track context return.
- Existing focus/disabled/loading/error variants in both themes, with corrected
  token-validation copy. Appearance only; no keyboard or credential entry claim.
- [Implementation handoff](../../frontend/plans/settings-connections/HANDOFF.md),
  [inventory](../../frontend/design/settings-connections/contexts/inventory.json),
  [installed sources](../../frontend/design/settings-connections/contexts/sources.json),
  [audit](../../frontend/design/settings-connections/contexts/audit.json),
  [native render manifest](../../frontend/design/settings-connections/contexts/renders.json)
  and the extended [ledger](../../frontend/design/figma-node-ledger.json).

The handoff identifies exact source IDs, components/properties, semantic modes,
reviewed dimensions, proposed centered-column measurement, finite interactions and
engineering dependencies. Existing Inter fallback and visual foundations retained;
no new production token API/dependency. Six token-status and six return-origin
variables are isolated from all original prototype state. Only that new state is
written by context controls/guide resets. The Today/Track examples show the same
paused Read, 18:00 and 12 confirmed minutes; they do not implement session storage.

## Verification

Environment: actual **macOS 26.6.2 / Darwin arm64**, Node **24.21.0**.

| Check | Actual result |
| --- | --- |
| Final full-window structure | 54 frames; 4,014 descendants including roots: 1,152 FRAME, 186 VECTOR, 1,614 TEXT, 942 INSTANCE, 42 ELLIPSE, 78 RECTANGLE. Zero raster UI, font, overflow or normal-flow overlap findings. |
| Guide structure | 86 nodes: 14 FRAME, 43 TEXT, 29 INSTANCE; zero overflow findings. |
| Canvas/ledger reconciliation | 4,106 nodes including six sections and guide; sorted-ID FNV-1a `59016469`. |
| Layout isolation | Zero inherited original task/timer/history bindings in all six lanes; 44 installed action sources per lane. |
| Installed actions | 285 sources total, including 21 guide controls. Captured after final origin routing. |
| New finite models | `node frontend/design/settings-connections/contexts/check-models.mjs --write`: **165 passed, 0 failed**. |
| Prior recovery regression | `node frontend/design/settings-connections/recovery/check-models.mjs`: **58 passed, 0 failed**, using its retained readback. Fresh live fingerprints matched all 145 prior sources: zero differences. |
| Prior Google routing regression | `node frontend/design/settings-connections/google/routing-model-check.js`: **19 passed, 0 failed**, retained readback; not a fresh replay of every Google state. |
| Renders | 30 PNGs exported at scale 1; PNG headers matched all expected native dimensions. Visually inspected overview, long bCourses, consent and offline for every width/theme, plus guide and selected session/removal views. |

The models interpret actual captured native reactions. They cover opening Settings
from Today and Track; returning to the initiating frame; Keep token as no-op;
explicit removal, retained sample result, lane-local reset, Google-scope Not now,
offline exit, separate policy/last success, source isolation, dimensions/modes and
sample-session consistency. They do not click presentation or execute real timers,
providers, storage, arbitrary resizing or keyboard behavior. No unrelated app suite
was rerun for this design/docs change.

Final local content checks: `python3 /tmp/bp-c06-verify.py` verified **360 local
Markdown links across eight files**, **nine JSON artifacts**, **30 PNG dimensions/
hashes**, ledger equality outside the new entry, twelve scoped variables, no
transient asset URLs/token patterns, preserved unrelated tracked diffs and an empty
Git index. `node --check frontend/design/settings-connections/contexts/check-models.mjs`
passed. Ten archived call bodies compiled with `AsyncFunction` without execution.
`git diff --check` passed. The checker was rerun after the final inventory/audit
reconciliation: 165 passed, 0 failed.

## Findings repaired

1. The inherited modal paint rendered opaque instead of dimming the background.
   Split the dim layer from the dialog container and applied node opacity, retaining
   semantic fills. Final Light/Dark renders show the context behind the dialog.
2. Reused property/binding behavior initially retained short default management
   copy. Applied the long-text override after layout edits and checked actual
   198/180px text height and scrolling.
3. Cloned instances retained/restored original reactions and height/visibility/text
   bindings. Finalized snapshot bindings, removed inherited actions after layout
   changes and rebuilt only the scoped routes. Readback shows zero original bindings
   or writes; original recovery fingerprints are unchanged.
4. Kept automatic policy visible separately from last complete success. Paused/
   offline background uses Resume, and its last-success copy no longer uses an
   incorrect relative “below” reference.
5. Added isolated origin state so closing Settings opened from Track restores Track
   rather than always returning to Today. Both origins pass installed-action models;
   the user’s directly reported return walkthrough was from Today.
6. Reused Input Error initially said “Enter a task name.” Corrected both specimens
   to token-validation feedback and re-exported the final guide.

Tool/check failures were resolved: oversized readbacks were narrowed; an initial
self-navigation write was safely rolled back and removed; an overlong script was
rejected before execution and reduced; all tool failures reported no committed
mutation. A contact-sheet helper found no system Pillow, so no dependency was added
and native images were inspected directly. The initial new checker rejected the
two offline Back controls as ambiguous; it now checks both equivalent exits and
passes. Executed construction calls are archived as evidence in
`contexts/executed-calls.json`; **do not replay** them. Reconcile canvas and ledger
before future edits.

Exact prompts and replies are preserved in [walkthroughs.json](../../frontend/design/settings-connections/contexts/walkthroughs.json).

## Bounded independent user design review

Prompt 1: “640 · Light · Start”: Settings → bCourses Manage; scroll the long course
names; Remove token → Keep token; Back to work → Open timer. The prompt explicitly
said these are fixed samples and other task/timer controls are visual references.
User: **“Clear; all those steps worked”.**

Prompt 2: inspect “640 · Dark · Start” and Google scope in its row for text/buttons,
gaps and clipped actions. User: **“Readable; layout looks right”.**

Prompt 3: bCourses “First connection” and “Rejected token”; Google “Simulate missing
permissions”; recovery “Local removal · Google unavailable”. The prompt asked about
recovery and the distinction between all-task/bCourses export, local disconnection
and confirmed Google revocation; it disclosed fixed simulations.
User: **“Clear in all examples”.**

These are verbatim user reports, not observed/timed interactions. Actual viewport,
zoom/input method and every individual click were not recorded. They do not certify
all guide examples, typing, real credentials, browser callbacks or provider results.
Earlier C05 Pause → Sync once → Resume report remains separate evidence.

## Follow-ups and implementation boundary

- A second independent technical/design-contract audit remains a follow-up; the
  independent review here is the user’s bounded design walkthrough.
- Actual keyboard/focus/assistive technology, 200% zoom, arbitrary browser resizing,
  very large text and the full setup/error matrix across all themes remain open.
  The static matrix is representative, not every C03–C05 state multiplied by six.
- New context lanes leave other controls as disclosed references. Direct synthetic
  removal omits pending/error stages; use C05 for those finite examples. Session
  ID, scroll/focus restoration and real persistence need APP-C checks.
- Carry forward the known `GoogleSync.while_idle` timeout barrier and automatic
  direct-reader Pause gaps to APP-C02/C04. Do not certify them from the prototype.
- Reconcile current backend/account work before building; no new API or migration
  was implemented. Proposed dimensions/font/breakpoints and the dedicated bCourses
  review placement are not all confirmed by these bounded reports.
- No commit/push was requested for UX-C06. Current authorization, remaining gates
  and next eligible unit live only in [PROGRESS](../PROGRESS.md).
