# M4 full-database backup and clean restore — October 31, 2026

Implementation review **Pass on the target Mac for this ticket**. The user explicitly requested the next
module and skipping remaining standby testing. The [cancelled hardware review](2026-10-31-mac-standby.md)
retains the unverified scope; no hardware pass is inferred from this work.

Base `d9b5f90`, actual macOS 26.6.2 (25G83), Darwin 25.6.0 arm64, Python
3.13.15, Node 24.21.0. Existing staged/unstaged planning edits and date-fixture
repair preserved. Read instructions, progress, plans/runbook, relevant reviews,
working/index diffs and storage/startup/instance-lock code before implementation.
No subagents, dependency changes, migration SQL changes, commit or push.

## Scope and acceptance

One ticket: local full-database snapshot creation/inspection, clean-folder restore,
daily/weekly startup copies and pre-upgrade protection. These are CLI maintenance
commands; plan-only import/export is a separate later ticket. No backup settings
screen, active-database replacement or core release certification is included.

Acceptance: create a consistent snapshot of a live WAL database containing plans,
closed weeks, sessions/intervals, original trees/coin awards, purchases, corrections
and receipts. Restore to a clean folder and compare every table/field; restart
preserves IDs, history and derived behavior. Restore validation/upgrades operate
only on a disposable stage. Existing backup/data destinations are never replaced.
Fail/retry and concurrent publication cannot discard the original. A saved running
session enters existing Needs review on launch without absence credit; a paused
session remains paused. Backup/inspection alone never starts TimerService.

Proposed defaults implemented: seven daily and four ISO-week copies, configurable
positive retention counts; pre-upgrade copies and manual exports are not pruned.
Daily/weekly copies are taken when due during startup, not by a background scheduler.
A 30-second snapshot deadline prevents indefinite retries on a busy database.
Required backup failure stops startup with an actionable message. No timer/reward
rule or default changes. Rollback uses the untouched original folder; restoring
over existing data is deliberately unavailable in this ticket.

## Implementation

- `backend/domain/backups.py`: application functions use SQLite's backup API,
  read-only source connections, private staged files, integrity/relationship and
  upgrade/schema checks, durable atomic publication without replacement, clean
  destination instance locking and bounded retention of owned automatic filenames.
- `backend/backup.py`: `create`, `inspect`, `restore --into`; JSON schema/counts
  without private titles, useful nonzero failures without tracebacks.
- `backend/__main__.py`: while owning the instance lock, create a safety copy before
  older-schema migration and due daily/weekly copies after successful open, before
  timer startup. Invalid retention configuration stops before database open.
- `README.md`: commands, Windows equivalents, folder selection/recovery, contents,
  privacy, retention and failure behavior. No frontend workflow change.

Sources checked: [SQLite online backup API](https://www.sqlite.org/backup.html)
and [Python sqlite3 backup](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup).
The API creates a consistent snapshot including committed WAL work while allowing
other connections. It does not make later writes part of an earlier snapshot.
No naive live database copy is used. Source backups contain only the database;
Keychain, environment/browser storage and other data-folder files are excluded.
The database's private content is not encrypted by this module.

## Checks and initial corrections

New behavioral coverage in `tests/test_backups.py` includes exact full-table
comparison after live WAL backup, writes during snapshot, existing/concurrently
created destination protection, private permissions, invalid/corrupt/newer schema,
fingerprint/foreign-key/schema failures, source-folder rejection, stage cleanup,
failed publication and upgrade retry, pre-upgrade originals, retention and manual
copy preservation, restored timer states and actual process/CLI restart.
`tests/test_startup_errors.py` adds failed-backup lock release and invalid retention.

Initial restricted command:

```sh
.venv/bin/python -m pytest -q tests/test_backups.py tests/test_startup_errors.py tests/test_migrations.py tests/test_paths.py
```

**65 passed, 3 failed, 2.22 s**. Two were new fixture mistakes: fingerprint damage
violated its 64-character constraint before exercising validation; Pause omitted
the required revision. Corrected the fixtures. The third was loopback access
denied by the sandbox; reran actual disposable-service checks with loopback access.
No product pass is claimed from those failed attempts.

Affected storage/startup/compatibility run after the first corrections:

```sh
.venv/bin/python -m pytest -q tests/test_backups.py tests/test_startup_errors.py tests/test_migrations.py tests/test_paths.py tests/test_service_restart.py tests/test_launch_compatibility.py tests/test_schema_validation.py tests/test_migration_fingerprints.py
```

**130 passed, 15.29 s**, exit 0. Subsequent added failure/concurrency/startup
coverage: `pytest -q tests/test_backups.py tests/test_startup_errors.py` →
**42 passed, 3.50 s**, exit 0. No normal personal database/service was tested.

## Completed verification and decision

Full core command with loopback/installed Chrome permission, exit 0:

```sh
BEARPLANS_E2E_CHANNEL=chrome BEARPLANS_EVIDENCE_DIR=.evidence/m4-backups-20261031/screenshots .venv/bin/python -m pytest -q
```

**785 passed, one skipped, zero failures, 171.65 s**. The sole skip is the real
Windows clock API, unavailable on this Mac. Includes core timer/reward/planning,
full correction browser journey, migrations, launcher and actual process recovery.
This full run preceded the final isolated backup-filename guard described below;
it is not represented as a full rerun after that guard.

Frontend, exit 0 for each:

```sh
npm --prefix frontend test -- --maxWorkers=2
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

**136 frontend tests passed, 7.25 s**; TypeScript and production build passed
(Vite 108 ms). No frontend source change; no new visual-layout claim is needed.

Final source review found that a chosen export filename could occupy an absent
SQLite sidecar or BearPlans instance path. Added a case-insensitive reserved-name
guard for those paths in the source folder, including equivalent existing folder
identities. Existing/concurrent destinations already used no-replace publication.
Added seven rejected-filename cases, including uppercase aliases. This is a
backup input-validation fix, with no change to timer/storage schema behavior.
The affected command listed above was rerun after the guard: first **142 passed,
15.49 s**, then final uppercase-path coverage **144 passed, 15.51 s**, both exit 0.
The unchanged full core/frontend results were not redundantly rerun for that guard.

Final source, new-file syntax/whitespace, scoped tracked diff and local Markdown
links checked. Logs, source fingerprints/environment and synthetic screenshots:
`.evidence/m4-backups-20261031/`; SHA-256 manifest verified, no database included.
All mutation/corruption/migration/restore experiments used disposable databases.
Normal user data and normal service were not inspected, restarted or migrated.
No changes to applied SQL, dependencies, existing user planning edits, index or
stashes; no commit or push.

**Pass for this implementation ticket on macOS/APFS.** Restore's original-folder
rollback, exact records, retry/failure and restart scenarios passed. Publication
requires destination hard-link support; unsupported filesystems fail while
preserving originals. No new Windows or removable-filesystem runtime certification.
The commands and automatic startup copies are available on the next deliberate
launch of this build. CLI maintenance is the current interface; plan-only transfer
is a separate ticket. M4's release gate, candidate freeze and seven-day trial remain
unfinished; skipped standby/hibernate remains unverified under the user's explicit
decision to advance. No later AI/integration work starts from this review.
