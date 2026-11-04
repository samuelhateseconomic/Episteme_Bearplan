# BearPlans UX Refresh — Figma Design and Handoff Plan

Prepared November 1, 2026 from the user's design-discovery decisions.

This is the canonical design brief and stable ticket definition. It was first
saved as documentation only. On November 1 the user authorized “build the prototype
first,” reprioritizing a connected review draft before the original checkpoints.
This authorizes Figma design, not application implementation. See
[shared progress](../docs/PROGRESS.md) for actual ticket status and the next action.
Read [shared agent guidance](../AGENTS.md) before using this plan.

The [UX repair plan](BEARPLANS_UX_REPAIR_PLAN.md) defines the small corrective
tickets following the 77/100 review, without replacing UX-01–36. It incorporates
the latest confirmed End Week/carryover and Stats Missed decisions. Planning
delivery does not begin those repairs; execution status stays in shared progress.

## 1. Outcome and working boundaries

Create an editable Figma component system, screen set and connected prototype for
refreshing the existing local BearPlans app. Finish with a handoff explaining
intended behavior, component structure, responsive layouts and future engineering
requirements. Application implementation will have its own later plan.

This roadmap covers design, documentation, agent guidance and a reusable design
skill. It does not include app code, APIs, migrations, data changes, a native
wrapper, persistent chat history, assistant write tools or integration implementation.
The November 3 Settings/Connections design extension in section 6 covers the
requested connection UX only; the original prototype does not include it. Do not
replace or modify the separate core-trial candidate through this work.

Track every ticket in one shared register in `docs/PROGRESS.md`, keeping one
delivery ticket active at a time. Most tickets should fit a focused 30–120-minute
session; these are sizing targets, not delivery promises. If a ticket proves
larger, split it into numbered subtickets before continuing. Reviewers may inspect
requirements and evidence within the active ticket; keep Figma editing serialized.

### Confirmed user decisions

| Area | Agreed direction |
| --- | --- |
| Product | Refresh the existing local app. |
| Primary layout | Split-screen first, with a wider laptop layout. |
| Navigation | Compact top bar: Plan, Track, Stats, Assistant. |
| Opening view | Plan opens to Today; Week is alongside it. |
| Today | Today's planned tasks, plus a collapsed Earlier unfinished section. |
| Task presentation | Compact title, smaller project/parent context, completion control and Start leading to Track. |
| Task entry | One Save for task details and its optional planned date. |
| Project controls | Rename below Projects; compact Add project immediately below it. |
| Completed work | Separate Active and Done; Done groups by planned year/month/week, not completion date. |
| Completed rows | Compact gray, struck-through title with an enabled checked checkbox; unchecking restores the normal task row. |
| Subtasks | Completed children remain accessible but compact beneath an unfinished parent. |
| Dragging | Both ordering within a day and moving between days. |
| Rewards | Streak prominent; forest and coins opened on demand. |
| Track and Stats | Short explanations, clear actions and secondary detail revealed when needed. |
| Assistant | Claude-inspired organization; the read-only layout sample preserves the app's separate current M5 capabilities. |
| End Week / carryover | Closure preview, then carryover choices open with eligible leaves checked for the same weekday next week as their last source date; Review and Apply remain explicit. |
| Stats Missed | “Missed: N” overall/per closed week; “Missed: N×” per task, based on unfinished planned leaves at closure. |
| Guidance | Update root AGENTS.md and create a repository-local reusable SKILL.md. |
| Scope | Figma design and handoff only; implementation planned separately. |

The user enters tasks through project management with a due date, time allocation
and day assignment; chooses work from the daily schedule; plans at week end; and
reviews Wednesday or Thursday. These habits inform the design, not automatic
scheduling or closure rules.

### Proposed defaults and preserved behavior

The following design contract makes the draft executable. Its visual measurements,
cross-month filing and Earlier unfinished selection details are proposed defaults,
not additional confirmed user requirements. Review concrete frames before
propagating rejected defaults. Existing domain rules remain authoritative unless
the user explicitly changes them. Accepted new behaviors must be labeled as
future capabilities until separately implemented and verified.

## 2. Design contract

### Layout and visual foundations

- Use **800 × 900** as the primary split-screen reference, **640 × 800** for
  compact-window verification, and **1440 × 900** for the wide layout. These are
  design reference sizes, not claims about the MacBook's display.
