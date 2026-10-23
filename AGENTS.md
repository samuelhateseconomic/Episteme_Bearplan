# BearPlans — shared agent guidance

Applies throughout this repository to Codex, Claude and other contributors.
Keep shared rules here; retain Claude's entrypoint in [CLAUDE.md](CLAUDE.md).
Use [docs/PROGRESS.md](docs/PROGRESS.md) as the single shared progress and handoff
record. Detailed review records remain evidence, not parallel task trackers.

## Read before working

1. Read this file, any applicable nested `AGENTS.md`, and the shared progress record.
   Claude should also read `CLAUDE.md` for its resumption/handoff workflow.
2. Inspect Git status, recent commits, the complete working diff and relevant
   untracked files. Understand unfinished work before changing it; never assume
   another agent's completion report proves the current tree passes.
3. Read the relevant planning documents and current reviews linked from progress:
   [build plan](BearPlans_Build_Plan.md),
   [review plan](BearPlans_Build_Review_Plan.md),
   [daily roadmap](BearPlans_Dated_Roadmap.md), and [README](README.md).

Explicit user instructions and the latest explicit product decisions take priority
over stale summaries. The roadmap supersedes timing only, not safety, persistence,
recovery or acceptance requirements. Keep proposed defaults distinct from confirmed
requirements. Record discrepancies in progress instead of silently weakening a
gate or rewriting historical evidence. Review filenames may use future target
dates; use their contents and commit history to determine which evidence is current.

## Product scope and completion rules

- BearPlans is a personal, local laptop productivity app. The primary target is the
  user's MacBook; development may also happen on Windows. Normal core operation is
  offline after setup. No hosting, public accounts, cloud models, cross-device sync,
  mobile, payments, distraction blocking or animated character in the current scope.
- Work within the authorized build. Keep one small ticket active; put new ideas in
  a later list. A calendar date is a target, not proof of completion. Current status
  and the next eligible build belong in progress; do not start it merely on handoff.
- A subtask is a task row with `parent_id`, in the same project as its parent.
  Nesting is one level only. Reject nonexistent parents, cross-project relationships,
  self-parenting and deeper nesting; do not introduce cycles.
- A task with no children has explicit completion control. A task with children
  derives completion entirely from them: it is complete exactly when all children
  are complete, with the completion instant of the last child completed.
- Reject direct completion or reopening of a parent container. Parent controls must
  never silently complete or reopen children. Show completed/total child progress.
  Completing the last child completes its parent; reopening a child or adding an
  unfinished child makes the parent incomplete. Repeated leaf completion/reopen
  requests preserve timestamps and revisions.
- Completion totals/statistics count leaf work items once, excluding containers.
  Additional parent work must be an explicit subtask. Removing the last child leaves
  an incomplete standalone task with explicit completion control, never a restored
  stale completion. M1 supports confirmed subtask removal; general task/project
  deletion and re-parenting remain deferred.
- New countdown sessions require an incomplete leaf task, scheduled or unscheduled.
  Completing a task during a running, paused or Needs review session preserves that
  session and its controls. Starting or finishing a timer never changes task
  completion. Measured sleep pauses at the last trusted checkpoint; waking or
  maintenance activity never resumes automatically. Unknown gaps, running-service
  restarts and clock discontinuities require explicit review. Continuing preserves
  the same session and excludes the gap; finishing saves confirmed time only.
  Paused restarts stay paused. Persist interruption records and replay-safe decisions;
  never estimate missing work or silently award it. Trees and coins use confirmed
  session time only; AI and integrations remain later builds. M2 Mac hardware
  acceptance requires actual Mac evidence. The user authorized M3 development
  before that acceptance, with combined M2/M3 Mac verification required before
  release readiness; deferral does not certify either milestone.
- One tree is enrolled atomically with each new forest-aware countdown; Pine is
  free, and the chosen owned species is locked at start.
  Sessions already present at the schema-9 upgrade remain ineligible, including
  unfinished sessions; never backfill on reads, retries or old finalization.
  Seedling is below 50% confirmed progress, sapling is at least 50%; mature requires
  finalized completed status, the full planned integer active duration and no
  unresolved interruption. Early/interrupted finishes save an unfinished tree.
  Pause/review preserve confirmed growth; recovery continues the same tree. One
  persistent tree per session and its outcome share the session transaction.
  Forest lives within Track and uses historical session context; task edits,
  moves and completion do not alter it. Tree artwork never earns time or completes
  tasks. Birch, Oak and Cherry are cosmetic purchasable species. Coin eligibility
  starts only with new coins-aware countdowns after schema 10; all earlier sessions
  stay ineligible, including unfinished sessions with trees. Capture the configured
  earning rate at start; multiply it by whole confirmed active minutes from the
  entire saved session. Persist one award, including zero, atomically with its
  finalized session/tree. Paused, review and uncertain time never earns coins.
  Purchases atomically revalidate displayed price, balance and ownership, then
  persist debit, ownership and replay result. Reused keys replay the original
  normalized request or conflict on different work; never overspend or backfill
  awards. Negative balances prevent new purchases. Rate 1 and Birch/Oak/Cherry
  prices 30/60/120 are configurable proposed defaults. Read-only statistics report
  current leaf completion/estimates and all-time saved intervals, with historical
  time retained after task removal. Saved-session corrections require a reason
  and reviewed preview, then revalidate revision, wallet and affected date totals
  inside the write transaction. Correct only consistent, finalized sessions with
  resolved interruptions. Retain immutable original interval ceilings and allow
  reductions/restoration within them; never add unconfirmed time, move dates or
  fill gaps. Persist before/after audit and replay result atomically with interval,
  session, existing-tree and captured-rate coin adjustments. Preserve the initial
  award, eligibility cutovers, purchases, task completion and closed snapshots.
  Reverse via another reviewed correction; never delete audit or adjustment rows.
