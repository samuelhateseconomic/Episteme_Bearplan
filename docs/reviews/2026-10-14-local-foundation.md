# Review record: Local foundation (M0, Oct 14 roadmap row)

**Build/commit:** uncommitted working tree on top of `23786cf`. Reviewed 2026-10-13 (the build was pulled forward from the Oct 14 slot).
**Milestone and ticket:** M0, first foundation build. Covers the React/TS interface, FastAPI service, SQLite migration 0001, shared `create_task`/`list_tasks`, task entry and saved-task list, data outside the repo, and one launch command.
**Expected behavior:** `python3 launch.py` starts a loopback-only service and opens the interface. You enter a task and it appears in the saved list. After you stop and relaunch, the same task (same ID) is still listed.
**Rule/default changes:** none. Proposed rules this build adds:
- Task titles are 1–200 characters after trimming whitespace and invisible characters.
- The default port is 8765.
- One running instance is allowed per data folder.
**Affected records/functions:** `tasks` and `schema_migrations` tables; `backend/domain/tasks.py` (`create_task`, `list_tasks`).
**Environment:**
- Windows 11, Python 3.14.5, Node 24.16.0, SQLite 3.50.4.
- Chrome or Edge, driven by Playwright 1.64.
- The target Mac was **not** available.

## Checks run and outcomes

| Check | Result |
| --- | --- |
| `pytest` (74 tests): paths, migrations, domain, API/local-only protection, real-process restart, second instance, busy port, corrupt DB, browser journey | Pass |
| `npm test` (8 component tests), `npm run typecheck`, `npm run build` | Pass |
| Restart through the real service process: graceful stop, and abrupt kill; task re-read with an identical record | Pass |
| Exact launch command `python launch.py --no-browser --port 18766` run twice against a scratch data folder. The task created in run 1 was listed in run 2. Both runs exited 0 and printed "BearPlans stopped." | Pass |
| A data folder inside the repository is refused, and no `.sqlite3` file appears in the source tree | Pass |
| Second instance on the same data folder points to the running one and leaves it unaffected | Pass |
| A cross-origin POST, a non-loopback Host, or `Sec-Fetch-Site: cross-site` is rejected and nothing is saved | Pass |
| A failed migration rolls back. A newer or unknown schema is refused. A corrupt DB gives a clear error and the file is left unchanged | Pass |
| Visual review at 1280 px and 375 px, dark mode, and with the service down (`evidence/`). No horizontal overflow, visible focus, the typed title is kept on error | Pass |
| Independent review: 5 reviewers plus adversarial verifiers. 12 findings upheld: 1 medium (corrupt-DB traceback), the rest low. All fixed and re-tested | Pass |

Startup transcript (path shortened):

```
BearPlans 0.1.0
  data:   ...\scratchpad\launch-data
  schema: version 1
  open:   http://127.0.0.1:18766/  (Ctrl+C to stop)
BearPlans stopped.
```

## Issues

| Severity | Issue | Next action |
| --- | --- | --- |
| Gate blocker (evidence missing) | The Mac sleep/wake experiment (lid close, sleep vs hidden tab) is not done. It needs the real Mac. | Owner: user. Run it on the Mac, record the observations here, and choose native power events or the "Needs review" fallback. |
| Gate blocker (evidence missing) | A fresh-clone launch on macOS has not been run (`python3 launch.py`, first-run setup, restart). | Owner: user. Repeat the launch and restart scenario on the Mac. |
| Low | Request protection allows requests with no `Origin` header (curl, local scripts). This is by design for local tools, and the full request-protection pass is scheduled for Oct 24. | Revisit on Oct 24. |
| Low | The browser test is skipped when neither Chrome nor Edge is installed. | Install Chrome on the Mac to run it there. |

## Decision

- **Change review (requested foundation build): Pass.** Every requested item is implemented and has evidence, and no blocker remains in the code.
- **M0 milestone gate: not yet passed.** The required Mac sleep/wake observation and the on-Mac repeat are missing. Do not start Oct 15 (M1) work until they are recorded.
