# M3 coins and tree shop — October 20, 2026

Baseline: `138cd3a`, following the user's “continue”. Environment: macOS 26.6.2
(25G83), Darwin arm64, Python 3.13.15, Node 24.21.0, Chrome 155.0.8059.82.
Status: **implementation review Pass on Mac; overall M3 incomplete**.
Prior staged/unstaged planning edits,
documentation handoffs and recovery stash are preserved.

## Scope, defaults and acceptance

Only coins, persistent species ownership, three cosmetic species and the small
Track shop/species selector are in this ticket. Streaks, statistics, manual session
correction, AI and integrations remain later work. Combined M2/M3 target-Mac
hardware/operator acceptance remains separate and pending.

Configurable proposed defaults (not newly confirmed product requirements): one
coin per **whole confirmed active minute**, Birch 30 coins, Oak 60, Cherry 120;
Pine remains free. The earning rate is captured at new-session enrollment. Sessions
already present at the schema upgrade, finished or unfinished, remain ineligible;
never award retroactively from reads, retries or their later finalization. Selected
owned species is locked at session start and recovery keeps the same tree.

Acceptance: completing/finishing an eligible countdown records integer confirmed
whole-minute earnings once with its session/tree outcome. Paused, review and
uncertain time earn nothing. Explicit purchase shows species/price, checks current
balance and ownership, and atomically saves one debit and ownership. Duplicate
requests, competing tabs and lost responses cannot award/debit twice or overspend;
operation-key reuse for different work conflicts. Failed saves preserve inputs and
allow exact retry. No refund/Undo or correction interface is added. Future manual
correction retains the planned adjustment-ledger policy and is not implemented here.

Required checks: independently calculated zero/subminute/full/early/interrupted
earnings, rate capture, legacy eligibility, repeated/concurrent finalization and
purchases, insufficient/negative balances, stale prices, injected write failures,
upgrade rollback/retry, exact legacy-field preservation, restart persistence,
owned-species selection, current timer/recovery/planner regressions, wide/narrow
keyboard/loading/error/retry browser behavior. All mutable test data is disposable.

## Implementation

Schema 10 adds `coin_enrollments`, `coin_ledger`, `owned_species` and
`shop_operations`. It expands the tree species constraint by copying every
existing tree field and rowid, preserving collection order and history; applied
migrations 1–9 are unchanged. The upgrade leaves all old sessions unenrolled.
New starts atomically capture the earning rate and selected owned species.
Finalization saves the session, tree result and one ledger award together.

Awards use `(confirmed_microseconds // 60_000_000) * captured_rate`. The entire
session is floored once, so separate intervals can contribute to its whole
minutes while fractions from different sessions never combine into coins.
Explicit zero awards distinguish eligible short finishes from legacy sessions.
Species selection is normalized and validated inside the write transaction;
Pine retains the original start fingerprint for legacy receipt replay.

Purchases check their persistent operation receipt first, then ownership,
displayed price and current available balance. Debit, ownership and original
response are one serialized write. Concurrent connections cannot overspend, and
reused IDs for different work conflict. A replay returns its original result even
after a config change; the interface then reads the current authoritative wallet.
Negative balances reject purchases, preserving the future correction policy.

Track includes coin balance, recent activity, an explicit name/price Buy action,
owned-species selector, three new SVG species and saved session earnings. The
exact pending purchase tuple is stored before POST and retained through uncertain
errors/reload. Failed reads disable new spending; a confirmed owned result can
acknowledge a lost response. Choices survive rejected starts and active/recovered
sessions retain the same species. Pine remains the next-form default on reload;
the started session's species and ownership are persistent.

Config is parsed once before startup touches data: `BEARPLANS_COINS_PER_MINUTE`
accepts 0–1,000,000; `BEARPLANS_BIRCH_PRICE`, `BEARPLANS_OAK_PRICE` and
`BEARPLANS_CHERRY_PRICE` accept 0–1,000,000,000. Invalid values return an actionable
startup error. Rate snapshots keep existing enrolled sessions stable after config
changes. No new dependencies or settings UI.

## Checks actually performed

