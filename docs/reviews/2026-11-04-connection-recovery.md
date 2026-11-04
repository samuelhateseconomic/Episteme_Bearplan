# UX-C05 — Pause, offline and connection recovery

November 4, 2026. Authorization: user “continue” after local checkpoint `96c0910`.
Codex was the sole Figma writer and source/visual/model reviewer; no independent
agent review was performed. Scope: Figma and design documentation only. No app
code, credentials, provider, service, database, dependency or core-trial copy changed.
Unfinished backend/account/CLAUDE work and duplicate files were preserved.

**Outcome: Pass with follow-ups for construction and installed-action models.**
The user reported the main Pause → Sync once → Resume walkthrough clear and
accepted its intended behavior. This is bounded user-report evidence, not observed
runtime, restart or provider verification. Remaining error/removal walkthroughs,
keyboard/focus, assistive technology, responsive/Dark and app checks remain open.
Acceptance comes from UX-C05 / FIG-04 in the [execution plan](../../frontend/plans/settings-connections/EXECUTION_PLAN.md)
and [test plan](../../frontend/plans/settings-connections/TEST_PLAN.md).

## Result and intended contract

[Review guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=270-6806&starting-point-node-id=270%3A6806&scaling=min-zoom)
contains 19 isolated sample starts. Three horizontal groups extend the existing
free canvas: [Pause/one-time sync](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=269-6534),
[offline/disconnect](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=269-6535)
and [setup/token removal](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=269-6536).
36 editable 540px Light dialogs/references plus an 800×738 guide. The
[inventory](../../frontend/design/settings-connections/recovery/inventory.json)
holds exact IDs and final dimensions. Existing canvas/page/node IDs remain.

- Pause request → Pausing → simulated acknowledgement → Paused. Resume receipt
  enables automation without inventing a new successful sync. Failed preference
  writes and unknown post-request results have separate recovery.
- Sync once discloses calendar reads, timed-plan publishing and all-task export,
  including added bCourses work. Cancel changes no sample state. Completion or
  failure keeps the chosen automatic preference; only complete success advances
  the last complete-success time.
- Paused + offline, enabled + partial failure, one-time partial/offline failures
  retain previous evidence/cache and explain that earlier remote writes can remain.
- Disconnect requires review, separates pending/local-failure/unknown states, and
  reports local sign-out separately from confirmed or unconfirmed Google revocation.
  Keep setup, local work/history, cache and remote copies. Reconnect uses C04 consent.
- Removing the Google setup file also disconnects locally. Partial removal can
  leave the setup file while the token is gone; the sample status check says so.
  This route cannot report Google revocation because its source response omits it.
- bCourses token removal is local only. Courses/cache/added tasks remain; no remote
  revocation is implied. Google can still sync previously added bCourses tasks.
- Working Settings Pause/Sync once/Remove token now enter these flows. C04 Google
  connection has Sync & access. Pending or uncertain operation guards block a
  conflicting policy/one-shot/sign-in/token-removal command in this finite demo.
- Four isolated recovery variables are included once in each of eight full resets;
  five Google and six bCourses assignments are retained. C04 examples reset Google
  policy/command/operation too. bCourses summary metadata updates on remove/save;
  its course-scope description no longer falsely asserts a saved token after removal.

Confirmed before this unit: Pause/Resume keeps connection and saved data.
Newly confirmed on November 4: **Pause persists after restart; explicit Sync once
keeps automation paused.** Remaining proposed details: covering every automatic
trigger, finishing active work before acknowledging Pause, and reconciling current
records on Resume. The proposed UI covers these explicitly; it does not implement
or certify them. Settings never starts, pauses, finishes or credits a countdown.

## Source reconciliation and open engineering issues

Read current `backend/routes/google.py`, `backend/domain/google_tasks.py`,
`backend/platform/google.py`, `backend/routes/connections.py`, and the relevant
unfinished diff. Source baseline is committed `a43a456` beneath design checkpoint
`96c0910`, with uncommitted account-isolation changes. These are source findings,
not fresh runtime tests or a reason to duplicate existing implementation.

1. **Acknowledgement/serialization gap:** `google_pause` saves the durable flag,
   then calls `GoogleSync.while_idle`. That helper calls its action even if its
   30-second lock acquisition times out. A long sync can still run when Pause
   returns, and Disconnect/adoption may run without owning the lock. APP-C04/C02
   must fix and barrier-test this before claiming the shown acknowledgement or
   safe credential/account serialization. No backend fix was authorized here.
2. Worker automatic calls check Pause under the sync lock; explicit `sync_now`
   bypasses the flag. UI-mounted calendar reads and other direct reader routes need
   the agreed automatic-versus-explicit boundary. Current `Google.tsx` can fetch
   an empty cache on mount. No Figma flow proves all automatic triggers are gated.
