# Settings and Connections — design implementation handoff

Design snapshot: November 4, 2026. Base checkout `01bb39c` plus the UX-C06
changes recorded in Git. This defines the reviewed design and its limits;
[PROGRESS](../../../docs/PROGRESS.md) holds current status and authorization.
Application implementation remains separately scoped through APP-C01–09.

## Open this version

- [Context/theme review guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=293-8853&starting-point-node-id=293%3A8853&scaling=min-zoom).
- [Free editing canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=2-5).
- [bCourses setup/recovery guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=241-6357&starting-point-node-id=241%3A6357).
- [Google setup/recovery guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=255-6835&starting-point-node-id=255%3A6835).
- [Pause/offline/removal guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=270-6806&starting-point-node-id=270%3A6806).

The existing page, product frames, flow IDs and three prior guides are preserved.
Six new named sections on the free canvas group the same nine context states by
window/theme; no page-sized enclosing frame was introduced. The guide has 18
isolated starts plus three links to the original guides.

| Window/theme | Section | Today start | Settings overview |
| --- | --- | --- | --- |
| 640×800 Light | 288:7328 | 288:7329 | 288:7494 |
| 800×900 Light | 290:7012 | 290:7013 | 290:7178 |
| 1440×900 Light | 290:7748 | 290:7749 | 290:7914 |
| 640×800 Dark | 290:8484 | 290:8485 | 290:8650 |
| 800×900 Dark | 290:9220 | 290:9221 | 290:9386 |
| 1440×900 Dark | 290:9956 | 290:9957 | 290:10122 |

Each lane contains Today with paused Read, overview, expanded Google, expanded
bCourses with long course names, paused Track, Google scope, paused/offline,
bCourses removal preview and local-removal result. Exact frame/dialog/source IDs,
size/mode, original source references, component specimens and all created IDs are
in [inventory.json](../../design/settings-connections/contexts/inventory.json).
The existing [node ledger](../../design/figma-node-ledger.json) adds only the
`settingsConnectionContexts20261104` record.

## Layout and reusable assets

- Retain the compact 60px navigation with Settings available from work and Track.
  The Settings content owns vertical scrolling below it. At 640px, long management
  content extends below the viewport; its actions remain reachable by scrolling.
- The wide Settings reference centers an 848px content container including 24px
  side padding. Its 800px inner column is a proposed reference measurement derived
  from the primary split layout, not a newly confirmed production breakpoint.
  The compact 640/800 references retain 24px padding.
- Dialog references use the existing 540px shell. Reading content and action
  footer are separate; the composed layout can constrain the body to vertical
  scrolling if needed. The reviewed consent content fits these three heights.
  No large-text/200% browser-zoom behavior is certified by that construction.
- Use vertical auto-layout and growing text. The long-course fixture is 198px high
  at 640px and 180px at the other two widths. Do not store those sample heights as
  fixed production constraints. Never clip a course/task title to preserve a card.
- Reuse Provider panel `218:5724`, Settings icon `218:5743`, Button set `3:241`,
  Input set `3:280`, Task row set `3:341`, existing streak and Track assets.
  Provider text properties are `Provider#218:0`, `Status#218:1`, `Summary#218:2`,
  `Evidence#218:3` and `Details#218:7`; disclosure is `Expanded#218:6`.
  Button text is `Label#3:54`; Input text is `Label#3:78` / `Value#3:79`.
- Control specimens reuse Primary Focus `3:204`, Disabled `3:207`, Loading
  `3:210` and Input Error `3:274` in both themes. Their appearance is reviewed;
  runtime tab order, focus trapping, Escape, error announcements and disabled
  semantics require the application checks.
