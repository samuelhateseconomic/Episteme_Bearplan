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

**UX refinement is paused at the user's request.** Twenty of the 24 repair tickets
are Done. **UX-R21 is unfinished and Paused**; formal UX-R22–24 are not started.
Codex stopped Figma mutations and saved this documentation checkpoint. Resume
design work only when the user asks. No application implementation is authorized
by the design request. The user subsequently authorized committing and pushing
this saved UI/UX checkpoint on November 2.

**UX-32.1 remains In review.** The original 75 screen IDs are preserved. The current
ledger indexes 89 product/state frames plus a separate review launcher; the last
responsive review covered 46 static references. The open two-dimensional editing
canvas remains. [Canvas](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=2-5),
[review launcher](https://www.figma.com/design/jobFe4sXDot7BKsej0arNB?node-id=141-7346),
[node ledger](../frontend/design/figma-node-ledger.json),
[execution evidence](../frontend/design/refinement-execution.json).

R21 work applied: shared current/frozen counts; Create/retry/closed-day blocking;
Read/Theme/Chapter completion pairs; Move and frozen planned dates; up to 12
reviewed carryover candidates; manual order across timer views; reversible reorder;
32px drag targets; guarded navigation/Start; Week preview/count cleanup; and a
separate reset launcher. The final time-context/correction patch was applied but
has not received installed-action or visual verification.

**Checks:** ten new Map-model checks against installed reactions passed for Save,
completion/reopen across five timer states, immutable closure/exclusions,
12-candidate Apply/replay, and Move → Saturday carryover. These are not browser
clicks. Earlier scoped checks are historical evidence and were not all rerun after
the latest mutations. Full-page wiring/audit calls hit the MCP request limit;
completion wiring was subsequently applied in bounded batches. No final complete
structural audit or post-pairing visual pass has passed.

**Design assessment:** original expert evaluation 77/100; a provisional independent
visual review scored **87.09/100** using the same 13 weights. It found no static P1
in the captured scope, but predates the last R21 changes and is not final R22
acceptance. [Provisional review](reviews/2026-11-02-ux-refinement-provisional-review.md),
[detailed checkpoint and remaining fixes](reviews/2026-11-01-ux-refinement.md).

**Resume R21 first (owner: Codex; reviewers: product_constraints,
skill_forward_test, ux_inventory):**

1. Repair the Reopen failed example: its Retry button has no action, and its direct
   start does not seed a completed Read task. Preserve timer state on retry.
2. Finish reset/entry integration and final navigation/Start/drag wiring after the
   new row pairs. Check reverse-reorder registry handling, new Read handles,
   completion disclosure defaults and the newly introduced context labels.
3. Verify the applied finite time/correction/wallet patch; bind finished-session
   text to captured task/context and saved totals. Reconcile the purchase-failure
   sample's fixed balance. Successful purchase is not currently demonstrated.
4. Partition the structural audit, rerun affected installed-action checks, then
   render Today/expanded/completed/timer, Week/reverse reorder, Projects, closure,
   Stats and the launcher after the latest changes. Only then start formal R22.
5. R23 requires actual core click/scroll journeys and the user's acceptance; R24
   follows with the reviewed handoff. The draft is saved, not accepted.

Browser clicks, scrolling, keyboard/focus and assistive technology remain
unverified (computer-control Node startup fails). The full 36-ticket acceptance,
application/core-trial and hardware gates remain open. Design work and
documentation are included in the UI/UX checkpoint commit. No tests, builds or
Figma verification were rerun for this Git operation, as requested.

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

1. **UX design paused by user:** on resumption finish the R21 fixes/checks above, then R22 independent QA, R23 user walkthrough and R24 handoff.
2. **User hands-on review of the Assistant in the app preview** (pending).
3. Then, each only when the user authorizes it, in this order
   ([build plan §8–9](../BearPlans_Build_Plan.md#assistant-architecture-orchestrator-and-specialists-user-approved-direction-2026-11-01)):
   (4) M6 Google Calendar → (5) bCourses access spike → (6) Canvas (bCourses) →
   (7) Gmail. CalCentral only after an access investigation; MCP only behind a
   vetted adapter boundary. Roadmap steps 1–3 are done (see COMPLETED.md).
   **bCourses connection built, comitted (2026-11-01; user moved it before
   Google Calendar):** direct read-only API (MCP vetted and not used), token in
   git-ignored `.secrets/bearplans.secrets.env`, course picker, review list, Add
   to a course project, due-date change review. Migration 15 → 16. Waiting on
   the user's hands-on check in the preview (port 8878) and commit.
   [Review](reviews/2026-11-01-bcourses-connection.md).

## Open follow-ups

- End Week carryover defaults + Stats "Missed" committed (`1656600`). Assistant
  carryover command with Undo committed (`81f5922`)
  ([review](reviews/2026-11-01-end-week-carryover.md#assistant-carryover-command)).
  **Migrations 14 → 16** (carryover, bCourses) run on the real data at the next
  launch (automatic backup first). Needs the user's hands-on check in the preview (port 8878).
  R13–R15 repairs now reflect these rules; final R21 integration remains unfinished.
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
| UX-35 | Run user walkthrough and fixes | Not started | UX-34 | User walkthrough / full handoff pending |
| UX-36 | Deliver handoff | Not started | UX-35 | User walkthrough / full handoff pending |

**Next concrete step:** no design ticket is Active while paused. On the user's
resumption, finish UX-R21 before formal R22–24. UX-06–34 retain draft evidence,
not full acceptance; UX-35/36 remain unstarted.

### UX repair register

Stable definitions/acceptance: [repair plan](../frontend/BEARPLANS_UX_REPAIR_PLAN.md).
Owner for the repair sequence: Codex; independent visual/product/verification
reviewers inspect the active ticket. Evidence is saved in the dated refinement
review and execution record. R21 is paused and unfinished; reviewers and the next
action are recorded above.
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
| UX-R21 | Prototype wiring | Paused | R13–R20 |
| UX-R22 | Independent QA/rescore | Not started | R20–R21 |
| UX-R23 | User walkthrough/corrections | Not started | R22 static readiness |
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