- `.venv/bin/python -m pytest tests/test_forest.py tests/test_forest_api.py tests/test_migrations.py -q`
  — **42 passed**, **1.04 s**.
- `.venv/bin/python -m pytest tests/test_rewards.py tests/test_shop_api.py tests/test_shop_restart.py -q`
  — **52 passed**, **3.57 s**, after the permitted loopback rerun. Independent
  boundary fixtures cover 0, fractional seconds, 59.999999, 60, 119.999999, 120,
  180 seconds and rate capture; aggregate interval flooring, separate-session
  fractions, pause/sleep/review/clock/restart exclusions and unchanged tasks pass.
- `.venv/bin/python -m pytest tests/test_rewards.py tests/test_shop_api.py tests/test_shop_restart.py tests/test_timer.py tests/test_timer_api.py tests/test_timer_recovery.py tests/test_timer_clock.py tests/test_timer_restart.py tests/test_forest.py tests/test_forest_api.py tests/test_migrations.py -q`
  — **216 passed**, **16.23 s**. Includes concurrent finish/purchases across database
  instances, all purchase-write rollback points, enrollment/final-award failure
  and retry, strict malformed inputs, local Host/Origin boundaries, stale prices,
  insufficient/negative funds, owned selection and persisted response replay.
  Schema-9 exact-history/tree-rowid preservation and failed-upgrade rollback/retry
  pass; legacy running/tree-aware sessions remain ineligible after finalization.
- `.venv/bin/python -m compileall -q backend` — passed.
- `npm --prefix frontend test -- --reporter=dot` — final **111 passed** in seven
  files; `npm --prefix frontend run typecheck` and `npm --prefix frontend run build`
  — passed. Includes uncertain-response/reload/exact retry, newer authoritative
  wallet versus old response, obsolete-read races, focus/visibility/finalization
  refresh, stale-price rejection, unavailable storage, disabled/busy/insufficient/
  negative states, owned selection, retained failed-start species, and saved awards.
- `BEARPLANS_EVIDENCE_DIR=.evidence/coins-shop BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q tests/test_shop_browser.py`
  — **1 passed**, **3.33 s** after correcting the native keyboard helper.
  A synthetic one-minute session at configured rate 60 earns 60 coins through
  domain functions. Real Chrome commits a 30-coin Birch purchase, loses its reply
  and wallet read, reloads, then replays exactly the same ID/payload: one debit,
  one ownership row and one receipt. A stale 60-coin view cannot buy Oak after
  the balance becomes 30. New Birch countdown, keyboard navigation/start,
  pause/reload, zero-coin early finish, exact wallet/forest restart equality,
  unchanged task records and SQLite integrity/FKs pass.
- `BEARPLANS_EVIDENCE_DIR=.evidence/coins-shop/full-core BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q -s`
  — **553 passed**, zero failed/skipped, **144.66 s**. Full core includes planner,
  history/carryover/Move-only, legacy storage/migrations, countdown/recovery,
  forest and the new coins tests. Real browser-closed monitor expiry saved
  **60.000000 s**, independently observed at **60.414 s**; unchanged task and one
  mature Pine. Read-only inspection of that disposable database also confirmed
  exactly one **1-coin** award for the same session, integrity and FKs intact;
  sanitized summary: `.evidence/coins-shop/one-minute-coins.json`. This is a
  same-host awake observation, not external-stopwatch or sleep acceptance.
  Separate short real timer saved **2.570892 s**; task writes median **0.006514 s**,
  maximum **0.014511 s**; browser task creation **0.067 s**.
- After the final Pine/404 compatibility follow-up, the 111-test frontend suite,
  typecheck and build above passed. Final production bundle browser check:
  `BEARPLANS_EVIDENCE_DIR=.evidence/coins-shop/final-browser BEARPLANS_E2E_CHANNEL=chrome .venv/bin/python -m pytest -q tests/test_shop_browser.py tests/test_timer_browser.py::test_countdown_navigation_tabs_pause_retry_and_history tests/test_timer_eligibility_browser.py`
  — **3 passed**, **10.01 s**. Full core predates only that small frontend follow-up;
  backend source did not change afterward. No unaffected long-timer repeat claimed.