- Reuse semantic color collection `VariableCollectionId:2:8` with Light `2:1`
  and Dark `2:2`, dimensions `VariableCollectionId:2:9`, and existing text styles.
  Tokens `VariableID:2:32–42` cover background/surface/text/muted/border/accent/
  onAccent/soft/error/errorBg/focus. Spacing 8/12/16/24 and radius 12 remain bound.
  [Existing foundations](../../BEARPLANS_UX_HANDOFF.md#components-and-foundations)
  define the complete mapping. Inter remains the existing Figma fallback; these
  examples do not change the app’s system-font direction or confirm that default.

## Interactions and simulation boundaries

The context lanes wire Settings, provider disclosure, explicit Google-scope review,
Plan/Track, Back to work, Keep token and a synthetic removal result. Six isolated
TEXT_CONTENT variables hold token-status samples; six nonvisual STRING variables
hold the originating Today/Track view. Opening Settings from Track records Track;
closing or Back to work returns there. From Today, it restores the same Today frame.
Each guide entry resets only its own lane. No existing task/session/history/reward,
calendar-choice, credential or provider state is written by a new lane control.

Token removal in these lanes transitions directly to a fixed receipt; the original
C05 guide retains the pending/failure/unknown variants. The same synthetic task
Read, 18:00 remaining, 12 minutes confirmed and Paused state appear across work and
Track. This is representative navigation, not evidence of a persisted session ID,
real countdown control or restored application scroll offsets. Task completion,
Start, other timer controls, courses, assignment review, Google continuation and
one-shot actions inside the new layout lanes remain visual references. Their
original flow guides expose the bounded setup/recovery simulations. The guide
states these limits before entry.

Implementation must preserve real Plan/day/project/task/scroll/focus context and
active session identity/control, rather than persisting prototype frame IDs.
Return to the initiating view; use the existing overlay behavior as source evidence
when reconciling the actual UI. Navigation must never finish or replace a session,
change completion, award time or rewrite closed history.

## Product and engineering contract

[SPEC](SPEC.md) remains authoritative; the context samples add no provider scope.

- bCourses is read-only/manual. Checking a token is separate from saving/access
  evidence. Assignments become local tasks only on Add; source deadline changes
  need review. Removal is local, keeps work/cache/courses and does not revoke at
  bCourses. Google can still export previously added tasks.
- Google has three linked functions: selected-calendar reads, timed-plan writes
  to the BearPlans-created calendar, and all-project/task/subtask Google Tasks
  sync. Calendar selection limits reads only. Personal calendars/lists/tasks are
  not write targets. Explain the whole scope before consent or explicit sync.
- Pause survives restart and Sync once keeps automatic work paused (confirmed
  intent). All-trigger gating, in-flight acknowledgement and current-record
  reconciliation on Resume remain the proposed detailed contract in SPEC.
  Resume acknowledgement never implies a successful sync.
- Access/setup, automatic policy, operation/error and last complete success remain
  separate. Keep prior cache/time on failure; disclose partial remote writes.
  Missing responses require unknown-result recovery. Local sign-out is separate
  from Google-confirmed revocation; removing a client file may partly succeed.
- Credential setup remains write-only/private, with no values in normal Settings,
  API responses, logs or evidence. Reconcile the current data-folder secret layout,
  callback invalidation, account boundary and concurrent uncommitted backend work.
- **Existing source gap:** `GoogleSync.while_idle` runs its action even after a
  lock timeout. Later APP-C02/C04 must establish a real barrier for Pause,
  Disconnect and adoption. Mounted/direct-reader automatic calls also need Pause
  gating. A Figma acknowledgement does not fix either gap. Reuse current backend
  capabilities rather than implementing the historical baseline again.

Use the [build skill](../../.agents/skills/bearplans-connections-build/SKILL.md) and
[APP-C sequence](EXECUTION_PLAN.md#4-application-sequence-app-c01app-c09) only within
a separately authorized application slice. Start by reconciling the current tree,
existing tests and account work; preserve the unrelated uncommitted changes.
The bCourses dedicated-review placement and earlier breakpoint/measurement/font/
cross-month defaults remain distinct from confirmed choices in PROGRESS/SPEC.

## Verification boundary

[Detailed review](../../../docs/reviews/2026-11-04-settings-context-handoff.md)
records the exact commands, user prompts/reports, repairs and remaining follow-ups.
Thirty native-size PNGs cover four Settings states at every width/theme plus the
guide and selected session/removal contexts; 54 window frames were structurally
checked. All 4,106 new nodes reconcile against the ledger. The pure installed-action
checker passes 165 cases. Fresh fingerprints match all 145 prior C05 reaction
sources. These checks do not execute Figma presentation or a local app.

The user reported compact scrolling/cancel/session return, Dark readability and
bounded provider recovery/scope examples clear. Codex was the sole Figma writer
and technical reviewer; there was no second technical agent audit. Reports were
not timed or directly observed, and actual user window/zoom/input method was not
reported. Arbitrary resizing/text reflow, full responsive setup matrices, browser
keyboard/focus, assistive technology, 200% zoom, real provider access/restart and
hardware/core-trial acceptance remain separate checks. This handoff does not
advance those gates or authorize the next build.