- Below 1280 px, project management opens in a drawer and Week uses a seven-day
  selector with one selected day's task list. At 1280 px and above, show project
  management beside the work area and provide the seven-column weekly board.
- Retain warm neutral surfaces and a forest-green accent. Use lighter borders,
  fewer nested boxes and clear primary/secondary actions.
- Preserve light and dark support. Establish light first, then verify the same
  components in dark mode.
- Preserve the system-font direction: SF Pro in Figma when available, otherwise
  Helvetica Neue; record the substitution. Verify actual available family/styles.
- Begin with 15 px task titles, 13 px context text and a 64 px active-task row minimum.
  Allow long names to expand without clipping controls.
- Use shared semantic color, typography, spacing and radius tokens. Start with
  spacing values of 4, 8, 12, 16, 24 and 32 px.
- Use restrained motion, with an equivalent reduced-motion specification.

### Today, Projects and Done

- Today's main list contains current tasks explicitly planned for the service's
  Today date. The browser does not independently choose Today.
- Earlier unfinished is collapsed initially. Proposed selection: current
  incomplete leaf work with a past saved planned date and no active placement for
  today or a future day. Include relevant archived membership without changing
  closed history. Deduplicate each task; opening the section never reschedules it.
- Clicking a task opens details. Start opens Track with that task selected; it
  does not immediately start a countdown.
- Use one task editor for title, due date, allocation and optional planned date.
  Existing field validation remains applicable. A failed Save retains input; the
  future implementation must save task and plan atomically when both are supplied.
- Project management has Active and Done views scoped to the selected project.
  Keep unscheduled work accessible.
- Done uses saved planned-week membership, including membership retained after
  End Week. Show a task once within each week, even if it has several planned days.
  A task associated with several weeks may appear in those weeks; overall totals
  count each current completed leaf work item once.
- Proposed filing: a week belongs to its Monday's year/month, with the full range
  visible, e.g. **October → Oct 26–Nov 1**. Show only nonempty groups, newest first.
- Completed tasks without saved week membership appear under **No planned week**.
- Active parents show progress and unfinished children, with completed children
  behind a disclosure such as **Completed · 2**. Parents have no direct completion
  action or Start control. All completion counts exclude parent containers.
- Completed current-work leaf rows, including open weekly cards, compact to a
  readable gray, struck-through task title and an enabled checked checkbox.
  Hide per-row project/parent metadata, due/estimate text, Start and other action
  buttons in this compact state; grouping context remains available outside the
  row and in its accessible name. Use less vertical padding without shrinking the
  checkbox target or making the row appear disabled.
- Unchecking explicitly reopens the same task. After a confirmed save, restore its
  normal appearance, applicable metadata/actions and unfinished-list position.
  Preserve keyboard focus through this transition. While saving or on failure,
  retain useful pending/error feedback and a recovery path; do not claim success
  or lose the checkbox. Shared placements, parent progress and totals refresh;
  any existing timer and frozen closed-week records remain unchanged.
- Done is a live view of current completion and task labels. Reopening removes a
  task from Done. Closed-week history remains separate and frozen, including its
  original completion, context and saved placements.

### Weekly interactions

- Keep unfinished work first and completed work in a collapsed section per day.
  Put completion count/progress near the week heading and End Week in the
  bottom-right footer, retaining the required preview.
- Incomplete weekly cards retain their due date. Completed current-work cards
  use the compact checkbox/title variant above. Historical cards keep their
  frozen details and read-only controls; do not treat them as live reopenable rows.
  The day identifies the planned date; omit redundant Planned metadata.
- Keep the grip to the left of the project/parent context above the leaf title,
  with an accessible name and no visible Drag text. Do not restore Add-another-day
  or modifier Add behavior.
- Dragging starts from the grip. Within-day drops change priority order;
  between-day drops move the existing placement into the indicated position.
  The accepted design extends current behavior; persisted ordering does not yet
  exist. Current same-day drops remain no-ops until a separate implementation.
- Show a lifted preview, insertion marker, destination highlight and restrained
  movement. Keep scrolling controlled; do not automatically change weeks.
- Same-position drops, Escape/cancellation and outside drops change nothing.
  Reject duplicate task/date destinations and changes involving archived IDs or
  closed weeks. Preserve other placements and shared completion.
- Retain keyboard/date Move and remove-date controls; specify keyboard ordering
  alongside the accepted within-day ordering behavior.
