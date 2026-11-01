# BearPlans seven-day real-use trial

Prepared November 1, 2026 for this Mac. Updated when parallel assistant development
was authorized: the tested core now has a separate runnable Desktop copy.
Candidate:
`bearplans-local-core-2026-11-01`. This checklist is prepared; no day of actual
use has been recorded yet. Start Day 1 on the date you first use it for real work.
If that is November 1, seven daily entries cover November 1–7; review after Day 7.
Do not count the earlier synthetic or stopwatch checks as trial days.

The [candidate manifest](reviews/2026-11-01-core-trial-candidate.json) records the
tested working tree, including uncommitted backup/restore work. The
[readiness review](reviews/2026-11-01-final-planner-readiness.md) records the tests.
This selects a local personal trial, not a full release or an unqualified M2/M3
pass. Deep Idle and Hibernate were observed. Separate Standby type 5 remains
unverified, with the source-version limitation in the
[platform assessment](reviews/2026-11-01-standby5-capability.md). No new system
power setting, overnight test, three-hour test or stopwatch is required here.

## 1. Open Terminal and locate the project

Press Command+Space, type `Terminal`, press Return. Call this **Tab A**.
Copy the contents of each code block, then press Return.

```sh
cd "/Users/hiberkeley/Desktop/BearPlans-core-trial-2026-11-01"
```

Open these instructions locally if helpful:

```sh
open -a TextEdit "/Users/hiberkeley/Desktop/BearPlans-core-trial-2026-11-01/docs/CORE_TRIAL_CHECKLIST.md"
```

## 2. Verify the candidate before its first launch

Run this whole block in Tab A. It reads code/build files only; it does not open
your database. It must print `Candidate verified` and the fingerprint below.

```sh
.venv/bin/python - <<'PY'
import hashlib
import json
from pathlib import Path
from backend.platform.build_info import current_build

manifest = json.loads(Path("docs/reviews/2026-11-01-core-trial-candidate.json").read_text())
expected = {**manifest["source_and_test_sha256"], **manifest["built_artifact_sha256"]}
different = [name for name, digest in expected.items()
             if not Path(name).is_file()
             or hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest]
build = current_build()
if different or build.build_fingerprint != manifest["build_fingerprint"]:
    raise SystemExit("Candidate differs; stop and send this result: " + repr(different))
print("Candidate verified:", manifest["candidate_id"])
print("Build:", build.build_fingerprint)
print("Schema:", build.supported_schema)
PY
```

Expected fingerprint:
`4ba3c8054da2b3db3ffa00beb480485fb376bc9d59567548078a0e860aab05da`.
Expected schema: `13`. If verification fails, retain your data and report it before
using this as the recorded candidate. This is a version record, not an immutable
checkout; a later source/build change requires a recorded candidate update and
appropriate checks. Documentation/daily-note edits do not change the app version.
The Desktop copy has its own Python environment and the original production
build. Assistant development takes place in the original Projects repository.
The copy contains no personal data; its launch still selects your normal data
folder explicitly below. Keep code edits out of the trial copy.

## 3. Start your normal copy

Use your normal data folder, **not** the source-test/restored-test Desktop folders
or the temporary final-planner test. If you normally use a different personal data
folder, use that same folder and record it rather than creating a second trial.

If your normal copy is already running, finish or pause any active session before
a deliberate service restart. In the Terminal tab that started that copy, press
Control+C once, wait for `BearPlans stopped.` and the command prompt. Do not kill
an unidentified process. If you cannot find its Terminal, report that rather than
stopping another service.

In **Tab A**, run:

```sh
BEARPLANS_DATA_DIR="$HOME/Library/Application Support/BearPlans" \
BEARPLANS_TIMEZONE=America/Los_Angeles \
BEARPLANS_COINS_PER_MINUTE=1 \
BEARPLANS_BIRCH_PRICE=30 \
BEARPLANS_OAK_PRICE=60 \
BEARPLANS_CHERRY_PRICE=120 \
BEARPLANS_BACKUP_DAILY_KEEP=7 \
BEARPLANS_BACKUP_WEEKLY_KEEP=4 \
.venv/bin/python launch.py --port 8765
```

These select the existing proposed reward/retention defaults for this trial;
they do not revise product rules or recalculate older sessions. Expected lines:

```text
data:   /Users/hiberkeley/Library/Application Support/BearPlans
schema: version 13
open:   http://127.0.0.1:8765/
```

The browser should open. Otherwise enter `http://127.0.0.1:8765/` in its address
bar. Check **Plan**, **Track** and **Stats** for your existing records. If you
expected existing work but the page is empty, stop adding work and report the
printed data path. A busy-port/error or existing-instance message needs resolving
before claiming this exact configuration is running. Leave Tab A open while using
the app. Its logs occupy the tab; further commands belong in Tab B.

## 4. Save one baseline backup and a private notes file

Press Command+T in Terminal to create **Tab B**. Run:

```sh
cd "/Users/hiberkeley/Desktop/BearPlans-core-trial-2026-11-01"
```

