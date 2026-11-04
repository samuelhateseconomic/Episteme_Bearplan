# UX-C04 — Google setup and browser authorization

November 4, 2026. Codex was the single Figma writer and source/visual/model reviewer.
User authorization: “continue” after publication of the prior session checkpoint.
Scope: Figma construction and design evidence only. No app, provider, credential,
service, database, dependency or core-trial copy changed.

**Outcome: Pass with follow-ups for construction and installed-action models.**
Actual Figma preview, user acceptance, keyboard/focus, assistive technology,
responsive/Dark and live Google checks remain pending. This is not runtime acceptance.
Acceptance definition: UX-C04 and FIG-03 in the
[execution plan](../../frontend/plans/settings-connections/EXECUTION_PLAN.md) and
[test plan](../../frontend/plans/settings-connections/TEST_PLAN.md).

## Delivered design

[File setup section](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=251-6374),
[browser section](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=251-6375),
[calendar/account section](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=251-6376).
[Review guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=255-6835&starting-point-node-id=255%3A6835&scaling=min-zoom)
has 22 isolated sample starts. Each guide entry restores only five Google demo
variables. The browser-boundary reference links to that guide for simulated outcomes.
It never opens a real Google URL or collects a password.

47 editable 540px dialog/reference states plus an 800×778 review guide. Three
horizontal flow groups extend the existing free canvas; no new file or page.
Current IDs and exact dimensions are in the
[inventory](../../frontend/design/settings-connections/google/inventory.json).
Historical construction bounds are retained separately from its current inventory.

- Choose/review a fixed sample Desktop client file; same-client replacement,
  different-client consequence review and retained reconnect error.
- Wrong client type, malformed/wrong-address file, oversized file, pre-write
  failure and uncertain-save recovery. Saved contents and IDs remain hidden.
- Setup-ready remains sign-in-needed. Before consent, disclose calendar reads,
  publishing timed plans with the current 30-minute reminder and export of every
  project/task/subtask, including tasks added from bCourses. Calendar selection
  affects reads only. State that copies leave the Mac for Google.
- Waiting, browser fallback, dismissal/re-entry, reviewed restart, denial,
  five-minute timeout, missing permissions, revoked/expired access and retry.
- Four calendar-selection combinations for Personal/Classes, draft Cancel,
  save/re-entry, empty list, load failure and saved-selection/event-read failure.
- Separate authorization, first combined sync and partial failure. Explicit
  different-account review preserves local work and remote copies; adoption
  resets synthetic calendar choices and does not claim a completed sync.

Existing Google setup Connect and working Sign-in & calendars now enter the flow.
Working overview/Google summaries bind to the synthetic status/evidence variables.
Close returns to Google management; Back to work retains the existing overlay-close
route. Direct guide/reference starts do not establish preservation of an original
Plan background. Pause/Sync once effects in the old overview remain C05 references.

## Source reconciliation and engineering boundaries

Reviewed committed baseline `a43a456` beneath documentation commits `e4e7804` /
`4544f74`, plus the relevant unfinished Google account-isolation diff. Source reads:
`backend/routes/connections.py`, `backend/platform/google.py`,
`backend/routes/google.py`, `backend/domain/google_account.py`,
`backend/domain/google_reading.py` and `frontend/src/Google.tsx`.
No saved secrets or personal data were read.

1. Client-file parsing checks Desktop format, bounded size and Google addresses;
   it does not authorize an account. Same-client saves preserve sign-in; a different
   client is written before old sign-in is disconnected. A later disconnect/status
   failure can follow a saved file. The uncertain state therefore never promises
   that nothing changed. Check status shows that setup exists without identifying
   which client was saved; Save again is the explicit replacement path.
2. Source starts loopback/PKCE authorization, expires attempts after 300 seconds
   and invalidates older generations on restart/disconnect. No cancel-only route
   exists. The design offers Close/Back and reviewed Start again, not a misleading
   Cancel sign-in that would secretly disconnect an existing connection. The pending
   attempt survives dismissal. Late-callback behavior is a runtime test obligation,
   not proved by the finite prototype.
3. Source sign-in can enable automatic sync before calendar selection. The scope
   disclosure and signed-in result make that clear. Presence-based `connected` or
   broad `working` status is not a successful combined-sync receipt.
4. Saving followed calendars commits selection before reading events. Recovery
   says choices saved and retries the event read; it does not resubmit selection.
   Combined sync can partially write to Google. Retry does not imply provider-wide
   rollback; duplicate prevention needs application tests.
5. Unfinished account code compares a hashed primary-calendar identity and offers
   reviewed adoption that clears local provider links/caches, retaining local work
   and remote copies. It was inspected, not altered, tested or certified here.
   No fabricated account email or seamless switching is shown. Before shipping,
   revalidate identity-unavailable/race/reconnect behavior and the current diff.