- Show pending, saved, failed and unconfirmed-response states. Do not represent an
  uncertain save as a confirmed rollback; provide a useful refresh/retry path.
- Latest confirmed carryover direction: after reviewed closure, open choices with
  all eligible leaves checked. Default to the last planned source date plus seven
  calendar days, with one candidate per task. Users may uncheck/redate, Review and
  Apply. Preselection creates no placements; Cancel leaves the week closed and
  saves no carryover. Deadlines and frozen history stay unchanged.
- Figma demonstrates representative drag sequences. Specify hit areas, scrolling,
  persistence and failure behavior for engineering; simulation is not evidence of
  production drag performance or data durability.

### Focus, rewards, statistics and Assistant

- Track prioritizes task, countdown, session state and controls. General
  explanations become disclosures; recovery choices, save errors and uncertain
  time remain visible when relevant.
- Keep task completion separate from finishing a session. Completing a task during
  a session must not remove that session or its controls.
- Measured sleep stays paused after wake. Needs review requires an explicit
  decision; uncertain time never becomes focus, reward or streak credit.
- Streak describes saved focus progress. Forest and shop open on demand within
  Track. Retain existing confirmed-time, species, purchase and retry semantics.
- Stats leads with Focus time, Tasks completed and Sessions, with time scope
  labeled. Daily/project/estimate detail opens when needed. Retain stale-report
  labels and useful read failures.
- Stats includes “Missed: N” overall/per closed week and “Missed: N×” per task.
  Count planned leaves unfinished at closure once per closed week; open weeks
  excluded. Later completion/carryover never erases a historical miss. Keep this
  distinct from Done's unique-current-leaf total and all-time saved session time.
- Corrections retain reason, reviewed time/streak/tree/wallet effects, apply,
  retry, audit history and reviewed reversal. Never imply adding unknown time.
- Assistant uses a central answer area, bottom composer, compact local-model
  selection, visible project/day/week context and collapsed Sources used.
- Preserve independent-question/read-only behavior and input on error/cancel.
  Do not imply persistent conversation history, write tools or model-dependent
  manual controls. Today context must not silently use a selected week's Monday.

## 3. Small, trackable delivery tickets

Execute in the order below; a ticket depends on acceptance of the preceding
ticket. Review checkpoints are built into the sequence. All status changes belong
in the shared progress record, not this stable definition table. A specification
being written does not complete any ticket requiring Figma or visual evidence.

### Phase A — Brief, tracking and agent workflow

| ID | Ticket and subtasks | Completion evidence |
| --- | --- | --- |
| UX-01 | Persist the brief and ticket register: decisions, defaults, scope, screen inventory, dependencies and acceptance. | Every requirement maps to a ticket; the shared register has explicit statuses and a next action. |
| UX-02 | Update AGENTS.md: design guidance, brief/skill links, tracking/review rules and current-versus-future drag behavior. | No conflicting drag instructions; existing data, timer, reward and history protections remain. |
| UX-03 | Create the reusable skill: routing, concise workflow, UI metadata and review/handoff reference. | Supports BearPlans design without absorbing ordinary implementation or debugging. |
| UX-04 | Validate skill/guidance: bundled validator, links and independent design/resumption scenarios. | Valid metadata and useful scenario behavior; distinguish document-only checks from unperformed Figma validation. |
| UX-05 | Establish Figma file and asset inventory: file/pages, available libraries/fonts, reusable assets and exact IDs. | File, pages, discovery decisions, font choice and ledger exist without duplicate assets. |

### Phase B — Reusable visual foundation

| ID | Ticket and subtasks | Completion evidence |
| --- | --- | --- |
| UX-06 | Foundations: semantic colors in both modes, type, spacing, radii, borders and motion specification. | Named variables/styles and initial contrast review. |
| UX-07 | Controls: buttons, icon buttons, inputs, date/allocation fields, checkboxes, segmented selector and menus. | Required default, hover, focus, disabled, loading and error states. |
| UX-08 | Task rows: standalone, subtask, compact gray/struck-through completed, parent, selected and long-title variants. | Correct leaf/parent controls; enabled completed checkbox, readable gray title and restoration after confirmed reopen. |
| UX-09 | Supporting patterns: disclosures, streak/progress, empty states, save/error/retry feedback and drag cues. | Reusable components cover agreed screens without unrelated library expansion. |
| UX-10 | Responsive shell: compact top navigation, Today/Week switch, project pane/drawer, details and compact timer. | Navigation and work area function at all reference widths. |
| UX-11 | Foundation review: compose Today with eight realistic tasks, long names, subtask context and streak. | User reviews actual density and direction before propagation. |

