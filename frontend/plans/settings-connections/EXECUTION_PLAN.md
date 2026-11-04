# Settings and Connections — detailed execution plan

Read [the entrypoint](README.md), [SPEC](SPEC.md) and [TEST_PLAN](TEST_PLAN.md).
This file defines steps and completion conditions; it is not a task tracker.
One small unit is active in [PROGRESS](../../../docs/PROGRESS.md). Mark later
units not started until their implementation actually begins.

## 1. Choose the authorized phase

- Documentation request: organize/specify/review these files and agent skills only.
- Design request: execute the eligible UX-C unit; no app/API/database/provider work.
- Application request: execute the separately scoped APP-C unit and its affected
  tests. A Figma acceptance or saved plan alone does not authorize this phase.
- Live provider mutation: establish the exact user-authorized account/resource/
  operation first. Prefer fake providers and disposable records for normal checks.

Use the latest explicit session authorization rather than asking permission again
for equivalent already-authorized work. If a missing choice affects behavior,
ask concisely while continuing independent work. Keep proposed defaults labelled
until resolved; do not expand scope to solve unrelated product ideas.

## 2. Common start and finish for every unit

1. Resolve checkout root with Git; the old nested project folder is stale. Read
   root/frontend AGENTS, PROGRESS, this unit's requirements and linked evidence.
2. Inspect status, recent commits, full relevant diff and untracked source. Reconcile
   concurrent work and exact current capabilities before changing anything.
3. Name the user-visible scenario, affected records/resources, intended rule/default
   change and cancellation/recovery behavior. Select the relevant test cases.
4. Set only this small unit Active in PROGRESS with owner, reviewer, inputs, evidence
   path and next action. Plan-only preparation does not activate a visual/build unit.
5. Work within that unit. Parallel readers can review; one agent writes Figma. Avoid
   concurrent writers to the same code/docs. Preserve unrelated changes.
6. Verify the resulting diff/artifact and meaningful behavior for the phase. Inspect
   rendered design/UI as applicable; successful writes are not completion evidence.
7. Record exact results, failures/skips, OS, source boundary, screens/IDs and limits
   in a dated `docs/reviews/` record. Use Pass / Pass with follow-ups / Fail honestly.
8. Update PROGRESS, append the finished item at the top of COMPLETED, and identify
   the next eligible unit. Commit only with explicit authorization; never auto-push.

## 3. Design sequence: UX-C01–UX-C06

### UX-C01 — Source/coherence review and executable contract

Inputs: root build/review plans, current providers/routes/UI, current handoff.

1. Map actual provider functions, credential locations, scheduler and source status.
2. Separate already implemented, in-progress/unverified and proposed capabilities.
3. Record confirmed Settings/Pause choices versus proposed layout/Pause details.
4. Check local setup, browser authorization, offline behavior and data consequences.
5. Map requirements CON-01–CON-12 to this sequence and the test plan.
6. Resolve documentation contradictions without rewriting historical evidence.

Verify: documentation cases; independent source/flow review. Output: coherent SPEC,
known gaps and pending choices with source links. Exit: review limits stated; no
runtime/Figma success implied. Existing C01 evidence remains in the shared record.

### UX-C02 — Compact Settings overview and navigation

Inputs: C01 contract, current ledger/inventory/components, CON-01/02/07/11.

1. Reconcile the target Figma file/page/current nodes through installed Figma skills.
2. Inspect compatible navigation, button, input, feedback, disclosure and typography
   components/tokens; load required fonts; keep original flow canvas/IDs intact.
3. Specify gear entry, Settings heading, Connections subsection and return route.
4. Build two compact provider panels: setup/auth indication, combined last-success,
   primary Connect/Manage, operation/paused/error presentation and recovery action.
5. Keep Google scope summary available before first consent. Do not invent email,
   per-function timestamps or capability toggles absent from the contract.
6. Add open/closed Manage variants and annotate preserved Plan/day/timer context.
7. Render primary 800×900 Light, repair layout, and record exact new/changed IDs.

