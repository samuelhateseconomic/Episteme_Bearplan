# Settings and Connections — product and interaction specification

Stable design contract, November 3, 2026. Status belongs in
[PROGRESS](../../../docs/PROGRESS.md); execution belongs in [the step plan](EXECUTION_PLAN.md)
and verification in [the test plan](TEST_PLAN.md). This replaces the detailed
connection text formerly in UX plan section 6; that anchor remains a forwarding link.

## Decisions and defaults

| Classification | Direction |
| --- | --- |
| User proposal to develop | One Settings page for bCourses and Google; credentials hidden from the normal view; separate setup popup. |
| Explicitly confirmed | Include Pause / Resume automatic Google sync, keeping the connection and saved data. |
| Existing confirmed integration scope | Read-only/manual bCourses with explicit Add and deadline review; Google selected-calendar reading, BearPlans-calendar publishing and all-task Google Tasks sync. |
| Recommended presentation | Settings → Connections, small gear in compact top bar, two provider panels, on-demand details. |
| Pending placement preference | Keep a dedicated bCourses assignment-review view while the user's location preference remains unanswered. Course/account management belongs in Settings. |
| Proposed Pause details | Persist across restart; cover all automatic Google triggers; explicit Sync once stays paused; finish an in-flight operation before acknowledging Paused; Resume reconciles current records. |
| Deferred | Multi-account switching, automatic bCourses refresh, independent Google capability switches, cache/remote deletion tools and Gmail. Do not add them as a side effect. |

User instructions and root guidance supersede this document. Resolve material
product ambiguity while doing independent work; do not seek repeat approval for
routine equivalent edits already authorized. The saved plan is not authorization
to start a later phase or a live provider mutation.

## Historical source baseline, not a completion tracker

At f375f24, credential files live in the resolved data folder's owner-only
`secrets/` directory; default Mac location is
`~/Library/Application Support/BearPlans/secrets/`. Startup copies legacy code-folder
credentials once without overwriting current ones; tests can override the location.
At 674db93, write-only `/api/connections` status/save/check/remove routes exist.
Existing `Google.tsx` and `BCourses.tsx` still supply work/status views at that
snapshot. Reconcile current source before each unit because parallel work continues.

No Settings screenshot or interaction is delivered by this specification. The
89-product/46-reference-frame handoff is the preserved earlier design baseline.
Source inspection does not certify real-account behavior or every failure path.

## Requirements

### CON-01 — Local lifecycle and offline operation

Normal planning, saved tasks and tracking work without provider access. Internet
is required for bCourses/Google requests. No hosted BearPlans service or public
BearPlans account is needed. Automatic Google work runs with the local service
while the Mac is awake and online, independently of which browser tab is visible.
Closing a tab is not Disconnect or Pause. Stopping the service stops its scheduler;
provider-side reminders already published may still occur.

Show last successful refresh/sync and useful offline/stale copy without erasing
saved source information or blocking local work. Do not imply sync happens while
the service is stopped or the Mac is asleep.

### CON-02 — Truthful connection state

Treat these as separate dimensions rather than one exclusive enum:

| Dimension | Examples | UI meaning |
| --- | --- | --- |
| Setup | Missing / configured / invalid | A token exists or Google client-file format is valid; this alone is not working authorization. |
| Authorization | Sign-in needed / waiting / saved sign-in / reconnect needed | Google flow and latest access evidence. Never infer an email/account from token presence. |
| Automatic-sync preference | Enabled / pausing / paused | The acknowledged scheduler policy; retain it alongside errors. |
| Operation | Idle / checking / syncing / saving | Current action; prevent duplicate conflicting submissions and preserve an available exit where supported. |
| Evidence | Never succeeded / last success / last error | Readable time and recovery action; offline can coexist with Paused or saved sign-in. |

Suggested overview copy: Setup needed, Sign in, Waiting for sign-in, Last synced,
Pausing…, Paused, or Needs attention. A stored token is not proof of usable access.
Do not let a generic success notice hide missing permissions or a failed sync.
Google has combined sync reporting at the source baseline; show its functions
without inventing independent per-function success timestamps.

