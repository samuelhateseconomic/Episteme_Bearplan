# BearPlans — working rules

Personal, local-only Mac laptop planner: weekly planning, task-linked countdowns, forest/coins/streaks, stats; local AI and connections later. Planning docs (repo root): `BearPlans_Dated_Roadmap.md` is the **current schedule**; `BearPlans_Build_Plan.md` (architecture, product rules) and `BearPlans_Build_Review_Plan.md` (acceptance gates, severities) define the requirements. The roadmap overrides their timing only, never their safety, persistence, recovery or acceptance rules.

## Current milestone

**M0 / Oct 14 — Local foundation: passed** on the target Mac, including the sleep/wake experiment (`docs/reviews/2026-10-14-local-foundation.md`).
**M1 / Oct 15 — Projects and tasks: implementation review Pass on 2026-10-13.** Schema version 2. Projects (create, rename), task/subtask editing, notes/deadline/estimate, derived completion, leaf-only totals and confirmed subtask removal. Current evidence and separate gate decisions: `docs/reviews/2026-10-13-m1-takeover.md`. Claude's earlier draft review is historical, not current proof.
**Projects/tasks build review: Pass.** The operator confirmed all six hands-on checks passed on 2026-10-13. The broader weekly-planner gate still requires the Oct 16/17 builds, which remain unimplemented. Weekly planning is the next eligible build; do not start it without a new instruction.

## Rules

- One FastAPI service, one SQLite database, bound to 127.0.0.1. No hosting, accounts, cloud models, sync or mobile.
- All mutations go through application functions in `backend/domain/` using `Database.write()` (serialized, short transactions). Routes, future AI tools and sync adapters never write SQL directly. Never hold a write transaction while waiting on a model or provider.
- Schema changes add a new `backend/storage/migrations/NNNN_name.sql`; never edit an applied migration. No BEGIN/COMMIT inside migration files.
- User data lives outside the source tree (`backend/platform/paths.py`). Never commit databases, tokens or personal data. Test against temp dirs/copies, never the real data folder.
- Store instants in UTC ISO-8601 with `Z`. Validate input in the domain layer; return `{"error": {"code", "message", ...}}`.
- Keep local request protection: loopback Host check and same-origin check on mutations (`backend/app.py`). No CORS.
- A subtask is a task with a `parent_id`, not a separate record. Nesting is one level: a subtask cannot have subtasks, which is what makes a parent cycle impossible.
- **Completion:** a task with no subtasks is complete when marked complete. A task with subtasks has no completion of its own — it is complete exactly when every subtask is, and its completion time is when the last one was completed. Both direct completion and reopening of containers are rejected without changing children. Adding an unfinished child makes a parent incomplete. Repeated leaf completion/reopen requests are no-ops.
- Count only leaf work items in completion totals. Additional parent work must be an explicit subtask. Removing the last child leaves the parent incomplete with explicit completion control; never restore stale completion. Only subtask removal is supported in M1, with UI confirmation. General deletion and re-parenting remain deferred.
- Finishing a timer never automatically completes a task. No timer exists in this build.
- Deadlines are date-only (`YYYY-MM-DD`) and never move with a timezone. Instants stay UTC with `Z`; write them at microsecond precision so stored timestamps stay comparable.
- Proposed product defaults (coin rate, prices, streak threshold) are configurable, not confirmed requirements. Changing a rule means updating its acceptance scenario, not the expected result.
- Scope: one feature per day at its smallest passing version. New ideas go to a later list. A failed required check stays a failure; never mark work done to keep the calendar.

## Workflow

- Run: `python3 launch.py` (Windows: `py launch.py`; `--no-browser`, `--port N`). Needs Python 3.12+ and Node 24 LTS. Dev deps: `.venv` python `-m pip install -r requirements-dev.lock`.
- Tests: `.venv` python `-m pytest` (includes real service restart and an installed-Chrome/Edge browser journey); `cd frontend && npm test && npm run typecheck`.
- Dependencies: edit `pyproject.toml`, then `uv pip compile pyproject.toml --universal --python-version 3.12 -o requirements.lock` (add `--extra dev -o requirements-dev.lock` for dev). Frontend uses `package-lock.json` (`npm ci`).
- Each build: state the acceptance scenario first; implement; run relevant checks (timer/reward/storage/AI changes need behavioral + retry tests; visual changes need a visual check at wide and narrow widths); write a short record in `docs/reviews/YYYY-MM-DD-<feature>.md` with commit, checks, evidence, issues and **Pass / Pass with follow-ups / Fail**.
- Commit only when asked.
