# BearPlans offline backup/restore checklist

Prepared November 1, 2026 for this Mac. This is a user-executed checklist, not a
record of a completed operator test. Use the commands in order. Copy only the
contents of each code block into Terminal, then press Return.

We will create sample data in a separate test folder, back it up, and open a
restored copy. Your normal BearPlans folder is not used during these steps.

## Names and locations

| Item | Exact location |
| --- | --- |
| Project code | `/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan` |
| Original test folder | `/Users/hiberkeley/Desktop/BearPlans-source-test` |
| Database inside original test folder | `/Users/hiberkeley/Desktop/BearPlans-source-test/bearplans.sqlite3` |
| Backup file | `/Users/hiberkeley/Desktop/BearPlans-backup.sqlite3` |
| Restored test folder | `/Users/hiberkeley/Desktop/BearPlans-restored-test` |
| Database inside restored folder | `/Users/hiberkeley/Desktop/BearPlans-restored-test/bearplans.sqlite3` |
| Test browser address | `http://127.0.0.1:8877/` |

The two databases have the same filename but live in different folders. The
backup is a separate snapshot file on your Desktop. Restore creates the restored
folder/database automatically. All three test names were unused when this guide
was prepared. If a command reports an existing file/folder, stop and keep it;
do not delete or replace it to get past the message.

## 1. Open Terminal and the local checklist

Press Command+Space, type `Terminal`, then press Return. Call this Terminal tab
**Tab A**. Tab A will run the test service.

Run:

```sh
cd "/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan"
```

To keep this checklist available while Wi-Fi is off, run:

```sh
open -a TextEdit "/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan/docs/BACKUP_RESTORE_OPERATOR_CHECKLIST.md"
```

## 2. Turn Wi-Fi off and start the original test copy

Open Control Center in the Mac menu bar, open Wi-Fi, and turn Wi-Fi off.
Disconnect any Ethernet adapter if one supplies internet. Keep internet off until
step 12. Local addresses beginning `127.0.0.1` still work.

In **Tab A**, create the original test folder:

```sh
mkdir "$HOME/Desktop/BearPlans-source-test"
```

Success produces no message. Then run:

```sh
BEARPLANS_DATA_DIR="$HOME/Desktop/BearPlans-source-test" BEARPLANS_COINS_PER_MINUTE=1 python3 launch.py --port 8877
```

Keep Tab A open. It should print lines containing:

```text
data:   /Users/hiberkeley/Desktop/BearPlans-source-test
schema: version 13
open:   http://127.0.0.1:8877/
```

The browser should open. If necessary, enter `http://127.0.0.1:8877/` in its address
bar. Use this test page throughout the checklist. An existing normal BearPlans
page on port 8765 is a different service.

If launch reports an error, a busy port, or missing setup/dependencies, stop here.
Turn internet back on when ready and send the exact error. A server running in
Tab A will keep displaying logs instead of returning a command prompt; that is
normal. Further commands go in Tab B below.

## 3. Create the exact sample project and task

In the browser test page:

1. Click **Plan** in the top navigation.
2. Under **Projects**, find the **New project** field (placeholder **Add a project**).
3. Enter `Backup Demo`, then click **Add project**.
4. Confirm the task-section heading is **Backup Demo**.
5. In the new-task form, enter these values:

| Field | Value |
| --- | --- |
| Title | `Backup test` |
| Deadline | November 2, 2026 (`2026-11-02`) |
| Estimate (minutes) | `1` |
| Notes | `Original backup test notes` |

6. Click **Add task**. Confirm **Backup test** appears with its checkbox unchecked.
7. In that task's controls, expand **Plan task**.
8. Set **Planned date for “Backup test”** to November 1, 2026 (`2026-11-01`).
9. Click **Add to day**. The card belongs under **Sunday, November 1**. Use **Today**
   if needed to return the board to the current week. On a narrow window, select
   Sunday's day button to see its card.

## 4. Save a one-minute countdown

1. Click **Track** in the top navigation.
2. In **Task to track**, select the option containing **Backup Demo / Backup test**.
3. Set **Duration (minutes)** to `1`.
4. Leave **Tree species** set to **Pine · Free**.
5. Click **Start countdown**.
6. Keep the Mac awake, lid open, for the minute. Leave timer controls untouched.
7. Wait for **Countdown completed** and a mature Pine.
8. In **Tree shop**, confirm **Your coins: 1**.
9. In **Your forest**, confirm there is exactly one saved mature Pine for **Backup test**.
10. Click **Stats**, then **Refresh statistics**. Confirm:
    - **Saved active time:** one minute.
    - **Saved sessions with intervals:** `1`.
    - **Current leaf completion:** `0 of 1 complete`.
11. Return to **Plan** and confirm **Backup test** is still unchecked. Finishing the
    countdown does not complete the task.

These are the records that the backup and restored copy must preserve. Leave the
task fields, checkbox and timer history unchanged for the rest of the check.

## 5. Open Terminal Tab B and create the backup

Click Terminal, then press Command+T. Call this new tab **Tab B**. Tab A continues
running the service. In Tab B, run:

```sh
cd "/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan"
```

Then run this exact command, including the data-folder prefix:

