# BearPlans — One-Day Feature Roadmap

Revised October 13, 2026. Start: October 14, 2026. Dates use America/Los_Angeles. Status: planned, not implemented or tested.

## 1. Revised delivery approach

This replaces the previous 10-hours-per-week calendar with daily feature builds. Assume one developer with 4–6 focused hours per day, including a short review, for October 14–31. Eighteen days provide 72–108 hours. If only 1–2 hours/day are available, the dates must move or feature scope must shrink.

Each feature gets one day for a small, usable version. A one-day timebox is a scope limit, not proof of completion. Deeper recovery testing, real usage and integration approval are separate gates. Failed required checks remain failures; reduce optional polish first and move unfinished essentials rather than mislabeling them as done.

The local laptop architecture, product rules and review standards remain. This roadmap targets a personal alpha; it does not promise a production-grade public application in eighteen days.

## 2. Targets

- October 17: usable weekly planner and previous-week history.
- October 19: countdown plus reviewed interruption handling.
- October 24: local core trial candidate with forest, coins, streaks, stats and backups.
- October 26: local assistant candidate with read and small action tools.
- October 27–29: connection prototypes if authorization is available.
- October 25–31: seven-day core-use trial, overlapping later feature work.
- October 31: personal alpha decision; only features passing their gates are included.

## 3. Daily builds

| Date (2026) | Main feature | One-day scope | End-of-day demonstration/review |
| --- | --- | --- | --- |
| Oct 14 | Local foundation | Frontend/backend skeleton, SQLite migration, launcher, local-only access. Prepare model setup/download if needed. | Launch locally, save a record, restart and retrieve it. Record a quick Mac sleep-handling experiment. |
| Oct 15 | Projects and tasks | Create/edit projects, tasks and subtasks; notes, deadline, estimate and completion. | Create a real course task and subtask; edits persist; completion does not double-count parent and child. |
| Oct 16 | Weekly planning | Projects beside the weekly board, Today, selected day, assignment and moving work. | Assign a task to a day, move it and preserve its deadline/identity. |
| Oct 17 | Weeks and history | Previous-week navigation, close-week snapshot, carry unfinished work forward. | Close a sample week, revisit its counts and move work without duplication. |
| Oct 18 | Countdown | Dedicated Track screen; start from a task or direct navigation; 1–180 minutes; pause/resume/finish; compact timer. | Both entry points work, an unscheduled task can be tracked, and only one active/paused session exists across tabs. |
| Oct 19 | Session recovery | Timestamp/interval persistence, expiry, refresh/restart recovery, sleep pause or Needs review fallback, retry-safe finish. | Reopen an interrupted session; uncertain gaps are not silently credited; repeated finish saves once. |
| Oct 20 | Growing forest | One free species, three growth stages and a session-linked tree collection. | A completed countdown plants one tree; early finish keeps time with an unfinished tree. |
| Oct 21 | Coins and shop | Coin ledger, three purchasable species, balance/ownership and reward adjustments. | Earn once, buy a species, reject insufficient funds and review correction behavior. |
| Oct 22 | Daily streak | Accumulate 60 active minutes; progress indicator; configured timezone and midnight allocation. | Two 30-minute sessions qualify; 59 minutes does not; paused time is excluded. |
| Oct 23 | Statistics | Completion and tracked-time totals by day/project/task; estimates versus actual time; session correction. | Known fixture totals match reports; correcting a session updates rewards and streaks consistently. |
| Oct 24 | Backup and core launch | Database backup/restore, data separate from code, migration safeguards, offline startup and basic local request protection. | Restore to a clean location; run without internet or model; review core regressions. Freeze a core trial candidate. |
| Oct 25 | Local assistant chat | Ollama connection, contextual panel, typed read tools for task/day/week lookup and exact summaries; bounded calls and model errors. | Ask about today's work and time totals; results match Python; unavailable model leaves the core operational. |
| Oct 26 | Assistant actions | A small tool set: create/update/assign tasks and start/pause/finish timers; revision/replay validation. Larger replans use a reviewed structured proposal. | Explicit requests work; ambiguous targets ask for clarification; edits have Undo; stale proposals cannot overwrite new work. |
| Oct 27 | Google Calendar connection | Read-only selected calendars, Keychain credentials, local event cache, source IDs, manual sync and visible status. | Sync twice without duplicates; show stale/offline state; test cancellation and revoked-access behavior. Scope live-account completion on access working. |
| Oct 28 | Canvas connection | Selected-course assignment import, source links, due dates, review inbox and duplicate prevention. | Repeat an import; preserve user edits on a changed deadline; missing dates remain explicit. Conditional on permitted API access. |
| Oct 29 | Gmail connection | Selected labels/filters, local extraction into suggested tasks, source links and manual review. | Uncertain dates are reviewed, duplicate messages do not duplicate tasks, and source text cannot authorize actions. Conditional on permitted access. |
| Oct 30 | Regression and AI evaluation | Run core and integration fixtures, 30 AI scenarios, slow-model responsiveness checks and high-priority fixes. | Exact stats match; no unauthorized mutations in the fixed set; evaluate the proposed 90% AI success gate. Record failures openly. |
| Oct 31 | Personal alpha release | Review seven-day trial, verify backup restore, fix remaining release blockers and tag the passing build. | Demonstrate a real plan-to-countdown-to-reward workflow and list included, provisional and deferred features. |

