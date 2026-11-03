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

## Current state — November 2, 2026

**UX refinement resumed at the user's request on November 2. UX-R21 native
wiring and UX-R22 independent static QA are complete (Pass with follow-ups).**
Twenty-two of the 24 repair tickets are Done. **UX-R23 is Paused at the user's request,
with partial walkthrough evidence**; R24 final handoff is not started. Codex remains the sole Figma writer. No application
implementation is authorized by this design request. Baseline Git checkpoint: `c4a5d14`. The user-authorized design checkpoint commit
contains this resumption; resolve its hash from Git history.

**UX-32.1 remains In review.** All 75 original screen IDs and ten original named
starts remain; the ledger contains 89 product/state frames plus a separate review
launcher, with 11 starts total. The free two-dimensional canvas remains.
[Canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=2-5),
[review launcher](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=141-7346),
[node ledger](../frontend/design/figma-node-ledger.json),
[execution evidence](../frontend/design/refinement-execution.json).

**R21 completed on resumption:** repaired failed reopen/Retry and pinned its error;
finished new-row Start/navigation/grip wiring; added working paired disclosure
states; corrected the wrapped parent header, repeated History and order cue;
reset all 206 prototype variables (202 at the R21 checkpoint) through eight review examples; fixed legacy
Back routes that lost source-week or timer context; removed five self-navigation
branches and duplicate entry handlers; preserved Assistant questions; bound saved
session labels to captured context; separated the new Forest record; reconciled
wallet/error labels and disabled unsupported sample controls visibly.

**Evidence:** 23 installed-reaction journey checks, 44 time/correction/wallet checks
and 601 navigation-return checks pass in read-only Map models. Initial structural
inspection covered all 89 product frames; 29 changed roots were rechecked after
repair. Final scope has no missing/cross-page destinations, malformed guards,
supported Start/completion/frozen-action gaps or self-navigation. All 90 roots have
at most one timed entry handler; 22 Cancel controls have no mutation side effects.
These are structural/model checks, not actual presentation clicks.

**Static assessment: 87.98/100 (88 rounded), up from 76.84/100.** Same 13
weights; heuristic design judgment, not measured task success. No unresolved
required static P1 in the reviewed scope. Fresh rendered checks cover the main
800×900 Light compositions plus 640×800 compact/enlarged text, 800×900 dark Today,
and 1440×900 wide Week. Earlier R20 46-reference evidence remains historical.
[R21 wiring review](reviews/2026-11-02-ux-r21-wiring.md),
[independent R22 review](reviews/2026-11-02-ux-r22-static-review.md).