Verify: Figma overview/state/navigation cases in TEST_PLAN; inspect hierarchy,
readability, action priority and no credential content. Output: editable overview
and return-state specification. Exit: render and source-contract review passed;
remaining responsive propagation belongs to C06, not a false all-width pass.

### UX-C03 — bCourses setup, replacement and work entry

Inputs: C02, CON-03/04/09/11/12, current bCourses/credential routes and tests.

1. Define Connect and Replace dialog entry/return, field labels, short instructions,
   optional provider help, Check and save, Cancel and busy semantics.
2. Build empty, masked input, validating, accepted, rejected, offline-check and
   save-failure states; distinguish saved credential from confirmed latest access.
3. Define input retention on failed open form and clearing after success/dismissal;
   saved values are never revealed. Use clearly synthetic examples only.
4. Show followed-course picker with empty/loading/unavailable/long-name cases and
   Save/cancel behavior; deselection never implies imported-task deletion.
5. Link to the existing dedicated assignment-review work view as a proposal while
   its location remains unanswered. Preserve Add, due-date review and source links.
6. Annotate failed replacement, token removal and retained-task consequences.
7. Render dialog + error + selected-course flow and reconcile IDs/evidence.

Verify: bCourses Figma/field/privacy/return cases; confirm cancellation causes no
save and only Add creates a task. Output: complete bounded bCourses design journey.
Exit: all displayed actions have meaningful destinations or are clearly annotated
static references; no fake live token validation claimed.

### UX-C04 — Google setup and browser authorization

Inputs: C02, CON-02/05/06/07/10/12, current OAuth/setup source.

1. Build Choose sign-in file, wrong/malformed/oversized file, format-valid, same-client
   retained-sign-in and different-client sign-in-required examples. Distinguish setup from consent.
2. Place the three-function/data-sharing summary before Continue with Google;
   explicitly include all-task export and added bCourses tasks.
3. Design browser handoff, Waiting, Open sign-in fallback and return instructions.
4. Add denial, timeout, missing permissions, expired/revoked authorization and Retry.
5. Define dismissal versus explicit Cancel sign-in; annotate callback invalidation
   and current engineering limits. Do not embed a Google password/consent form.
6. Add selected-calendar picker and first-sync result; selection affects reads,
   while task export and BearPlans-calendar publishing retain their current scope.
7. Add same-account reconnect and a blocked/reviewed different-account state; do
   not offer seamless switching without identity safeguards.
8. Render key success/error/waiting states and reconcile their exact IDs.

Verify: Google authorization/state/scope Figma cases and data-flow review. Output:
complete finite Google setup journey with external-browser boundary. Exit: no
valid-file→Connected shortcut and no claim that popup dismissal cancels OAuth.

### UX-C05 — Pause, offline and connection recovery

Inputs: C03/C04, CON-01/02/08/09/10 and proposed Pause details.

1. List the selected Pause semantics in the ticket: automatic triggers covered,
   restart persistence, in-flight boundary, one-shot behavior and Resume strategy.
2. Build Enabled → Pausing → Paused → Resume results, retaining last-success time.
3. Show local edit/continued timer and stale-calendar context while paused/offline.
4. Define explicit one-time provider work while paused; it never enables automation.
5. Add active-sync failure/retry, showing that earlier provider writes may remain.
6. Build Disconnect/remove/replacement consequence and failure states; retain local
   tasks/history and show accurate local-only sign-out versus provider revocation.
7. Add late-callback and conflicting-action behavior annotations for engineering;
   protect newer attempts and prevent a false completed-disconnect state.
8. Render representative combinations (Paused + offline; signed-in + sync failure)
   instead of forcing every dimension into one status label.

Verify: Pause/offline/recovery Figma cases; independent state-transition review.
Output: intended control/status contract and explicit implementation gaps. Exit:
proposed choices remain identifiable, and no backend implementation is implied.

