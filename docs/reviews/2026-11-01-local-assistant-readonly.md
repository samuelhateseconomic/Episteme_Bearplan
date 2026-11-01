# Local assistant read-only preview — November 1, 2026

**Adapter/UI engineering: Pass. Model preview: Pass with follow-ups. Full M5:
not passed.** This ticket exposes only bounded reads. It does not certify
assistant writes, Undo, the full 30-case evaluation, integrations or M4 release.

## Authorization, acceptance and protected core

User explicitly authorized developing the remaining modules alongside the core
trial. This supersedes the earlier broad development stop, without certifying
outstanding release/hardware gates. One implemented ticket: ask about day/week
plans, task details/search and saved time through local Ollama; display exact
domain-source values; reject mutation/invalid tools; keep Plan/Track responsive
when inference is slow, missing or cancelled. No database/schema/default change.
Assistant questions/replies are transient; no Undo is needed for reads. Existing
task/timer controls retain their own behavior.

Before modifying runtime code, preserved the tested core in
`/Users/hiberkeley/Desktop/BearPlans-core-trial-2026-11-01`: all **141** candidate
source/test/build hashes matched, with an independent copied Python environment.
No personal database was copied or opened. A disposable launch from that copy
reused completed offline setup, returned schema 13 health and stopped with exit 0.
See `preserved-core-smoke.json` in the evidence folder. The
[updated trial guide](../CORE_TRIAL_CHECKLIST.md) uses that copy; the original
Projects checkout is now development. Actual trial Day 1 is still unreported.

Development base: `d9b5f90` plus preserved M4/fixture work and this ticket.
Final runtime fingerprint:
`364ed37e0a01c31cb64e1010df5555f15876754c05fb2babf64b7fb134313b8e`,
schema **13**. Exact 145 source/test and production artifact hashes are in
`development-build.json`. Existing edits/index/stashes retained; no commit/push.

## Implementation

- `backend/domain/assistant_tools.py`: five typed, extra-field-rejecting read
  tools. Existing planning, task/project and corrected-statistics functions provide
  values. Closed plans use saved history; leaf denominators remain unique. Search
  uses literal matching, stable IDs, pagination and an explicit project scope.
  Results are bounded and truncation is labeled.
- `backend/domain/assistant.py`: read-tool allowlist, five rounds/ten calls,
  24 KB context/result budgets, 90-second request deadline and one inference slot.
  No model/provider wait holds a database transaction. Prompt `readonly-v3`
  treats record text/context as data and prohibits write-success claims.
- `backend/platform/ollama.py`: async HTTP pinned to `127.0.0.1:11434`; proxies
  and redirects disabled; local installation/tool capabilities checked; reported
  remote/cloud models rejected. Bounded responses and useful errors. Model
  reasoning is separated/discarded; token-limited partial answers are rejected.
  No app-driven downloads. The existing HTTP client moved from dev-only to runtime
  dependencies, constrained to its already installed 2.13 line.
- Same-origin `/api/assistant/status` and `/chat`; disconnect cancellation drains
  the task and releases the slot. Existing loopback/request protection retained.
- React Assistant screen: model selection, independent contextual questions,
  Cancel, retained input after errors and exact source cards. No HTML/Markdown
  execution from model or task text. Navigation cancels pending inference.
  Qwen3 8B is preferred when installed; manual selection remains available.

Operator commands and separate preview data/port are in the
[local assistant guide](../LOCAL_ASSISTANT.md). Code contains no mutation tool,
shell, arbitrary SQL, filesystem access or external provider adapter.

## Actual checks

Target: **Mac15,9, macOS 26.6.2 (25G83), Darwin arm64**, Python **3.13.15**,
Node **24.21.0**, installed Chrome **156.0.8078.74**, Ollama **0.34.3**.
Evidence: `.evidence/assistant-readonly-20261101/` (no databases).

| Command/check | Actual result |
| --- | --- |
| `BEARPLANS_EVIDENCE_DIR="$PWD/.evidence/assistant-readonly-20261101/screenshots-final" .venv/bin/python -m pytest -q -rs` | **819 passed, 1 skipped, 0 failed, 258.76 s** on final source. Only skip: real Windows API unavailable on Mac. Earlier successful run: same counts, 267.23 s; retained separately. |
| `.venv/bin/python -m pytest tests/test_assistant.py -q` | **26 passed** after final search-scope changes; transport failures, cancellation/timeout/loop bounds, untrusted calls, corrected totals, frozen history, same-origin validation and core concurrency covered. Included in the final full run. |
| `npm --prefix frontend test -- --maxWorkers=2` | **142 passed**, 11 files, final run 18.77 s. Six new assistant tests cover keyboard/context, exact source values, failure/retry, stale-result exclusion, navigation/cancel and untrusted text. |
| `npm --prefix frontend run build` | **Pass**, TypeScript included; final Vite build 208 ms. Separate typecheck passed. |
| `.venv/bin/python -m pip check` | **Pass**, no broken requirements. Harmless unwritable pip-cache warning retained. |
| `uv pip compile pyproject.toml --universal --python-version 3.12 -o requirements.lock` and equivalent `--extra dev` command | **Pass**, both locks regenerated. Runtime/dev use HTTP client 2.13.1. |
| Existing launcher setup-stamp checks | Python environment and frontend stamps both match final inputs. |
| `tests/test_assistant_browser.py` through real Chrome | Wide 1440 px and narrow 375 px, no horizontal overflow; keyboard Ask, explicit error/input retention, Cancel and return to Plan passed. Deterministic provider replies are labeled fixtures, not live-model evidence. |
| `.venv/bin/python .evidence/assistant-readonly-20261101/measure_responsiveness.py` | Three real Qwen3 8B generations overlapped timer Start/Pause pairs. **Six ACKs, median 8.675 ms, maximum 11.881 ms**, all below proposed 1 s target; generation remained pending through each Pause. All disposable sessions finalized. |

