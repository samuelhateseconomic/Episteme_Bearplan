# Final planner and core readiness check — November 1, 2026

**Planner engineering check: Pass. Trial-entry recommendation: Pass with follow-ups.**
No blocking product defect was observed. This is an agent-operated synthetic
planner demonstration and fresh core regression run on the target Mac. It does
not certify a seven-day personal release trial or the user's real-coursework
workflow. No candidate was frozen, committed, tagged or started in this check.

## Reviewed scope and build

User authorized execution of the final planner/readiness check. Acceptance:
create a project with a parent and two children; complete both and reopen one;
schedule and move a leaf without changing its identity/deadline; cancel an End
Week preview without writes, then close; edit current details; restart and revisit
the unchanged history; explicitly preview and carry unfinished work to the next
week; restart again and replay closure/carryover without duplicate records.

Only synthetic project/task, active placement, closed snapshot/archive and
carryover receipt records were affected. No timer or reward records were created
by this manual journey. No rule, default, schema or application source changed.
Closed weeks have no reopen operation; disposable data is the recovery boundary.
The original personal data and its service were neither opened nor changed.

Build: `d9b5f90e10579d8687c4ffbd8e132a7121573ac1` plus the existing uncommitted
backup/restore implementation and test-fixture repair. Preserved all existing
working/index edits and stashes; no commit/push. The pre-existing review-plan
checkmark is not independent evidence of operator acceptance. Old roadmap/README
status text is historical; [PROGRESS.md](../PROGRESS.md) is authoritative.

Actual environment: **Mac15,9, macOS 26.6.2 (25G83), Darwin arm64**, Python
**3.13.15**, Node **24.21.0**, installed Chrome **156.0.8078.74** for the automated
browser journeys. Additional interactive demonstration used the in-app browser.
Its service timezone was explicitly `America/Los_Angeles`; the full suite also
exercises system-local timezone and configured-zone/date/DST cases.

## Execution and results

Evidence directory: `.evidence/final-readiness-20261101/`. Application/test input
SHA-256 values are in `operator-service.json`; built files and logs are included
in the final evidence manifest. Test data stays outside the checkout.

| Exact command/check | Result |
| --- | --- |
| Initial `.venv/bin/python -m pytest -q` | 752 passed, 24 failed, 17 skipped, 20.19 s. Restricted loopback service binding and installed-browser launch prevented required process/browser tests. This run was not accepted as a pass. Log: `pytest.log`. |
| Loopback/browser-permitted `BEARPLANS_EVIDENCE_DIR="$PWD/.evidence/final-readiness-20261101/screenshots" .venv/bin/python -m pytest -q -rs` | **792 passed, 1 skipped, zero failed, 150.93 s**. Only skip: `tests/test_timer_clock.py:65`, real Windows API unavailable on macOS. Required Mac browser tests ran. Log: `pytest-authorized.log`. |
| `npm --prefix frontend test -- --maxWorkers=2` | **136 passed**, 10 files, 5.97 s. |
| `npm --prefix frontend run build` | **Pass**, includes TypeScript checking; Vite build 76 ms. |
| `.venv/bin/python -m pip check` | **Pass**, no broken requirements. Pip cache permission warning did not affect dependency validation. |
| `.venv/bin/python .evidence/final-readiness-20261101/planner_service.py` | Owned disposable service `http://127.0.0.1:58171`, two graceful restarts, final exit 0. |
| `.venv/bin/python .evidence/final-readiness-20261101/snapshot.py NAME` at each recorded stage | Read-only planning/full-table snapshots; integrity `ok`, no foreign-key violations. |
| `.venv/bin/python .evidence/final-readiness-20261101/audit_planner.py` | **13 of 13 checks passed**, including repeated saved-operation replay and exact all-table equality across restart. |

The service's disposable data path was
`/private/tmp/bearplans-final-planner-20261101-_sdg1po2/data`.
`operator-service.json` records owned PIDs and final stopped state. The helper
and its service exited, and the agent's temporary browser tab was closed. No
power configuration was changed and no new sleep observation was attempted.

### Visible planner journey and saved records

- UI created **Final planner check → Prepare weekly seminar → Draft seminar
  notes / Review seminar sources**. Parent control was disabled. Completing both
  children showed 2/2 and completed the parent; reopening Draft showed 1/2 and
  reopened the parent. Parent was excluded from the denominator.
- Draft initially had deadline **2026-11-20**, estimate **45 minutes** and original
  notes. Planned date moved **2026-10-30 → 2026-11-01** while every task field, task
  ID, placement ID and placement creation time remained unchanged. Different
  children could share November 1.
- End Week preview showed **1/2 (50%)**. Cancel left every table unchanged. Closing
  October 26–November 1 archived the original placements with their original
  fields and did not modify any task.