- Visually inspected all six synthetic shop screenshots at **1440/375 px**,
  including purchase uncertainty, active owned species, saved collection and dark
  mode. No horizontal overflow or page errors. Local screenshots remain ignored
  under `.evidence/coins-shop/`; only synthetic tasks are used.
- Independent source review found no unresolved implementation blocker. Scoped
  diff/whitespace and local Markdown link/anchor checks passed. Preservation hashes
  confirm the original two planning files and their staged/unstaged patches,
  Git-sync review, HEAD and recovery stash stayed unchanged. The earlier progress
  review remains unchanged. Applied
  migration files are unchanged; no user database/content was added to Git.

## Initial failures and corrections

- New domain/API/restart subset initially had **50 passed / 2 failed**, **1.68 s**:
  sandbox loopback bind permission errors in both real process tests. The approved
  rerun passed 52; no bypass or skipped environment case is counted as a pass.
- First 216-case backend regression had **215 passed / 1 failed**, **16.02 s**.
  A schema-5 preservation helper dynamically classified the new empty tables as
  original data. It now captures the actual pre-upgrade table names and compares
  every original table exactly. Final 216 and full 553 pass; no product SQL rule
  or preservation assertion was weakened.
- Initial frontend typecheck found one fixture missing `coin_award`; corrected.
  An initial suite had **98 passed / 2 failed** because decorative catalog Pine
  SVGs matched old session-tree accessibility assertions. Catalog artwork is now
  decorative (`aria-hidden`), with species names supplied by accessible headings.
  Later tests include precise negative-balance shortfall and obsolete-read races.
- Initial shop browser attempts failed at the native select helper after the
  purchase/reload/replay/stale-balance assertions had passed. First attempt raced
  a focus-triggered shop refresh and Enter submitted the default Pine; the next
  ArrowDown attempt did not commit a native Mac selection. The helper now uses
  Playwright's normal selection API, then verifies real Tab focus and Enter start;
  no application assertion or native selector code was removed.
- Final review identified a real old-service compatibility issue: sending explicit
  Pine in every start was rejected by the earlier strict request model. Pine now
  omits that optional key; paid species remain explicit. A new API payload test
  enforces both shapes. Shop 404 now explains that the local service needs restarting
  while Pine tracking stays available; a component test exercises that flow.
- One read-only real-minute inspection helper initially counted pytest's `current`
  symlink and concrete directory twice. Deduplicating resolved paths selected the
  same one disposable database, then all ledger/tree/integrity assertions passed.
- Whole-tree whitespace inspection reported the pre-existing planning-document
  trailing space at `BearPlans_Build_Review_Plan.md:51`. It remains preserved;
  checks scoped to this ticket's files pass.

## Decision and remaining gates

**Implementation review: Pass on macOS.** No unresolved implementation blocker.
The user subsequently requested a local commit. This implementation and its
handoff/review records are included in that commit against `138cd3a`, excluding
the unrelated staged/unstaged planning edits. No push, normal-app restart,
personal-data migration or operator purchase was performed. Starting the
normal app is a separate rollout and may apply pending migrations through schema 10.
The preserved native-event recovery stash is not applied over this different build.

**Overall M3 is incomplete.** Daily streaks and statistics/session corrections are
not started. Actual target-Mac M2/M3 hardware/operator acceptance remains pending:
sleep/wake and repeated maintenance wakes, supported battery/standby/hibernate,
externally referenced long-duration acceptance and the full combined checklist in
the [M2 review](2026-10-18-m2-recovery.md#target-mac-acceptance-still-required).
Current deterministic and Mac software regressions do not substitute for it.

Next eligible ticket is [daily streaks](../PROGRESS.md#next-m3-session--daily-streaks-not-started),
prepared in shared progress and not started. Preserve existing awards, purchases,
species and session history when deriving later reports or adjustment ledgers.

## User-requested local commit

Scope: application code, migration 10, tests, AGENTS/README, shared progress and
the Git-sync/progress/coins-shop review records. The two user planning documents
remain outside the commit with their original staged/unstaged split; the recovery
stash remains unchanged. Scoped whitespace, document links and preservation
checks passed before the path-limited commit. Application source is unchanged
since the verification above, so no unrelated test rerun is claimed. No push.