### UX-C06 — Prototype wiring, responsive review and handoff

Inputs: C02–C05, complete ledger and TEST_PLAN Figma/user scenarios.

1. Arrange new flow sections on the free canvas; reuse existing components/tokens.
2. Wire the representative Settings entry, bCourses and Google journeys, Cancel,
   return, error/Retry and Pause paths. Keep reset/session/task state coherent.
3. Use fixed synthetic values and visibly label simulated/static references. Never
   embed live authorization URLs, real credentials or private course/task content.
4. Propagate 640×800, 800×900, 1440×900 and Light/Dark; review long names, scrolling,
   button reachability, labels, disabled/loading/focus/error states and return routes.
5. Inspect actual rendered frames; test prototype links via supported preview. If
   only reaction metadata/model checks are available, record that limitation.
6. Run an independent design/contract review. Fix blockers and reinspect affected
   frames; reconcile installed IDs after an uncertain tool call before retrying.
7. Ask for a bounded user walkthrough covering setup, cancel/recovery, Pause, scope
   understanding and return to work; record the exact report and limits.
8. Update handoff/inventory/ledger with exact returned IDs, asset properties,
   dimensions/themes, finite simulations and engineering dependencies.

Verify: full Figma category and walkthrough cases; no application test required
for design-only changes. Output: reviewed editable prototype/handoff. Exit: separate
construction, interaction verification, user reports and runtime gates honestly.

## 4. Application sequence: APP-C01–APP-C09

This is an implementation plan for later scoped authorization. Reuse current
React/TypeScript, FastAPI/domain/storage and credential mechanisms. Backend work
can exist before a new prototype; do not discard or reimplement it because the
visual sequence is unfinished. Integrate the accepted design when authorized.
Do not invent endpoint/schema names in Figma or edit applied migrations.

### APP-C01 — Reconcile baseline, requirements and test fixtures

1. Establish current Git/diff, running-instance identity if relevant and applicable
   authorization. Do not start/stop a real service merely to inspect plans.
2. Read current setup/provider UI, API types/routes, sync/auth/domain/persistence and
   tests. Inventory supplied work versus missing requirements; adopt existing code.
3. Link each CON requirement and selected UX state to an application unit/test case.
4. Record resolved defaults and unresolved behavior, especially Pause semantics,
   bCourses work-view placement and same/different-account recovery.
5. Prepare fake providers/clocks and disposable data/secrets outside the checkout.
   Disable all real provider paths in fixtures; never load the owner's credentials.
6. State affected records: credential/status files, preference if added, auth attempt,
   sync mappings/cache, existing task/placement identity; preserve immutable history.

Verify: baseline/fixture/document cases. Output: current contract/test map and one
small next build. Exit: no credentials touched and existing work understood.

### APP-C02 — Credential/auth replacement, cancellation and account boundaries

1. Review existing `/api/connections` and Google auth behavior; extend rather than
   duplicating routes. Separate format acceptance, provider check and live consent.
2. Test failed/rejected/offline replacement with a previous valid configuration.
3. Implement the chosen atomic/preservation or explicit recovery contract across
   client-file/token/status changes, including a disk failure after any stage.
4. Coordinate explicit cancellation, Disconnect and replacement with pending OAuth
   and sync. Late callbacks/retries must not resurrect or overwrite a newer state.
5. Bind/validate provider identity for reconnect before reusing mappings; implement
   a safe blocked/recovery path for different accounts without silent deletion.
6. Preserve local work and remote resources on disconnect. Keep local sign-out copy
   truthful; provider revocation is separate work unless included in this scope.
7. Keep write-only credential responses, size/type/host validation, owner-only files,
   same-origin protection and no credential exposure through errors/logs/backups.

Verify: credential/auth/identity API and data-failure cases using injected faults
and delayed fake callbacks. Output: verified lifecycle boundary and safe errors.
Exit: preserved/recoverable old setup, no late reconnect, no foreign-account mapping
reuse, and source-backed UI promises. Do not certify these with happy-path tests.