Before adding trial work, create the baseline snapshot while Tab A keeps running:

```sh
BEARPLANS_DATA_DIR="$HOME/Library/Application Support/BearPlans" .venv/bin/python -m backend.backup create "$HOME/Desktop/BearPlans-before-trial-2026-11-01.sqlite3"
```

Then inspect it:

```sh
.venv/bin/python -m backend.backup inspect "$HOME/Desktop/BearPlans-before-trial-2026-11-01.sqlite3"
```

Expected: successful JSON, schema `13`, restored schema `13`, record counts.
Reveal the exact file:

```sh
open -R "$HOME/Desktop/BearPlans-before-trial-2026-11-01.sqlite3"
```

If that filename already exists, it is preserved. Do not delete/overwrite it;
report the conflict so a new filename can be selected. A backup error should be
resolved before starting the trial. No repeat restore exercise is required: the
offline clean restore already passed. Never restore over the normal folder.

Copy the blank notes template to your Desktop. `cp -n` preserves an existing file:

```sh
cp -n docs/CORE_TRIAL_NOTES_TEMPLATE.txt "$HOME/Desktop/BearPlans-trial-notes.txt"
chmod 600 "$HOME/Desktop/BearPlans-trial-notes.txt"
open -a TextEdit "$HOME/Desktop/BearPlans-trial-notes.txt"
```

The private copy is **BearPlans-trial-notes.txt**, directly on your Desktop. Edit
that copy, not the repository template. Save with Command+S. Keep coursework
details/private notes outside Git; summaries in chat can omit task titles.

## 5. Use BearPlans normally for seven days

Use actual coursework or other real work. Each day, use **Plan** to select work,
**Track** for any focus session you need, and **Stats → Refresh statistics** to
compare saved time. Complete a task separately with its checkbox when appropriate.
A countdown does not complete it automatically.

After natural sleep or a restart, inspect the session before continuing. Paused
stays paused; Needs review requires an explicit decision. Resume/continue excludes
the gap. Finish saves confirmed work only. Do not change power settings or provoke
crashes against your personal data. No daily minimum timer duration is imposed by
this trial; the one-hour streak rule is a separate feature.

Across the week, include the following when useful to your work:

| Workflow | What to check |
| --- | --- |
| Plan real work, including a parent with subtasks if you use them | Saved details are useful; the parent derives completion from its children. |
| Move unfinished planned work | Same task and deadline; no duplicate task or lost notes. |
| Pause/resume, navigate screens and reload | The same session remains; paused/uncertain time does not grow. |
| Stop/start the service normally when convenient | Existing work persists; no duplicate tree or award. Use Tab A Control+C, then the launch command in step 3. |
| Review saved forest, coins and Stats | Confirmed saved work agrees with tree outcome and whole-minute rewards. Existing purchases/corrections affect the wallet. |
| End Week when you actually want to freeze that plan | Read the preview before confirming. Closure is permanent; cancellation changes nothing. |
| Revisit that closed week, then carry unfinished work if needed | Historical details stay frozen. Select destination dates in the immediately following week and review the carryover preview. No cloned task. |

If you start on Sunday November 1, you can close October 26–November 1 when done
with that week, then carry selected work into November 2–8. Do not close a week
early merely to satisfy this checklist. Record a workflow as not used if it was
not needed; the closing review will identify any remaining personal acceptance.

Write a two-minute daily note: actual date/workflows, useful or frustrating parts,
unexpected time, missing records, reward consistency, any correction and exact
error text. `None observed` and `Not used` are valid; do not prefill a pass.
No scheduled monitoring or reminder has been created.

Automatic daily/weekly backups occur on launch when due, not continuously at
midnight. Finder → Go → Go to Folder (Shift+Command+G) opens this location:

```text
/Users/hiberkeley/Library/Application Support/BearPlans/backups
```

On a day you leave the service running, you can also create a manual snapshot
from Tab B using a fresh filename such as `BearPlans-trial-day-2.sqlite3`. Keep
the same data-folder prefix as step 4. Existing filenames are never overwritten.

If time is wrong, records disappear, rewards duplicate or saves fail, record what
happened and report it promptly. Preserve the database/backups; avoid adding more
work to an apparently damaged copy. A correction requires a reason and preview;
do not use it to conceal a suspected timer/reward defect.

## 6. Report Day 1 and close the trial after Day 7

After the first real use, send a short report:

```text
Trial Day 1 date:
Candidate verified: yes / error
Printed data path:
Baseline backup created and inspected: yes / error
Real planner/timer work used:
Problems: none observed / description
```

After seven actual daily entries, send the date range and a redacted summary of
your notes. We will compare saved plans/history/time/rewards, confirm backup
coverage, review planner usefulness and resolve any release blockers. A fix during
the trial needs its version and affected checks recorded; earlier observations
remain evidence for their original version. Calendar time alone does not pass M4.

All seven days and the closing review are still pending. AI and integrations
remain later work. This preparation does not commit, push or tag the candidate.