### Phase C — Tasks and Today

| ID | Ticket and subtasks | Completion evidence |
| --- | --- | --- |
| UX-12 | Project management: selection, requested Rename placement, collapsed Add project, empty and failed-save states. | No large permanent creation form; actions remain discoverable. |
| UX-13 | Task editor: details and planned date, optional fields, validation, saving, cancellation and input retention. | One Save has a clear outcome; handoff names atomic-save requirement. |
| UX-14 | Active hierarchy: parent progress, unfinished children, completed disclosure, add subtask and removal confirmation. | Partial completion is compact; scheduled-task restrictions have useful messages. |
| UX-15 | Done: year/month/planned-week groups, expansion, multi-date deduplication, multi-week membership and No planned week. | Planned-week grouping, parent context and unique overall totals are correct. |
| UX-16 | Today states: Earlier unfinished, completed section, no work, crowded list, loading, failed reads and compact timer. | Earlier work is accessible without implying rescheduling. |
| UX-17 | Capture-to-focus review: create, inspect, find in Today and open Track; inspect Done and partial parents. | Core information is found without unnecessary forms; component fixes propagate. |

### Phase D — Weekly planning and movement

| ID | Ticket and subtasks | Completion evidence |
| --- | --- | --- |
| UX-18 | Weekly board: navigation, progress, wide columns, compact selector, gray title-only completed rows and footer. | Both layouts retain readable unfinished metadata and compact completed rows; unchecking restores the normal row without changing history. |
| UX-19 | Within-day ordering: grip, lift, insertion, result, keyboard alternative, cancellation and same-position drop. | Intended order is obvious before/after the simulated drop. |
| UX-20 | Between-day moves: target position, ordering, conflicts, pending/unconfirmed save and date alternatives. | Identity/other placements survive; invalid destinations are actionable. |
| UX-21 | End Week: footer entry, preview, cancel/confirm, loading, stale preview and failure. | Consequences are clear before confirmation; failed closure is recoverable. |
| UX-22 | History: frozen cards, At closure status, distinct current status, navigation and empty history. | Historical and current information are unmistakable. |
| UX-23 | Carryover and planner review: immediate post-close choices, eligible same-weekday defaults, selection/exclusions, next-week dates, preview/apply, retry and conflicts. | Closing alone transfers nothing; reviewed Apply preserves task identity, deadlines and frozen history. |

### Phase E — Track, rewards, Stats and Assistant

| ID | Ticket and subtasks | Completion evidence |
| --- | --- | --- |
| UX-24 | Track setup: task/duration/species selection and unavailable/invalid task states. | Today entry selects the right task; setup stays concise. |
| UX-25 | Running/paused: countdown hierarchy, controls, navigation away and compact timer. | Controls dominate; task and session completion remain separate. |
| UX-26 | Recovery: measured-sleep pause, Needs review, confirmed time, continue/finish and failed-save state. | No implied automatic resume or uncertain-time credit. |
| UX-27 | Outcomes and Forest: completed/early finishes, unfinished/mature trees, collection and session details. | Saved work is clear; Forest opens on demand inside Track. |
| UX-28 | Shop: balance, ownership, selection, purchase, insufficient/negative funds and lost-response retry. | Consequences/recovery are visible without crowding focus controls. |
| UX-29 | Stats: summary scopes, Missed overall/week/task, recent daily chart, project/estimate detail and stale/error states. | Figures are concise; frozen misses, current completion and saved time remain distinct. |
| UX-30 | Corrections: edit/reason, effects preview, apply/retry, audit and reviewed reversal. | Time, streak, tree and wallet effects remain explicit. |
| UX-31 | Assistant and secondary-screen review: composer, answer/sources, context/model, cancel, unavailable model and errors. | Restrained layout truthfully represents local read-only independent questions. |

### Phase F — Prototype, verification and handoff

