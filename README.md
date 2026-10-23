# BearPlans

A personal, local-only laptop planner. Your data stays on your computer.
Current state: **weekly planning, closed-week history, reviewed carryover and
countdown tracking with checkpoint recovery, growing trees, a saved forest,
coins, a species shop, daily streaks, statistics and reviewed session corrections implemented**. Target-Mac M2 hardware
acceptance remains pending for combined M2/M3 verification. Projects, tasks and subtasks retain their
previously passed behavior.
A Monday–Sunday board supports date assignment, drag Move, unscheduling, End Week and
immutable history. The joined M1 technical review passed; no new itemized operator
demonstration is claimed. See
[shared progress](docs/PROGRESS.md),
[M1 review](docs/reviews/2026-10-16-m1-review.md) and
[countdown review](docs/reviews/2026-10-16-countdown.md). The current interface
refinement is recorded in the [eligibility review](docs/reviews/2026-10-16-countdown-eligibility.md).
Current scheduling behavior is recorded in the [move-only interface review](docs/reviews/2026-10-16-drag-simplification.md).

A task without subtasks has an explicit completion checkbox. With subtasks, its
completion comes from its children; finish every child to complete the parent.
Reopening a child or adding unfinished work reopens the parent. Progress totals
count leaf work items once, excluding containers. Put additional parent work in an
explicit subtask. Subtask removal is available through Edit and requires confirmation;
removing the last child leaves an incomplete task with an enabled checkbox.
General task/project deletion and re-parenting are deferred. Reopening closed weeks,
recurring tasks, automatic bulk carryover, advanced reports, AI and
integrations are later work. Finishing a timer never automatically completes its task.

## Grow a tree

Track grows a tree for each new countdown. Pine is free; choose any owned species
using **Tree species** before starting. That choice stays with the countdown
through pauses, recovery and restarts. Tree eligibility began at schema 9; earlier
sessions, including sessions already in progress at that upgrade, keep their saved
history without receiving trees.

Confirmed active time drives growth: seedling below half the chosen duration,
sapling from halfway, then mature only when the entire countdown is confirmed and
finalized. Pausing preserves growth. Needs review freezes it; explicitly continuing
after recovery keeps the same tree and excludes uncertain time. Browser animation
never adds progress. Finishing early or saving an interrupted session keeps the
tracked work and an unfinished tree.

**Your forest** within Track lists saved mature and unfinished trees with their
associated session, original task/project context and confirmed time. Session and
tree finalization save together, once, including retries and restarts. Task edits,
completion and scheduling do not change saved trees. Use **Refresh forest** to
reload results from another tab or retry a failed read. Trees do not complete tasks.
Pine/forest, coins/shop, daily streaks, statistics and saved-session corrections are implemented.
Combined M2/M3 Mac
verification remains required before release readiness.

## View statistics

Open **Stats** for all-time saved active time by service-local date, project and
task, plus current leaf completion counts/percentages and estimates versus actual
saved time. Parent containers and repeated planned dates do not duplicate work.
The task-detail project filter leaves the overall summaries visible.

Saved early finishes, resolved interruptions and legacy closed intervals count;
unfinished sessions and uncertain gaps do not. Historical time remains after task
removal. Current names/estimates describe existing leaves; historical-only rows
contribute time without current completion or estimates. A missing estimate stays
unspecified. Daily completions reflect currently complete leaves on their saved
completion dates, so reopening/removing a task changes them. Closed-week history
remains frozen and separate.

Use **Refresh statistics** after saving in another tab. A failed read retains and
labels the last report until a successful retry. Reports are read-only; reviewed
edits are available separately through **Saved session corrections**.

## Correct saved session time

In **Stats → Saved session corrections**, choose a saved session and **Correct
saved time**. Change each interval's active seconds, enter a reason, then choose
**Review correction**. Decimal seconds support up to six places. Correct time
within each interval's original confirmed maximum; dates and gaps stay fixed.
Only finalized sessions with complete, consistent intervals and resolved
interruptions are eligible. Missing/unconfirmed work cannot be added here.

The preview shows saved time, affected daily totals and streak qualification,
tree outcome, coin adjustment and resulting wallet balance. **Apply correction**
revalidates these effects before saving them together. A changed session, wallet,
timezone or affected daily total requires a fresh review. Cancel changes nothing.
Reports and streaks then use the corrected intervals. Task completion and
closed-week history stay unchanged. Original session context/outcome is retained.

