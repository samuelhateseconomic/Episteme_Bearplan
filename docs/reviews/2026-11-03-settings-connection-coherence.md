# Local Settings / Connections coherence review

Date: November 3, 2026, America/Los_Angeles. Environment: Darwin/macOS arm64.
Scope: source-backed UX review and plan amendment, not implementation or a live
connection test. Codex reviewed with independent connection-runtime and UX-flow
agents. No Figma reads/writes, credentials, user data or provider APIs were used.

## Outcome

**Pass with follow-ups for the plan/coherence review.** One Settings → Connections
page fits the local app. The initial proposal needs explicit setup/authorization,
local runtime, truthful status, Pause and recovery contracts before prototype work.
This does not certify either connection or the new Settings UI at runtime.

User explicitly confirmed Pause / Resume automatic Google sync. The bCourses
review-list location is unanswered. Preserve a dedicated work view as a reversible
proposal. Other Pause details remain proposed, not confirmed user requirements.

## Source boundary and findings

Reviewed committed baseline f375f24, including new credential relocation, current
Google/bCourses UI/routes, Google auth/sync worker, source models and plans. During
the review, another process added uncommitted setup routes and credential helpers;
read their complete relevant diff and new route file. They were not executed or
accepted on the strength of this inspection. Preserve that work.

| Finding | Evidence | Plan implication |
| --- | --- | --- |
| Credentials already moved outside code | f375f24; backend/platform/secrets.py, AGENTS.md | Correct the earlier discussion's proposed/not-started relocation claim. Default Mac path is app data/secrets; custom data-dir/environment overrides remain. |
| Google has three combined functions | frontend/src/Google.tsx; backend/domain/google_tasks.py sync | Describe calendar reads, BearPlans-calendar writes and Google Tasks. All tasks, including added bCourses tasks, participate; calendar selections affect reading only. |
| Automatic sync belongs to the local service | backend/app.py lifespan; google_tasks.py GoogleSyncService; launch.py service.wait | No hosted service needed. Sync while service runs/Mac awake/online; closing browser tab does not stop it. |
| Token presence is not verified access | google.py configured/connected; routes/google.py GoogleState | Separate setup ready, signed-in, working last checked, failure and stale data. |
| Google Desktop file is not account authorization | google.py client parsing/start_sign_in | Setup file → system browser OAuth → return, with waiting, denial/timeout/retry. |
| Pause is not implemented | GoogleSyncService, current Google routes/state | Add durable pause contract across all automatic triggers; proposed one-shot and in-flight semantics are explicit. |
| Disconnect lacks revocation and pending/in-flight coordination | google.py disconnect and token write in sign-in callback | Do not claim immediate cancellation/revocation. Late callbacks and worker writes need engineering guards/tests. |
| No account identity/mapping namespace | migrations 17–19 and GoogleState | No seamless account switch; reconnect must not reuse previous-account mappings unsafely. |
| bCourses is read-only/manual, with task review | BCourses.tsx; domain/bcourses.py and routes | Course choices belong in Settings; assignment Add/deadline decisions remain a reachable work surface. No invented bCourses autosync. |
| Current source is evolving | uncommitted routes/connections.py, platform helpers and app mount | Credential save/check/remove is in-progress source, not wholly absent; no setup frontend or passing evidence inferred. |

The new in-flight Google replacement route calls Disconnect for a different client
before writing the replacement file. A disk error can therefore remove the old
connection despite a failed replacement. Record an engineering recovery requirement
before showing copy that promises the previous connection always survives a failed
save. This is a source finding, not a reproduced runtime failure.

Current explicit Disconnect only clears the memory access cache and local token.
It does not invalidate a pending callback, which may later write a token, nor wait
for the sync lock. These are source-level race concerns requiring targeted tests.
Do not silently weaken the plan's desired outcome or present untested fixes as done.

## Changes to design plan

Added [canonical UX plan section 6](../../frontend/BEARPLANS_UX_PLAN.md#6-local-settings-and-connections-extension):
confirmed versus proposed direction, capability map, status/credential lifecycle,
Pause semantics, six manageable tickets UX-C01–C06, responsive/theme review targets
and eight future verification scenarios. Narrowed the original scope exclusion to
integration implementation; this design extension does not authorize application
code or provider requests. UX-C01 is the completed review; no Figma construction
started and the prior repair/handoff acceptance is unchanged.

The original 89-product/46-reference frame handoff contains no connection extension.
No live canvas inspection or revised frame-count claim was made. New screens must
reuse the existing editable system and flow canvas, with exact returned IDs.

## External reference

Google's [Desktop OAuth documentation](https://developers.google.com/identity/protocols/oauth2/native-app)
confirms system-browser authorization and a local redirect. This supports the
local flow without a hosted BearPlans account/server. The current implementation
already uses a loopback callback and PKCE. File validation alone cannot certify
Google consent, granted scopes or enabled APIs.

## Checks and limits

Read-only source/diff/plan review on macOS, including two independent reviews.
After authoring, Python content/relative-link/whitespace checks passed for all
four touched documents; six unique UX-C01–C06 definitions and confirmed/proposed
scope checks passed. `git diff --check -- frontend/BEARPLANS_UX_PLAN.md
docs/PROGRESS.md docs/COMPLETED.md` passed. Independent final document review found
no blocking issue; clarified that opening Settings itself does not change task
completion while legitimate provider completion still applies through sync. No app tests, live sign-in/sync, credential migration,
Figma render or user walkthrough ran for this documentation-only change. Existing
reported test totals in the concurrent commit are historical, not rerun here.

Next concrete step: obtain the pending bCourses work-view preference, then scope
UX-C02. Building the Settings prototype or application is not started by this review.
