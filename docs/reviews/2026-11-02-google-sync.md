# Google Calendar and Google Tasks sync — decisions and progress

Started 2026-11-02. Status: **steps 1–3 done; step 4 built and checked live 2026-11-03, awaiting the user's check and commit.**

## User decisions (2026-11-02)

The user asked for Google to send notifications, so this connection **writes** to
the user's Google account (a change from the earlier read-only plan for M6).

- **OAuth client:** Desktop app type, not marked "for an AI-powered agent". File at
  git-ignored `.secrets/google_oauth_client.json` (mode 600). Sign-in tokens are
  stored next to it in `.secrets/`, never logged, printed or committed.
- **Reading calendars:** the user picks which of their calendars BearPlans reads.
  Events are shown beside each day **and** any event can be turned into a task.
  BearPlans never changes the user's own calendars.
- **Calendar notifications:** planning gains an optional **start time**. A planned
  task with a time becomes an event (length = the task's estimate) with a popup
  reminder **30 minutes before**, in a calendar BearPlans creates ("BearPlans").
  Writing is limited to that calendar (scope `calendar.app.created`).
- **Google Tasks:** **every** project, task and subtask syncs. Project → task list
  (named the same as the project), task → task, subtask → subtask (both sides allow
  one level only). BearPlans remembers which lists it created and touches only those.
- **Direction:** BearPlans → Google, plus completion ticked in Google comes back to
  BearPlans. Other edits made in Google are overwritten by BearPlans.
- **Google task date:** the deadline if set, else the next planned day, else none.
  Google Tasks accepts a date only; its own app decides when to notify.

## Known limits told to the user

- The Google Tasks permission (`tasks`) covers all of the user's task lists; there is
  no app-only variant. BearPlans enforces "only lists it created" in code.
- Google Tasks reminders cannot be set by an app; only the due date.
- The user must enable both the Google Calendar API and the Google Tasks API in the
  Cloud project. Permission is granted at sign-in, not by the credential file.

## Build steps

1. Access spike `tools/google_spike.py` — **passed 2026-11-02**: all four permissions
   granted; 5 calendars, 25 primary events in 7 days, 4 task lists (counts only).
   First attempt was blocked (403 access_denied) until the user added themselves as a
   test user; the consent screen app name was "ChatGPT" (renamed by the user).
2. Google Tasks sync — **committed `d41534e` (2026-11-02).**
3. Optional planned start time + "BearPlans" calendar events with 30-minute reminders — **built 2026-11-03.**
4. Read chosen calendars, show events beside days, event → task — **built 2026-11-03.**

## Step 2 — Google Tasks sync (built 2026-11-02)

Files: `backend/platform/google.py` (sign-in with loopback + PKCE, token refresh,
Tasks client; Google API hosts only, no redirects, verified TLS),
`backend/storage/migrations/0017_google_tasks.sql` (`google_task_lists`,
`google_tasks`, `google_sync`; no foreign keys so removed tasks can be removed from
Google), `backend/domain/google_tasks.py` (sync + background service),
`backend/routes/google.py` (`GET /api/google`, `POST /connect`, `/disconnect`,
`/tasks/sync`), `backend/app.py` (service started in lifespan; a successful change
under `/api/` nudges a sync ~4 s later; otherwise every 2 minutes),
`frontend/src/Google.tsx` (new `#google` tab: Connect/Reconnect, Disconnect, Sync now,
counts, last sync, errors, missing permissions), `api.ts`, `App.tsx`.

Implementation decisions (mine, within the user's decisions):
- A tick made in Google applies only if BearPlans still has the completion it last sent;
  otherwise BearPlans wins and is sent again.
- Ticking a parent in Google completes its open subtasks; unticking a parent in Google
  is not applied (its completion comes from its subtasks).
- A parent with no deadline gets the next planned day of its subtasks.
- A list or task deleted in Google is created again; a task moved to another project
  is deleted from the old list and created in the new one.
- Each created Google item is recorded in its own short write, so an interrupted sync
  never duplicates on retry. Failures are saved in `google_sync.last_error`.
- Ticks that arrive by background sync don't refresh an open page until the next
  reload or Sync now (follow-up).

Checks (2026-11-02):
- `tests/test_google_tasks.py`: 15 passed (fake Google). Full pytest: 906 passed,
  1 Windows-only skip. `test_bcourses.py` migration-order assertion updated.
- `frontend/src/Google.test.tsx`: 4 passed; Vitest 159 passed; typecheck and build pass.
- Live check against the user's Google Tasks from a throwaway database: 2 lists and
  4 tasks created; deadline due, subtask nesting and parent date correct; tick in
  Google came back; rename and reopen sent; removed subtask removed; both test lists
  then deleted. Counts only were printed.

Not yet done: the user's first real sync (migration 16 → 17 runs at the next launch,
with the automatic backup first); a real-Chrome test of the Google tab.

## Step 3 — start times and BearPlans calendar events (built 2026-11-03)

Files: `backend/storage/migrations/0018_planned_time_and_calendar.sql`
(`placement_times`, `google_calendar`, `google_events`), `backend/domain/planning.py`
(`Placement.start_time`, `set_placement_time`; reads fall back when the table is absent
for legacy-upgrade paths), `backend/routes/planning.py` (`PUT /api/placements/{id}/time`),
`backend/domain/google_calendar.py`, `backend/platform/google.py`
(`GoogleCalendarClient`; shared `_GoogleApi`), `backend/domain/google_tasks.py` (each sync
runs Tasks then Calendar; `synced_events`), `backend/app.py`, `frontend/src/WeeklyPlanner.tsx`
(start-time form inside "Move or remove"; time shown on cards and in the summary),
`frontend/src/Google.tsx`, `api.ts`.

Implementation decisions (mine, within the user's decisions):
- Start time is stored in its own table, not a new `planned_items` column, so placements
  and archived closed-week copies keep exactly their existing fields (13 existing
  upgrade/close tests compare full rows).
- Event length = the task's estimate, else 30 minutes. Title = task title; description
  = project (› parent) and notes. Times are sent with the local UTC offset.
- Only open tasks get events. Finishing the task, clearing the time or removing the
  placement deletes the event only if it hasn't started; past events are never deleted,
  so closing a week keeps them. A placement whose time already ended gets no new event.
- The calendar is created only when the first timed task needs it; if the user deletes
  it in Google, a new one is made at the next sync. Edits to its events are overwritten.
- Carryover to a new week does not copy the start time (follow-up if wanted).

Checks (2026-11-03):
- `tests/test_google_calendar.py`: 16 passed. Full pytest: 922 passed, 1 Windows-only skip.
- `frontend/src/PlacementTime.test.tsx`: 2 passed; Vitest 161 passed; typecheck and build pass.
- Live check from a throwaway database in a temporary calendar named
  "BearPlans sync check": event at 14:00 Pacific, 45 minutes, popup reminder 30 minutes;
  retimed to 09:30 on the same event; repeat sync changed nothing; finishing the task
  removed it; the temporary calendar was then deleted.

## Step 4 — reading followed calendars (built 2026-11-03)

Files: `backend/storage/migrations/0019_google_calendar_reading.sql`
(`google_source_calendars`, `google_source_events`, `google_event_tasks`),
`backend/domain/google_reading.py`, `backend/platform/google.py` (`calendar_list`,
`list_events`: GET only), `backend/domain/google_tasks.py` (each sync also re-reads
followed calendars), `backend/routes/google.py` (`GET/PUT /api/google/calendars`,
`POST /calendars/refresh`, `GET /events`, `POST /events/add`), `backend/routes/planning.py`
(`GET /api/planning` now also returns `calendar_events` for the shown week, so the Plan
screen needs no extra request), `backend/app.py`, `frontend/src/Google.tsx` ("Calendars to
show" picker), `frontend/src/WeeklyPlanner.tsx` (`CalendarEvents` under each day:
time or All day, calendar, location, "Add as task" / "Added as a task"), `api.ts`, `styles.css`.

Implementation decisions (mine, within the user's decisions):
- No calendar is followed until the user ticks one; the BearPlans calendar itself is
  not offered. Events are cached from 14 days back to 56 days ahead, replaced on each sync.
- "Add as task" creates a task in the default project titled like the event, with the
  event's length as the estimate and notes giving the calendar, time, place and Google
  link; it is planned on the event's first day (if that week is open) **without** a
  start time, so it doesn't create a second event. Repeating Add returns the same task.
- Only `https://www.google.com/calendar/` links are kept.

Checks (2026-11-03):
- `tests/test_google_reading.py`: 7 passed. Full pytest: 929 passed, 1 Windows-only skip.
- `frontend/src/CalendarEvents.test.tsx` 2 and a new picker test in `Google.test.tsx`;
  Vitest 164 passed; typecheck and build pass. A first version fetched events
  separately and broke 12 existing request-order tests; events now come with the plan.
- Live read-only check (throwaway database, counts only): 5 calendars offered (1 main);
  28 events this week, 204 in the window; event → planned task worked.

## Follow-ups done 2026-11-03

- **Open page refreshes after a background sync.** `GoogleSyncService.version` goes up
  when a sync changes what the page shows (task revisions/completion, followed-calendar
  events or calendars; compared by fingerprint before/after). `GET /api/google/changes`
  returns it; `useGoogleChanges` in `Google.tsx` (used by `App.tsx`) checks every 30 s
  while visible and on focus/visibility, never at mount, and refreshes projects, tasks
  and the week plan when it changes. Tests: backend version test; fake-timer hook test.
- **Real-Chrome test** `tests/test_google_browser.py` (fake Google clients, connected
  auth): choose a calendar → event under today → Add as task (45-min estimate, place in
  notes) → start time 23:15 → Sync now puts it in the BearPlans calendar with a 30-minute
  popup → a tick made in Google shows as checked after a focus check → 375 px without
  horizontal overflow. Skips after 23:00 Pacific (the event must still be upcoming).
  Screenshots: `.evidence/google-20261103/`. Fixed "1 tasks in 1 lists" plurals.
- Checks: full pytest 931 passed, 1 Windows-only skip; Vitest 165; typecheck and build pass.

## Follow-ups decided and done 2026-11-03 ("1. yes 2. Yes")

- **Start times carry over.** When unfinished work carries to the next week (End Week
  carryover and the assistant's carryover, which share `weeks._apply_carryover_tx`),
  the new placement keeps the start time of the task's last planned day in the closed
  week. The time is read from the closed week's snapshot (placements in it include
  `start_time` since migration 0018; weeks closed earlier carry no time). Carryover
  candidates and preview items now show `start_time`; the carried placement then becomes
  a BearPlans calendar event on the next sync. Test:
  `test_carryover_keeps_the_last_days_start_time`.
- **"From your calendar" is collapsible.** Each day's section is a `<details>` closed
  by default, titled "From your calendar (N)". Vitest and the real-Chrome test open it
  before adding an event as a task.
- **Carryover screen shows the time.** Each eligible task says "Keeps its start time,
  2:30 PM", and the review reads "Planned Oct 22, 2026 at 2:30 PM". Vitest test added.
- Checks: full pytest 932 passed, 1 Windows-only skip; Vitest 166; typecheck and build pass.

## Credentials moved to the data folder (2026-11-03, connection setup step 1)

User asked to manage credentials from the app instead of VS Code
([plan](../../BearPlans_Build_Plan.md#connection-setup-inside-the-app-requested-2026-11-03-plan-only--not-started)).
Step 1: the bCourses token and both Google files now live in
`~/Library/Application Support/BearPlans/secrets/` (folder 700, files 600). At startup
`move_legacy_secrets()` copies the three known files from the code folder's `.secrets/`
once (never overwriting, old folder left in place, a marker stops a second copy so a
credential removed later is not restored). Setup messages point to the new folder.
Checks: `tests/test_secrets_location.py` (5); pytest 937 passed, 1 Windows-only skip;
Vitest 166; typecheck and build pass. The real copy runs at the user's next launch;
the dev spike scripts in `tools/` still read `.secrets/`.
