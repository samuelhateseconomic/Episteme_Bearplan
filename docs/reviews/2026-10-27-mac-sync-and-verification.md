# Mac synchronization and automated verification — October 27, 2026

User requested syncing this Mac so verification can proceed. Baseline `d20eddf`,
new HEAD `d9b5f90e10579d8687c4ffbd8e132a7121573ac1`. Host: macOS 26.6.2
(25G83), Darwin arm64, Python 3.13.15, Node 24.21.0, Chrome 156.0.8078.48.
Hardware-model sysctl read was sandbox-denied; no model is claimed.

Acceptance: local application source matches the fetched GitHub build; local work
and both recovery histories remain recoverable; preparation/tests use disposable
data. No product/default changes or normal-data rollout. New source schema is 13;
the normal user database was not opened or migrated. No normal service listened
on port 8765 at the read-only inspection; none was stopped or restarted.

## Synchronization and preservation

Inspected guidance/progress, full working and staged diffs, untracked status note,
recent commits, plans/README and current reviews. Saved worktree/index contents,
binary patches, Git status/stash identities and SHA-256 manifest to
`/private/tmp/bearplans-before-sync-20261027-1ym3tug0/`. Verified all saved hashes.

`git fetch origin` initially could not write `.git/FETCH_HEAD` under the sandbox;
rerun with granted access succeeded. Inspected fetched three-commit diff,
especially updated guidance, roadmap and overlapping progress. New
`git stash push --include-untracked -m before-mac-sync-2026-10-27-planning-and-status`
preserved all local changes. `git merge --ff-only origin/main` succeeded.

New sync stash: `c8984fc6fa4d4634d6cde00a16daa177e168e281`.
Original recovery stash: `ed5e990c6c1fd649ed60083ec8e61b90bdf2153c`, unchanged.
Verified sync-stash worktree/index bytes against every saved tracked file and
its untracked parent against the original status review. Restored exact review-plan
index/worktree versions using `git restore --source='stash@{0}^2' --staged --
BearPlans_Build_Review_Plan.md` and the saved worktree bytes. Restored status review
and merged its progress section alongside the newer remote handoff.

Roadmap three-way preview conflicted on the outdated status paragraph and task
rows. Kept GitHub's current roadmap, whose completion marks already include the
local intent; original staged/unstaged roadmap versions and patches remain intact
in the sync stash and snapshot. No conflict markers or unresolved Git merge exist.
Do not reapply the whole stash: progress and roadmap now contain newer information.

`git rev-list --left-right --count HEAD...origin/main`: **0 / 0**.
Application/source/test inputs had no local diff at sync completion. Captured 132
input SHA-256 values before full-core execution; all remained fixed through that
run. The test-only follow-up below changes one browser fixture. Runtime source
still matches GitHub. No commit or push made.

## Automated verification

Logs and screenshots:
`/private/tmp/bearplans-before-sync-20261027-1ym3tug0/verification/`.
Logs, input manifests and synthetic screenshots also retained durably in ignored
`.evidence/mac-verification-20261027/`; disposable databases are not copied there.
All mutation, migration, restart and browser fixtures use disposable databases.

- `.venv/bin/python -m pip check`: pass (cache permission warning, cache disabled).
- `npm --prefix frontend run build`: pass, including TypeScript; Vite 104 ms.
- `npm --prefix frontend test -- --maxWorkers=2`: **136 passed**, 10 files, 7.01 s.
- `BEARPLANS_E2E_CHANNEL=chrome BEARPLANS_EVIDENCE_DIR=<verification>/screenshots .venv/bin/python -m pytest -q --basetemp=<verification>/pytest`:
  **755 passed, 1 failed, 1 skipped**, 165.09 s. The skip requires the real Windows
  clock API. The failure is the correction browser fixture described below.
- Same environment, `pytest -q tests/test_corrections_browser.py
  --basetemp=<verification>/correction-recheck-data`, with screenshots under
  `correction-recheck`: **1 passed**, 3.07 s, after the test-only repair.
- Final full suite with `final-screenshots` and `final-pytest` paths: **756 passed,
  1 skipped, zero failures, 164.23 s**. Skip: real Windows clock API, unavailable
  on Mac. All 132 final input hashes remained fixed during this run. The suite
  includes actual disposable process restart/stall/expiry, correction/reward/
  report/browser/migration/rollback/retry and existing planner regressions.

The correction browser test seeded October 23 and asserted the last returned
streak day held its 30 minutes. The API correctly returns a rolling seven-day
window ending today; October 27 had zero. This was a date-dependent assertion,
not lost correction credit: saved rows and the all-time Stats total were correct.
`tests/test_corrections_browser.py` now seeds yesterday's 11:00–12:00 UTC and
checks that explicit date's 30-minute/unqualified result. It stays in the rolling
window even when the run crosses midnight. No assertions or coverage were removed.
The complete journey then passed lost-response reload/replay, negative balance
blocking, retained ownership, reviewed reversal, exact audit rows and restart.
Inspected new narrow preview/reversal screenshots: controls/text fit, exact
30-minute reduction and restoration appear, and audit remains visible. No runtime
application code changed. No second frontend run is needed for this Python
fixture-only change; the build/frontend results above apply unchanged.

Synchronization decision: **Pass**. Automated Mac verification: **Pass**, with the
test-only follow-up above. Scoped new-file/test whitespace and local Markdown
links pass. Original review-plan whitespace/stray-slash edits remain unchanged.
Git HEAD matches origin/main; runtime application source remains unchanged, and
both stashes remain present. No commit, push, normal-data rollout or normal-service
launch occurred. Asked the user's availability for a five-minute sleep check;
no hardware probe started without coordination.

Actual sleep/power, external stopwatch and long-duration operator
evidence remain pending; combined M2/M3 acceptance is **not passed**. Broader M1
operator certification is separate. No M4, AI or integration work started.
