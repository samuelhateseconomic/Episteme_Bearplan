# Saved-session corrections — October 23, 2026

Baseline: `9cade8c`. User authorized the next session under AGENTS.md. One ticket:
reviewed corrections/reversals of saved credit, with reports and reward adjustments.
No backup/restore, AI, integration or normal-data rollout in this ticket. User
subsequently requested a local commit of this session; no push requested.

## Acceptance and implemented scope

From Stats, choose a saved session, edit its interval active seconds, enter a reason,
review the effects and apply. Only finalized sessions with closed valid intervals,
matching interval/session totals and resolved interruptions are eligible. Each
interval has an immutable original confirmed ceiling. Reduce credit or restore a
previous reduction within that ceiling. No new interval, timestamp change,
uncertain-gap fill or unrecorded manual time grant is available. This bounded first
correction policy preserves confirmed-time requirements; the original plan did not
specify a mechanism for arbitrary added time.

Preview is read-only and shows exact before/after session credit, affected daily
totals/60-minute qualification, tree outcome, captured-rate coin delta and wallet.
Apply checks session revision and a deterministic preview fingerprint inside the
serialized write transaction. A wallet, timezone or affected daily-total change
requires another review. Reason is required (max 500 code points); credits are
strict integer microseconds. Decimal seconds are parsed without binary rounding.

Schema **13** adds immutable original interval snapshots, correction audit/results
and a separate append-only coin adjustment ledger. No applied migration was edited.
Each adjustment captures the last initial-ledger position, preserving existing
insertion order while interleaving new adjustments without depending on wall-clock
ordering. Historical schema-10 reads retain their pre-adjustment behavior until
upgrade; normal startup still validates the complete current schema before serving.
The recorded schema version controls the old/new reward path. A missing current
adjustment ledger fails reads and purchases instead of silently restoring a
pre-correction balance.
Existing interval/session credit and existing tree outcome update atomically with
audit/receipt/adjustment. Before/after audit remains forever; reversal is a new
reviewed edit using the latest audit's before-values. Reused operation IDs replay
the original normalized request/result, even after another correction; conflicting
reuse rejects. Failed writes roll back every affected record and permit exact retry.

Initial awards remain untouched. Eligible contributions use the captured earning
rate times whole minutes of the entire corrected session, then subtract the prior
effective contribution to create one adjustment (including zero). Legacy sessions
retain their original eligibility; no tree/award enrollment is backfilled. Wallet
and recent activity include initial awards, purchases and adjustments; existing
negative-balance purchase protection applies to their sum, including free items.
Owned species are never removed. Timer coin contribution reflects adjustments.

Tree ID/species/finalization timestamp remain; its outcome is recomputed from the
corrected integer total and original session outcome. Only an originally completed
countdown restored to its full duration can regain mature status. Early/interrupted
outcomes remain unfinished. Original session identity, requested duration,
timestamps, historical context and outcome stay; only credit/revision change.
Task completion, placements and immutable closed-week snapshots are untouched.

Reports and streaks continue deriving from the same corrected interval source and
service calendar. A preview includes other saved sessions in the affected daily
totals, so it cannot silently cross a streak threshold against stale work.

## UI recovery

Saved sessions load on demand; unavailable/older services explain refresh/restart.
Cancel/back make no mutation. After a preview, editing is disabled until Back.
Pending apply requests persist separately by operation ID, preventing one tab from
erasing another tab's retry. Unknown/network/storage outcomes retain the exact
request across reload. Definitive validation/conflict failures clear its pending
operation and restore inputs for a new preview, including after reload. Inability
to persist a retry request prevents apply before any network mutation. Original
receipt results are described as results of that request; refreshed reports show
current saved records after any later edits. History explains before/after values
and offers reviewed reversal rather than erasing audit.

## Verification

Actual host: Windows 11 `10.0.26300`, Python **3.14.5**, Node **24.16.0**, installed
Chrome **155.0.8059.85**. All fixtures use disposable databases outside source;
normal personal data and existing services were not opened or restarted. Browser
timezone is Asia/Tokyo while service allocation is UTC. This is not Mac power,
battery/standby/hibernate or long-session evidence.

- `.venv\Scripts\python.exe -m pytest -xq tests/test_migrations.py tests/test_rewards.py tests/test_statistics.py tests/test_migration_fingerprints.py`
  — **79 passed**, 43.10 s, initial correction-schema regression.
- `.venv\Scripts\python.exe -m pytest -xq tests/test_corrections.py tests/test_corrections_api.py`
  — **38 passed**, 15.01 s. Covers original ceiling/reversal, captured rates,
  fractional whole-minute cutoffs, zero adjustments, legacy coin/tree cutovers,
  multiple intervals/gaps, immutable closed history, paused-timer isolation,
  finish retry, duplicate/concurrent operations, stale revision/wallet/zone/day
  totals, malformed/duplicate/missing intervals, reason validation, corrupt or
  unfinished records, transactional save failure/retry, immutable audit triggers,
  genuine schema-12 upgrade preservation and failed schema-13 rollback/retry.
  Later full core includes the final unfinished-session error-message guard.
- `npm --prefix frontend test -- --maxWorkers=2` — **136 passed**, 10 files,
  69.63 s. Review/cancel, exact decimal parsing, keyboard retry, response loss,
  remount/replay, stale conflict/input preservation, reversal preparation,
  eligibility/loading/errors, independent pending keys and blocked local storage.
