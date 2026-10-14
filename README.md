# BearPlans

A personal, local-only laptop planner. Your data stays on your computer.
Current state: **M1 projects and tasks implemented and checked on macOS**. Create and
rename projects; create and edit tasks and subtasks with notes, date-only deadlines,
estimated minutes and completion. The operator demonstration is still pending.
See [the current review](docs/reviews/2026-10-13-m1-takeover.md).

A task without subtasks has an explicit completion checkbox. With subtasks, its
completion comes from its children; finish every child to complete the parent.
Reopening a child or adding unfinished work reopens the parent. Progress totals
count leaf work items once, excluding containers. Put additional parent work in an
explicit subtask. Subtask removal is available through Edit and requires confirmation;
removing the last child leaves an incomplete task with an enabled checkbox.
General task/project deletion and re-parenting are deferred. Weekly planning,
timers, rewards, AI and integrations are later builds. Finishing a future timer
must never automatically complete its task.

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
