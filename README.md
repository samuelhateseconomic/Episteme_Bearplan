# BearPlans

A personal, local-only laptop planner. Your data stays on your computer.
Current state: **weekly planning, closed-week history, reviewed carryover and
normal countdown tracking implemented**. Projects, tasks and subtasks retain their
previously passed behavior.
A Monday–Sunday board supports date assignment, drag Move/Add, unscheduling, End Week and
immutable history. The joined M1 technical review passed; no new itemized operator
demonstration is claimed. See
[shared progress](docs/PROGRESS.md),
[M1 review](docs/reviews/2026-10-16-m1-review.md) and
[countdown review](docs/reviews/2026-10-16-countdown.md). The current interface
refinement is recorded in the [eligibility review](docs/reviews/2026-10-16-countdown-eligibility.md).
Current scheduling behavior is recorded in the [drag scheduling review](docs/reviews/2026-10-16-drag-scheduling.md).

A task without subtasks has an explicit completion checkbox. With subtasks, its
completion comes from its children; finish every child to complete the parent.
Reopening a child or adding unfinished work reopens the parent. Progress totals
count leaf work items once, excluding containers. Put additional parent work in an
explicit subtask. Subtask removal is available through Edit and requires confirmation;
removing the last child leaves an incomplete task with an enabled checkbox.
General task/project deletion and re-parenting are deferred. Reopening closed weeks,
recurring tasks, automatic bulk carryover, advanced reports, rewards, AI and
integrations are later work. Finishing a timer never automatically completes its task.

## Track a countdown

Open **Track** directly using the navigation or `/#track`, or choose **Start tracking**
on an incomplete leaf task/subtask in the task list or an open weekly-board card.
Select incomplete leaf work from any project, including scheduled and unscheduled
tasks, then choose a whole number of minutes from **1–180**. Completed tasks have
Start tracking disabled without extra text beneath the control. If none are eligible,
Track explains how to add or reopen work. Start, Pause, Resume
and Finish early control the same backend session across all tabs. Finish saves a
session result; marking the task complete remains a separate task action.
Completing a task during tracking leaves its existing session visible and available
to pause, resume or finish, even though that task is excluded from new-session choices.

The compact timer stays visible while planning. Navigation, a hidden tab, refresh,
and closing the browser leave the service tracking. Keep the local service running.
Its monitor resolves expiry even with no browser open. The interface interpolates
the backend's remaining time for display; browser ticks do not save or earn time.
Saved UTC active intervals stay where the work occurred when the task is later moved
or edited. Pause time is excluded, and active time cannot exceed the chosen duration.

**Countdown recovery is provisional.** The service checkpoints about once a second.
Restarted/interrupted sessions, unexplained service sampling gaps over five seconds,
and clock inconsistencies become **Needs review** with only previously confirmed time.
The timer slot remains occupied until you explicitly save confirmed time and finish,
discarding the unverified gap. Automatic sleep/crash/clock-change reconciliation and
time corrections are not in this build. Browser visibility is never treated as sleep.
Actual Mac sleep/wake, battery/standby/hibernate, midnight/DST and longer-session
acceptance remain gates for the recovery build and overall M2.

## Plan your week

The project/task list sits beside the weekly board. On narrower laptop windows,
choose a day using the Monday–Sunday buttons; on very narrow windows the board sits
above the task list. Previous, Next and Today navigate weeks without moving work.

Open **Plan task** on a leaf task or subtask, choose a **Planned date**, and use
**Add to day**. Each leaf task or subtask may appear on **several planned dates**,
with one placement per task/date. Those cards reference the same task and share
completion; weekly totals count each scheduled leaf once. Parents remain context
for their scheduled children; unscheduled work stays in the project list.
**Planned** dates and **Due** deadlines are displayed separately.

Drag a card's **Drag** handle onto another day to **Move** that placement. Hold
**Option on macOS / Alt on Windows** while dropping to **Add** a destination
placement and keep the source. The visible Move/Add indicator and highlighted days
show the operation and destinations. On narrow screens, drop onto one of the seven
day buttons. Dragging does not switch weeks or select another day automatically.
Checkboxes, tracking buttons and other card controls do not initiate dragging.

Cancel, drop outside a valid destination, or drop onto the source day to leave the
plan unchanged. A destination already containing that task is a conflict; both
existing placements stay in place. Different tasks may share a date. Failed saves
show an error and keep the saved board displayed; refresh the weekly plan to check
its saved state after a lost response before retrying.

Keyboard/date alternatives remain available: open **Move or remove** on a card to
**Move placement** or **Remove from plan**. Open **Add another planned day** on a
card or in the task's planning details and choose a date, then **Add to day**.
Date controls can also move/add outside the displayed week. Moving changes only
that placement and preserves its ID; adding creates a placement for the same task.
Move back or remove an added placement to reverse a saved scheduling change.
Removal keeps the task and its completion. The task list shows all its active dates,
including dates outside the displayed week. Completing/reopening any card updates
the shared task and all its cards; finishing a timer still leaves completion alone.

Before adding subtasks to a scheduled standalone task, remove all its placements
and then schedule the children. Before deleting a scheduled subtask, unschedule it
from every active date.
Neither operation silently removes active planned dates. Previous-week views remain
live until you explicitly close that week.

## End a week and carry unfinished work forward

In an open week, choose **End Week**, review its displayed task details, dates and
completion totals, then **Close week**. Cancel leaves everything unchanged. Closure
does not complete or delete tasks. It freezes a snapshot and archives that week's
placements with their original IDs. The build cannot reopen closed weeks, and
closing is allowed for past, current or future weeks.

The board changes to **Closed week · read-only history**. Use **Closed-week history**
or Previous/Next to revisit it. Titles, project/parent context, notes, deadlines,
estimates and **At closure** completion stay frozen after later edits or restarts.
**Current task** status is separate; the project list always edits current tasks.
Historical cards have no completion or scheduling controls. Empty weeks show
0 of 0 complete (0%); every unique scheduled leaf counts once, excluding parents.

From a closed week, choose **Carry unfinished work**. Select work and destination
dates in the immediately following Monday–Sunday week. **Review carryover** shows
the current task details and destination dates; **Apply carryover** creates plans
for the same task IDs while leaving the closed source unchanged. Work must have
been unfinished at closure and still be an incomplete leaf. Completed, removed,
new-parent and already-planned tasks are explained and excluded. A closed
destination week cannot receive work. Existing active plans must be moved or
removed explicitly before carrying that task over.

Changes since preview require another review. Failed saves retain your choices;
retry the same Apply action after a connection failure. Persistent operation IDs
prevent repeated requests from creating duplicate plans. No automatic bulk
carryover, recurring work, reopening or advanced reports are included.

The multi-date upgrade preserves existing records. Schema 7 removes the former
one-placement-per-task index while retaining task/date uniqueness. A schema-3
database with several dates uses an atomic compatibility upgrade through the
superseded one-day migration, preserving every date. Failed upgrades roll back and
keep recoverable data; do not remove valid saved dates to satisfy the old rule.

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