### APP-C03 — State/API contract and frontend data access

1. Define minimal typed view data for setup/auth, automatic-sync preference,
   operation, last success and actionable error. Reuse existing route/status fields.
2. Add only missing shared service/domain/API behavior; keep validation/mutations
   in the existing architecture. Provider requests stay outside write transactions.
3. Resolve status precedence/combinations (paused + stale; saved token + rejected
   access; valid client + unsigned-in) without claiming unverified readiness.
4. Add frontend API helpers/types and cancellation/stale-response protection where
   needed; retain existing error structure and inputs for recovery.
5. Verify no secret value, suffix, client contents or account invention appears in
   serialized response, frontend state persistence or source evidence.

Verify: API/status mapping and frontend error/readback cases. Output: stable
minimal data contract; no speculative per-function switches/status endpoints.
Exit: every shown state is backed by reliable data or clearly identified evidence.

### APP-C04 — Durable global automatic Pause / Resume

1. Confirm/scopingly adopt proposed semantics before coding persistence. Inspect
   storage conventions; add a new migration only if the chosen design needs one.
2. Apply preference to periodic, post-edit and all other automatic triggers across
   Tasks, BearPlans calendar and selected-calendar reading.
3. Serialize preference acknowledgement with sync start/in-flight operations. Show
   Pausing while applicable; no new automatic operation after acknowledged Paused.
4. Preserve preference through restart and service recovery, credentials/cache and
   local task/timer operation. No automatic Resume after restart or reconnect.
5. Implement explicit Sync once while staying paused if adopted. Calendar picker
   refresh/save must disclose one-shot work or defer it; neither silently resumes.
6. Resume reconciles current source records; do not replay each paused edit as a
   separate mutation. Reuse mapping/idempotency guarantees and structured errors.
7. If schema changes: run legacy upgrades, rollback/retry/fault/restart checks with
   safe copies and preserve IDs/timestamps/history. Never modify applied migrations.

Verify: fake scheduler/clock/barrier tests for every trigger, simultaneous clicks,
active sync, queued nudge, offline retry and restart; DATA cases if persistence
changes. Output: acknowledged durable preference and exact operation semantics.
Exit: no automatic provider calls while paused; one-shot cannot flip the preference.

### APP-C05 — Settings shell, panels and dialog framework

1. Add the compact Settings entry/route within the existing app; preserve Today-first
   startup and existing Plan/Track/Stats/Assistant/work views.
2. Build provider panels from the contract using existing styles/components; primary
   actions, last-success/error and details stay compact and readable.
3. Implement reusable labelled dialog/sheet behavior, focus trap/return, field error
   associations, keyboard submission/dismissal and loading/conflicting-action state.
4. Preserve prior Plan/day/scroll/selection and the same timer across navigation.
   Background legitimate sync updates remain visible without resetting the page.
5. Keep tokens transient in the new-input form only; clear on success/dismissal,
   never localStorage/sessionStorage, and never load saved credentials into inputs.

Verify: UI/keyboard/status/privacy/navigation cases, actual wide/narrow rendering.
Output: working shell with backed states; no placeholder actions described as done.
Exit: controls and errors remain reachable and navigation preserves active work.

### APP-C06 — bCourses Settings and assignment-review integration

1. Connect token Check and save/Replace/Remove to verified existing credential APIs.
2. Render rejection versus offline/unknown check distinctly; preserve the previous
   credential and open failed form as specified. Handle saved-but-readback-failed
   without falsely instructing a second save.
3. Move/manage course choices in Settings without duplicating their source of truth.
   Expose the chosen assignment-review entry and preserve review functionality.
4. Preserve Add identity, source URL, due-date decisions, undated/past/dismissed work,
   local edits and tasks after course deselection or credential removal.
5. Replace obsolete edit-files setup errors with the Settings route; optional setup
   help can explain the data-folder location without exposing stored values.