```sh
BEARPLANS_DATA_DIR="$HOME/Desktop/BearPlans-source-test" .venv/bin/python -m backend.backup create "$HOME/Desktop/BearPlans-backup.sqlite3"
```

The prefix selects the original test data from steps 3–4. Output should include
`"path": "/Users/hiberkeley/Desktop/BearPlans-backup.sqlite3"`,
`"schema_version": 13`, and record counts. The source service may keep running
while this snapshot is made.

Reveal the file in Finder:

```sh
open -R "$HOME/Desktop/BearPlans-backup.sqlite3"
```

Finder should select **BearPlans-backup.sqlite3** directly on your Desktop. Use
the commands below to inspect/restore it; it is a database file rather than a
document to edit in Finder.

## 6. Inspect that backup

In **Tab B**, run:

```sh
.venv/bin/python -m backend.backup inspect "$HOME/Desktop/BearPlans-backup.sqlite3"
```

Expected output is JSON with `"schema_version": 13`,
`"restored_schema_version": 13`, and `"record_counts"`. Relevant counts should
include `"tasks": 1`, `"timer_sessions": 1`, `"trees": 1`, `"coin_ledger": 1`.
Other table counts are normal. If there is an error, stop before restoring.

## 7. Stop the original test service

Click **Tab A**, the tab displaying the running service's logs. Press
**Control+C** once. Wait for **BearPlans stopped.** and the command prompt.
This stops the original test copy on port 8877; its folder and backup stay saved.

## 8. Restore the backup into the second folder

Return to **Tab B** and run:

```sh
.venv/bin/python -m backend.backup restore "$HOME/Desktop/BearPlans-backup.sqlite3" --into "$HOME/Desktop/BearPlans-restored-test"
```

The command creates **BearPlans-restored-test** on your Desktop and puts a database
named **bearplans.sqlite3** inside it. It should print a path ending in
`/Desktop/BearPlans-restored-test/bearplans.sqlite3` and **Restore saved.**

Reveal the restored database in Finder:

```sh
open -R "$HOME/Desktop/BearPlans-restored-test/bearplans.sqlite3"
```

Finder should now show **bearplans.sqlite3 inside BearPlans-restored-test**.
The original **BearPlans-source-test** folder and the Desktop backup file remain.

## 9. Launch the restored copy

In **Tab A**, run:

```sh
cd "/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan"
```

```sh
BEARPLANS_DATA_DIR="$HOME/Desktop/BearPlans-restored-test" BEARPLANS_COINS_PER_MINUTE=1 python3 launch.py --port 8877
```

Check the Terminal line carefully. It must now say:

```text
data:   /Users/hiberkeley/Desktop/BearPlans-restored-test
```

Open `http://127.0.0.1:8877/` and press Command+R to reload it. The browser address
is the same as before; the Terminal's **data:** path proves which folder is now
being served.

## 10. Compare the restored copy with the original

In the browser:

| Where to look | Expected restored result |
| --- | --- |
| **Plan → Projects** | Project **Backup Demo** exists; click it. |
| **Plan → Backup Demo** | Task **Backup test** exists and is unchecked. |
| Task's **Edit** form | Notes **Original backup test notes**, deadline November 2, estimate **1**. Click **Cancel** after looking. |
| Weekly board, Sunday November 1 | **Backup test** is planned there. |
| **Track → Your forest** | Exactly one mature Pine for **Backup test**. |
| **Track → Tree shop** | **Your coins: 1**. |
| **Stats → Refresh statistics** | One minute saved, one session, **0 of 1 complete**. |

The saved-session panel may differ after navigation; use **Your forest** and
**Stats** to verify historical data. Starting another timer is unnecessary.

## 11. Check one restart of the restored copy

In **Tab A**, press Control+C and wait for **BearPlans stopped.** Then run:

```sh
BEARPLANS_DATA_DIR="$HOME/Desktop/BearPlans-restored-test" BEARPLANS_COINS_PER_MINUTE=1 python3 launch.py --port 8877
```

Check the restored **data:** path again. Reload the browser with Command+R and
repeat the comparisons in step 10. There should still be one mature Pine and one
coin, with the same task and minute of saved time.

## 12. Finish and report

Press Control+C in **Tab A** to stop the test service. Turn Wi-Fi back on through
Control Center, and reconnect Ethernet if you disconnected it. Keep both test
folders and the backup file for now.

Send these results in chat, with any exact error text:

```text
Offline launch: worked / error
Backup created and inspected: worked / error
Restored data path: /Users/hiberkeley/Desktop/BearPlans-restored-test
Project/task/notes/deadline/planned date: matched / difference
Saved time: 1 minute / other
Forest: 1 mature Pine / other
Coins: 1 / other
Task completion: unchecked / other
After restored restart: everything remained / difference
```

To open your normal BearPlans afterward, use Tab A:

```sh
BEARPLANS_DATA_DIR="$HOME/Library/Application Support/BearPlans" python3 launch.py
```

Its normal data path is `/Users/hiberkeley/Library/Application Support/BearPlans`,
and its usual address is `http://127.0.0.1:8765/`. Keep its Terminal tab open while
using it. The test folders above remain separate from that normal data folder.