- Current Draft was renamed **Revise seminar notes**, given deadline **2026-12-01**
  and current notes. After a real service restart, closed history still displayed
  **Draft seminar notes**, **November 20** and original notes. The stored snapshot
  was exactly equal before/after edit and both restarts.
- Carryover offered the unfinished original leaf only, previewed its current
  deadline/notes and destination **2026-11-03**, then created one new placement in
  November 2–8. Task count stayed **3**, and all task fields stayed identical to
  their current edited values. The completed sibling was not offered.
- A second service restart preserved every table exactly. Replaying both closure
  and the saved carryover operation twice returned the original results with no
  writes, new placements or cloned tasks. Integrity/FK checks passed throughout.

Saved task `214cbe3d-51e3-497a-852c-a4a665e71633`; original placement
`407754d7-22b3-4b32-876b-cb3776555d84`; carried placement
`33053823-6d4e-4f52-adbc-b390111e30d2`. Audit source and JSON retain the exact
assertions and carryover receipt ID.

The full suite additionally covers stale closure/carryover previews, lost-response
retries, conflict rollback, invalid relationships, last-child removal, legacy
multi-date plans, drag Move/cancel/Alt behavior, unscheduled Track eligibility,
session-linked edits, request protection, migration failure/retry, live-WAL
backup, clean restore, timing/recovery, rewards and corrections. These are
automated cases, not additional physical hardware observations. Current Chrome
journeys assert wide/narrow layouts, keyboard actions, disabled controls and
input retention after failed saves. Inspected the generated 375 px carryover and
wide historical views; no blocking layout problem observed.

Interactive evidence: `operator-close-preview.png`, `operator-carryover-preview.png`,
`operator-carried-after-restart.png`. Automated screenshots include
`screenshots/m1-joined-01-planned.png`, `m1-joined-02-revisited.png` and
`m1-joined-03-carried-narrow.png`.

### Tooling follow-ups, resolved

The first interactive service start and an HTTP snapshot read encountered the
same sandbox loopback restriction. The service was started with the required
access; snapshots then used read-only domain/database reads of this disposable
folder. No normal service was stopped. The first audit used generic table names
`sessions`/`session_intervals`; corrected them to the actual
`timer_sessions`/`timer_intervals` before the successful 13-check run. Its earlier
replay assertions had already passed and did not write records. These were
verification-harness issues, not app data failures.

Whole-tree `git diff --check` still reports existing trailing whitespace at
`BearPlans_Build_Review_Plan.md:51`. That user edit was preserved. Scoped new
review/progress content and local links were checked separately.

## Readiness decision and remaining stage

| Area | Decision and evidence limit |
| --- | --- |
| Planner correctness and persistence | **Pass** for the agent-operated synthetic journey and fresh regression suite. The user's real-coursework usefulness judgment remains part of personal acceptance; it is not fabricated by this check. |
| Target-Mac timing/recovery and joined rewards | Previously observed AC/battery Deep Idle, repeated maintenance wakes, overnight sleep, process recovery, ten-minute reference and uninterrupted three-hour reference remain accepted at their recorded precision. [Hibernate recovery](2026-11-01-distinct-standby-preparation.md#actual-hibernate-observation-and-verified-completion) also passed and all settings were restored. No new hardware pass is claimed here. |
| Separate Standby type 5 | **Unexercised/unverified**. [Platform assessment](2026-11-01-standby5-capability.md) established no documented supported trigger under the reviewed public ARM64 default, with a running-kernel/source-version caveat. Include this explicit limitation in candidate scope; do not certify type 5, silently waive the old matrix or request another identical sleep. |
| Backup, restore, offline launch | [Implementation checks](2026-10-31-backup-restore.md) and [user offline/restore report](2026-11-01-offline-restore-operator.md) pass at their stated scope. Fresh full suite now includes the final backup guards. |
| Full personal release / M4 | **Not passed yet**: seven days of actual use and a closing review remain. No severe timer/persistence/reward defect was found in this check. |

Recommendation: select this tested **local core** for a seven-day trial, with
Deep Idle/Hibernate in observed coverage and separate Standby 5 explicitly outside
certified coverage. The complete historical M2/M3 matrix is not given an
unqualified Pass by this recommendation. Candidate selection must record that
scope decision and the exact build fingerprint before day one. No commit/tag or
freeze was requested/performed here.

The remaining execution stage is **one seven-day real-use trial**, not another
round of ten-minute/three-hour or unchanged overnight tests. Use actual work;
include normal scheduling/movement, a deliberate End Week preview/history visit
and selected carryover when appropriate. Record a short daily note: date, work
done, friction/errors, unexpected time, missing records, reward consistency and
any reviewed correction. Retain backups and use disposable copies for failure
tests. At the closing review, compare those notes with saved plans/time/rewards
and resolve blockers before declaring release. This also supplies the user's
remaining planner usefulness judgment. AI/integrations remain deferred.