Verify: bCourses UI/API/browser/Add-once/due-date tests and active-task/timer return.
Output: complete credential→courses→review flow. Exit: no silent import/deletion,
no false working-connection badge, and useful retry with retained work.

### APP-C07 — Google Settings and Plan integration

1. Wire file picker/validation/save/replacement and truthful Setup ready state.
2. Show the three-function sharing summary before browser sign-in; explain all-task
   export, including imported bCourses tasks and read-only calendar selection scope.
3. Implement browser fallback, waiting/polling, return, explicit cancellation if
   backed, denial/timeout/retry/missing-permission and reconnect states.
4. Bind Pause/Resume/Pausing/Sync once to verified service semantics and retain
   acknowledged state across navigation/reload. Never show a successful Pause early.
5. Connect calendar selection and existing Plan events/start-time publishing without
   changing personal calendars or Google-owned resource boundaries.
6. Handle combined sync progress/partial failure/last success; refresh open views
   after legitimate background changes without losing task form/timer context.
7. Wire safe Disconnect/replacement/account-mismatch recovery and exact retained-data
   copy. Do not promise cloud revocation unless its result is actually verified.

Verify: Google UI/API/scheduler/browser tests including late callback and account
mismatch, cross-export, one-shot, partial sync, event→task identity and retry.
Output: coherent end-to-end Google experience. Exit: scope understood, state truthful,
provider data safe and user input/context recoverable.

### APP-C08 — Integrated browser, restart, failure and regression review

1. Run the full affected fake-provider journeys in a real installed Chrome/Edge:
   fresh setup, invalid replacement, auth denial/timeout, Pause/edit/restart/Resume,
   offline recovery, reconnect, bCourses Add/deadline and Google calendar/task flows.
2. Exercise fault injection at credential/status writes, callback completion,
   provider read/write stages and service restart; check no unintended replay/clone.
3. Inspect actual 640/800/1440 layouts Light/Dark plus browser 200% zoom/reflow,
   keyboard/focus, error announcements and targeted assistive-technology behavior.
4. Run affected backend/frontend tests, typecheck/build and foundation regressions;
   broaden to full suite at this integrated feature boundary as root guidance requires.
5. Record exact passes/failures/skips and OS. Missing browser or unavailable manual
   access is an open gate, not a runtime pass. Do not claim Mac hardware evidence
   from another OS or recertify timers via UI visibility.
6. Independently review diff/data consequences and reproduce blocker fixes with the
   relevant targeted cases; do not rerun unrelated checks without a reason.

Verify: full applicable UI/API/SYNC/DATA cases and command matrix. Output: dated
implementation review distinct from an operator/live review. Exit: no required
scenario missing or unresolved failure hidden by aggregate test counts.

### APP-C09 — Operator walkthrough and final handoff

1. Summarize exactly what is built, tested with fakes, accepted in Figma and still
   awaiting operator evidence. Record defaults chosen, migrations and limitations.
2. Provide the operator walkthrough using disposable data first with VS Code closed.
3. If separately authorized, perform the bounded real-account cases in TEST_PLAN;
   name outbound mutations before applying and retain only redacted/count evidence.
4. Verify local startup, restart persistence, offline work, same-account reconnect,
   Pause and invalid replacement in the actual app as scoped. Keep provider approval
   and hardware/core-trial/release gates separate.
5. Update setup/use/help, PROGRESS/COMPLETED and implementation handoff; preserve the
   original prototype evidence as historical. Do not store credentials in artifacts.
6. Commit the scoped change only if requested; report any remaining manual gate and
   next concrete action, without automatically starting another feature.

Verify: operator/live category where authorized, review/evidence completeness and
final diff/privacy check. Output: reviewable local Settings delivery with honest
limits. Exit: user-facing success is supported by the corresponding evidence layer.


## 5. Keep implementation work small