Interactive in-app browser additionally verified actual Gemma rejection with input
retained, Qwen3 8B reply/source cards and live Cancel. A subsequent unsupported-model
probe returned `model_tools` rather than busy, confirming the server slot released.
All saved rows before/after those read-only UI actions were exactly equal. Final
disposable records: **1,830,232,746 µs**, five saved sessions, current completion
0/2 and wallet **30** including correction adjustments; integrity/FK checks pass,
no active session. Source cards and the model's numeric reply matched those totals.
Screenshots: `operator-model-error.png`, `operator-answer.png`,
`operator-sources.png`; wide/narrow fixture screenshots are separately named.

## Model comparison and limitations

User explicitly approved both downloads. Registry tags **qwen3:4b** and
**qwen3:8b**, Q4_K_M, were pulled successfully. Exact full digests/details are in
the comparison JSON. No prior model was removed or its configuration changed.

Ten fixed synthetic retrieval cases were written before observing outputs: Today,
week, duplicate-name search across projects, task details, corrected saved total,
leaf completion, frozen historical plan, nonexistent title, empty future day and
saved total/timezone. Each checks the requested domain-source values; literal
answer-term checks are supplemental, not a substitute for source inspection.

| Run | Actual result and decision |
| --- | --- |
| Initial `readonly-v1`, interrupted after four results | 1/4 successful source checks. `think:false` with the downloaded template exposed unfinished reasoning as content. Stopped and retained `comparison-*-initial-v1.json`. Corrected reasoning separation and token-limit handling. This is not passing evidence. |
| Same ten cases per model, `readonly-v2` | **4B: 7/10** exact-source successes, three incomplete-answer errors. Successful-response median/max 26.478/50.730 s. **8B: 9/10**, successful-response median/max 18.265/43.759 s. Its all-project search was incorrectly narrowed to selected context. All saved rows remained unchanged for every case. |
| Selected 8B, final `readonly-v3`, same ten cases | **9/10** exact-source successes, no saved-row changes. All-project search now returned both projects. One leaf-completion question hit the token limit and returned a clear error. Successful-response median/max **25.483/35.259 s**. The nine completed replies were inspected against their source records; no incorrect returned total/date was accepted. |

Commands: `compare_models.py` and `validate_selected_model.py` in evidence,
run with `.venv/bin/python`. Cases/results and source code are retained separately
for each stage. Comparison timings include local machine/test load and are small
sample observations, not latency guarantees. A 4B literal check also rejected a
correct answer expressed as 1,800,000,000 µs instead of containing the word `30`;
its exact source check passed. That heuristic mismatch was not silently rewritten.

**Open follow-up, owner: development agent:** improve/re-evaluate the bounded
completion-count question before claiming stronger assistant reliability. Keep
the safe error, exact source cards and manual Stats fallback. Qwen3 4B remains
less reliable on this set; prefer 8B for this preview. The fixed 30-case M5 gate,
write authorization/replay/Undo cases and later provider acceptance are unrun and
are not certified by this 9/10 read-only result. No daily assistant writes enabled.

## Resolved verification issues and cleanup

The first targeted test used the wrong completion function name; corrected to
`set_task_completion`. A timeout test left its 10 ms monkeypatch active for its
loop-limit portion; restored the normal deadline before that assertion. Both
subsequently passed. Offline dependency resolution first lacked cache access,
then metadata; authorized normal resolution succeeded and downloaded resolver
Python 3.12.14. An initial unconstrained runtime resolution selected HTTP client
2.16 while dev retained 2.13; constrained the reused client line and regenerated
both locks. No runtime upgrade to 2.16 was performed.

The responsiveness harness first assumed `session` rather than `active_session`.
It started one disposable countdown and closed its inference client on error.
Inspected/finalized that identified test session, fixed the harness, then obtained
all three valid overlap samples. That cleanup's confirmed test time is included
in the UI totals, separate from the untouched model-comparison databases. An
initial wallet audit summed only initial ledger rows; corrected it to include
immutable coin adjustments and cross-checked ShopService (30). These are disclosed
harness issues, not evidence of app timer/reward loss or duplicated awards.

All owned preview services/helpers and temporary UI tab were stopped/closed after
verification. No personal service/database, power setting, credential or installed
Gemma model was changed. The two explicitly approved Qwen downloads remain;
Ollama's existing user service was left running. New docs links/JSON/shell syntax,
scoped diffs and evidence hashes checked. Pre-existing review-plan whitespace
and user index edits were preserved.

Next small ticket: assistant actions with explicit intent, revisions, durable
replay and reviewed Undo, followed by the full fixed evaluation before daily
writes. It is **not started** by this review. Calendar, Canvas and Gmail remain
unstarted. Real-use trial and M4 closing review remain pending independently.
