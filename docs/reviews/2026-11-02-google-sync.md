# Google Calendar and Google Tasks sync — decisions and progress

Started 2026-11-02. Status: **step 1 passed; step 2 (Google Tasks sync) built and checked live; steps 3–4 not started.**

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
2. Google Tasks sync — **built 2026-11-02, awaiting the user's hands-on check and commit.**
3. Optional planned start time + "BearPlans" calendar events with 30-minute reminders.
4. Read chosen calendars, show events beside days, event → task.

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
