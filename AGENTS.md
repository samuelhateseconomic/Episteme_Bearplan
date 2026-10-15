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
- Finishing a timer never automatically completes its task. Timers, rewards, AI
  and integrations are later builds; do not infer implementation from their plans.
- Deadlines are date-only `YYYY-MM-DD` and never shift with timezone. Store actual
  instants as UTC ISO-8601 with `Z`, at microsecond precision. Compare timestamps as
  instants, not raw strings with mixed precision.

## Weekly planning rules

- A placement references one existing leaf task on a date; never clone tasks or
  copy completion into placements. Multiple planned days are allowed, with a unique
  task/day pair. Parent tasks appear as context, not scheduled work.
- Move only the selected placement, preserving its identity. A destination that
  already contains that task is a conflict: leave all records unchanged and explain
  it. Removing a placement keeps the task and its other placements. Scheduling must
  preserve task identity, project, notes, deadline, completion and history.
- Unscheduled tasks remain accessible. Display planned dates separately from
  deadlines. Monday–Sunday weeks use calendar dates, not elapsed-hour arithmetic.
  Today is determined by the service using `BEARPLANS_TIMEZONE` (an installed IANA
  timezone), or the operating system's local timezone by default. The browser's
  timezone does not independently determine Today. No timezone settings UI exists.
- A scheduled standalone task must be unscheduled before gaining children; a
  scheduled subtask must be unscheduled before deletion. Reject those changes with
  a useful message instead of silently removing placements or scheduling containers.
- Week closure, snapshots, historical reports and bulk carryover are later work.

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