- Daily streaks derive from corrected confirmed closed intervals of finalized sessions,
  including early/interrupted finishes and legacy sessions without coin/tree
  eligibility. Unfinished sessions and unresolved interruptions do not count.
  A day qualifies at 3,600,000,000 integer microseconds. Divide saved credit across
  local dates using UTC interval overlaps, conserving credit when wall duration
  differs from monotonic duration; never include paused or uncertain gaps.
  The current service timezone applies to all dates; changing it reattributes
  historical progress without rewriting records. Today counts when qualified;
  otherwise yesterday's consecutive run remains while today is unfinished.
  Derive from saved records rather than persisting a separate streak counter.
- Deadlines are date-only `YYYY-MM-DD` and never shift with timezone. Store actual
  instants as UTC ISO-8601 with `Z`, at microsecond precision. Compare timestamps as
  instants, not raw strings with mixed precision.

## Weekly planning rules

- A placement references one existing leaf task on a date; never clone tasks or
  copy completion into placements. A leaf may have several active planned dates,
  with at most **one placement per task/date**. Completion is shared across its
  dates, and totals count each scheduled leaf once. Parents appear as context and
  complete only when all their children complete. Preserve existing multi-date
  records and schema-7 compatibility; the later interface simplification does not
  restore a one-active-date constraint or remove saved dates.
- Drag a placement's icon handle to Move it, preserving its identity and other
  placements. Option/Alt does not change this operation. Initial scheduling is
  available for unscheduled tasks; remove the Add-another-day interface and modifier
  Add behavior (latest user refinement, 2026-10-16). Keep keyboard Move/remove date
  controls. Show the icon to the left of the project/parent-task context line,
  above the leaf/subtask title, with an accessible name and no visible Drag text;
  omit the open-board dragging instructions. Weekly cards show the due date, while
  their column identifies the planned day; omit redundant Planned-date metadata
  on open and historical cards. Keep planned dates in task planning, date controls,
  accessibility labels and saved records.
  Cancel, outside drops and same-day drops change nothing. Reject an
  occupied task/date destination atomically, explain the conflict and preserve all
  existing placements. Different tasks may share a date. Removing a placement keeps
  its task. Scheduling preserves task identity, project, notes, deadline, completion,
  session history and closed snapshots. Never discard legacy plans during migration.
- Unscheduled tasks remain accessible. Display planned dates separately from
  deadlines. Monday–Sunday weeks use calendar dates, not elapsed-hour arithmetic.
  Today is determined by the service using `BEARPLANS_TIMEZONE` (an installed IANA
  timezone), or the operating system's local timezone by default. The browser's
  timezone does not independently determine Today. No timezone settings UI exists.
- A scheduled standalone task must be unscheduled before gaining children; a
  scheduled subtask must be unscheduled before deletion. Reject those changes with
  a useful message instead of silently removing placements or scheduling containers.
- End Week requires a preview. In one transaction, freeze the displayed task,
  parent/project details, original placements and completion, then archive those
  placements with their original IDs/fields. Closing never modifies task records.
  Stored snapshots and historical placements are immutable; later edits, completion
  or permitted subtask removal cannot change the closed view. Show historical
  completion separately from current status. Count unique scheduled leaves once,
  excluding parent containers; empty weeks show 0/0 and 0%, never an undefined value.
- Reject all scheduling into closed weeks, and any move/removal of archived IDs,
  in shared domain functions as well as the interface. Repeated closure returns
  the original snapshot. Reopening is deferred; closure may be past, current or
  future because no date restriction was requested.
- Carryover requires a closed source, explicit selection and preview of destination
  dates in the immediately following Monday–Sunday week. Include only work that
  was unfinished at closure and still exists as an incomplete leaf. Explain current
  completion, removed tasks, new containers, closed destinations and existing active
  placements. Preserve task identity/fields/history and the closed source; create
  new destination placements, never new tasks or changes to historical rows.
- Revalidate previews inside serialized write transactions. Stale review, conflicts
  or failed writes leave no partial closure/carryover. Persist carryover operation
  IDs and results atomically; retries of the same normalized source/selections
  return the original result, while key reuse with different work/dates conflicts.
  Recurring work, advanced reports and bulk automatic carryover remain deferred.

