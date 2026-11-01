"""Local maintenance commands: python -m backend.backup --help."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from backend.domain.backups import create_backup, inspect_backup, restore_backup
from backend.platform.paths import DATABASE_FILENAME, DataDirError, resolve_data_dir
from backend.storage.db import StorageError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Back up BearPlans or restore it into a clean data folder.")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create", help="save a full snapshot, including committed WAL records")
    create.add_argument("destination", type=Path, help="new backup filename, outside the source folder")
    inspect = commands.add_parser("inspect", help="validate a backup and show schema/counts without restoring it")
    inspect.add_argument("source", type=Path)
    restore = commands.add_parser("restore", help="restore a verified backup into an empty data folder")
    restore.add_argument("source", type=Path)
    restore.add_argument("--into", required=True, type=Path, help="empty data folder outside the source folder")
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            result = create_backup(resolve_data_dir() / DATABASE_FILENAME, args.destination)
        elif args.command == "inspect":
            result = inspect_backup(args.source)
        else:
            result = restore_backup(args.source, args.into)
        print(json.dumps(result, indent=2))
        if args.command == "restore":
            print("Restore saved. Launch BearPlans with BEARPLANS_DATA_DIR set to this restored folder.")
            print("Running sessions require explicit review on launch; paused sessions stay paused.")
        return 0
    except (StorageError, DataDirError, sqlite3.Error, OSError) as exc:
        print(f"BearPlans backup {args.command} failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