APP-C parents define the sequence, not a license for one large active ticket. Use
the following slices as the active work item; follow the parent's numbered actions
only as needed for that slice. Target a focused 30–120-minute work session, not a
calendar promise. Split again before starting if the slice remains too large.
Only mark a parent complete when all its scoped slices and required gates pass.
A focused user request can authorize selected slices without the whole roadmap.

| Parent | Suggested small execution slices and checks |
| --- | --- |
| APP-C01 | .1 reconcile checkout/source (DOC-01); .2 map acceptance/fixtures/defaults (DOC-02, DATA-01). |
| APP-C02 | .1 credential replacement/fault recovery (API-02–04, DATA-02–03); .2 auth attempts/cancel/late callback (API-05–06); .3 disconnect/sync coordination (API-07); .4 identity/mapping boundary (API-08, DATA-07). Apply API-09 to every changed route. |
| APP-C03 | .1 backend status contract (DOC-03, API-01/09/10); .2 frontend API/state mapping (UI-01 and failure/readback assertions). |
| APP-C04 | .1 durable preference and upgrades (DATA-03–04, API-10); .2 all automatic trigger gates (SYNC-01–03); .3 in-flight/queued-work barrier (SYNC-04); .4 one-shot/Resume reconciliation (SYNC-05–06, UI-06 contract). |
| APP-C05 | .1 Settings route/context (UI-10, DATA-05); .2 dialog/focus/transient input (UI-02–05, UI-09); .3 backed provider panels/busy/errors (UI-01/06/08). |
| APP-C06 | .1 bCourses credential form (UI-02, API-02); .2 courses/review/work return (UI-07, SYNC-07–08, DATA-06). |
| APP-C07 | .1 file/browser authorization UI (UI-03–05, API-05–06); .2 Pause/status/combined sync UI (UI-06, SYNC-01–06/12); .3 Plan/calendar/task integration (UI-08, SYNC-08–11, DATA-06); .4 reconnect/disconnect recovery UI (API-07–08, DATA-07). |
| APP-C08 | .1 process/fault/regression checks (applicable API/SYNC/DATA); .2 browser/accessibility/widths (UI-09–10, DATA-08); .3 independent final diff and evidence review (DOC-04). |
| APP-C09 | .1 operator walkthrough (LIVE-04); .2 bounded optional live checks (LIVE-01–03 only with established scope/isolation); .3 setup/help/handoff/records (DOC-04). |

Subslice notation expands to the full parent ID, for example APP-C04.3. Cases may
cover multiple slices; run the meaningful assertions for the actual change, then
complete integrated parent checks at its boundary. Do not replace a required race
or persistence check with a screenshot merely because a slice is small.

## 6. Unit-to-case verification routing

Use exact cases in [TEST_PLAN](TEST_PLAN.md); a range includes both endpoints.
These are evidence selections, not completion marks. Expand only for actual diff
risk or new failures. Cases depending on proposed semantics apply once adopted.

| Unit | Principal verification cases |
| --- | --- |
| UX-C01 | DOC-01–03 |
| UX-C02 | FIG-01 |
| UX-C03 | FIG-02 |
| UX-C04 | FIG-03 |
| UX-C05 | FIG-04 |
| UX-C06 | FIG-01–06, DOC-04 |
| APP-C01 | DOC-01–02, DATA-01 and fixture isolation checks |
| APP-C02 | API-01–09, DATA-01–03, DATA-07 |
| APP-C03 | DOC-03, API-01, API-09–10, UI-01 |
| APP-C04 | API-10, SYNC-01–06, DATA-03–04, UI-06 |
| APP-C05 | UI-01–10, DATA-05 |
| APP-C06 | UI-02, UI-07, API-02, SYNC-07–08, DATA-06 |
| APP-C07 | UI-03–08, API-05–08, SYNC-08–12, DATA-06–07 |
| APP-C08 | Applicable UI/API/SYNC/DATA cases plus the command/regression matrix |
| APP-C09 | DOC-04, LIVE-01–04 only within their established authorization and evidence scope |
