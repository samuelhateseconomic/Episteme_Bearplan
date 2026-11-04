# BearPlans — progress (in progress)

Read [AGENTS.md](../AGENTS.md) first; Claude also reads [CLAUDE.md](../CLAUDE.md).
This file holds **only current state**: what is active, what is next, open
follow-ups, pending manual gates and decisions waiting on the user. Finished work
is recorded in [COMPLETED.md](COMPLETED.md), newest first; detailed evidence stays
in the linked reviews.

**How to update.** When an item here finishes, add a dated entry at the top of
`COMPLETED.md` (checks, files/commits, review link), then remove or shorten the
item here and update [Build status](#build-status). Keep this file short; do not
paste long check logs here.

## Current state — November 4, 2026

**UX repair/handoff delivered: 24/24 repair subtickets Done.** R23 passed with
follow-ups for the bounded user-reported walkthrough; R24 passed with follow-ups
for the reconciled implementation handoff. Settings overview UX-C02 and bCourses flow UX-C03 are delivered with follow-ups
under the user’s November 3 requests. UX-C04 Google setup/browser flow is delivered
with follow-ups under the November 4 “continue” request. UX-C05 Pause/offline/removal
flow is delivered with follow-ups; the user reported its main flow clear. No unit is active;
application delivery remains a later unit. Original UX-01–36 checkpoint
acceptance remains distinct from this repair subset.

**Start here:** [refined UX handoff](../frontend/BEARPLANS_UX_HANDOFF.md),
[exact inventory](../frontend/design/handoff-inventory.json),
[free editing canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=2-5),
[reset launcher](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&starting-point-node-id=141%3A7346),
[canvas handoff notes](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=22-85).
Live reconciliation resolved all 89 product/state frames and 46 reference frames;
launcher is separate, with 11 starts total. Original IDs/free canvas preserved.

**Review evidence:** [R23 reports/repairs](reviews/2026-11-03-ux-r23-continuation.md),
[R24 handoff review](reviews/2026-11-03-ux-r24-handoff.md),
[independent R22 assessment](reviews/2026-11-02-ux-r22-static-review.md).
Latest installed-reaction model: 111/111 pass, Reset covers 206 variables. Earlier
44 time and 601 navigation models remain historical. Static score 87.98/100 is
heuristic, not measured task success; no new score was inferred from user reports.
The preview-cancel finding was repaired/rechecked; user reports then accepted
carryover, frozen Missed, active-session completion, interruption review, Stats,
Assistant cancel/error retention and static validation. Exact cause of the initial
early-closure report was not reproduced independently and remains in its evidence.

**Remaining boundaries:** keyboard/focus, assistive technology, arbitrary drag,
actual text reflow/breakpoint behavior, general task editing, real storage/timing,
optional full reward/correction tours and original checkpoint/hardware/core-trial
acceptance are not certified. User reports were not timed or agent-observed; actual
window/zoom was not reported. Reference controls and fixed simulations remain
bounded as detailed in the handoff. The agent had no working browser/computer
control. Application/core-trial copies, service and database were not changed.

**Next eligible design-related work:** UX-C06 Settings context/theme and remaining
walkthrough/handoff review. Separately scope app implementation when requested,
first resolving the proposed measurement/breakpoint/fallback/Earlier/
cross-month decisions below. Do not automatically start a build. Preserve newer
M5/M6 capabilities, including concurrent Google/calendar work omitted by this
prototype. Legacy provider ordering elsewhere in this record was not re-audited
by the design handoff; reconcile it against current Git before any provider work.

**Session checkpoint:** `e4e7804` and the 11 earlier commits were pushed to
`origin/main` on November 4 after the user explicitly approved all 12 commits.
The ordinary push advanced the remote from `c4a5d14` to `e4e7804`; earlier approval
rejections are resolved. Uncommitted backend/CLAUDE edits and duplicate files remain
excluded and untouched. Original checkpoint checks passed: 63-file staged scope,
59 inspected evidence/guidance files, 134 local links, JSON/PNG consistency,
ten archived-script syntax checks and scoped diff whitespace. No application
changes or new acceptance evidence were added by publishing the checkpoint.

Earlier design baseline commit: `23faa2d`. November 3 refinements, handoff, frontend
connection plans/skills and UX-C02/C03 evidence form the user-authorized design
checkpoint. Commit/push results are recorded in Git. Concurrent unfinished backend
work, CLAUDE.md edits and untracked `(1)` copies remain outside this checkpoint. Detailed finished items are in
[COMPLETED](COMPLETED.md), rather than parallel mutable design trackers.

- **M5 assistant:** actions through router → grounding → library → gate → Apply,
  replay and Undo; orchestrator with direct answers and plan/tasks/time
  specialists; 30-case evaluation **Pass** with qwen3:8b (runs 4–5: 30/30,
  routing 100%, 0 unauthorized changes; reruns 6–8 after later fixes also pass). See the
  [actions review](reviews/2026-11-01-assistant-actions.md) and
  [evaluation](reviews/2026-11-01-m5-evaluation.md). Last recorded: pytest 863
  passed, 1 Windows-only skip; Vitest 145.
- **Frontend redesign:** bounded repaired prototype and handoff delivered; full original checkpoint/runtime acceptance remains open
  ([UX register](#ux-delivery-register)).
- **M4 core trial:** candidate recorded; actual seven-day trial not reported.

## Next up

1. **Settings UX-C02–C05 delivered with follow-ups.** Latest [recovery review](reviews/2026-11-04-connection-recovery.md): 36 compact Light states, 19 starts, 58/58 installed-action models; main Pause → Sync once → Resume user report accepted. Restart persistence and one-shot keeping Pause are confirmed intent, not runtime evidence. Next eligible design unit: UX-C06, not started — full-width/theme contexts and remaining walkthrough/accessibility/handoff checks. App implementation stays separately scoped. Existing core/hardware gates remain open.
2. **User hands-on review of the Assistant in the app preview** (pending).
   **Connection setup baseline:** credential relocation is committed in f375f24
   and write-only setup routes in 674db93. Current source continues to advance;
   these are source observations, not a fresh runtime certification by design.
   **Settings plan/agent package delivered:** [frontend plan index](../frontend/plans/README.md),
   [connection entrypoint](../frontend/plans/settings-connections/README.md),
   [spec](../frontend/plans/settings-connections/SPEC.md),
   [steps](../frontend/plans/settings-connections/EXECUTION_PLAN.md),
   [54-case test plan](../frontend/plans/settings-connections/TEST_PLAN.md) and
   [frontend AGENTS](../frontend/AGENTS.md) with linked design/build skills.
   [Package review](reviews/2026-11-03-frontend-connections-agent-package.md).
   User confirmed Pause / Resume automatic Google sync, restart persistence and
   one-shot sync keeping automation paused; remaining trigger/acknowledgement/Resume
   details remain proposed. bCourses review placement remains unanswered; the dedicated-view
   recommendation did not block the overview. The original documentation request started
   no execution; the later “go for the first work” request delivered UX-C02. Next
   eligible design unit is UX-C06; application slices remain separately scoped.
3. Then, each only when the user authorizes it, in this order
   ([build plan §8–9](../BearPlans_Build_Plan.md#assistant-architecture-orchestrator-and-specialists-user-approved-direction-2026-11-01)):
   (4) M6 Google Calendar → (5) bCourses access spike → (6) Canvas (bCourses) →
   (7) Gmail. CalCentral only after an access investigation; MCP only behind a
   vetted adapter boundary. Roadmap steps 1–3 are done (see COMPLETED.md).
   **bCourses connection committed (`422081e`, 2026-11-01; user moved it before
   Google Calendar):** direct read-only API (MCP vetted and not used), token now
   in data-folder `secrets/bearplans.secrets.env` (f375f24), course picker, review list, Add
   to a course project, due-date change review. Migration 15 → 16. Waiting on
   the user's hands-on check.
   [Review](reviews/2026-11-01-bcourses-connection.md).

## Open follow-ups

- End Week carryover defaults + Stats "Missed" committed (`1656600`). Assistant
  carryover command with Undo committed (`81f5922`)
  ([review](reviews/2026-11-01-end-week-carryover.md#assistant-carryover-command)).
  **Migrations 14 → 16** ran on the real data at the user's launch on 2026-11-01 23:26
  (backup `backups/pre-upgrade-v13-20261101T232614-….sqlite3`). Needs the user's hands-on check.
  R13–R15/R21 reflect these rules; the bounded R23 prototype walkthrough was reported successful. App hands-on verification remains separate.
- M5: no applied-action history view (receipts persist; in-page only).
- M5: daily assistant writes not certified until the user's UI review.
- Organization: agree a compact frontend/backend/shared-tests ownership and
  documentation map, then add focused subsystem entrypoints (requested, not started).
- Codex's project registration still names the old nested folder; the user must
  reopen/select `/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan`.

## Pending manual gates

- **M4 local-core trial:** run the [trial guide](CORE_TRIAL_CHECKLIST.md) against
  `/Users/hiberkeley/Desktop/BearPlans-core-trial-2026-11-01`; report actual Day 1
  (date, data path, baseline backup result, real work used), then seven days of
  notes and a closing review. Full M4 release is pending this.
- **Standby type 5:** unexercised/unverified; no supported trigger established
  under the reviewed ARM64 policy
  ([assessment](reviews/2026-11-01-standby5-capability.md)). Do not certify the
  historical combined M2/M3 matrix silently.

## Waiting on user decisions

- Proposed assistant defaults 2–6 in the
  [actions review](reviews/2026-11-01-assistant-actions.md) (unused-only Undo of
  created tasks, exact `completed_at` restore, no timer Undo, one change per
  request with ≤4 clarification rounds, stateless proposals). "Every action
  requires Apply" is confirmed.
- UX draft defaults still unconfirmed: measurements (59px draft rows versus proposed 64px, and the 1280px threshold versus fallback references), filing cross-month weeks
  under their Monday's month, detailed Earlier selection, and Inter as the Figma-only
  fallback for unavailable SF Pro/Helvetica Neue.

## Settings and Connections delivery register

Stable definitions/tests: [frontend package](../frontend/plans/settings-connections/README.md).
Only the active small unit/subslice belongs here; completed documentation is not
visual construction or application delivery. No unit is currently Active.
UX-C05 delivered: [review](reviews/2026-11-04-connection-recovery.md),
[36-state inventory](../frontend/design/settings-connections/recovery/inventory.json),
[recovery guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=270-6806&starting-point-node-id=270%3A6806&scaling=min-zoom).
Codex sole writer/self-reviewer; 145 installed sources plus eight reset summaries,
58/58 finite models. Five final Light renders inspected; 467 scoped editable nodes,
nine existing layouts also checked; zero font/raster/overflow/overlap findings.
User answer to Pause → Sync once → Resume: “Clear; this behaviour works for me”.
The report confirms intended one-shot retention and saved Pause across restart,
not actual restart/provider/keyboard verification. Four new demo variables join
all eight full resets; old Google/bCourses/task/session resets retained. No app,
credential, service, DB or provider work. The user requested a local UX-C05
checkpoint; Git records the commit. No push requested. Next: UX-C06, not started, for widths/themes, remaining error/removal
walkthroughs, accessibility and consolidated handoff. **Source gap to carry forward:**
`GoogleSync.while_idle` still executes after a lock-acquisition timeout; Pause and
Disconnect cannot yet certify the designed in-flight barrier. Mounted/direct-reader
automatic work also needs Pause gating. See review for later APP-C02/C04 obligations.

UX-C04 delivered: [review](reviews/2026-11-04-google-settings-flow.md),
[47-state inventory](../frontend/design/settings-connections/google/inventory.json),
[review guide](https://www.figma.com/proto/jobFe4sXDot7BKsej0arNB?page-id=2%3A5&node-id=255-6835&starting-point-node-id=255%3A6835&scaling=min-zoom).
Codex was the single Figma writer/self-reviewer. 47 540px Light states plus an
800×778 guide, 126 installed sources and 59/59 aggregate action models. Repaired
calendar re-entry routing; nineteen affected/new models reran successfully. No
font/raster/overflow/overlap findings in the final 606-node audit. Five isolated
Google variables are added to all eight resets; all six bCourses resets remain.
99/99 Settings gears retained. Actual preview/keyboard/focus, responsive/Dark,
user acceptance and provider/runtime checks remain pending. Account-isolation
source was inspected, not certified. No app/data/provider changes. The user requested
a local UX-C04 commit; Git records the checkpoint. No push was requested for this
unit. UX-C04 is committed locally as `96c0910`; not pushed. UX-C05 is recorded above.

UX-C03 delivered under “continue”: [review](reviews/2026-11-03-bcourses-settings-flow.md),
[25-state inventory](../frontend/design/settings-connections/bcourses-inventory.json)
and [31/31 installed-action models](../frontend/design/settings-connections/bcourses-models.json).
Codex was the single writer/self-reviewer. 21 compact dialogs and four 800×900 Light
work views; 80 installed sources; zero structural font/raster/overlap/width findings.
All 99 Navigation headers retain one Settings gear. Six isolated demo variables
are included in all eight reset starts; original task/timer/history variables are
not touched by connection actions. Actual preview, keyboard/focus, responsive/Dark
and user acceptance remain pending; secondary work controls are references.
UX-C03 actual preview and wider acceptance remain open alongside UX-C04.

Earlier UX-C02 navigation correction covered 95 headers after the user found
missing gears on Track/Stats/Assistant (89 workspace entries and six close controls).
UX-C03 adds four review headers; current 99-header coverage is recorded above.
Actual preview/keyboard/focus checks remain pending.
Earlier overview unit: UX-C02, Codex single writer with source/structural/visual self-review;
[review and limitations](reviews/2026-11-03-settings-overview.md). Build skill used
to reconcile source, not to duplicate backend work. Source includes a43a456
Pause/status/disconnect work; concurrent account-isolation work remains unverified by design.

| Unit | Current state | Evidence / next step |
| --- | --- | --- |
| UX-C01 | Done — Pass with follow-ups | [Coherence review](reviews/2026-11-03-settings-connection-coherence.md); detailed package/guidance validation delivered. |
| UX-C02 | Done — Pass with follow-ups | [Overview review](reviews/2026-11-03-settings-overview.md): six editable 800×900 Light states, two components; navigation correction covers all 95 headers (89 workspace entries), with zero missing/duplicate/clipped gears. Initial 56/56 assertions and latest 89 return models are metadata/model evidence. Static commands, actual preview and broader acceptance remain explicit. |
| UX-C03 | Done — Pass with follow-ups | [Review](reviews/2026-11-03-bcourses-settings-flow.md): 25 editable states, 31 models, explicit cancel/save/refresh recovery; actual preview and wider acceptance pending. Dedicated review placement remains proposed. |
| UX-C04 | Done — Pass with follow-ups | [Review](reviews/2026-11-04-google-settings-flow.md): 47 states, 59 aggregate installed-action models, file/auth/sync separation; actual preview and broader acceptance pending. |
| UX-C05 | Done — Pass with follow-ups | [Review](reviews/2026-11-04-connection-recovery.md): 36 states, 58 models, main user report accepted; other walkthroughs/responsive/accessibility/runtime evidence pending. |
| UX-C06 | Not started | Responsive prototype/user review/handoff after construction. |
| APP-C01–09 | Not started as this execution sequence | Reuse committed migration/credential routes and any newer concurrent source. Existing capability is not absent because these new ticket definitions are unstarted. Select a small authorized slice before app work. |

## UX delivery register
This is the sole mutable UX status table; stable ticket details/acceptance live in
the frontend plan. Owner for completed setup: Codex; reviewers: independent content
and semantic-dry-run agents. Draft owner: Codex; reviewers: independent visual and semantic agents. Formal
acceptance remains pending for draft subsets. A new active-ticket entry must record owner/reviewer, acceptance
link, evidence and next action. Original dependencies below remain the full design acceptance path; UX-32.1 is
the user-requested prototype-first draft, with formal checkpoint acceptance pending.

| ID | Ticket | Status | Depends on | Evidence |
| --- | --- | --- | --- | --- |
| UX-01 | Persist brief and ticket register | Done | — | [UX docs review](reviews/2026-11-01-ux-plan-and-skill.md) |
| UX-02 | Update shared AGENTS.md | Done | UX-01 | [UX docs review](reviews/2026-11-01-ux-plan-and-skill.md) |
| UX-03 | Create repository-local design skill | Done | UX-02 | [UX docs review](reviews/2026-11-01-ux-plan-and-skill.md) |
| UX-04 | Validate guidance and skill | Done | UX-03 | [UX docs review](reviews/2026-11-01-ux-plan-and-skill.md) |
| UX-05 | Establish Figma file and asset inventory | Done | UX-04 | [File/asset inventory](reviews/2026-11-01-figma-prototype.md) |
| UX-06 | Create visual foundations | In review | UX-05 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-07 | Build basic controls | In review | UX-06 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-08 | Build task-row families | In review | UX-07 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-09 | Build supporting patterns | In review | UX-08 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-10 | Build responsive shell | In review | UX-09 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-11 | Review foundation in Today | In review | UX-10 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-12 | Design project management | In review | UX-11 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-13 | Design task editor | In review | UX-12 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-14 | Design Active hierarchy | In review | UX-13 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-15 | Design Done browsing | In review | UX-14 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-16 | Complete Today states | In review | UX-15 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-17 | Review capture-to-focus flow | In review | UX-16 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-18 | Design weekly board | In review | UX-17 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-19 | Design within-day ordering | In review | UX-18 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-20 | Design between-day moves | In review | UX-19 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-21 | Design End Week | In review | UX-20 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-22 | Design closed-week history | In review | UX-21 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-23 | Design carryover and planner review | In review | UX-22 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-24 | Design Track setup | In review | UX-23 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-25 | Design running and paused sessions | In review | UX-24 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-26 | Design recovery | In review | UX-25 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-27 | Design outcomes and Forest | In review | UX-26 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-28 | Design shop | In review | UX-27 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-29 | Design Stats | In review | UX-28 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-30 | Design corrections | In review | UX-29 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-31 | Design Assistant and review | In review | UX-30 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-32 | Connect prototype | In review | UX-31 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-32.1 | First connected review prototype (user reprioritization) | In review | UX-04; prototype-first request | [Draft delivered; runtime/user gates open](reviews/2026-11-01-figma-prototype.md) |
| UX-33 | Complete responsive/theme coverage | In review | UX-32 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-34 | Run independent design QA | In review | UX-33 | [Draft subset; acceptance open](reviews/2026-11-01-figma-prototype.md) |
| UX-35 | Run user walkthrough and fixes | In review | UX-34 | R23 bounded repair walkthrough Done; original full checkpoint acceptance remains open |
| UX-36 | Deliver handoff | In review | UX-35 | R24 scoped repair handoff delivered; original full checkpoint acceptance remains open |

**Next concrete step:** no repair ticket is active. Use the handoff to scope a separately authorized implementation; original UX-06–36 checkpoint acceptance remains distinct.

### UX repair register

Stable definitions/acceptance: [repair plan](../frontend/BEARPLANS_UX_REPAIR_PLAN.md).
Owner for the repair sequence: Codex; independent visual/product/verification
reviewers inspect the active ticket. Evidence is saved in the dated refinement
review and execution record. All 24 repair subtickets are complete for their scoped acceptance; R23/R24 evidence is linked above. Original roadmap and runtime follow-ups remain explicit.
Only one ticket may be Active; future dependencies follow the plan. These subtickets do not complete original UX
acceptance by themselves.

| ID | Repair | Status | Depends on |
| --- | --- | --- | --- |
| UX-R01 | Baseline and latest decisions | Done | — |
| UX-R02 | Synthetic task/session fixture | Done | R01 |
| UX-R03 | Cross-view fact consistency | Done | R02 |
| UX-R04 | Compact bounds and scroll ownership | Done | R03 |
| UX-R05 | Today density | Done | R04 |
| UX-R06 | Week navigation | Done | R04 |
| UX-R07 | Contextual Move/Reorder | Done | R03, R06 |
| UX-R08 | Compact Week overview/progress | Done | R05–R07 |
| UX-R09 | Readable wide Week | Done | R06–R08 |
| UX-R10 | Selection versus manual order | Done | R05, R07–R08 |
| UX-R11 | Crowded Projects/task entry | Done | R04, R10 |
| UX-R12 | Done and frozen history | Done | R02–R03, R11 |
| UX-R13 | End Week/carryover defaults | Done | R01–R03, R06, R12 |
| UX-R14 | Reviewed carryover/re-entry | Done | R07, R13 |
| UX-R15 | Stats scopes/Missed | Done | R12–R14 |
| UX-R16 | Track/task selection | Done | R03–R04, R10 |
| UX-R17 | Recovery consequences | Done | R16 |
| UX-R18 | Assistant affordances | Done | R03–R04 |
| UX-R19 | Contrast/control states (early) | Done | R03–R04 |
| UX-R20 | Responsive/theme propagation | Done | R05–R19 |
| UX-R21 | Prototype wiring | Done | R13–R20 |
| UX-R22 | Independent QA/rescore | Done | R20–R21 |
| UX-R23 | User walkthrough/corrections | Done | R22 static readiness |
| UX-R24 | Revised handoff | Done | R22–R23 |

## Build status
| Build | State | Evidence / relevant commits |
| --- | --- | --- |
| M0 / foundation | Implementation and Mac/operator gate passed | [M0 review](reviews/2026-10-14-local-foundation.md); `36f6e48`, `f4c59dd` |
| Projects/tasks/subtasks | Implementation and all six operator checks passed | [Takeover review](reviews/2026-10-13-m1-takeover.md); `a9ba50b`, `d2174a6` |
| Weekly planning + one-day refinement | Implementation Pass; original individual checklist not newly attested | [Refinement](reviews/2026-10-15-single-planned-day.md), `a21cb49`; [weekly evidence](reviews/2026-10-15-weekly-planning.md), `801cbc3` |
| Weeks/history/carryover | Implementation Pass; overall user acceptance Pass | [History review](reviews/2026-10-15-weeks-history.md), `7155bc2`; acceptance `69c6630` |
| Joined M1 technical review | Pass; broader operator gate not newly certified | [October 16 review](reviews/2026-10-16-m1-review.md) |
| M2 normal countdown | Implementation Pass; overall M2 gate not passed | [Countdown review](reviews/2026-10-16-countdown.md), `c4b7dd3` |
| Countdown eligibility/weekly-card refinement | Implementation Pass; overall M2 pending recovery acceptance | [Eligibility review](reviews/2026-10-16-countdown-eligibility.md), `bbe6059`; cosmetic follow-up in `a7de8bf` |
| Weekly drag Move / Option–Alt Add | Implementation Pass; Add interface superseded by later follow-up | [Drag review](reviews/2026-10-16-drag-scheduling.md), `a7de8bf` |
| Move-only drag interface refinement | Implementation Pass | [Current review](reviews/2026-10-16-drag-simplification.md), `861d851` against `a7de8bf` |
| Card context/due-only refinement | Implementation Pass | [Follow-up](reviews/2026-10-16-drag-simplification.md#card-context-and-due-date-follow-up), `861d851` |
| M2 recovery | Implementation Pass on Linux; Mac/operator gate pending | [Recovery review](reviews/2026-10-18-m2-recovery.md), `580b017` against `a10c788` |
| M3 growing trees / forest — first session only | Implementation Pass on Linux; Mac acceptance deferred | [M3 review](reviews/2026-10-20-m3-growing-forest.md); `e0ccf1b` |
| M3 coins/shop | Implementation review Pass on Mac; normal-app rollout and combined hardware/operator gate pending | [Coins/shop review](reviews/2026-10-20-coins-shop.md), `05a976e` against `138cd3a` |
| M3 daily streaks | Implementation review Pass on Mac; normal-app rollout and combined hardware/operator gate pending | [Daily-streak review](reviews/2026-10-21-daily-streaks.md), user-requested local commit against `05a976e` |
| M3 statistics | Implementation review Pass on Windows | [Statistics review](reviews/2026-10-23-statistics.md), `9cade8c` |
| M3 saved-session corrections / reward adjustments (schema 13) | Implementation review Pass on Windows | [Correction review](reviews/2026-10-23-session-corrections.md), `635e1e7` |
| Combined M2/M3 target-Mac hardware acceptance | Scoped passes; distinct Standby type 5 **unverified** | [Acceptance summary](reviews/2026-10-31-mac-acceptance-summary.md); later Nov 1 entries in [COMPLETED.md](COMPLETED.md) |
| M4 backup/inspection/restore | Implementation review Pass on Mac; committed `7e38d7c` | [Backup review](reviews/2026-10-31-backup-restore.md); offline restore operator Pass |
| M4 local-core trial | Candidate recorded; seven-day real-use trial **not started/reported** | [Candidate manifest](reviews/2026-11-01-core-trial-candidate.json) |
| M5 read-only assistant preview | Adapter/UI Pass; model preview Pass with follow-ups; superseded by actions/orchestrator below; committed `7e38d7c` | [Assistant review](reviews/2026-11-01-local-assistant-readonly.md) |
| M5 actions/Apply/Undo + orchestrator | Implementation Pass; 30-case evaluation **Pass** (runs 4–5, qwen3:8b); user UI review pending; committed `cf3178b`–`57aaa8e` | [Actions review](reviews/2026-11-01-assistant-actions.md), [Evaluation](reviews/2026-11-01-m5-evaluation.md) |
| M5 larger replans, integrations, plan-only transfer | **Not started** | Separate authorized scope and acceptance required |

## Guidance discrepancies retained
- Earlier Settings/package reviews describe the 674db93 baseline. Newer a43a456
  source adds durable worker Pause, sign-in/disconnect coordination, best-effort
  revocation and save-before-disconnect replacement. UX-C02 reconciled these as
  source observations, not fresh runtime passes. Automatic empty-cache UI refresh
  and explicit calendar-fetch behavior still need Pause reconciliation; concurrent
  account-isolation changes also need their own review. Credential relocation in
  f375f24 and data-folder secrets supersede prior code-folder instructions.
- The explicit October 16 Option/Alt Add request supersedes October 15's one-active
  date refinement. Multiple dates now reference the same leaf, unique per task/date,
  with shared completion, unique-leaf totals and immutable historical placements.
  The later October 16 simplification removes modifier Add and Add-another-day UI,
  without reinstating a storage constraint or deleting existing dates. Earlier
  reviews retain historical evidence and link to the new decision.
- User-edited roadmap says planned/not tested while checkmark rows say otherwise;
  its unstaged checkmarks now include weeks/history and countdown. The review-plan
  edit removes an older M1 status paragraph. Preserve these edits;
  use this record and linked evidence for actual decisions.
- Historical Claude projects/tasks draft and earlier next-build text are evidence,
  not current instructions. Review filenames may use target dates. Follow contents,
  explicit user decisions and commits.
- Original build plan suggested native sleep events. M0 measured two Mac clocks and
  selected monotonic credit plus a scoped Needs review fallback. That policy does
  not replace the new timer's hardware/recovery acceptance.
- Deadlines are date-only; the old due-date/time sketch does not add time-of-day.
  Proposed reward/price/streak defaults are separate from confirmed requirements.

Before either agent stops or transfers work, update this file with the current
state and next concrete action, and record finished work at the top of
[COMPLETED.md](COMPLETED.md) with actual checks, files/commits and review links.
