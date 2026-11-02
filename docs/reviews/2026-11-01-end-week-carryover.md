# End Week carryover defaults and missed work in Stats

Date: 2026-11-01. macOS 26.6.2 (arm64), Python 3.13.15.

**Result: Pass** for this scope (End Week → carryover defaults, Stats "Missed").
The assistant carryover command is not built (see Open).

## Request and decisions (user, 2026-11-01)

- Unfinished work moves to the **same weekday next week** (unfinished Tuesday →
  next Tuesday); the **due date stays**; the miss is recognized in Stats.
- Choose which tasks carry **when using End Week**.
- Stats wording: **"Missed: N"**.
- Rule change: carryover may preselect every eligible task (still reviewed and
  applied by the user), replacing "bulk automatic carryover deferred".

## Acceptance scenario

Close a week with unfinished planned work → the carryover choices open at once;
each eligible task is checked with the same weekday next week as its last planned
day in the closed week; tasks that cannot carry are shown with the reason; the
user unchecks or redates any, reviews and applies. Deadlines, task fields and the
closed snapshot never change. Stats shows "Missed: N" overall, per closed week
("X of Y finished as planned · Missed: Z") and per task ("Missed: 2×").

Affected records: none new. Carryover creates placements exactly as before;
Stats derives everything from existing `closed_weeks` snapshots (read-only).
No migration. Undo: unchanged (carried placements can be moved/removed in Plan).

## Changes

- `backend/domain/weeks.py`: `CarryoverCandidate.suggested_date` = last planned
  day in the closed week + 7 days (eligible candidates only).
- `backend/domain/statistics.py`: `missed`, `weeks[]` (completed/total/missed per
  closed week) and per-task `missed_count`. A task planned on two days in a week
  counts once; finishing it later does not erase the miss.
- `frontend/src/WeekActions.tsx`: closing opens carryover choices; eligible tasks
  preselected with the suggested date; re-checking restores it; End Week preview
  says unfinished work counts as missed and that choices follow.
  `WeeklyPlanner.tsx` keys `WeekActions` by week only so the flow survives the
  closed/open switch.
- `frontend/src/Statistics.tsx`: "Missed" in the summary, a "By week" list, and
  "Missed: N×" on task rows with misses.
- `AGENTS.md`: carryover and Missed rules updated.

## Checks

| Command | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | 863 passed, 1 skipped (Windows-only), 182.16 s |
| `.venv/bin/python -m pytest -q tests/test_weeks_browser.py` (after adding the auto-open step) | 1 passed |
| `npm --prefix frontend test -- --run` | 149 passed |
| `npm --prefix frontend run typecheck` / `build` | pass |

New tests: same-weekday suggestion incl. two-day task and ineligible task, due
date unchanged (`tests/test_weeks.py`); missed per week/task across carryover and
later completion, open week excluded, no writes (`tests/test_statistics.py`);
preselection, uncheck/recheck, close → choices open (`WeekActions.test.tsx`);
Missed summary/week/task display and empty state (`Statistics.test.tsx`); real
Chrome: choices open after Close week with Monday → next Monday, Wednesday → next
Wednesday and no placement saved until Apply (`tests/test_weeks_browser.py`).

## Open

- Assistant command: built (below); waits on the user's hands-on check.
- Figma End Week/carryover (UX-21/23) and Stats (UX-29) drafts predate this
  rule; update them during the design review.

## Assistant carryover command

User choice (2026-11-01): **With Undo**, accepting a migration.

- Router intent `carry_over_week` (prompt `router-v6`); the action library takes
  the week from a date slot, "last/previous week" (today − 7), or today.
- `propose_action` writes nothing. It blocks an open week ("Close it first: in
  Plan, choose End Week") and a week with nothing eligible. The card title counts
  tasks that cannot carry over; `preview.items` lists title, project/parent,
  destination date and the unchanged deadline. `expected.preview_token` ties
  Apply to the reviewed carryover; a changed task gives "Review carryover again".
- Apply reuses `weeks._apply_carryover_tx` with the assistant key as operation
  ID, so replay returns the same receipt. Undo is all-or-nothing: any moved or
  removed carried plan refuses Undo with no change.
- Migration `0015_assistant_carryover.sql` rebuilds `assistant_actions` (CHECK
  plus `carry_over_week`) and `assistant_action_undos`, keeping rows and
  recreating the four immutability triggers. Real data upgrades 14 → 15 on next
  launch after the automatic backup.

Checks: `tests/test_assistant_carryover.py` (8 tests: no-write proposal,
apply/replay/undo/replay, stale and reused key, all-or-nothing Undo, open/empty
week, malformed proposals, router this/last week, migration keeps receipts and
immutability); `Assistant.test.tsx` card list and review token. Full pytest 871
passed, 1 skipped; Vitest 150; typecheck and build pass; evaluation run 9 gate
passed. Not yet: real Chrome assistant carryover journey; user hands-on review.