### CON-03 — bCourses credential setup

Flow: Connect/Replace → instructions → masked new token input → Check and save →
confirmation → chosen courses. The bCourses token is not Google OAuth. Check with
a bounded read-only bCourses request; distinguish rejection from unavailable check.
Keep the old credential when validation fails. Keep new input only in the open
form for retry/correction; clear it on success or dismissal. Never read back,
reveal or partially display a stored token. Use short instructions and optional
provider-help links; ordinary use does not require VS Code/file editing.

Cancel before applying leaves existing configuration untouched. Save/double-click,
lost response and retry must produce truthful results without duplicated changes.
A file/status-write failure must not create a false claim of an unchanged or
working setup; implement preservation or explicit recoverable state.

### CON-04 — bCourses work and course selection

Settings controls selected courses and connection management. Keep assignments,
Add, Dismiss/Restore and changed-deadline decisions reachable in a work view.
Refresh is manual at the reviewed baseline. Followed courses determine fetched
content, not automatic task creation. Only Add creates a local task in its course
project. Repeat Add preserves the same task identity.

Keep Upcoming, No due date, Past due, Added and Dismissed distinctions; preserve
source links. A provider due-date change uses Use new due date / Keep mine and
never silently overwrites planning or local edits. Course deselection/token removal
does not delete imported tasks or history. Opening Settings does not import work.

### CON-05 — Google client-file setup

Flow: choose a Desktop-app client JSON file → validate size/type/Google addresses
→ save → Setup ready → Continue with Google. File-format validation is not Google
account consent, working APIs or verified permissions. Explain this distinction
in the result, without exposing saved file contents, IDs, secret fragments or tokens.
Invalid replacement leaves existing setup usable. Fresh setup or a different
OAuth client needs sign-in; replacing the same client preserves an existing usable
sign-in rather than forcing sign-out. Preserve any prior reconnect/error state
unless newly verified. Disclose sign-in consequences before applying. Coordinate file,
local-token and displayed-status changes so disk failure has an accurate recovery.
Keep local filesystem location in optional help.

### CON-06 — Google authorization lifecycle

Show the connection scope summary before opening the system browser. The app
opens Google authorization with the existing local callback/PKCE flow. Include
Waiting for sign-in, an Open sign-in link fallback, return instructions, provider
denial, timeout, missing permissions and retry. A link must not expose tokens or
retain transient authorization details in durable evidence.

Dismissing an app setup/status popup is different from cancelling authorization.
If Cancel sign-in is offered, invalidate pending attempts/late callbacks before
claiming cancellation. A previous unsuccessful attempt must not overwrite a newer
one. Disconnect or replacement must coordinate with in-flight authorization.
Google consent remains in the system browser, not an app-owned password form.

### CON-07 — Three Google functions and their relationship

| Function | Direction / scope | Working surface |
| --- | --- | --- |
| Calendars to show | Read selected personal calendars; never modify them | Events beside Plan days; explicit Add as task. |
| BearPlans calendar | Publish timed placements to BearPlans' own calendar using current estimates/reminder policy | Optional planned start time; current reminder is 30 minutes before. |
| Google Tasks | All local projects/tasks/subtasks → BearPlans-created lists; Google completion → same local leaf; other Google edits replaced | Work remains editable in Plan/Projects. |

Calendar selection controls reading only. It does not select which local tasks
are exported. A bCourses assignment added as a task is ordinary local work and
therefore participates in Google Tasks sync. Explain this before first Google
consent. Connected operation creates remote task/event copies; do not describe all
content as remaining only on the Mac. Preserve current owned-resource boundaries,
leaf/parent completion rules and explicit event/assignment Add identity.

A combined Google sync has several provider operations, not a provider-wide atomic
transaction. Failure may follow successful writes; show Retry/last success without
claiming everything rolled back. Never create duplicate tasks/events on recovery.

