# M5 assistant actions with explicit Apply, replay and Undo — implementation review

Date: 2026-11-01. Environment: macOS 26.6.2, Python 3.13.15, Ollama local
(`qwen3:8b`). Result: **Pass with follow-ups** for this implementation ticket.
This does **not** pass the full M5 gate (30-case evaluation, ≥90% end-to-end,
daily assistant writes) and does not change core-trial or Standby 5 status.

Workflow skill created for this ticket:
[`.agents/skills/bearplans-assistant-actions`](../../.agents/skills/bearplans-assistant-actions/SKILL.md)
(linked for Claude at `.claude/skills/bearplans-assistant-actions`).

## Ticket

- **User-visible change:** the Assistant can prepare small changes —
  `create_task`, `update_task`, `assign_task_date`, `complete_task`,
  `start_timer`, `pause_timer`, `finish_timer`. Each appears as a *Proposed
  change* card with **Apply**/**Dismiss**; after Apply, task/plan changes offer
  **Undo**. Plan, Track and the compact timer refresh after Apply/Undo.
- **Acceptance scenario:** "Mark Essay draft complete" → proposal card, no data
  changed → Apply → task complete → Undo → task incomplete with its exact prior
  state. "Complete Reading" with two matching tasks → the assistant asks which
  one; no proposal. Applying a proposal after the task was edited elsewhere →
  409, nothing changed. Retrying an Apply whose response was lost → original
  result, never a second change.
- **Affected records:** `tasks`, `planned_items`, timer tables via
  `TimerService`; new immutable `assistant_actions` and
  `assistant_action_undos` (migration `0014_assistant_actions.sql`, schema 14).
- **Recovery/Undo:** Undo restores the recorded before-state only when the
  target still has the exact revision the action produced (and, for an undone
  creation, has no subtasks, planned/closed dates or countdown history). Undo
  is replay-safe and recorded once; receipts are never deleted. Timer actions
  have no Undo; Track remains the control.

## Decisions

Confirmed requirements (build plan §8, review plan M5, AGENTS): bounded typed
tools, stable IDs, expected revisions, request IDs for replay, no SQL/shell/
filesystem tools, ambiguous names prompt for selection, no reward-grant tools,
mutations through domain functions in short serialized transactions, never
while waiting on the model.

Confirmed by the user (2026-11-01): **every action requires Apply**, and
requests run through a multi-agent pipeline that classifies the request, looks
up the tool and required information in a library, and asks the user until the
information is sufficient (see "Pipeline restructure" below).

Proposed defaults introduced here (review/confirm):

1. (Confirmed above.) Every action requires Apply, including direct requests the
   build plan says "may execute after valid task resolution".
2. Undo of an assistant-created task deletes it only while unused (see above).
   General task deletion remains deferred.
3. Undo of a completion change restores the exact previous `completed_at`.
4. No Undo for timer actions (time/reward rules). Pause on an already paused
   countdown is the timer's existing idempotent no-op.
5. One change per request (the router reports `multiple` and asks for one at a
   time); at most 4 clarification rounds, then start over.
6. Proposals are stateless: the browser returns kind/arguments/expected
   revisions; the service fully revalidates them (same trust as manual controls).

## Implementation

- `backend/domain/assistant_actions.py` — schemas, `propose_action` (validates
  via the real apply path inside a rolled-back write; timers via read checks),
  `apply_action` (receipt + revision check + mutation in one transaction; timer
  actions reuse `TimerService` operation-ID replay), `undo_action`.
- `backend/domain/tasks.py`, `backend/domain/planning.py` — transaction-level
  helpers (`_create_task_tx`, `_update_task_tx`, `_set_completion_tx`,
  `_delete_unused_task_tx`, `_create_placement_tx`, `_remove_placement_tx`)
  shared by the public functions; public behavior unchanged.
- `backend/domain/assistant.py` — action tools offered to the model; calls
  produce proposals only; prompt `actions-v1`; `proposals` in replies.
- `backend/routes/assistant.py` — `POST /api/assistant/actions/apply`,
  `POST /api/assistant/actions/{operation_id}/undo`; `backend/app.py` wires the
  timer and maps `ActionConflict` to 409 `assistant_action_conflict`.
- Frontend: `Assistant.tsx` proposal cards (stable apply/undo keys across
  retries), `api.ts`, `App.tsx` refresh hook, `styles.css`.
- Tests: `tests/test_assistant_actions.py` (12), `Assistant.test.tsx` (+2);
  `tests/test_corrections.py` schema assertion now follows the migration count.

## Checks run

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | 831 passed, 1 skipped (Windows-only clock API), 174.85 s |
| `npm --prefix frontend test -- --run` | 11 files, 144 tests passed |
| `npm --prefix frontend run typecheck` | Pass |
| `npm --prefix frontend run build` | Pass |

Backend tests cover: model action call writes nothing (all tables compared);
guessed/duplicate-name IDs not proposed; proposal bound/dedupe; create apply,
replay, conflicting key reuse, Undo, Undo replay, double Undo refused; Undo of
creation refused once planned; stale update refused with no change; Undo
refused after a later user edit; parent completion rejected; exact completion
instant restored; duplicate date and closed week rejected; invalid/extra
arguments and unknown kinds rejected; timer start/pause/finish apply, replay,
stale session revision, no Undo; receipts survive reopen and are immutable;
API status codes and error shapes.

## Live model smoke (disposable data, synthetic tasks)

Service on port 8879 with a scratch data folder (schema 14), `qwen3:8b`,
stopped gracefully (`BearPlans stopped.`).

| Prompt | Result |
| --- | --- |
| Mark Essay draft complete. | Proposal; Apply 200; replay returned `replayed`; Undo 200 (28.5 s) |
| Plan Essay draft for 2026-11-03. | Proposal; Apply + replay OK (30.9 s) |
| Complete Reading. (two projects) | No proposal; asked which project (14.2 s) |
| Create a task called Outline chapter 2 due 2026-11-12. | Proposal in Inbox; Apply + replay OK (13.0 s) |
| Start Essay draft for 45 minutes. | First try **503 incomplete answer** (output limit, 50.4 s); retry proposal, Apply → running, Undo correctly 409 (39.8 s) |

Small sample; not the 30-case evaluation.

## Follow-ups

1. Model wording: one reply said the task "is marked complete" before Apply
   while also saying it was ready to apply. Cards are authoritative; tighten the
   prompt during the evaluation.
2. Output-limit failures (`num_predict` 1536 with thinking) now affect a timer
   request as well as the earlier completion-count question; tune with
   measurements during the M5 evaluation, not ad hoc.
3. Full M5 evaluation (30 scenarios incl. 10 task changes, 5 timers, 5
   ambiguity/injection) remains **not run**; daily assistant writes are not
   certified. Larger replans (`propose_replan`) and integrations not started.
4. Applied-action history is in-page only (receipts persist; no list view).
5. No browser (Playwright) test for proposal cards yet; covered by Vitest.


## Pipeline restructure (same day, after user direction)

The model no longer calls change tools. Flow: **router agent** (structured JSON,
no tools, thinking off) → **grounding** (code) → **action library** (code) →
**sufficiency gate** (code: exact record resolution, deterministic day parsing,
questions/choices with returned `pending` state) → **proposal card → Apply**.
Questions go to the **reader agent**, which now has only the five read tools.

Live findings that shaped it (qwen3:8b, disposable data):

- The model mapped "Tuesday" (today Sunday 2026-11-01) to 2026-11-02, a Monday.
  Fix: the router copies day words; `parse_day` resolves them in code ("next
  <weekday>" = that day in the following Monday–Sunday week; numeric 11/12 is
  asked, not guessed). Cards show the weekday.
- The router invented `estimate_minutes: 60`, a date and a duration for a plain
  create request. Fix: grounding keeps only details the intent uses and the
  message states; dropped names are returned in `route.ignored_details`. Cards
  now show estimate/notes/due date.
- A multi-change request was first misread; router examples fixed it.

Final live run (`router-v2`): 17/17 cases behaved as intended — proposals for
complete, plan (Tue 2026-11-03), deadline edit, create with project/estimate,
timer start ("an hour" → 60); duplicate "Reading" → choice buttons → proposal;
"Reopen Reading in History" narrowed by project; missing duration asked then
"45 minutes" continued; delete/tree-purchase injection → unsupported; two changes
→ one at a time; question → reader (18.7 s). Router turns 0.2–2.2 s (no
thinking). Remaining: the router sometimes omits "in History" on create (card
then shows Inbox, so it is visible before Apply).

Checks after the restructure (macOS 26.6.2, Python 3.13.15):

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | 842 passed, 1 skipped (Windows-only), 175.36 s |
| `npm --prefix frontend test -- --run` | 11 files, 145 tests passed |
| `npm --prefix frontend run typecheck` / `build` | Pass / Pass |


## Follow-up fix: listing subtasks by status

User report: "Check the incomplete subtasks" (selected project in context)
answered that no tasks matched — the reader only had `search_tasks`, so it
searched the literal word "subtask" and also scoped to the selected project.
Fix: new bounded read tool `list_tasks(status, level, project_id?, offset,
limit≤20)` with levels `subtasks`/`top_level`/`work_items`/`any`, parent titles
and project names, plus reader guidance to use it instead of search. Prompt
`router-v3`. Tests: filtering across projects, pagination, invalid values,
no writes.

Live qwen3:8b (disposable data): with and without a selected project, the
question called `list_tasks(level=subtasks, status=incomplete)` across all
projects and listed both open subtasks with parents (24.5 s, 33.1 s); "Which
subtasks are done in Writing?" scoped to that project correctly (63.5 s).
Follow-up: the model presented a UTC completion time as local ("10:58 PM" vs
2:58 PM Pacific); a service-local completion date field would prevent this.

Checks: pytest 843 passed, 1 skipped (176.17 s); Vitest 145 passed;
typecheck/build pass.


## Speed fixes (plan step 1)

Changes: question agent sends `think: false` explicitly for thinking-capable
models (omission enabled qwen3 thinking); model keep-alive 2 min → 15 min
(`KEEP_ALIVE`); `search_tasks`/`list_tasks` accept an exact project name
(`project`), with unknown names listing available projects; lookup validation
errors now name the tool's accepted arguments and point to `list_tasks` for
status/level filters (previously a generic error the model could not correct).
Prompt `router-v4`.

Measurements, qwen3:8b, same synthetic data, warm model:

| Question | Before (thinking on) | After, run 1 / run 2 |
| --- | --- | --- |
| Check the incomplete subtasks | 53.1 s, output-limit failure | 8.3 / 8.4 s, correct |
| Which subtasks are done in Writing? | 78.7 s, correct | 10.4 / 10.7 s, correct (`project: Writing`) |
| What is planned today? | 19.8 s | 6.3 / 6.3 s |
| Show this week's plan. | — | 6.3 / 6.5 s |
| How much saved active time do I have in total? | — | 6.3 / 6.5 s |
| Find tasks titled Reading and tell me their projects. | — | 9.5 / 9.8 s |

An intermediate run without the actionable errors failed "done in Writing" both
times (`search_tasks` called with `level`). After: 12/12 correct, no output-limit
failures. Wording follow-up: the time summary said "0 microseconds" instead of
a readable duration.

Checks: pytest 847 passed, 1 skipped (176.52 s). Frontend unchanged.


## Specialists and direct answers (plan step 2)

Orchestrator adds a question `topic` (plan, tasks, time). Code then answers
fully specified lookups directly (`backend/domain/assistant_answers.py`):
today's/this week's plan, all-time saved time, tasks/subtasks by status,
"titled/named/called X" searches and upcoming deadlines (new `list_tasks`
`has_deadline`/`order=deadline`). Filters come from the user's own words
(regexes), project scope from an exact project name in the message; anything
unclear, relative ("last week") or project-scoped plan/time questions go to a
specialist with only its own tools (plan: day/week; tasks: list/search/get;
time: summary), and unclassified questions to the general reader. Readable
durations and singular/plural wording in code. Prompt `router-v5`.

Live finding: qwen3:8b's router returned only `{"intent": "question", "topic":
"tasks"}` for questions — no project or title — so the first run answered
"done in Writing" across all projects and sent "titled Reading" to a specialist
that failed. Code-side extraction fixed both.

Live qwen3:8b, synthetic data, 11 requests: 7 direct (0.4–2.5 s: incomplete
subtasks, done subtasks in Writing, today, this week, all-time total, titled
Reading, due soonest), plan specialist for last week (4.2 s, Oct 19–25 correct),
time specialist for this week (6.1 s), change requests blocked/clarified as
expected (0.6–0.7 s). All 11 as intended.

Checks: pytest 855 passed, 1 skipped (176.87 s); Vitest 145 passed; typecheck/build pass.