**R23 paused — last owner Codex; walkthrough participant user.** Acceptance scenarios:
[repair plan §8](../frontend/BEARPLANS_UX_REPAIR_PLAN.md#8-required-validation-matrix-and-walkthrough).
The user reported “nothing stuck” for the first two examples: lower-row Today
selection/start/pause/return and Read completion/reopening under Prepare seminar
discussion, with Reset between them. No fix was requested. This is user-reported
success, without direct observation, timing or viewport evidence.
[Walkthrough evidence](reviews/2026-11-02-ux-r23-walkthrough.md).

**Stopped after the requested spacing fix; resume only when the user asks.**
The weekly-flow report found no interaction issue but flagged inconsistent day
styling and an Outline gap. Repaired nine day/result views and collapsed hidden
Read layout slots across 42 roots; Reset now covers 206 variables. Wednesday,
Saturday and completed-Read Today renders passed the scoped spacing check; the
23 journey models were rerun and passed. [Evidence](reviews/2026-11-02-ux-r23-walkthrough.md#weekly-feedback-and-spacing-repair--stop-checkpoint).

**Next on resumption:** user review of the latest spacing repair, affected compact/
dark states, then task Save/error, compact eighth-row access, crowded Projects
scrolling, closure/carryover/re-entry, frozen Missed, interruption recovery and
Stats/Assistant. Overall R23 acceptance and R24 handoff remain open. The separate
examples do not establish completion during an active timer.

Browser/computer control is unavailable in this session. Other presentation
journeys, explicit scroll behavior, keyboard/focus, arbitrary dragging and
assistive technology remain unverified.
Finite examples simulate one 12-minute save and three task toggles;
successful purchase/ownership and a general session ledger are not demonstrated.
R24 reviewed handoff follows R23 acceptance. The full original 36-ticket acceptance,
application/core-trial and hardware gates remain open. No service/database operations or app tests were performed for the design work.
The user authorized a scoped checkpoint commit after this repair; no push is authorized. Concurrent
CLAUDE.md edits and untracked `(1)` file copies appeared during work and are preserved.

- **M5 assistant:** actions through router → grounding → library → gate → Apply,
  replay and Undo; orchestrator with direct answers and plan/tasks/time
  specialists; 30-case evaluation **Pass** with qwen3:8b (runs 4–5: 30/30,
  routing 100%, 0 unauthorized changes; reruns 6–8 after later fixes also pass). See the
  [actions review](reviews/2026-11-01-assistant-actions.md) and
  [evaluation](reviews/2026-11-01-m5-evaluation.md). Last recorded: pytest 863
  passed, 1 Windows-only skip; Vitest 145.
- **Frontend redesign:** first Figma prototype constructed; user/runtime review pending
  ([UX register](#ux-delivery-register)).
- **M4 core trial:** candidate recorded; actual seven-day trial not reported.

## Next up

1. **UX design paused:** resume R23 only when requested; review the spacing repair, finish remaining journeys, then R24 handoff.
2. **User hands-on review of the Assistant in the app preview** (pending).
3. Then, each only when the user authorizes it, in this order
   ([build plan §8–9](../BearPlans_Build_Plan.md#assistant-architecture-orchestrator-and-specialists-user-approved-direction-2026-11-01)):
   (4) M6 Google Calendar → (5) bCourses access spike → (6) Canvas (bCourses) →
   (7) Gmail. CalCentral only after an access investigation; MCP only behind a
   vetted adapter boundary. Roadmap steps 1–3 are done (see COMPLETED.md).
   **bCourses connection committed (`422081e`, 2026-11-01; user moved it before
   Google Calendar):** direct read-only API (MCP vetted and not used), token in
   git-ignored `.secrets/bearplans.secrets.env`, course picker, review list, Add
   to a course project, due-date change review. Migration 15 → 16. Waiting on
   the user's hands-on check.
   [Review](reviews/2026-11-01-bcourses-connection.md).

## Open follow-ups

- End Week carryover defaults + Stats "Missed" committed (`1656600`). Assistant
  carryover command with Undo committed (`81f5922`)
  ([review](reviews/2026-11-01-end-week-carryover.md#assistant-carryover-command)).
  **Migrations 14 → 16** ran on the real data at the user's launch on 2026-11-01 23:26
  (backup `backups/pre-upgrade-v13-20261101T232614-….sqlite3`). Needs the user's hands-on check.
  R13–R15 and R21 reflect these rules; R23 actual walkthrough remains pending.
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
- UX draft defaults still unconfirmed: measurements, filing cross-month weeks
  under their Monday's month, detailed Earlier selection, and Inter as the Figma-only
  fallback for unavailable SF Pro/Helvetica Neue.

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
| UX-35 | Run user walkthrough and fixes | In review | UX-34 | R23 first two examples reported successful; remaining walkthrough pending |
| UX-36 | Deliver handoff | Not started | UX-35 | User walkthrough / full handoff pending |

**Next concrete step:** wait for the user to resume, then review the latest spacing fix. UX-06–34 retain
design evidence, not full acceptance; UX-35 is In review and UX-36 remains unstarted.

### UX repair register

Stable definitions/acceptance: [repair plan](../frontend/BEARPLANS_UX_REPAIR_PLAN.md).
Owner for the repair sequence: Codex; independent visual/product/verification
reviewers inspect the active ticket. Evidence is saved in the dated refinement
review and execution record. R21 native wiring and R22 static QA are complete with execution follow-ups;
R23 ownership and the next action are recorded above.
Only one ticket may be Active. Execute R19 after R04 before later optional proposals;
other dependencies follow the plan. These subtickets do not complete original UX
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
| UX-R23 | User walkthrough/corrections | Paused | R22 static readiness |
| UX-R24 | Revised handoff | Not started | R22–R23 |

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