| ID | Ticket and subtasks | Completion evidence |
| --- | --- | --- |
| UX-32 | Connected prototype: named starts, primary journeys, alternate/error routes and reset paths. | Every agreed journey works without dead ends or misleading controls. |
| UX-33 | Responsive/theme coverage: all primary screens at three widths, shared components in both modes, dark error/recovery examples. | No clipped actions, unreadable labels or squeezed columns. |
| UX-34 | Independent QA: requirements, behavior, contrast, focus annotations, content, reuse and links. | Findings have evidence and an honest review decision. |
| UX-35 | User walkthrough and corrections: representative work using synthetic content, then reviewed fixes. | Required journeys accepted; remaining cosmetic follow-ups explicit. |
| UX-36 | Handoff: screen/node index, component/token map, interactions, engineering implications, evidence and boundaries. | Another agent can plan implementation without guessing agreed behavior. |

## 4. Guidance, tracking and Figma execution

### Document responsibilities

- [Root AGENTS.md](../AGENTS.md): concise durable shared guidance and domain rules.
- [Shared progress](../docs/PROGRESS.md): the only mutable ticket/handoff register.
- This frontend document: canonical design decisions, defaults, stable ticket
  definitions and acceptance, with no competing current-status table.
- [BearPlans design skill](../.agents/skills/bearplans-design/SKILL.md): reusable
  design workflow, not a duplicate product-rule manual.
- Dated reviews under `docs/reviews/`: exact checks, reviewed frames, results and
  evidence. A machine-readable node ledger is an artifact index, not task status.

Paths are repository-relative so the plan survives checkout relocation. Do not
restore the former nested repository or hardcode the developer's Mac path.

### Agent guidance and skill package

AGENTS.md should link this brief and skill, preserve confirmed decisions, keep one
active ticket and one Figma writer, require actual completion evidence, distinguish
prototype from implemented capability and retain existing preservation/commit rules.
Reconcile accepted future ordering with current same-day no-op behavior explicitly.

The repository-local skill is named `bearplans-design` and lives in
`.agents/skills/bearplans-design/`. It contains:

- `SKILL.md`: discovery, scope selection, installed Figma-skill routing, editable
  construction, verification and handoff.
- `agents/openai.yaml`: minimal display name, description and invocation example;
  normal automatic discovery remains enabled.
- `references/review-and-handoff.md`: reusable review and handoff checks.

Do not add scripts, assets, copied plugin manuals or duplicate product rules
without a demonstrated need. Validate metadata with the bundled skill validator
and independently examine Today creation, incomplete-ledger resumption,
timer-recovery review, planned-week Done and unrelated debugging requests. Such
dry runs must not mutate Figma or start a design ticket without authorization.

