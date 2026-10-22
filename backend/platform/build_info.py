"""Dependency-free identity for the source inputs shipped with a local build."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re

SOURCE_ROOT = Path(__file__).resolve().parents[2]
_MIGRATION = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")
_ROOT_INPUTS = ("launch.py", "pyproject.toml", "requirements.lock", "requirements-dev.lock")
_FRONTEND_INPUTS = (
    "index.html", "package.json", "package-lock.json", "tsconfig.json", "vite.config.ts",
)


@dataclass(frozen=True)
class BuildInfo:
    build_fingerprint: str
    source_root: str
    supported_schema: int


def current_build(source_root: Path = SOURCE_ROOT) -> BuildInfo:
    """Hash code/config inputs, excluding documents, builds, caches and user data.

    Relative paths are part of the hash; checkout identity is carried separately.
    Nothing imports the app, opens its database, reads environment values, or
    requires an installed Python/frontend dependency.
    """
    root = source_root.resolve()
    paths = {root / name for name in _ROOT_INPUTS if (root / name).is_file()}
    backend = root / "backend"
    paths.update(path for path in backend.rglob("*") if path.is_file() and path.suffix in {".py", ".sql"})
    frontend = root / "frontend"
    paths.update(frontend / name for name in _FRONTEND_INPUTS if (frontend / name).is_file())
    for name in ("src", "public"):
        paths.update(path for path in (frontend / name).rglob("*") if path.is_file())
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    versions = [
        int(match.group(1))
        for path in (backend / "storage" / "migrations").glob("*.sql")
        if (match := _MIGRATION.fullmatch(path.name))
    ]
    return BuildInfo(digest.hexdigest(), str(root), max(versions, default=0))