## Architecture and data safety

- Extend the existing React/TypeScript/Vite interface, Python/FastAPI/Pydantic
  service, SQLite storage and shared Python domain functions. Keep one repository,
  one local service/Uvicorn worker and one database; reuse dependencies where practical.
  FastAPI serves the production interface from the same origin.
- Keep validation and business/completion rules in `backend/domain/`. All mutations
  use its application functions and short, serialized `Database.write()`
  transactions. Routes, future AI tools and connection adapters do not write SQL
  independently. Never wait on a model/provider inside a write transaction.
- Keep foreign keys enabled, WAL mode and versioned migrations. Add
  `backend/storage/migrations/NNNN_name.sql` for schema changes; never edit an applied
  migration and never put `BEGIN`/`COMMIT` in migration SQL. Preserve existing task
  IDs, timestamps, revisions and user fields through upgrades.
- User data lives outside source/build folders via `backend/platform/paths.py`.
  Never commit databases, tokens or personal content. Migration, corruption,
  interruption, restore and failure tests use disposable databases or safe copies,
  never the only saved user database. Use SQLite's backup API for a live WAL database;
  do not naively copy it. Failed updates must preserve recoverable data, never reset it.
- Preserve unrelated and uncommitted work. Do not discard, reset, overwrite or stash
  changes without understanding them and having authorization for that action.
- Bind to `127.0.0.1`; preserve loopback Host and same-origin mutation checks in
  `backend/app.py`. No CORS. Return structured `{"error": {"code", "message", ...}}`
  errors; failed saves must be actionable and keep the user's input available.
- Future AI/connections call the same application functions, stay outside write
  transactions while fetching/generating, and follow the build plan's bounded tools,
  revision/replay checks, preview/Undo and credential/privacy requirements.

## Commands and dependencies

Python 3.12+ and Node 24 LTS are the preferred setup; see README and
`frontend/package.json` for accepted Node versions.

```sh
python3 launch.py --no-browser
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pytest
npm --prefix frontend test
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

On Windows use `py launch.py` and `.venv\Scripts\python.exe`. Launcher options:
`--no-browser`, `--port N` (or `BEARPLANS_PORT`). Set `BEARPLANS_DATA_DIR` to a
disposable directory outside the repository when testing startup/persistence.
For hot reload, use `npm run dev` in `frontend/`; Vite proxies `/api` to the service.
The launcher reuses an existing instance, so launching again may retain stale backend
code. If UI/API versions disagree, identify the instance/data folder, stop it
gracefully, restart deliberately and verify persisted records; do not kill blindly.

Python dependency changes start in `pyproject.toml`, then regenerate the locks:

```sh
uv pip compile pyproject.toml --universal --python-version 3.12 -o requirements.lock
uv pip compile pyproject.toml --extra dev --universal --python-version 3.12 -o requirements-dev.lock
```

Frontend dependencies use `package-lock.json` and `npm ci`; do not add a second
package manager or rebuild the project from scratch on resumption.

## Verification, reviews and handoff

- Before implementation, state the user-visible acceptance scenario, affected
  records, rule/default changes and recovery/Undo behavior where relevant. Give a
  brief progress update after inspection, then continue routine authorized work.
- Verify requirements, diff and behavior; reported test totals are historical
  claims until supported by evidence for the build being reviewed. Run appropriate
  backend tests, frontend tests/typecheck/build and affected foundation regressions.
  Run the full core suite at milestone/release boundaries. Documentation-only changes
  need content/link/diff checks rather than an unrelated application test rerun.
- Persistence/schema changes need upgrade compatibility, rollback/retry and restart
  checks. Cover invalid input/relationships, completion transitions, leaf denominators
  and useful save errors. Timer/reward/storage/AI changes need behavioral and retry
  tests. Use fake clocks for timing boundaries; inspect UI changes at wide/narrow
  widths, keyboard navigation, disabled/loading controls and failure recovery.
- Detect the actual OS and report it. Never claim Mac launch or sleep/wake evidence
  from Windows/Linux. Browser visibility is not sleep evidence; unknown timer gaps
  must not silently earn time. Read the M0 measured sleep decision before later
  timer work; it does not replace the M2 hardware/recovery acceptance tests.
- Record exact commands/results, failures/skips, environment, evidence and issues
  in `docs/reviews/YYYY-MM-DD-<feature>.md`. Separate implementation review from
  milestone/operator review. Use **Pass / Pass with follow-ups / Fail** honestly;
  missing required evidence cannot become a pass to keep the calendar. Complete
  independent work and explicitly identify any remaining manual gate.
- Before stopping or transferring agents, update `docs/PROGRESS.md` with completed
  work, current work, relevant files/commits, checks actually run, pending manual
  evidence, blockers and the next concrete step. Link detailed reviews rather than
  maintaining duplicate status in each agent's instructions. Mark planned work as
  not started until implementation actually begins.
- Commit only when explicitly asked/authorized; scope the commit to relevant changes.
  Do not push unless separately authorized. A documentation/handoff request alone
  does not request a commit or authorize the next application build.
