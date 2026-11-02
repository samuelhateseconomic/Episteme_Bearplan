---
name: bearplans-assistant-actions
description: Implement, extend or review BearPlans local-assistant write actions (task create/update/complete, date assignment, timer start/pause/finish) through the router → grounding → action library → sufficiency gate → Apply pipeline, with clarifying questions, revision checks, durable replay and Undo. Use for M5 action/Undo backend, API, UI and tests; not for read-only lookups, Figma design or provider integrations.
---

# BearPlans assistant actions

Assistant actions let the local model *propose* a small change; the user applies
it explicitly, and BearPlans records a replay-safe receipt with a reviewed Undo.
Complete only the requested ticket. Larger replans (`propose_replan`), Calendar,
Canvas or Gmail writes and reward-granting tools are separate scopes.

## Establish the active work

Resolve the repository root (`git rev-parse --show-toplevel`) and read, relative
to it: `AGENTS.md`, `CLAUDE.md` (Claude), `docs/PROGRESS.md`, the build plan's
"AI implementation and evaluation" section, the review plan's M5 gate and
`docs/LOCAL_ASSISTANT.md`. Inspect Git status and the working diff; preserve
uncommitted work and the user's staged index. Do not commit: the user commits
and pushes, so finish with a suggested commit message and pathspec.

Before coding, state the user-visible acceptance scenario, affected records,
default/rule changes and Undo behavior (build-review-plan requirement).

## Pipeline (confirmed by the user, 2026-11-01)

Every request flows through separate agents; no single model call both decides
and acts:

1. **Router agent** (`assistant._route`, model, structured JSON, no tools, no
   records): classifies the latest message into `question`, one of the seven
   change intents, `multiple`, `unsupported` or `other`, and copies only stated
   details. Day words are copied, never converted.
2. **Grounding** (`action_library.ground`, code): keeps only details the chosen
   action uses and the message actually states (text present, numbers as digits
   or hours, reopen only with a reopen phrase). Dropped names are reported in
   `route.ignored_details`.
3. **Action library** (`action_library.LIBRARY`, code): one tool per intent and
   its required/optional information.
4. **Sufficiency gate** (`action_library.evaluate`, code): resolves names to
   exact records (exact title, then contained text; a named project narrows
   duplicates), converts day words with `parse_day`, and returns questions or
   choice buttons for anything missing, unknown or ambiguous. The browser returns
   the `pending` state (revalidated each turn) until sufficient; at most
   `MAX_CLARIFICATION_ROUNDS`. No-op and rule-violating requests are blocked.
5. **Proposal → Apply**: a sufficient request becomes one proposal card; **every
   action requires the user's Apply** (confirmed decision).
6. **Questions** (not changes): a direct code answer (`assistant_answers`) when
   the request is fully specified, else one read-only specialist (plan, tasks or
   time, each with only its own lookups), else the general reader. None of them
   holds change tools. At most two model calls per request.

When adding an action: add its schema to `assistant_actions`, its spec to
`LIBRARY` and `ALLOWED`, questions for its required slots, router intent text
and an example, card summary fields, Undo rules, and tests for each stage.

## Contract (do not weaken)

1. **No write during inference.** Model calls never mutate. Only the gate calls
   `propose_action`, which validates against current records and returns a
   *proposal*: kind, normalized arguments, target IDs, a human summary showing
   every field it will set, and the expected revisions it was based on.
2. **Explicit intent.** Only the user's Apply request (`POST
   /api/assistant/actions/apply`) changes data. A model reply claiming success
   without an applied receipt is a defect.
3. **Exact targets.** Actions take stable IDs obtained from read tools. Titles,
   guesses or ambiguous matches are rejected with guidance to search and ask
   the user to choose; never pick the first duplicate.
4. **Revision checks.** Apply rechecks every expected revision inside the same
   serialized `Database.write()` transaction as the mutation and its receipt.
   A stale proposal fails with a 409 and changes nothing.
5. **Durable replay.** Every apply/undo carries a client UUID. The receipt row
   stores a fingerprint of the normalized request and the JSON result. Same key +
   same work returns the original result; same key + different work conflicts.
   Timer actions reuse `TimerService` operation IDs so a lost response replays.
6. **Reviewed Undo.** Undo restores the recorded before-state only if the target
   is still exactly at the after-revision recorded by the receipt, the week is
   open and no dependent records appeared. Otherwise explain and change nothing.
   Undo is itself replay-safe and recorded; receipts are never deleted. Timer
   actions have no Undo (rewards/time rules); point the user to Track.
7. **Domain reuse.** Mutations reuse `backend/domain` transaction helpers (the
   `_..._tx(conn, ...)` forms shared with the public functions). Routes and the
   assistant coordinator do not write SQL. Completion, placement, closed-week,
   subtask and timer rules stay in their existing modules.
8. **Bounded surface.** Fixed action schemas with `extra="forbid"`, at most a few
   proposals per question, no SQL/shell/filesystem/network tools. Notes and
   titles are untrusted data.

## Build and verify

- Schema changes: a new `backend/storage/migrations/NNNN_name.sql` (never edit an
  applied one, no BEGIN/COMMIT); update schema-version assertions in tests.
- Pipeline tests (fake provider `routes=`): routing per intent, grounding drops
  invented values, questions/choices until sufficient, pending tampering,
  round limit, unsupported/multiple/blocked, reader has only read tools.
- Backend tests (fake provider, no Ollama): proposal never mutates (compare all
  tables), apply/replay/conflicting key, stale revision, closed week, parent
  completion rejection, ambiguous/unknown IDs, Undo success, Undo after a later
  edit refused, Undo replay, timer apply with replay and no Undo, restart
  persistence of receipts, and API error shapes.
- Frontend: proposal cards with Apply/Dismiss, applied state with Undo, conflict
  messages that keep the reply visible; Vitest + typecheck + build.
- Run `.venv/bin/python -m pytest` (full suite at milestone boundaries),
  `npm --prefix frontend test`, `npm --prefix frontend run typecheck`,
  `npm --prefix frontend run build`. Report exact results and the OS.
- Live-model behavior (Ollama) and the 30-case M5 evaluation are separate
  evidence; fixture success does not certify them. Rerun
  `tools/m5_evaluation.py --model <model>` after any model, prompt or schema
  change; never weaken its per-turn all-table check to make a run pass —
  investigate the changed rows it reports.

## Hand off

Write `docs/reviews/YYYY-MM-DD-assistant-actions.md` (scenario, decisions marked
proposed vs confirmed, commands/results, gaps) and update `docs/PROGRESS.md` and
`docs/LOCAL_ASSISTANT.md`. Mark remaining gates (live model evaluation, daily
writes) explicitly unpassed.
