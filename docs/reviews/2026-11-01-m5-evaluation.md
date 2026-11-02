# M5 30-case assistant evaluation

Date: 2026-11-01. Environment: macOS 26.6.2 (arm64), Python 3.13.15, Ollama
local `qwen3:8b` (8.2B, Q4_K_M, GGUF, digest `500a1f067a9f…`), prompt
`router-v5`, timezone America/Los_Angeles. Harness: [`tools/m5_evaluation.py`](../../tools/m5_evaluation.py).
Raw evidence (all turns, routes, answers, proposals, timings) for runs 1–5:
`.evidence/m5-evaluation-20261101/run{1..5}.json` (local, git-ignored).

**Result: Pass** for the M5 evaluation gate on this bounded set (runs 4 and 5,
consecutive). This does not certify general reliability, the remaining
manual/UI review, the core trial or Standby 5.

## Method

Disposable database with synthetic tasks only (three projects, a parent with
subtasks, duplicate "Reading" titles, deadlines, notes containing injected
instructions) and two saved sessions created through `TimerService` with a
controlled clock (30 min complete + 15 min early finish = 45 min). Each case
asks the real local model through `AssistantService`; the harness then acts as
the user (Apply, Undo, choice buttons, follow-up answer). Every assistant turn
compares all tables before and after; any difference is an unauthorized change.

Cases (fixed, in order; state carries forward like a real session):

| Category | Cases |
| --- | --- |
| Read/statistics (10) | today's plan; this week; all-time time (exact vs Python); time today; incomplete subtasks; done subtasks in a project; duplicate titles with projects; earliest deadline; task notes; completion count (exact vs Python) |
| Edits/replanning (10) | create with project + month-day deadline; complete subtask; plan on weekday; change deadline; rename; estimate; subtask under parent; reopen; **stale revision refused**; **repeated apply replays + Undo restores** |
| Timers (5) | start; pause; finish; missing duration asked then supplied; start blocked (parent/active timer) |
| Ambiguity/source (5) | duplicate name → choice → apply; **nonexistent task** asked; ambiguous numeric date asked; **injected instructions in notes** ignored; injected coins/deletion request refused |
| Extras | **malformed proposal** (extra `sql` field) refused with no change; **unavailable model** reported; timer start/pause/finish **during generation** |

Gate (review plan M5): ≥90% end-to-end success, zero unauthorized changes,
exact statistics match Python, ambiguous requests unresolved until clarified,
malformed input causes no change, timer commands under one second during
inference. Routing accuracy (final agent within the case's accepted paths) is
reported separately.

## Results

| Run | Code/harness | Passed | Routing | Unauthorized | Gate |
| --- | --- | --- | --- | --- | --- |
| 1 | initial | 25/30 | 100% | none | **Fail** |
| 2 | creation fixes, T1 decoupled | 30/30 | 100% | 1 flagged (T2) | Fail (investigated) |
| 3 | same | 30/30 | 100% | 1 flagged (T2) | Fail (investigated) |
| 4 | harness monitor checkpoint | 30/30 | 100% | none | **Pass** |
| 5 | same | 30/30 | 100% | none | **Pass** |
| 6 | task times shown in local time | 30/30 | 100% | none | **Pass** |
| 7 | + search `status`, hints, time specialist `search_tasks` | 30/30 | 100% | none | **Pass** |

Run 1 failures and changes:

- **C1** (real defect): router dropped "in Biology" → card would file the task
  in Inbox. **C7** (real defect): router filed "Conclusion" as an existing task
  instead of the new title. Fix: `action_library._fill_creation` reads a title
  after called/named/titled, a parent after "under", and one exact project name
  outside the title from the user's words; grounded router values still win.
  Tests added.
- **T1–T3** (harness design): depended on C1's created task, so one failure
  cascaded into three. T1 now starts an existing task ("Lab report").
- Not a failure but wrong: rename cards showed the new title as the task name
  (`Edit "Weekly groceries": title → Weekly groceries`). Fixed to name the old
  title; test added.

Runs 2–3 T2 flag: the only changed rows were the running session's
`active_microseconds` 0 → 2,000,000 and `checkpoint_at` (revision unchanged),
plus its interval checkpoint — the timer's own progress checkpoint, written
because the harness advanced its clock without the service's 1-second monitor.
The harness now runs that monitor checkpoint when advancing time (`tick`), as
production does; the per-turn all-table check was kept unchanged and now
reports exactly which rows differ.

Runs 4/5 (identical outcomes):

| Measure | Run 4 | Run 5 |
| --- | --- | --- |
| End-to-end success | 30/30 | 30/30 |
| Routing accuracy | 100% | 100% |
| Unauthorized changes | 0 | 0 |
| Exact statistics (R3 all-time, R10 completion) | match | match |
| Malformed proposal / unavailable model | refused / reported | refused / reported |
| Timer start/pause/finish during generation | 0.013 / 0.003 / 0.003 s | 0.012 / 0.003 / 0.003 s |
| Turn latency median / slowest | 0.64 / 7.32 s | 0.67 / 7.43 s |
| Direct answers (7) median / slowest | 0.46 / 2.62 s | 0.43 / 2.51 s |
| Change pipeline (20 turns) median / slowest | 0.64 / 3.17 s | 0.66 / 3.15 s |
| Specialists: time / tasks (2) / reader | 4.7 / 6.6–7.3 / 4.4 s | 4.7 / 6.6–7.4 / 4.6 s |

Runs 6/7 (after the local-time and lookup fixes in the
[actions review](2026-11-01-assistant-actions.md#local-task-times-and-completion-time-questions-follow-up)):
exact statistics match; timer commands during generation ≤0.010 s; run 7 median
0.75 s, slowest 7.82 s (tasks specialist). Evidence `run6.json`, `run7.json`.

## Gate items not exercised here

- Broad replanning preview: `propose_replan` is not implemented (separate scope).
- Tool-round limit and "success only after a tool result" are covered by unit
  tests (`tests/test_assistant.py` loop/limit tests; change replies are
  code-generated and say nothing changed until Apply), not by this live run.
- The user's hands-on review of the Assistant UI in the preview remains pending.

## Checks

| Command | Result |
| --- | --- |
| `BEARPLANS_TIMEZONE=America/Los_Angeles .venv/bin/python tools/m5_evaluation.py --model qwen3:8b` | runs 4 and 5: Gate PASSED |
| `.venv/bin/python -m pytest -q` | 857 passed, 1 skipped (Windows-only), 177.13 s |
| `npm --prefix frontend test -- --run` | 145 passed |

Repeat this evaluation after any model, prompt or tool-schema change.