6. Existing UI automatically refreshes an empty calendar cache and does not yet
   reflect every Pause rule. Pause/recovery and provider-trigger reconciliation
   remain UX-C05 and later authorized application work.

## Actual checks and repairs

Environment: macOS 26.6.2, Darwin 25.6.0 arm64. Session
`5d94b33e-2248-4cee-a5ff-d6427a1d518b`, page `2:5`.

- Code Connect search found no repository mappings. No subscribed Figma libraries;
  scoped file searches returned no matching composites/assets. Reused local Button
  variants, checked/unchecked Checkbox and connection-option instances, existing
  semantic color/spacing/radius variables and the five Connections text styles.
- Typography: Inter Regular/Medium/Semi Bold, the existing documented fallback
  after unavailable/missing SF Pro. No new font-default decision or broad migration.
- Final [structural audit](../../frontend/design/settings-connections/google/audit.json):
  606 nodes including the guide (132 Frame, 338 Text, 132 Instance, 4 Vector),
  zero raster UI, missing/wrong fonts, overflow or normal-flow overlaps. All 47
  references belong to their intended sections. All 99 Navigation headers still
  have one Settings gear.
- Five isolated variables; all eight existing full-demo resets include each once
  and retain all six bCourses reset assignments. New journey actions write only
  the five Google variables, with no real provider URL action. Existing task,
  timer and history variables are not changed by Google journey actions.
- [59/59 installed-action models](../../frontend/design/settings-connections/google/models.json)
  pass in aggregate. Initial 46/49 exposed calendar Classes/None and post-adoption
  re-entry failures. Figma normalized a multi-branch conditional into if/else;
  nested conditionals were rejected safely. Mutually exclusive flat conditions
  repair all four calendar and ten connection-state routes. Nineteen affected/new
  checks were then rerun successfully; unchanged earlier passing cases retain
  their evidence. These are in-memory evaluations of read-back reactions, not
  clicks in actual preview or a real browser.
- Reusable routing check: `node frontend/design/settings-connections/google/routing-model-check.js`
  evaluates 19 affected models against saved installed evidence. Archived
  construction/wiring/repair scripts are execution records, not rerunnable tools.
- Visual inspection found raw black fallback fills, fixed-width labels, overlapping
  browser-boundary actions and three references outside their sections. Resolved
  Light fallback paint values, hugging labels, a stacked boundary action row and
  explicit section placement repaired these. Final four Light renders were inspected:
  [file](../../frontend/design/settings-connections/google/file-light.png),
  [browser](../../frontend/design/settings-connections/google/auth-light.png),
  [calendar/account](../../frontend/design/settings-connections/google/cal-light.png),
  [guide](../../frontend/design/settings-connections/google/guide-light.png).
  No unchanged screenshots were repeated after the final relevant repairs.

Documentation/JSON/local-link/diff checks accompany the handoff. No application
suite was rerun for this design-only unit. The agent had no browser/computer-control
capability to run actual preview or accessibility checks. 640×800, full 800×900 /
1440×900 context, Dark and browser 200% reflow remain C06 checks; a 540px dialog
render is not evidence for those windows. No native picker, real OAuth, persisted
setting, provider write, race, restart or hardware acceptance is certified.

## Handoff validation commands and results

- `node frontend/design/settings-connections/google/routing-model-check.js`:
  **19 passed, 0 failed** on Node 24.21.0. The first invocation failed because
  the initial helper used CommonJS inside the frontend ES-module package; changed
  only that helper to imports / `import.meta.url`, then reran successfully.
- Python content/link/evidence check: **287 existing local links**, four JSON
  files parsed, four PNG headers/dimensions valid, 47-state/606-node/126-source/
  59-model counts consistent, no credential markers or transient asset URLs.
- Node `AsyncFunction` syntax checks: **three archived scripts passed**, none
  executed. The standalone model checker executes only saved reaction data.
- `git diff --check -- docs/PROGRESS.md docs/COMPLETED.md frontend/FIGMA_PROTOTYPE.md frontend/design/figma-node-ledger.json`:
  **Pass**. Reviewed the scoped documentation/ledger diff and relevant untracked
  Google evidence. Existing unfinished backend/CLAUDE changes and duplicate files
  were preserved. No commit or push performed for UX-C04.

## Next concrete step

UX-C05: Pause/Resume, pausing acknowledgement, one-shot sync, offline/partial-failure,
disconnect/revocation and removal consequences, using current source. Not started.
UX-C06 then covers integrated preview/user review, widths/themes and handoff.
No application build, commit or push is implied by this design continuation.
