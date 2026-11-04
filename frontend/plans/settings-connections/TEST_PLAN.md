# Settings and connections — verification plan

Read the [entrypoint](README.md), [specification](SPEC.md) and [execution plan](EXECUTION_PLAN.md) together. The stable design brief is [UX plan §6](../../BEARPLANS_UX_PLAN.md#6-local-settings-and-connections-extension). Current work, ownership and gates belong only in [PROGRESS](../../../docs/PROGRESS.md); this file defines cases rather than tracking their completion.

## Scope and evidence boundaries

Prepared November 3, 2026 from macOS/Darwin and source at `674db93`. That commit includes write-only connection-setup routes and their existing tests; `f375f24` includes credential relocation. Source may advance independently: APP-C01 must reconcile the actual checkout, diff and running service before implementation. Reading an existing test is not a fresh pass. No application test, browser run, provider call, credential read or Figma operation was performed to author this plan.

Pause/Resume automatic Google sync is confirmed. Persistence across restarts, finishing an in-flight sync before acknowledging Paused, explicit Sync once while paused and fresh reconciliation on Resume remain **proposed details**. Cases that depend on them become acceptance gates after those details are agreed; do not treat them as current implementation claims. Assignment-review placement is also unresolved; exercise its agreed destination rather than silently choosing one.

Use these evidence layers independently:

| Layer | What a pass establishes | What it cannot establish |
| --- | --- | --- |
| Documentation | Consistent contracts, links, ticket boundaries and traceability. | Built controls or working providers. |
| Figma/static | Readable editable screens, finite transitions and specified focus/keyboard intent. | Real input, persistence, security, network, scheduler or browser accessibility. |
| User report | The user reported the named steps clear/successful at an identified prototype start. | Direct observation, timing or runtime correctness unless independently captured. |
| UI | React/browser behavior against deterministic mocked requests or a disposable local service. | Actual provider authorization/delivery. |
| API/domain | Request validation, writes, scheduler behavior and retries against fake providers. | Actual Google/bCourses behavior or Mac hardware acceptance. |
| Data/restart | Disposable database/files, process restart and failure-injection behavior. | Safety of an untested upgrade on the only saved database. |
| Authorized live | Exactly the explicitly authorized provider operations and observed result. | Other accounts, continuous availability, generalized reliability or release readiness. |

Every executed case records ticket, case ID, commit/diff identity, OS, exact command, actual result, failures/skips and evidence location in a dated `docs/reviews/` record. Screenshots use synthetic content and record actual viewport/theme. Preserve failed attempts and subsequent retests. A skipped required case remains an open gate. Never convert a static frame or prior walkthrough into an application pass.

## Fixtures and safety controls

- Use disposable databases/data folders outside source and the preserved core-trial copy. Set `BEARPLANS_SECRETS_FILE` to an empty path in a disposable folder before any standalone startup; the test suite already isolates it through `tests/conftest.py`.
- Inject fake bCourses, Google Tasks, Calendar, OAuth/token and revocation transports. Reject unexpected outbound requests. Fake-provider writes are recorded in memory only; **no fixture sends a write to a real provider**. Never reuse an owner's signed-in browser profile.
- Give synthetic accounts A/B distinct stable provider identities, same-named calendars/lists and deliberately overlapping source IDs. Include an existing BearPlans mapping, a personal list/calendar and an unknown item inside a BearPlans-created list.
- Include course assignments that are dated, undated, past due, removed remotely and already added locally; a local parent with two leaves; repeated task placements; timed/untimed work; one closed week; and a running/paused/Needs review timer with known session ID.
- Use fake clocks/barriers rather than long sleeps for 120-second periodic sync, short edit debounce, 300-second sign-in timeout, service restarts and in-flight responses. Acknowledged Paused is an observable barrier, not just the button label changing.
- Capture credential canaries only inside fixtures. Assert their absence from responses, errors, status files, logs, screenshots, database/backups, artifacts and Git. Never print real secrets to diagnose a failure. New unsaved input may remain only inside its masked open dialog; saved values must never be fetched back into the browser.
- Failure injection covers provider denial/offline/partial success, invalid JSON, permission/disk failures, interrupted publication, concurrent save/remove and callbacks arriving after cancel/disconnect/client replacement.
- Tests touching task completion must preserve parent-derived completion, unique leaf totals, task identity, active session controls and immutable closed-week snapshots.

## Requirement coverage

Requirement IDs are defined in [SPEC](SPEC.md); case groups below keep their layer/ticket visible. Some requirements deliberately require more than one evidence layer.

| Requirement | Principal cases |
| --- | --- |
| CON-01 · Local lifecycle/offline | DOC-01, UI-10, SYNC-01, SYNC-07, SYNC-12, DATA-08, LIVE-04 |
| CON-02 · Truthful status | DOC-03, FIG-01, UI-01, API-01, API-05, SYNC-12 |
| CON-03 · bCourses credentials | FIG-02, UI-02, API-02, API-04, DATA-01–03, LIVE-01 |
| CON-04 · bCourses review | FIG-02, UI-07, SYNC-07–08, DATA-06, LIVE-01 |
| CON-05 · Google client-file setup | FIG-03, UI-03, API-03–04, DATA-01–03 |
| CON-06 · Google OAuth lifecycle | FIG-03–04, UI-04–05, API-05–07, DATA-03, LIVE-02 |
| CON-07 · Three Google functions/cross-export | DOC-03, FIG-03, UI-08, SYNC-08–12, DATA-06, LIVE-03 |
| CON-08 · Pause | FIG-04, UI-06, API-10, SYNC-01–06, DATA-03–04, LIVE-03–04 |
| CON-09 · Replacement/disconnect/cache consequences | FIG-04, UI-02–03, UI-05, UI-08, API-04, API-06–07, SYNC-12, DATA-05–06 |
| CON-10 · Account identity | API-08, DATA-07, LIVE-02 |
| CON-11 · Navigation/responsive/accessibility | FIG-01, FIG-05–06, UI-09–10, DATA-05, DATA-08, LIVE-04 |
| CON-12 · Evidence/privacy | DOC-01–04, API-09, DATA-01–02, all LIVE cases and fixture/evidence rules |

## Documentation cases

| Case / layer / ticket | Preconditions | Actions | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| DOC-01 · Documentation · APP-C01 | Current checkout and all plan files available. | Compare Git/source with the baseline and capability table; inspect uncommitted/untracked relevant work. | Existing setup routes are recognized; missing Pause/auth safeguards stay explicit; no stale claim that backend setup is wholly unbuilt. | Source paths/commit and discrepancy notes; documentation checks below. |
| DOC-02 · Documentation · UX-C01 / APP-C01 | User decisions and proposals listed. | Trace Settings, separate credential dialogs, confirmed Pause and each proposed detail to SPEC and tickets. | No proposed default becomes a user decision; design and app authorization/status remain distinct. | Decision-to-ticket map and unresolved questions. |
| DOC-03 · Documentation · APP-C03 | Status/control contract drafted. | Review wording for setup, saved token, authorization, successful sync, stale cache, partial failure, disconnect and removal. | No Ready from file/token presence; no fake account email/per-function timestamp; no provider-wide rollback or unsupported revocation promise. | Copy/state matrix and source reconciliation. |
| DOC-04 · Documentation · APP-C09 | Final handoff candidates exist. | Check relative links, unique case/ticket IDs, command/file references, open-gate links and single status record. | Documents agree; no duplicate mutable tracker, invented Figma IDs or undocumented runtime gate. | Link/ID checks, scoped diff and handoff review. |

## Figma and prototype cases

These belong to UX-C02–06. Record exact returned node IDs and actual rendered widths/themes. User reports supplement static/prototype evidence; they do not substitute for the runtime cases below.

| Case / layer / ticket | Preconditions | Actions | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| FIG-01 · Figma/static · UX-C02 | Existing shell/tokens and Settings overview draft. | Enter Settings from Plan; inspect both compact provider summaries and management disclosure. | Clear entry/back path; status, last success and actionable problem visible; credential details on demand; local service limitation readable. | Render, node IDs, component/token references. |
| FIG-02 · Figma/static · UX-C03 | bCourses setup/replacement/error examples. | Follow masked entry → Check and save → courses → assignment-review entry; Cancel and retry examples. | Saved secret is never shown; failure retains masked draft for correction and prior setup; cancellation/dismissal clears unsaved secret. | State links/render and bounded-flow inspection. |
| FIG-03 · Figma/static · UX-C04 | Google setup/auth examples. | Inspect valid/invalid file, browser handoff/fallback, waiting, denied, timeout, missing permission and retry states. | File validation and consent are distinct; all three Google functions and bCourses task export are explained before first consent. | State matrix, renders, prototype routes. |
| FIG-04 · Figma/static · UX-C05 | Agreed Pause details reflected in draft. | Exercise Pausing → Paused → Sync once → Paused → Resume; inspect offline/partial-failure and disconnect examples. | No automatic success from click alone; distinct consequences/retained data; explicit new runtime requirements annotated. | Named starts, finite transition results and simulation limits. |
| FIG-05 · Figma/static · UX-C06 | Overview, dialogs, long names and errors available. | Render 640×800, 800×900 and 1440×900 in Light/Dark; inspect expanded panels and largest text fixture. | No clipping/obscured actions; clear scroll ownership, useful errors and readable focus/disabled states. | Actual-size screenshots and viewport/theme log; browser zoom remains separate. |
| FIG-06 · Prototype/user report · UX-C06 | Named resettable starts and wired return/cancel paths. | User walks both providers and Pause/recovery; returns to prior Plan/day/task and active timer example. | User can explain outcomes; ambiguity is logged and repaired; fixed inputs/unwired references are disclosed. | Exact prompt, verbatim report, observed steps if any, reset/start IDs and retest evidence. |

## Frontend and browser cases

Extend existing React/browser suites after the relevant application ticket starts. Existing suites do not yet prove the new Settings UI. Add narrowly scoped new tests only where an existing file is unsuitable, then record their real paths before citing them as runnable commands.

| Case / layer / ticket | Preconditions | Actions | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| UI-01 · UI · APP-C05 | Mock missing/invalid/valid client, saved/expired token and last-success states. | Open overview and provider detail for each combination. | Correct setup/auth/sync distinction; errors retained until resolved; timestamps honest; no invented account/per-function result. | Component assertions and representative browser renders. |
| UI-02 · UI · APP-C05 | Existing bCourses token; masked replacement dialog. | Enter new draft; reject/check offline; correct and save; dismiss another draft by Cancel/Escape. | Failure keeps masked editable draft and old setup; success/dismissal clears draft; reopening never reloads saved secret. | Request mocks, DOM/value assertions without logging canaries. |
| UI-03 · UI · APP-C05 | Google file dialog and mocked validation. | Select wrong type/oversized/invalid file; replace with valid Desktop file; cancel a selection. | Actionable field error; previous setup remains; fresh/different-client format success leads to Sign-in needed, not Connected; same-client replacement preserves prior usable sign-in or prior reconnect state without inventing new validity; filename/content handled privately. | File-input assertions and failure/retry screenshots with synthetic names. |
| UI-04 · UI/browser · APP-C05 / C07 | Browser open succeeds/blocked; provider callback simulated. | Continue with Google; use fallback when blocked; leave Settings and return while pending. | No false “opened” claim if blocked; usable provider link; waiting status survives navigation; no credential in app URL. | Browser-open mocks, return instructions and pending-state assertions. |
| UI-05 · UI/browser · APP-C05 / C07 | Existing connection; pending sign-in; fake clock. | Deny/timeout; close only the status dialog; separately choose explicit Cancel sign-in, then deliver late callback. | Closing dialog differs from canceling auth; old setup is retained on denial/error; canceled attempt cannot show success or reconnect later. | State-transition assertions aligned with API-05–06. |
| UI-06 · UI · APP-C05 | Running sync then proposed pause response sequence. | Pause repeatedly, inspect Pausing, wait for acknowledgement, Sync once, Resume, and fail each request. | Busy/retry controls prevent duplicate intent; Paused only after backend confirms; one-shot remains paused; no optimistic false success. | Mocked pending/resolved/error responses and live status announcements. |
| UI-07 · UI/browser · APP-C05 / C06 | bCourses manual Refresh, chosen courses and review list. | Change course draft, fail Save, retry; enter review list; Add/dismiss/restore; review changed due date. | Choices/input retained after error; clear review entry; nothing imported before Add; source reading and local changes remain distinguishable. | Existing BCourses suite extended and fake-service browser journey. |
| UI-08 · UI/browser · APP-C05 / C07 | Personal calendars and Google sync summary. | Save/unsave calendar selection; inspect Tasks/publishing details; disconnect/remove preview and cancel. | Calendar selection affects display reads only; all-task export remains clear; distinct consequences; no deletion from canceled action. | Google/CalendarEvents assertions and browser state. |
| UI-09 · UI/browser · APP-C05 / C08 | Settings/dialogs, failed save and pending operation. | Navigate entirely by keyboard; Tab/Shift+Tab, Escape, submit, retry; inspect screen-reader names/status and focus after error/close. | Labeled dialogs and inputs; contained focus, logical order, visible focus; no accidental background submit; return focus to trigger; error associated with field. | Keyboard trace, browser accessibility inspection and assistive-technology notes. |
| UI-10 · UI/browser · APP-C05 / C08 | Selected past/current Plan day, project/task, scroll position; timer running/paused/Needs review. | Open/close Settings and dialogs; switch provider details; simulate background completion; inspect 640/800/1440 widths, Light/Dark and 200% browser zoom. | Same work context and session ID/controls survive navigation; legitimate sync completion updates separately; no clipping/lost action; no time credit from navigation. | Before/after state, real browser screenshots and timer assertions; actual OS/zoom logged. |

## API and authorization cases

Use existing `tests/test_connections.py` and Google/bCourses tests as foundations. For new auth/session controls, extend the appropriate suite or create a focused suite in APP-C02–03; do not invent new endpoint contracts in a test before agreeing the state model.

| Case / layer / ticket | Preconditions | Actions | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| API-01 · API · APP-C02 / C03 | Empty/disposable credential folder; configured-but-unsigned and expired examples. | Read Connections/Google/bCourses status before/after format check, sign-in and failed sync. | Presence, last credential check, pending auth and last provider success stay distinct; response contains no secret or fabricated live validity. | Status/schema assertions and safe fixtures. |
| API-02 · API · APP-C02 | Good old token and fake bCourses checker. | Save malformed/oversized/rejected replacement; simulate network/TLS/rate failure; then valid replacement. | Invalid input cannot reach provider; check is bounded/read-only; failed check keeps old value; valid save preserves unrelated secret lines. | Existing connection tests extended; recorded fake request method/host/count. |
| API-03 · API · APP-C02 | Good old Google client; signed-in token. | Submit invalid JSON, Web client, missing fields, oversized/multibyte body or malicious provider URL; then valid same/different client. | Invalid input leaves old client/auth; validation uses permitted Google addresses and Desktop type; format success makes no live-access claim. | Parsing/request assertions, boundary cases and old/new file state. |
| API-04 · API/data · APP-C02 | Working credentials and signed-in token; injected disk/status publication faults. | Fail before/after replacement staging and auth transition; retry exact intent; interleave save/remove. | No false “previous setup kept” after losing it; retain prior usable setup or accurate recoverable state; no torn files, stale success or silent signed-out result. | Fault-injection timeline, safe file equality checks and response assertions. |
| API-05 · API/auth · APP-C02 | Existing auth and new attempt with fake callback/token transport. | Deny; omit scopes; time out at boundary; close browser with no callback; retry. | Old usable auth survives failed replacement; scope failure is actionable; timeout is bounded; no phantom success or disclosure in errors. | Fake-clock/transport assertions and attempt-state trace. |
| API-06 · API/auth · APP-C02 | Pending sign-in plus controllable token-exchange response. | Cancel before callback, during exchange and after newer attempt; disconnect/remove/replace client; then deliver old callbacks. | Invalidated attempt cannot save/recreate token or supersede current auth; cancellation acknowledgement is truthful; repeated cancellation safe. | Generation/revision guard assertions and late-response barriers. |
| API-07 · API/auth · APP-C02 | Connected account, active sync, optional fake revocation transport. | Disconnect repeatedly; inject revocation offline/failure if implemented; remove client separately. | Requests serialize with auth/sync; local disconnection stays effective; local tasks/history/cache and remote copies retained; report revocation only if actually observed. | Local token/access checks, fake calls and distinct result states. |
| API-08 · API/auth · APP-C02 / C07 | Account A mappings; reconnect same account or different account B with overlapping IDs. | Complete reconnect, then request sync and calendar reads. | Same identity reuses safe mappings; mismatch is blocked or isolated before any provider work; no old-account cache leak, cross-account writes or guessed identity. | Stable synthetic identity, mapping/query assertions and provider call audit. |
| API-09 · API/security · APP-C02 / C03 | Local API with fixture secrets and no real transports. | Call mutations with remote Host/foreign Origin; malformed JSON/extra fields; attempt unsupported Assistant access; inspect debug/error responses. | Existing loopback/same-origin protections apply; structured safe errors; credentials cannot be read/changed through Assistant tools; no request-body logging. | Existing origin/security tests plus response/log canary assertions. |
| API-10 · API · APP-C03 / C04 | Agreed Pause/control/status contract. | Query/submit repeated stale and conflicting Pause/Resume/Sync once intents; interrupt save and retry. | Durable accepted state and truthful busy/status; failed write does not acknowledge Pause; operations cannot race into a contradictory scheduler state. | Contract tests and revision/serialization/retry evidence. |

## Synchronization and local lifecycle cases

Pause cases below depend on the proposed detailed contract being accepted. All three Google functions share the automatic-control boundary; a display preference or navigation event must not bypass it.

| Case / layer / ticket | Preconditions | Actions | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| SYNC-01 · Domain/process · APP-C04 / C08 | Fake providers; awake service; open then closed browser tab. | Advance periodic/debounce clocks; save local task; close tab; stop service; restart. | Automatic work follows service lifecycle, not tab visibility; stopped service makes no requests; no claim of always-on/cloud scheduling. | Controlled worker calls and process start/stop log. |
| SYNC-02 · Domain · APP-C04 | Automatic sync enabled, no operation active. | Pause; trigger periodic, edit debounce, startup/reauthorization and other automatic hooks; mount/reopen Settings while connected with an empty calendar cache; advance clocks. | After acknowledged Paused, no automatic Tasks push/pull, calendar publish or calendar read starts, including UI mount/empty-cache fetches outside the worker; credentials/cache/local edits retained. A deliberate disclosed picker refresh remains separate one-shot work. | Per-function fake call counts and trigger coverage map. |
| SYNC-03 · Domain/data · APP-C04 | Pause acknowledged; durable setting stored. | Restart service and reload UI; edit locally and advance periodic clock. | Still paused; no launch-time/migration/auth hook bypass; no paused-state reset on read or token refresh. | Restart snapshot and zero automatic provider calls. |
| SYNC-04 · Domain · APP-C04 | Active sync blocked at each of Tasks/read/publish stages. | Request Pause, queue edits, release barriers; repeat at stage boundaries. | Pausing while current work settles; no second sync starts; Paused only after boundary is effective; completed remote writes are not rolled back. | Interleaving trace and exact final fake provider state. |
| SYNC-05 · Domain/API · APP-C04 | Paused, connected, unsent edits; one-shot proposal accepted. | Request Sync once; repeat/double-click; complete or fail it; advance automatic triggers. | One serialized deliberate sync; remains paused on success/failure; no automatic resume; actionable partial-error status. | Calls/state assertions and retry behavior. |
| SYNC-06 · Domain/data · APP-C04 | Paused through several local edits/completions/moves; possible Google completion. | Resume; allow one reconciliation, then periodic operation; repeat Resume. | Reconcile current records and conflict rules, not every historical edit; no duplicate lists/tasks/events; current completion wins where specified. | Before/after mappings, revisions and fake call records. |
| SYNC-07 · Domain/API · APP-C06 | bCourses manual cache and selected courses; Google may be paused. | Wait/visit Settings; explicitly Refresh; fail provider read; retry. | No automatic bCourses scheduler invented; failure preserves cache/local tasks/last success; Google Pause does not prevent explicit bCourses refresh. | Fake GET counts, cache equality and saved sync status. |
| SYNC-08 · Domain/integration · APP-C06 / C07 | Chosen bCourses course; Google configured; dated/undated assignments. | Refresh without Add; Add assignment twice; sync; change source due date; Keep mine then explicit Use new due date. | No local import before Add; one local task/source mapping; ordinary added task enters Google Tasks export; source refresh never silently changes local deadline. | Stable task/source/Google IDs, one-task counts and reviewed deadline changes. |
| SYNC-09 · Domain/integration · APP-C07 | Local projects, leaves, parent and personal Google list. | Sync twice; edit on either side; complete leaf/Google parent; reopen child; delete remote mapped task; retry interrupted sync. | Identity/idempotency and owned-resource boundaries preserved; only eligible leaf completion applies. Remote parent ticks must not silently complete/reopen children under root rules; flag any existing adapter discrepancy instead of adopting it as a new requirement. Unique leaf counts remain correct. | Existing Google Tasks suite plus Settings-trigger integration assertions. |
| SYNC-10 · Domain/integration · APP-C07 | Selected/unselected calendars; all-day, recurring/exception, changed/canceled events; cached window boundaries. | Read/refresh; toggle selection; Add event twice; inspect Plan; repeat after source changes. | Personal calendars never written; selections affect reads only; explicit Add creates one task; no duplicate publishing for imported event without start time; service date/timezone rules retained. | Reading fixtures, stable event/task IDs and Plan response assertions. |
| SYNC-11 · Domain/integration · APP-C07 | Timed placement, estimate, prior event and closed-week carryover. | Sync twice; retime/move/complete/clear; carry over unfinished task with time; inspect past event. | Same mapped event updated; current 30-minute reminder; only BearPlans calendar written; future-event removal/past retention and carried start time preserved. | Existing calendar/weeks fixtures and fake event/reminder payloads. |
| SYNC-12 · Domain/API · APP-C07 / C08 | Tasks stage succeeds, later Calendar/read fails or service loses connection. | Observe status; retry; revoke/expire permissions; recover; fail mid-retry. | Partial success reported honestly; last complete success stays unchanged; cache/local work usable; retries converge without duplicate writes or claim that nothing changed globally. | Stage fault trace, provider contents, last-success/error and mapping assertions. |

## Data, restart and regression cases

| Case / layer / ticket | Preconditions | Actions | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| DATA-01 · Data/process · APP-C01 / C08 | Disposable old/new credential folders and environment override. | Run startup relocation twice; existing destination, deleted destination, marker present, no legacy folder and override variants. | Current one-time copy semantics preserved; no real folder touched; no overwrite/reimport after intentional removal; owner-only permissions. | `test_secrets_location.py` extension and process evidence. |
| DATA-02 · Data · APP-C02 / C08 | Fixture credential canaries, saved status and normal log/error capture. | Save/check/remove/retry; create/inspect/restore disposable SQLite backup; inspect generated artifacts and Git diff. | No secret in API/status/log/database/backup/screenshots/Git; credentials remain outside SQLite; unrelated secret keys and saved work preserved. | Canary absence assertions and backup/content audit without echoing values. |
| DATA-03 · Data/restart · APP-C02 / C08 | Credentials and agreed Pause state; successful/failed last-sync records. | Graceful restart, crash at publication points, retry; make directory read-only or simulate disk full. | Old/new complete files only; no reset; truthful recoverable error; Pause not falsely acknowledged; no automatic reauthorization/account crossover. | Injected-write tests, file permissions and restart state. |
| DATA-04 · Data/migration · APP-C04 / C08 | Pre-change database with IDs/revisions, mappings, closed snapshots, sessions/rewards and legacy placements. | Upgrade; inject migration failure; retry/reopen twice; test newer unsupported schema. | Versioned migration atomic/retryable; existing identities/history/persistence preserved; no applied SQL edits or old-eligibility backfill. | Disposable upgrade diffs and existing migration/fingerprint regressions. |
| DATA-05 · UI/data · APP-C05 / C08 | Plan on chosen day/project, selected row and scrolled list; timer in each supported state. | Open/close Settings, disconnect/remove provider, restart and recover timer as required. | Navigation/settings writes never replace/finish session, complete task, award time/coins or change closed history; normal explicit recovery rules remain. | Session IDs/revisions, frozen snapshot equality and timer tests. |
| DATA-06 · Domain/data · APP-C06 / C07 | Several task dates, parent/children, closed week and existing imported tasks. | Refresh/reconnect; repeated Add; sync completion then reopen; remove connection/source selection. | Same tasks remain; unique leaf totals, explicit review and frozen Missed unchanged; unselect/disconnect never deletes local tasks/history. | Task/placement/source mappings and snapshot/statistics assertions. |
| DATA-07 · Domain/process · APP-C07 / C08 | Account A source cache, mappings and completed imports; interrupted account-B attempt. | Fail/cancel mismatch recovery; restart before/after agreed resolution; attempt sync. | No mapping/cache from A is silently applied to B; safe blocking or verified isolation persists; local imports survive; remote A copies not deleted. | Account-keyed state and zero unauthorized provider calls. |
| DATA-08 · Browser/process · APP-C08 | Built frontend, fake providers and disposable service; existing core regressions available. | Run both provider journeys and affected Plan/timer/week flows; check service version/instance before and after restart. | UI/backend build agree; no page errors or repeated mounted-worker side effects; failed provider never breaks offline local planning/tracking. | Exact browser commands, screenshots, console errors and skip reasons. |

## Optional operator/provider checks

These are separately gated by APP-C09. No live request is authorized by saving this plan. Use fake providers for normal verification. Establish the user's existing explicit authorization for the named account, read scope, synthetic fixture, any remote writes and cleanup before live work. Honor it when it already covers the intended operation; ask only for missing or expanded scope. A historical successful test alone is not authorization.

| Case / layer / ticket | Preconditions | Actions | Expected result | Evidence |
| --- | --- | --- | --- | --- |
| LIVE-01 · Authorized live read · APP-C09 | User permits bounded bCourses read; safe local setup; no Google export triggered. | User enters token privately; check; choose one course; Refresh; inspect review list. | Source is read-only; no import without Add; failures safe; no token output. | Consent scope, user/operator observation, counts-only result and redacted UI. |
| LIVE-02 · Authorized live auth/read · APP-C09 | User authorizes sign-in/named calendar reads; before authorization, durable Pause is acknowledged and every automatic path (including UI mount) is gated, or an isolated read-only harness is used; user enters client privately; account guard ready. | Confirm no automatic Tasks/calendar writes can start; authorize in system browser; test denied/missing path if practicable; explicitly request only authorized calendar-list/event reads. If writes cannot be prevented, defer this read-only case or establish authorization covering all bundled exports first. | Honest identity/auth status; no unapproved Tasks export or calendar publishing; personal calendars unchanged; selected events appear as read-only cache. Read/auth permission alone never authorizes bundled writes. | Existing authorization scope, acknowledged Pause or harness isolation, per-function call audit, account match and observed success/error without sensitive content. |
| LIVE-03 · Authorized live writes · APP-C09 | Separate permission explicitly covers all configured Google Tasks export and BearPlans-calendar writes, or isolated synthetic app data/account; cleanup agreed. | Publish one synthetic timed task, repeat sync, update it, complete/reopen; exercise Pause/Resume and agreed one-shot. | Only approved BearPlans-owned objects changed; one identity per mapped item; correct reminder; no new automatic work while paused; cleanup only identified test objects. | Before/after IDs/counts, actual provider outcomes, cleanup record; provider notification delivery reported only if observed. |
| LIVE-04 · Operator/local · APP-C09 | Disposable local app accepted by automated gates; actual Mac; VS Code closed. | User sets/replaces credentials, recovers an error, visits review list/Plan and active timer; closes tab, reopens, then stops/restarts service. | Setup usable without editing files; service-vs-window limitation understood; state/paused choice preserved; local work available offline. | Verbatim user feedback plus observed steps, OS/build/data path and remaining manual gates. |

## Future commands and existing test homes

Run from the actual repository root after implementation is separately authorized. These are **future commands**, not results. Paths and npm script names were checked while writing this plan. New Pause/auth/browser coverage must be added during its ticket; running the existing files alone cannot certify unimplemented cases.

```sh
# Focused existing API/domain/data suites; fake providers and isolated secrets.
.venv/bin/python -m pytest tests/test_connections.py tests/test_secrets_location.py tests/test_bcourses.py tests/test_google_tasks.py tests/test_google_calendar.py tests/test_google_reading.py

# Existing React homes for connection/task/calendar behavior and navigation.
npm --prefix frontend test -- src/Google.test.tsx src/BCourses.test.tsx src/CalendarEvents.test.tsx src/App.test.tsx src/WeekActions.test.tsx src/api.test.ts
npm --prefix frontend run typecheck
npm --prefix frontend run build

# Existing fake-provider real-browser journeys; needs built frontend and Chrome.
BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest tests/test_bcourses_browser.py tests/test_google_browser.py

# Affected persistence and core regressions, selected again after actual diff review.
.venv/bin/python -m pytest tests/test_migrations.py tests/test_migration_fingerprints.py tests/test_backups.py tests/test_weeks.py tests/test_weeks_restart.py tests/test_timer.py tests/test_timer_recovery.py tests/test_timer_restart.py tests/test_instance_build.py tests/test_launch_compatibility.py

# Full boundaries before milestone/operator handoff, not for documentation alone.
.venv/bin/python -m pytest
npm --prefix frontend test
```

The current Google browser journey skips after 23:00 America/Los_Angeles because its synthetic event must be upcoming; missing browser/build also causes skips. Record these as skips, not passes. Replace time-of-day dependence with a controlled clock where the new ticket needs deterministic boundary evidence. Preserve the existing test isolation and browser fixture behavior rather than pointing tests at the running personal service.

For manual disposable startup, create empty temporary secrets and data paths outside the repository, set `BEARPLANS_SECRETS_FILE` and `BEARPLANS_DATA_DIR`, then use `python3 launch.py --no-browser --port N`. Identify and stop only that test instance gracefully. Never launch against the owner's normal folders as a shortcut. Browser evidence location is supported through `BEARPLANS_EVIDENCE_DIR`; prefer a disposable path and publish only synthetic/redacted artifacts.

For this documentation-only task, verify links, unique IDs, ticket references, command/file existence and scoped whitespace/diff. Do not rerun the application suite or make provider requests merely to validate prose.

## Exit criteria and handoff

- UX-C06 requires actual Figma renders/prototype checks and a bounded user walkthrough; unresolved choices and finite simulation limits remain explicit.
- APP-C02–07 require the relevant API/domain/UI cases before claiming their capability. APP-C08 adds data/restart/browser regressions and records any unimplemented or failed requirement honestly.
- APP-C09 requires a review tied to the exact current build, automated results, open manual gates and operator findings. Optional live cases can remain not performed with a stated limit; they cannot be fabricated from fake-provider results.
- Missing mandatory race, persistence, identity or credential protection evidence prevents the affected implementation pass. A missing optional live check does not invalidate completed independent work, but limits the claim to tested fixtures.
- Existing hardware, release and seven-day core-trial gates remain separate. No Settings test certifies Mac sleep/Standby behavior, unconfirmed time or full release readiness.