Corrections retain the original coin award and create explicit adjustments using
the earning rate captured at session start. Legacy sessions stay ineligible for
new coins/trees. Existing tree identity/species stay; corrected time can change its
growth/outcome. If already-spent coins create a negative balance, purchased
species stay owned and new purchases wait until the balance recovers.

Lost responses retain the exact request for **Retry correction**, including after
reload. Each pending request has its own browser record; a retry cannot erase
another tab's request. Retries return the original receipt and refresh current
records. A browser that cannot persist this retry request must allow local storage
before applying. Under **Correction history**, **Prepare reversal of latest
correction** restores its prior interval values for another preview/apply. This
adds a new audit/adjustment; original history is never deleted.

## Coins and the tree shop

**Tree shop** within Track shows your coins, owned species, prices and recent coin
activity. Finish a new eligible countdown to earn coins from its saved confirmed
time, including early or interrupted finishes. With the proposed default rate,
each whole active minute earns one coin: 59 seconds earns 0, and 2 minutes 30 seconds
earns 2. Whole minutes are calculated once across the entire session, not separately
for each interval. Paused, review and uncertain time earn nothing. Starting or
pausing a countdown does not award coins; its final session, tree and coin award
save together once, even after retries or restart.

Coin eligibility starts with new countdowns created by the coins-aware build
(schema 10). All sessions already present at that upgrade stay ineligible,
including unfinished sessions and completed trees. They keep their existing time,
tree and task history without retroactive awards.

Birch, Oak and Cherry cost **30, 60 and 120 coins** by default. Review the species
and displayed price, then select **Buy**. Ownership and the coin deduction save
together; you cannot buy an owned species twice or spend more coins than you have.
Owned species become available for future countdowns and remain yours after
restart. They are cosmetic and do not change earned time or task completion.

Use **Refresh shop** to load changes from another tab or retry a failed read.
If a purchase response is lost, its exact request stays available after page reload:
refresh to check the saved result or use **Retry … purchase**. The backend replays
the saved result without a second charge. Failed purchases keep your selection.
Shop refunds and purchase Undo remain unavailable; session corrections and their
reviewed reversals are separate actions in Stats.

Earning rate and prices are configurable proposed defaults, not fixed product
requirements. Set these environment variables before launching; no settings UI is
provided yet. The rate is captured for each new session, so a later restart or
configuration change cannot alter that session's award. Price changes affect new
purchases; stale displayed prices require a shop refresh before purchase.

| Environment variable | Default | Accepted values |
| --- | --- | --- |
| `BEARPLANS_COINS_PER_MINUTE` | 1 | Whole number 0–1,000,000 |
| `BEARPLANS_BIRCH_PRICE` | 30 | Whole number 0–1,000,000,000 |
| `BEARPLANS_OAK_PRICE` | 60 | Whole number 0–1,000,000,000 |
| `BEARPLANS_CHERRY_PRICE` | 120 | Whole number 0–1,000,000,000 |

Invalid configuration stops startup with an actionable error before opening data.
The [coins/shop review](docs/reviews/2026-10-20-coins-shop.md) records verification
and the separate outstanding milestone gates.

## Daily streaks

**Daily streak** within Track shows today's saved confirmed time toward one hour,
your consecutive qualifying days and the last seven days. Two saved 30-minute
sessions qualify a day. A total of 59 minutes 59.999999 seconds does not. Time
accumulates across projects and tasks; early finishes and explicitly resolved
interrupted sessions count their confirmed work. Earlier saved sessions with
recorded intervals count too, independently of tree and coin eligibility.

Running, paused and Needs review sessions contribute after they are finished and
saved. Pauses and uncertain gaps never count. If today has not reached one hour,
yesterday's streak remains available to extend today. An unqualified previous day
breaks the streak; there is no coin penalty.

Dates use the displayed service timezone, `BEARPLANS_TIMEZONE` or the computer's
local timezone. Sessions spanning midnight split their saved credit between dates,
including daylight-saving changes. Changing the service timezone recalculates
historical dates from stored UTC intervals without editing those records; original
session timezones were not recorded by earlier builds. Use **Refresh streak** to
retry a failed read. Track also refreshes after saves, on return and while visible.
Streaks add no saved counter or independent reward. Saved-session corrections in
Stats update the intervals from which streaks are derived.

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

The service saves a checkpoint about once a second. Measured sleep **pauses** the
countdown at its last saved time; waking the laptop does not resume it. Choose
**Resume** when you are ready. This also excludes time during brief maintenance
wakes while the lid is closed. The entire unobserved interval is excluded rather
than guessing when you stopped working.

