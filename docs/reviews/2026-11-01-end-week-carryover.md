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

- **Assistant command** ("move this week's unfinished to next week" → one
  preview card → Apply/Undo) not built. Apply/Undo receipts need a new action
  kind, which requires a migration of `assistant_actions` (its `kind` CHECK lists
  the seven current kinds). Waiting on the user's choice.
- Figma End Week/carryover (UX-21/23) and Stats (UX-29) drafts predate this
  rule; update them during the design review.