Repository-local skills are supported by the
[official skill documentation](https://learn.chatgpt.com/docs/build-skills);
[AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
explains repository instruction discovery.

### Tracking fields and execution rules

Each active ticket records ID/title, status, dependency, owner/reviewer,
acceptance criteria (or canonical ticket link), evidence and next action. Statuses:
**Not started → Ready → Active → In review → Done**, with **Blocked** only for an
actual dependency. A review can be Pass, Pass with follow-ups or Fail.

Update progress after each ticket. Done requires its acceptance and relevant
review; written specifications or successful tool calls do not certify rendered
frames. Preserve earlier evidence rather than rewriting historical reviews.

Independent agents may inspect sources, requirements and screenshots within the
active ticket. They must not concurrently modify Figma. Continue routine work
within an authorized, accepted direction without repeatedly reopening settled
choices. Scope or material design decisions require concrete review.

### Figma organization and recovery

For further Figma work, resume the existing editable **BearPlans — Local UX
Refresh** file indexed in [FIGMA_PROTOTYPE.md](FIGMA_PROTOTYPE.md). Current pages
are **Canvas · Flows**, **Brief**, **Foundations**, **Components**, **Screens** and
**Review and Handoff**. Canvas · Flows replaces the former Prototype page name,
opens first and preserves the user's free two-dimensional editing workspace.
Reuse its native sections and exact ledger IDs instead of creating another file.

Load the installed Figma creation, library/component, screen-generation and
`figma-use` skills for their respective operations. Discover file libraries before
searching assets; inspect compatible existing components, fonts and variables
before creating replacements. Build only the inventory this plan requires.

Use editable text/vector layers, auto-layout, component instances and named token
bindings. Do not substitute flattened screen captures for the deliverable. No
published full library, Code Connect source generation or application changes are
required in this phase.

Keep exact returned file/node/component/variable IDs in an execution ledger and
checkpoint a content-safe durable copy with review evidence. Record its location
in progress. Inspect the canvas before retrying uncertain writes; never blindly
recreate nodes or delete user-owned content. Use deterministic names for discovery.

Inspect rendered output after each coherent composition and after targeted fixes.
Use synthetic tasks, sessions and reward examples, not private planner records.

## 5. Acceptance, review checkpoints and final handoff

### Review checkpoints

- **UX-11:** actual task density, split-screen shell and visual direction.
- **UX-17:** Today, projects, capture and Done.
- **UX-23:** weekly organization, dragging, closure, history and carryover.
- **UX-31:** focus, recovery, rewards, Stats and Assistant.
- **UX-35:** connected prototype and final corrections.

Review actual frames. Continue routine work within accepted directions; do not
turn each minor edit into a separate permission request.

### Required walkthrough scenarios

1. Find and start one task from a list of eight.
2. Create a task with details and planned day through one Save.
3. Expand a parent containing unfinished and completed children.
4. Browse Done by planned week, including cross-month and multi-week membership.
5. Find earlier unfinished work without silently rescheduling it.
6. Reorder within a day and move to another day.
7. Cancel a drag and encounter an occupied-date conflict.
   Complete a live weekly task to see its gray, struck-through title-only row;
   uncheck to reopen and restore metadata/actions. Exercise keyboard focus and
   failed-save recovery, including a task with another placement or active timer.
8. Preview/cancel End Week, then close and revisit frozen history.
9. Carry selected unfinished work into the following week.
10. Pause, navigate away and resolve an interruption.
11. Finish a session without automatically completing its task.
12. Open Forest/shop on demand and inspect a failed purchase.
13. Review a time correction and its material consequences.
14. Ask Assistant, inspect sources, cancel generation and recover from a missing model.
15. Inspect keyboard/focus annotations and loading, disabled, error, empty,
    long-title and crowded states.

Figma can demonstrate representative sequences and document keyboard behavior.
Actual browser accessibility, persistence, drag performance and timer correctness
require verification during later implementation. Do not count prototype review
as new Mac sleep evidence, core-trial completion or application release approval.

### Engineering implications for handoff

No application API or schema change is performed here. Document these future needs:

- Persisted placement ordering, including destination position for date moves,
  keyboard ordering, replay/stale-write protection and old-history compatibility.
- Done membership across active and archived planned weeks, with unique overall
  current-leaf totals and unchanged frozen snapshots.
- Atomic task-details/planned-date saving, with no partial create or duplicate
  task after a failed/lost response; input must remain recoverable.
- A consistent Earlier unfinished projection using current work and saved plans.
- Correct Assistant context for Today versus selected Week.

Specify observable behavior and transaction expectations. Do not invent endpoint
names, migrations or a complete engineering architecture during the design phase.

### Final deliverables

- Editable Figma file and named prototype starting points.
- Reusable components, variables, styles and light/dark treatment.
- Responsive screen/state inventory with exact node links.
- Interaction, keyboard, focus and accessibility annotations.
- Updated AGENTS.md and validated repository-local skill.
- Shared progress register and evidence-backed review records.
- Future engineering requirements and explicit remaining follow-ups.

The first connected Figma draft is indexed in [FIGMA_PROTOTYPE.md](FIGMA_PROTOTYPE.md).
It uses synthetic, representative interactions and includes static responsive/theme
references. The current M5 app has action/Apply/Undo capability; this prototype keeps
the selected read-only Assistant layout as a deliberate subset. Actual presentation
execution, full ticket acceptance and the user walkthrough remain open. See shared
progress for evidence/status; application implementation remains separately scoped.

## 6. Local Settings and Connections extension

The connection plans are organized in the frontend
[Settings/Connections package](plans/settings-connections/README.md).
Read its [canonical specification](plans/settings-connections/SPEC.md),
[detailed design/application steps](plans/settings-connections/EXECUTION_PLAN.md)
and [verification plan](plans/settings-connections/TEST_PLAN.md).
UX-C01–C06 definitions now live there; the original UX-01–36 and repair IDs remain
unchanged. This anchor is preserved for existing links without keeping a second
copy of connection requirements. Actual status remains in
[PROGRESS](../docs/PROGRESS.md).

Use [frontend AGENTS.md](AGENTS.md) and the applicable frontend-local design/build
skill linked from the package. Documentation creation does not start Figma work,
application implementation or provider requests.
