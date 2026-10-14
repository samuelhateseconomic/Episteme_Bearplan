#!/usr/bin/env python3
"""BearPlans one-command launcher: python3 launch.py [--port N] [--no-browser]

Prepares what is missing or out of date, then starts the local service:
  1. .venv with the pinned Python dependencies (requirements.lock)
  2. the built interface in frontend/dist (npm ci + npm run build)
  3. python -m backend, which applies migrations, binds 127.0.0.1 and opens the browser

After the first run, steps 1-2 are skipped unless their inputs change, so normal
launches need no network access. Uses only the standard library.
"""

from __future__ import annotations

import hashlib
import shutil
import signal
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 12)
ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.lock"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
VENV_STAMP = VENV / ".bearplans-requirements.sha256"
NODE_MODULES_STAMP = FRONTEND / "node_modules" / ".bearplans-lock.sha256"
DIST_STAMP = DIST / ".bearplans-build.sha256"
FRONTEND_INPUTS = ("index.html", "package.json", "package-lock.json", "tsconfig.json", "vite.config.ts")


class SetupError(RuntimeError):
    pass


def _venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def _hash_files(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _stamp_matches(stamp: Path, value: str) -> bool:
    return stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == value


def _run(command: list[str], cwd: Path = ROOT) -> None:
    print(f"  $ {' '.join(command)}", flush=True)
    if subprocess.call(command, cwd=cwd) != 0:
        raise SetupError(f"Command failed: {' '.join(command)}")


def _venv_version(python: Path) -> str | None:
    """The venv interpreter's version, or None when it is missing or broken (e.g. its base Python was removed)."""
    try:
        result = subprocess.run(
            [str(python), "-c", "import sys; print('%d.%d.%d' % sys.version_info[:3])"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except OSError:
        return None
    version = result.stdout.strip()
    try:
        major_minor = tuple(int(part) for part in version.split(".")[:2])
    except ValueError:
        return None
    if result.returncode != 0 or major_minor < MIN_PYTHON:
        return None
    return version


def ensure_python_env() -> Path:
    python = _venv_python()
    version = _venv_version(python)
    if version is None:
        print("Creating Python environment in .venv ...")
        _run([sys.executable, "-m", "venv", "--clear", str(VENV)])
        version = _venv_version(python)
        if version is None:
            raise SetupError(f"The new environment in {VENV} does not run. Delete .venv and retry.")
    wanted = f"{version}:{_hash_files([REQUIREMENTS])}"
    if not _stamp_matches(VENV_STAMP, wanted):
        print("Installing Python dependencies ...")
        _run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", str(REQUIREMENTS)])
        VENV_STAMP.write_text(wanted, encoding="utf-8")
    return python


def ensure_frontend() -> None:
    inputs = [FRONTEND / name for name in FRONTEND_INPUTS if (FRONTEND / name).is_file()]
    inputs += [p for p in (FRONTEND / "src").rglob("*") if p.is_file()]
    inputs += [p for p in (FRONTEND / "public").rglob("*") if p.is_file()]
    wanted = _hash_files(inputs)
    if (DIST / "index.html").is_file() and _stamp_matches(DIST_STAMP, wanted):
        return
    npm = shutil.which("npm")
    if npm is None:
        raise SetupError("The interface needs building, but npm was not found. Install Node.js 24 LTS and retry.")
    lock_hash = _hash_files([FRONTEND / "package-lock.json"])
    if not _stamp_matches(NODE_MODULES_STAMP, lock_hash):
        print("Installing interface dependencies ...")
        _run([npm, "ci", "--no-audit", "--no-fund"], cwd=FRONTEND)
        NODE_MODULES_STAMP.write_text(lock_hash, encoding="utf-8")
    print("Building the interface ...")
    _run([npm, "run", "build"], cwd=FRONTEND)
    DIST_STAMP.write_text(wanted, encoding="utf-8")


def main(argv: list[str]) -> int:
    if sys.version_info < MIN_PYTHON:
        print(f"BearPlans needs Python {'.'.join(map(str, MIN_PYTHON))}+; this is {sys.version.split()[0]}.")
        return 1
    try:
        python = ensure_python_env()
        ensure_frontend()
    except SetupError as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1
    # Ctrl+Break (Windows) and SIGTERM stop the launcher the same way Ctrl+C does.
    for name in ("SIGTERM", "SIGBREAK"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), signal.default_int_handler)
    try:
        service = subprocess.Popen([str(python), "-m", "backend", *argv], cwd=ROOT)
    except OSError as exc:
        print(f"Could not start the service with {python}: {exc}. Delete .venv and retry.", file=sys.stderr)
        return 1
    while True:
        try:
            return service.wait()
        except KeyboardInterrupt:
            # Console Ctrl+C/Ctrl+Break already reach the service. On macOS/Linux, also pass on a
            # SIGTERM sent to the launcher alone; the service stops gracefully on either signal.
            # (On Windows send_signal(SIGTERM) would force-kill, so rely on the console group there.)
            if sys.platform != "win32" and service.poll() is None:
                service.send_signal(signal.SIGTERM)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