Connection rows allocate a one-day prototype slot. Provider setup/approval is not under the developer's control. Full incremental sync, recurrence coverage and resilience must pass their required cases before the connection is described as reliable. A prototype failing that gate stays disabled or explicitly provisional; the local core can still ship.

## 4. Scope to keep a feature within a day

- Use simple assignment buttons before elaborate drag-and-drop.
- Start with basic forms and one consistent laptop layout.
- Use three discrete tree growth stages and four total species.
- Keep shop prices and coin rate configurable.
- Query exact plans/stats directly in Python. Use text search initially; embeddings are deferred unless retrieval evaluation demonstrates a need.
- Expose a small set of typed AI tools, with request IDs and record revision checks. No arbitrary Python/SQL/shell tool.
- Use manual and on-launch connection sync first. Add scheduled background synchronization only after reliable import/update behavior works.
- Keep a simple model selector. Extensive provider options, cloud models and hardware tuning are outside this build.
- Keep one application/service and one local database. No hosting, mobile, public accounts or cross-device sync.

Some one-day scopes are ambitious, especially timer recovery, assistant actions and provider connections. Their gates must stay intact. The day delivers the smallest passing version; additional polish enters a later backlog.

## 5. A daily working pattern

Allocate approximately 15 minutes to the acceptance scenario, 2.5–4 hours to implementation, 45–60 minutes to relevant tests/demo, and 15 minutes to the review record. Use the remaining time for fixes.

Daily record:
- Date, feature and build/commit ID.
- Expected behavior and any rule changes.
- Checks performed, actual results and evidence.
- Issues, severity and next action.
- Decision: Pass / Pass with follow-ups / Fail.
- Next feature only when its prerequisites pass.

Visual-only changes require visual review. Timer, reward, storage and AI-action changes require meaningful behavioral and retry tests. Fake clocks cover duration boundaries; actual Mac sleep/wake needs a hardware demonstration. Private-data exposure, data loss, wrong time credit, duplicate rewards, failed restore and unauthorized AI actions block release.

## 6. Seven-day trial and dependency handling

Use the frozen core candidate on October 25–31 while assistant and integration work occurs on separate development changes. Keep personal data backed up; use copies/fixtures for failure tests. Each day, note real tasks tracked, friction, unexpected time, missing data and reward consistency. Merge core fixes into the candidate only after their affected checks pass.

Trustworthy intervals precede rewards/streaks; working application functions precede AI tools. If a day fails, use October 30's fix slot where feasible, reduce optional scope, and revise dependent dates. Never advance a broken timer just to keep the calendar.

On October 31, release the local core only if its seven-day trial and required checks pass. Include assistant/connections only if their own gates pass. State any untested live provider cases; fixture success alone does not certify real account behavior.

The earlier build and review documents remain technical references. This one-day calendar supersedes their weekly scheduling assumptions, not the safety, persistence, recovery or acceptance requirements.

