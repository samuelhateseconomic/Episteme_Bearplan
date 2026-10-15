# BearPlans

A personal, local-only laptop planner. Your data stays on your computer.
Current state: **weekly planning implemented and verified on macOS**. Projects,
tasks and subtasks retain their previously passed behavior. A Monday–Sunday board
now supports date assignment, individual placement moves and unscheduling. The
weekly-planning operator demonstration remains pending. See
[shared progress](docs/PROGRESS.md) and the
[current review](docs/reviews/2026-10-15-single-planned-day.md).

A task without subtasks has an explicit completion checkbox. With subtasks, its
completion comes from its children; finish every child to complete the parent.
Reopening a child or adding unfinished work reopens the parent. Progress totals
count leaf work items once, excluding containers. Put additional parent work in an
explicit subtask. Subtask removal is available through Edit and requires confirmation;
removing the last child leaves an incomplete task with an enabled checkbox.
General task/project deletion and re-parenting are deferred. Week snapshots/history,
bulk carryover, timers, rewards, AI and integrations are later builds. Finishing a future timer
must never automatically complete its task.

## Plan your week

The project/task list sits beside the weekly board. On narrower laptop windows,
choose a day using the Monday–Sunday buttons; on very narrow windows the board sits
above the task list. Previous, Next and Today navigate weeks without moving work.

Open **Plan task** on a leaf task or subtask, choose a **Planned date**, and use
**Add to day**. Each leaf task or subtask has **one planned day maximum**, across
all weeks. Break work requiring several days into smaller subtasks and plan each
one separately. Complete every child to complete its parent. Parents remain context
for their scheduled children; unscheduled work stays in the project list.
**Planned** dates and **Due** deadlines are displayed separately.

On a board card, open **Move or remove**. **Move placement** changes only that
placement, including to another week. Already scheduled tasks show **Move or remove
plan** in the task list, with no second assignment form. A second assignment from a
stale tab is rejected with the existing date and guidance to Move or split the work.
Different tasks may share a date. **Remove from plan** keeps the task, its fields and
completion. The task list also shows its planned date outside the displayed week.
Completion agrees between the task list and its board card.

Before adding subtasks to a scheduled standalone task, remove its placement and
then schedule the children. Before deleting a scheduled subtask, unschedule it.
Neither operation silently removes planned dates. Previous-week views are live
plans; closed-week snapshots and historical reports are not implemented.

The one-day upgrade preserves existing records. If an older database has several
dates for one task, startup stops safely without deleting plans. Open the previous
build, remove the extra planned dates so each task has only one, and retry the
update. Split multi-day work into subtasks after unscheduling its standalone parent.

Today comes from the service's application timezone. With no timezone setting yet,
the default is the computer's local timezone, including its DST rules. Optionally
set `BEARPLANS_TIMEZONE` to an installed IANA name such as `America/Los_Angeles`
before starting the service. The interface displays the active timezone. Dates
remain date-only across browser timezones. Today metadata refreshes on navigation,
saves or page reload; the Today button asks the service for the current date again.

## Requirements

- Python 3.12 or newer. On macOS install it from python.org or `brew install python@3.12`; check with `python3 --version` (Apple's built-in `python3` is 3.9 and will be rejected).
- Node.js 24 LTS (or 22.22.2+) with npm — needed to build the interface the first time and after interface changes.

## Launch

```sh
python3 launch.py        # macOS / Linux
py launch.py             # Windows (or: python launch.py)
```

On first run this creates `.venv`, installs the pinned Python packages (`requirements.lock`), installs and builds the interface (`frontend/package-lock.json`), applies database migrations, and opens <http://127.0.0.1:8765/>. Later launches skip setup unless those inputs changed, so they work offline. Stop with Ctrl+C.

Options: `--port N` (or `BEARPLANS_PORT`), `--no-browser`. Launching again while BearPlans is running opens the existing instance instead of starting a second one.

## Where your data lives

| System | Location |
| --- | --- |
| macOS | `~/Library/Application Support/BearPlans/` |
| Windows | `%LOCALAPPDATA%\BearPlans\` |
| Linux | `$XDG_DATA_HOME/bearplans/` (default `~/.local/share/bearplans/`) |

The folder holds `bearplans.sqlite3` (plus SQLite `-wal`/`-shm` files while running). Set `BEARPLANS_DATA_DIR` to use another folder, for example a scratch copy for testing. The service refuses a data folder inside the source tree. Do not copy the database file while BearPlans is running; backup/restore arrives in a later milestone.

## Development

```sh
python3 launch.py --no-browser         # first run creates .venv
.venv/bin/python -m pip install -r requirements-dev.lock     # Windows: .venv\Scripts\python
.venv/bin/python -m pytest              # service, storage, restart and browser tests
cd frontend && npm test && npm run typecheck
```

Interface work with hot reload: run the service (`python3 launch.py --no-browser`) and, in `frontend/`, `npm run dev`, then open <http://127.0.0.1:5173/>. Vite proxies `/api` to the service.

The browser test (`tests/test_e2e_browser.py`) drives an installed Chrome or Edge through Playwright and skips if neither is available or the interface is not built. Set `BEARPLANS_EVIDENCE_DIR` to keep its screenshots.

Planning documents: `BearPlans_Dated_Roadmap.md` (schedule), `BearPlans_Build_Plan.md` (architecture), `BearPlans_Build_Review_Plan.md` (review gates). Review records: `docs/reviews/`.