3. Resume clears the flag and nudges the worker; that receipt is not a successful
   combined sync. Complete-sync evidence, policy, offline/error and authorization
   must remain independent dimensions in the future UI/API.
4. Disconnect invalidates OAuth generations, clears access/local token, then attempts
   Google revocation. Revocation can be true/false/absent; local unlink failure or
   lost responses need truthful recovery. Setup-file deletion discards the revoke
   result; bCourses removal is local only. Status update can fail after deletion,
   so an error must not universally promise the old credential was retained.
5. C04 same/different-client review, pending callback and account-isolation rules
   remain. Late callbacks, concurrent requests, restart, atomic credential writes,
   duplicate prevention and real identity safeguards need application tests.

## Verification and repairs

Environment: actual **macOS 26.6.2 / Darwin arm64**, Node 24.21.0. Reused Inter
Regular/Medium/Semi Bold as the existing documented Figma fallback for unavailable
SF Pro, existing Buttons, text styles, surface/text/error/border/space/radius tokens.
No new visual foundation or app dependency was introduced.

- Read-back audit: 37 new scoped frames/guide, **467 nodes** (94 FRAME, 269 TEXT,
  104 INSTANCE). Nine changed existing layouts also audited. Zero raster UI,
  missing/wrong fonts, overflow or normal-flow overlap findings.
- **145 installed reaction sources** captured in full plus **eight reset summaries**.
  `node frontend/design/settings-connections/recovery/check-models.mjs`:
  **58 passed, 0 failed**. Covers request/receipt separation, both policy modes,
  Cancel/no-op, error/unknown checks, pending-command guards, local versus provider
  removal results, help Back, bCourses replacement metadata, no task/timer/history/
  reward/calendar-choice writes by new controls, and reset preservation.
- Five final Light renders inspected: three 2580px-wide flow sections, 800×738
  guide and 540px C04 Google controls. Screenshot exports include section margins.
  These are composition references, not tested application window/breakpoint sizes.
- Initial compact-read request exceeded the Figma 48KB limit; narrowed output and
  retried. Initial wiring used an AND expression with three operands, rejected by
  the validator with safe rollback. Changed to nested binary AND and reran.
- Visual review found shared default policy labels contradictory on paused canvas
  references; replaced those reference labels with fixed matching text. Action
  review found help Back assigning sign-out/setup state; changed it to non-mutating
  Back. Added pending-operation guards and truthful bCourses metadata. Models and
  affected renders passed afterwards. Old evidence files remain historical.

Inventory, [installed actions](../../frontend/design/settings-connections/recovery/sources.json),
[audit](../../frontend/design/settings-connections/recovery/audit.json),
[models](../../frontend/design/settings-connections/recovery/models.json), final
renders and execution records are in `frontend/design/settings-connections/recovery/`.
`*-executed.js` and `repairs.json` are historical execution evidence: **do not replay**.
The pure model checker is safe to rerun; it makes no Figma/provider writes.
Documentation/evidence check: 303 local Markdown links resolved; seven new JSON
files parsed; five PNG headers/dimensions matched; 36/58/145+8 counts agreed; no
transient asset URLs or token markers. Two archived scripts and four repair calls
syntax-checked with AsyncFunction without execution. `git diff --check` passed.
No app test suite was rerun for this design/docs-only unit.

## Bounded user report and remaining evidence

Guide `270:6806` opened in the embedded Figma view. Prompt:

> I’ve opened the Pause & recovery guide. Try “Pause → sync once → Resume”: pause,
> sync once, then resume. Does it clearly keep automatic sync paused during the
> one-time sync, and is that the behaviour you want? This is a fixed simulation;
> the proposed pause also persists after restarting the app.

User answer: **“Clear; this behaviour works for me”**.
No agent-observed steps, timing, actual window, zoom or restart was reported.
The narrow main-flow report does not accept all error/removal examples.

Busy examples use fixed 2.5-second simulated responses. Closing their overlay does
not cancel the simulated intent; it pauses that reference transition until reopened.
No native file picker, browser authorization, scheduler, storage, provider call,
restart or real clock runs. Direct guide starts lack an original Plan background;
Back to work there cannot prove prior day/task/scroll or active-session preservation.
Unknown-result checks choose one disclosed fixed observation; they do not inspect
real files. Shared variable-bound one-time references show default policy on the
editing canvas, and the selected policy in the finite preview.

Next eligible unit: **UX-C06**, not started: review full 640×800/800×900/1440×900
Light/Dark contexts, long content/scroll, actual preview and remaining provider
walkthroughs; reconcile final handoff. Keyboard/focus, assistive technology, 200%
zoom, all-trigger Pause/restart/race/provider checks and original core/hardware/
release gates remain separately open. Current source gaps above must travel into
any separately authorized application slice.