- `npm --prefix frontend run build` — pass (TypeScript and Vite, final bundle
  `index-BDWezgUV.js`, 340 ms Vite build). `pip check` — pass.
- `.venv\Scripts\python.exe -m pytest -xq tests/test_corrections_browser.py`
  with `BEARPLANS_EVIDENCE_DIR=docs/reviews/evidence/corrections` — **1 passed**,
  31.82 s. Real service/browser: earn/spend 60, review 60→30 minutes, lose the
  successful apply response, reload/retry without a second adjustment, retain Birch
  and block Oak purchase at -30, then reviewed reversal restores 60 minutes,
  qualification, mature original tree and balance zero. Original initial ledger,
  owned species, tasks and closed history match. Real stop/restart and replay of
  the older receipt leave all final rows unchanged. No page errors or overflow at
  1440/375 px. Wide/narrow/light/dark and lost-response screenshots inspected.
- After the historical compatibility/order follow-up:
  `.venv\Scripts\python.exe -m pytest -xq tests/test_launch_compatibility.py tests/test_corrections.py tests/test_corrections_api.py tests/test_shop_api.py`
  — **59 passed**, 24.25 s. Genuine schema-10 timer/shop behavior, unchanged original
  activity order after upgrade, and current adjustments all pass together.
- `.venv\Scripts\python.exe -m pytest -xq tests/test_m2_probe.py tests/test_corrections.py tests/test_corrections_api.py`
  — **53 passed, 1 skipped**, 18.00 s. Existing POSIX SIGINT smoke is skipped on
  Windows. The diagnostic probe now explicitly closes its read-only SQLite
  connection and takes one read snapshot before Windows temporary-file cleanup;
  the former transaction-only context left a connection open and raised
  PermissionError. The normal app/data remain untouched.
- `.venv\Scripts\python.exe -m pytest -xq tests/test_shop_browser.py tests/test_corrections_browser.py`
  — **2 passed**, 33.48 s, on the final backend. The existing shop replay case
  now uses actionability-aware click after reload; another wallet refresh could
  disable the button between focus and Enter. Keyboard purchase is still covered
  earlier in the same journey, and exact replay/one-charge assertions are retained.
- `npm --prefix frontend run typecheck` and `git diff --check` — pass after final
  source review. Local documentation links pass.
- `.venv\Scripts\python.exe -m pytest -xq tests/test_corrections_api.py tests/test_launch_compatibility.py`
  — **16 passed**, 10.87 s, after the final missing-ledger guard. A disposable
  current-schema corruption case drops the adjustment ledger after a correction:
  wallet GET and purchase POST both fail with storage 503, preserving all remaining
  records. Genuine pre-adjustment schema behavior still upgrades without changes.

- Final `.venv\Scripts\python.exe -m pytest -q` — **753 passed, 4 skipped**,
  **589.26 s**, no failures, source held fixed throughout. Skips: POSIX SIGINT
  probe (1), POSIX process stop/continue (1), Unix OS-local timezone switching via
  `tzset` (2). All configured IANA-zone cases, correction/ledger/migration cases,
  planner/completion, forest, restart, browser and real-minute expiry regressions
  pass. Applied migration SQL 1–12 remains unchanged. The final current-schema
  missing-ledger guard is included in this full run.

Implementation review: **Pass on Windows** for the bounded correction ticket and
its necessary compatibility/verification follow-ups. M3 feature implementation
includes corrections; combined M2/M3 target-Mac hardware/operator acceptance is
still pending. No normal-data migration, milestone sign-off or release claim.

Known fixtures were specified independently: 60-minute initial award 60, spend
60, reduce to 30 => delta -30/balance -30/goal lost/tree unfinished; reverse =>
delta +30/balance zero/goal restored/same mature tree. Rate 3 at 60 seconds reduced
by one microsecond loses 3 coins. Two 30-second intervals reduced by one microsecond
use one whole-session floor, not separate per-interval floors. Across a six-
microsecond midnight span, corrected credit 3 allocates 1+2 microseconds; DST
fall-back keeps all three microseconds on its single local date.

Initial failures/attempts: the unrestricted-worker frontend run had two existing
App/Countdown timing failures under Windows contention (125 passed); limiting to
two workers passed all 134 tests then, and all 136 after final recovery tests.
Typecheck caught two unused test imports; removed before the successful build.
The first full-core attempt was stopped after 44 checks to rebuild the final
rejected-draft recovery UI. A subsequent diagnostic full run exposed the missing
adjustment-table assumption in the genuine schema-10 fixture, Windows probe
cleanup and shop retry focus race; it was stopped after those were isolated.
The real-launcher regression passed in isolation without changing its behavior.
The focused follow-ups above verify the fixes before the final full rerun. A
subsequent partial run was stopped before the final recorded-version ledger guard;
the last full run holds source fixed throughout.
These attempts do not count as final passes. No acceptance rule was weakened.

Pending manual gate: combined M2/M3 verification on the target Mac, including
hardware sleep/recovery and independent long-duration acceptance. No milestone or
release readiness is certified by Windows automated results.

Evidence: [preview wide](evidence/corrections/correction-01-preview-wide.png),
[preview narrow](evidence/corrections/correction-02-preview-narrow.png),
[preview dark](evidence/corrections/correction-03-preview-dark.png),
[lost response](evidence/corrections/correction-04-lost-response.png),
[reversal](evidence/corrections/correction-05-reversed.png).
