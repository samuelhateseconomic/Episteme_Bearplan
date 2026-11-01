# Repository relocation — November 1, 2026

**Decision: Pass for the folder relocation.** Subsystem documentation reorganization
is not started. This does not advance M4/M5 or certify an outstanding manual gate.

## Acceptance and scope

User requested opening one `Episteme_Bearplan` folder rather than two nested copies,
before later frontend/backend/documentation cleanup. The existing repository is now
`/Users/hiberkeley/Desktop/Projects/Episteme_Bearplan` (formerly that path plus
`/Episteme_Bearplan`). It is the same physical Git checkout, not a fresh clone.
Source layout, product rules/defaults, schema and external saved-data locations
are unchanged. Runtime fingerprint remains
`364ed37e0a01c31cb64e1010df5555f15876754c05fb2babf64b7fb134313b8e`, schema 13.
HEAD remains `d9b5f90e10579d8687c4ffbd8e132a7121573ac1`; no commit/push.

The former wrapper held only the repository and Finder metadata. A checked helper
renamed the wrapper temporarily, renamed the inner checkout to its final canonical
path, preserved the wrapper metadata in ignored evidence, and removed the empty
wrapper. Failure of the second rename had a rollback to the original layout.
No old-path symlink was created. Original generated environment text is retained
in ignored evidence if a deliberate relocation rollback is ever needed; restoring
the old layout would require stopping the app and reversing both paths/repairs.
There is no product-record Undo operation because no product mutation was made.

## Preservation and affected files

Immediately after the rename, all **11,331** inventoried filesystem entries had
identical content hashes, permissions, link targets and inodes. Git status including
all untracked files, HEAD, index SHA-256, refs and both stash identities matched.
Captured the original working/staged binary diffs without resetting or stashing.
Then intentionally repaired 15 generated `.venv/bin` text scripts/activation files
and `.venv/pyvenv.cfg`, and replaced the old path only in these current guides:

- [Assistant preview](../LOCAL_ASSISTANT.md)
- [Backup/restore operator checklist](../BACKUP_RESTORE_OPERATOR_CHECKLIST.md)

README now maps the root and current folders; shared progress records this handoff.
No application, migration or test source was edited for relocation. Historical
reviews and previous `.evidence` paths/manifests retain the original observations.
The independently preserved Desktop core-trial snapshot was not modified.

## Existing app and private data

Preflight found the user's app listening on loopback port 8765 from the old checkout,
with a session already in **Needs review**. Its state/revision/confirmed time were
recorded without exporting task contents. Read-only SQLite transactions computed
hashes for every saved table, without copying private rows into the evidence.
Captured only `BEARPLANS_*` configuration from the process; none was set.

Deliberately sent SIGINT to the identified backend, waited for instance release and
port closure, performed the move, and reopened the launcher from the new root.
New backend PID **39648**, launcher PID **39643**; the app remains available at
`http://127.0.0.1:8765/`. The old launcher/backend stopped. All **21 table digests**
and the exact selected timer fields matched after reopening. No timer control,
reward, correction, task edit, resume or finish occurred. No power setting changed.
New instance metadata records the canonical root and the same fingerprint/schema.
The normal external data folder remains unchanged.

## Actual checks

Environment: Darwin arm64, Mac15,9, **macOS 26.6.2 (25G83)**; Python **3.13.15**,
Node **24.21.0**. Commands below ran from the canonical root.

| Command/check | Result |
| --- | --- |
| `.venv/bin/pytest tests/test_paths.py tests/test_instance_build.py tests/test_startup_errors.py tests/test_launch_compatibility.py -q -rs` | **68 passed**, 0 failures/skips, **1.07 s**. |
| `.venv/bin/python -c 'import sys; print(sys.prefix)'` | New root's `.venv`. |
| `.venv/bin/pip --version`, `.venv/bin/pytest --version` | Direct repaired entrypoints work: pip 26.2.1, pytest 9.1.1. |
| `.venv/bin/python -m pip check` | No broken requirements. |
| Fresh zsh `source .venv/bin/activate`, then inspect `VIRTUAL_ENV`/`sys.prefix` | Both canonical `.venv` paths. |
| `npm --prefix frontend run typecheck` | Pass. |
| `npm --prefix frontend run build` | Pass; unchanged CSS/JS asset names, Vite 89 ms. |
| Launcher environment/frontend setup with `_run` replaced by a fail-on-work sentinel | Pass after refreshing the generated build stamp; no install/network/build required on the next launch. |
| Disposable launcher at port 64707 with `--no-browser`, repeated after graceful stop | Schema 13 health, exact built asset bytes, identical synthetic task list after restart, both stop codes 0; instance metadata removed after stop. |
| Disposable SQLite integrity and FK checks | Pass; no active disposable session. |

The direct Vite build intentionally empties `dist`, removing the launcher's generated
stamp. The first strict no-work probe therefore stopped before creating test data.
Refreshed the stamp through `launch.ensure_frontend()` (one offline build, 86 ms),
then repeated the no-work probe and completed both disposable launches successfully.
This was a verification sequencing issue, not a relocation defect. No new tests
were added for this reversible filesystem change. The full 819-test core suite and
142 frontend tests from the prior M5 review were not rerun or claimed as fresh here.

Evidence: `.evidence/repo-relocation-20261101/`: `relocate.py`, exact before-file
inventory, Git patches/state, relocation result, redacted operator preservation
checks, frontend/test logs and `smoke.json`. Disposable data:
`/private/tmp/bearplans-relocation-smoke-92p9b45l/data`; its service is stopped.
The existing personal app was reopened intentionally and remains running.

## Follow-up

Codex still registers the old project path. The available project tools cannot
rewrite a local project's source-folder path; select/reopen the canonical folder
for future coding sessions. No Codex internal configuration database was edited.
This registration follow-up does not affect Finder or app launch from the new root.

Next requested work: a compact frontend/backend/shared documentation map and focused
agent entrypoints. Keep shared rules in root `AGENTS.md` and one progress record;
avoid duplicating domain rules, architecture or task status across guides. File
moves beyond flattening, UI redesign and further module implementation are deferred.
