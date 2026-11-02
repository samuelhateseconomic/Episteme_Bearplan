# bCourses (Canvas) connection — November 1, 2026

## User decisions (2026-11-01)

- Connect bCourses **before** Google Calendar.
- Tokens live in the git-ignored file `.secrets/bearplans.secrets.env`
  (`BCOURSES_TOKEN=`; folder 700, file 600) instead of Mac Keychain.
- After vetting Canvas MCP servers: **direct read-only API**, not MCP.
- Assignments go to a **review list**; **Add** makes one task in a project named
  after the course, with the due date and a bCourses link in the notes.
- The user **picks which courses** to follow.
- Assignments **without a due date are shown**, marked "No due date", and can be added.

## MCP vetting (read code only, nothing run)

| Server | Result |
| --- | --- |
| `rbrtlol/canvas-readonly-mcp` | Best MCP fit: local stdio, GET only, token only to the Canvas origin, manual redirects. New (2026-10-30), single author, keeps its own content cache. Not used. |
| `boyuchengz/canvas-mcp` | Rejected: hosted-server design keeps the token in the cloud. |
| `vishalsachdev/canvas-mcp` | Rejected: write and instructor tools. |

## Access spike

`tools/bcourses_spike.py` (counts only). Token accepted; 12 active courses; 90
assignments readable, 0 courses refused; 46 dated; fields due_at, html_url,
lock_at, points_possible, updated_at. python.org Python on macOS lacked a CA list:
certificates are verified against `/etc/ssl/cert.pem`, never disabled.
The first token was pasted into chat; the user was asked to revoke and replace it.

## Design

- `backend/platform/secrets.py` reads `KEY=value` from the secrets file
  (`BEARPLANS_SECRETS_FILE` overrides; tests point it at an empty temp path).
- `backend/platform/bcourses.py`: GET only, `https://bcourses.berkeley.edu` only,
  header token, string IDs, pagination limited to that host, no redirects,
  verified TLS, user-safe error messages that never include the token.
- Migration `0016_bcourses.sql`: `source_courses`, `source_assignments`,
  `source_sync`. Schema 15 → 16; real data upgrades at next launch after the
  automatic backup.
- `backend/domain/bcourses.py`: refresh fetches outside transactions, then one
  write stores courses (and assignments of followed courses). A refresh never
  changes the user's task. Due date → local day via the application calendar.
  A later due-date change (by local day, not time) is flagged; "Use new due
  date" changes only the task deadline, "Keep mine" only clears the flag.
  Add is idempotent; a task removed later makes the assignment available again.
  Assignments missing from bCourses stay, marked "No longer listed".
  Only `https://bcourses.berkeley.edu/` links are kept.
- Routes `/api/bcourses` (state, `refresh`, `courses`, `assignments/{id}/add`,
  `/dismissed`, `/due-date`), same loopback/same-origin protection; bCourses
  failures return 502 with a structured error.
- Frontend: new **bCourses** tab — course picker, Upcoming, No due date,
  Past due (collapsed), Added, Dismissed, due-date change review, Refresh,
  last-updated time and errors.

## Checks

- `tests/test_bcourses.py`: 18 tests (refresh cache, follow, Add once with course
  project, local due day, refresh keeps user task, due-change review, time-only
  change, dismiss/restore, removed items, removed task, failed refresh keeps
  cache, HTTP flow/errors/origin, unconfigured service, secrets parsing and
  permissions, client header token/pagination/host/error messages).
- `frontend/src/BCourses.test.tsx`: 5 tests.
- Full pytest 889 passed + 1 fixed assertion (8/8 rerun), 1 Windows-only skip;
  Vitest 155; typecheck and build pass.
- Live read-only smoke test against bCourses with a throwaway database: 12
  courses, 90 assignments, 46 dated, 90 with links, no error (counts only).

- Real Chrome (`tests/test_bcourses_browser.py`, in-process service with a fake
  client): first visit lists courses only; choose and save a course; review list
  with link and no import before Add; Add creates exactly one task with the local
  due day and the course project appears in Plan; Refresh flags a moved due date;
  "Use new due date" updates the deadline; no horizontal overflow at 1440/375 px;
  no page errors. Screenshots: `.evidence/bcourses-20261101/`.

## Open

- User hands-on review in the preview (port 8878).
- Assistant Sources specialist (read-only questions over the cache) not built.
- Automatic periodic refresh not built; Refresh is manual.