A running session interrupted by a service restart, crash, unexplained sampling
gap over five seconds, or clock inconsistency becomes **Needs review**. Track shows
the last confirmed active time and interruption details. **Continue with confirmed
time** keeps the same session and remaining duration while excluding the gap;
**Save confirmed time and finish** saves an interrupted outcome. Neither option
adds uncertain time. Already paused sessions stay paused across service restarts.
Recovery decisions and interruption details persist, including safe retries after
a lost response. A crash can lose work since the last successful checkpoint; during
storage failures that interval can be longer than one second. Browser visibility
never determines sleep or earned time. Saved-time corrections are available in
Stats within original confirmed interval ceilings; they cannot fill unknown gaps.

M2's target-Mac hardware acceptance remains separate from Linux automated checks.
Use the disposable evidence tool without touching your normal planner data:

```sh
.venv/bin/python tools/m2_probe.py precision --seconds 600 --output /tmp/bearplans-m2-precision.json
.venv/bin/python tools/m2_probe.py sleep --seconds 300 --output /tmp/bearplans-m2-sleep.json
```

The sleep probe observes a sleep you initiate; it never changes power settings or
suspends the computer. Check real sleep/wake, repeated maintenance wakes, battery
and standby/hibernate conditions on the target Mac. The precision probe compares
against another process on the same host; also compare against an external timer.
See the [recovery review](docs/reviews/2026-10-18-m2-recovery.md) for the acceptance checklist.

## Plan your week

The project/task list sits beside the weekly board. On narrower laptop windows,
choose a day using the Monday–Sunday buttons; on very narrow windows the board sits
above the task list. Previous, Next and Today navigate weeks without moving work.

Open **Plan task** on a leaf task or subtask, choose a **Planned date**, and use
**Add to day**. Already scheduled work offers Move/remove controls. Existing saved
dates stay intact, including several placements for the same task. Those cards
reference the same task and share completion; weekly totals count each scheduled
leaf once. Parents remain context
for their scheduled children; unscheduled work stays in the project list.
**Planned** dates and **Due** deadlines are displayed separately.

Drag the grip icon to the left of a card's project/parent-task line onto another day to **Move** that
placement. Holding Option/Alt still moves it. The visible Move indicator and
highlighted days show the operation and destinations. On narrow screens, drop onto
one of the seven day buttons. Dragging does not switch weeks or select another day automatically.
Checkboxes, tracking buttons and other card controls do not initiate dragging.

Weekly cards show the task's due date; the day column identifies its planned day.
The redundant Planned-date line is omitted on both open and historical cards.
Planned dates remain in the task list and date controls.

Cancel, drop outside a valid destination, or drop onto the source day to leave the
plan unchanged. A destination already containing that task is a conflict; both
existing placements stay in place. Different tasks may share a date. Failed saves
show an error and keep the saved board displayed; refresh the weekly plan to check
its saved state after a lost response before retrying.

Keyboard/date alternatives remain available: open **Move or remove** on a card to
**Move placement** or **Remove from plan**. Date controls can move outside the
displayed week. Moving changes only that placement and preserves its ID and any
other saved placements for the task. Move back to reverse a saved move.
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

Options: `--port N` (or `BEARPLANS_PORT`), `--no-browser`. Launching again reuses an existing instance only when its recorded source build, checkout and supported schema match this launch. The launcher checks this before installing dependencies or rebuilding the interface. A different or unknown running build stays running, and the launcher explains that a deliberate restart is needed; it does not rebuild over that service or open its interface. Finish or pause active work before stopping the existing service with Ctrl+C, then launch again. A service still starting may need a moment before its build identity is available. `--no-browser` also applies when reusing the same build. No instance is stopped or restarted automatically.

Migration 11 repairs the known case of a schema-10 database missing its timer-interruption table. It preserves saved tasks, session checkpoints, trees and coins. An affected active timer stays in **Needs review**, and no unconfirmed time is added. The repair does not reconstruct missing interruption history.

Startup also checks the resulting database structure against the current migrations before starting the timer. Other missing or incompatible tables, columns, foreign keys, required indexes, validation checks or history-protection triggers produce a clear storage error instead of a late timer traceback. Extra legacy tables and columns are retained. If startup reports a schema problem, keep the full error and the existing database; do not delete it or create replacement records. Review a SQLite-safe backup or restore a verified backup before trying to repair unsupported damage.

Migrations from version 12 onward also record a content fingerprint. Startup refuses a changed file for an already applied migration. Earlier migration records retain their original names and timestamps; their historical file contents cannot be verified retroactively, so startup checks the resulting structure without inventing old fingerprints.

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