### CON-08 — Confirmed Pause / Resume and proposed detailed semantics

Include Pause / Resume automatic Google sync. Proposed behavior for implementation
scoping: cover periodic, post-edit, launch/reconnect and other automatic triggers
for all three functions. Save preference durably; restart does not silently resume.
Keep credentials, local tasks, cached sources and Google copies. Local work remains
available. Do not confuse this control with pausing a countdown session.

An undisclosed fetch triggered by mounting/reopening Settings, including an empty
calendar-cache refresh, is automatic work too and must respect Pause. Explicitly
requested picker refresh is distinct one-time work.

If work is in flight, show Pausing… Finishing the current sync. Acknowledge Paused
only when no new automatic operation can begin; do not promise rollback of provider
writes already completed. Explicit Sync once may run while staying paused. Any
other action that contacts a provider while paused (calendar-list refresh or Save
calendars) must disclose its one-time work or save selection locally for later;
never silently turn automation on. Resume reconciles the current state rather than
replaying every paused edit. Clarify these proposed details when scoping the build.

### CON-09 — Replacement, Disconnect and retained data

Separate actions and consequences: replace bCourses token, replace Google setup
file, disconnect Google sign-in, remove a setup credential, and delete cached/remote
content. Only the first four belong in this connection scope. Keep local tasks,
session/closed history and remote copies unless separate explicit deletion is
scoped. Credential removal does not erase the task created from a source.

Coordinate Disconnect/replacement with the sync operation and pending browser
callbacks before reporting completion. Reviewed Disconnect removes the local Google
token/access cache; provider revocation is a separate missing capability at the
source baseline. Do not label local sign-out as verified Google revocation. If
revocation is later implemented, report offline/failed revocation accurately.

### CON-10 — Reconnect and account identity

Keep one account per connection in this scope; no seamless Switch account feature.
Do not display invented account identity. A reconnect can still choose a different
Google account in the browser: verify identity or stop before using previous-account
resource mappings. Preserve existing local work; do not reuse another account's
calendar/task IDs or silently clear its cache. Define/test safe same-account
reconnect and different-account recovery before shipping those controls.

### CON-11 — Navigation, layout and accessibility

Proposed entry: a small gear in the existing compact top navigation. Settings →
Connections shows two compact provider panels; Manage reveals detail; setup uses
a focused dialog/sheet. Secondary explanations stay on demand while errors,
required decisions and action consequences remain visible. Reuse existing tokens,
editable components and Light/Dark styles, not oversized credential forms.

Preserve Today-first opening, the prior Plan/week/day/task/scroll state and the
same active countdown when returning. Opening/closing Settings never mutates work;
legitimate Google completion remains a separate sync operation. Keep dialogs
keyboard reachable, labelled, focus-contained with focus restored; errors must be
associated with fields and status announced. Escape/outside dismissal must have
truthful cancellation semantics and cannot silently apply changes.

Design reference widths: 640×800, 800×900 and 1440×900, Light and Dark, long names
and scroll cases. These references are not the Mac's actual window size or browser
200% zoom proof. Runtime verification must include actual zoom/reflow, keyboard,
focus/busy/error states and an assistive-technology check.

### CON-12 — Privacy, evidence and handoff

Use synthetic fixtures in Figma/tests. Never use real token/file contents in
screenshots, logs, API responses, Git, localStorage/sessionStorage or database
backups. Keep credentials in the existing owner-only data-folder mechanism.
Do not add Assistant tools for connection setup or let source content authorize
settings changes. Keep loopback/same-origin protection and the shared domain rules.

Record actual OS, source/diff boundary, commands/results/skips, dimensions/themes,
node IDs and limitations. A screen spec is not a built screen; an installed-reaction
model is not a user walkthrough; a fixture pass is not live provider/hardware
acceptance. Full core-trial/release gates remain separate. Store actual status only
in PROGRESS and finished records in COMPLETED.
