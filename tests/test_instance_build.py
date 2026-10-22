"""Source identity prevents stale backend reuse and mixed UI/backend builds."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import launch
from backend import __main__ as entry
from backend.platform.build_info import BuildInfo, current_build
from backend.platform import instance_lock as instances


def source_fixture(root: Path) -> Path:
    inputs = {
        "backend/app.py": "app source",
        "backend/storage/migrations/0001_initial.sql": "first migration",
        "backend/storage/migrations/0008_timer_recovery.sql": "recovery migration",
        "launch.py": "launcher source",
        "pyproject.toml": "python project",
        "requirements.lock": "python locked dependencies",
        "requirements-dev.lock": "development locked dependencies",
        "frontend/src/App.tsx": "interface source",
        "frontend/public/pine.svg": "public artwork",
        "frontend/index.html": "index source",
        "frontend/package.json": "frontend project",
        "frontend/package-lock.json": "frontend dependencies",
        "frontend/tsconfig.json": "typescript config",
        "frontend/vite.config.ts": "vite config",
    }
    for name, content in inputs.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return root


def metadata(build: BuildInfo, **overrides) -> dict:
    return {
        "pid": 123, "url": "http://127.0.0.1:18789/",
        "build_fingerprint": build.build_fingerprint, "source_root": build.source_root,
        "supported_schema": build.supported_schema, "started_at": "2026-10-22T20:00:00.000000Z",
        **overrides,
    }


def write_info(path: Path, value: dict) -> None:
    (path / instances.INSTANCE_FILENAME).write_text(json.dumps(value))


def test_fingerprint_excludes_documents_secrets_saved_data_and_build_outputs(tmp_path: Path):
    root = source_fixture(tmp_path)
    before = current_build(root)
    for name in (
        "docs/private-note.md", "data/bearplans.sqlite3", ".env", ".aws/credentials",
        "frontend/dist/index.html", "frontend/node_modules/dependency.js", "backend/__pycache__/app.pyc",
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic private content which must not affect identity")
    assert current_build(root) == before
    assert before.supported_schema == 8 and before.source_root == str(root.resolve())
    assert len(before.build_fingerprint) == 64
    assert "synthetic" not in repr(before)


@pytest.mark.parametrize("name", [
    "backend/app.py", "backend/storage/migrations/0008_timer_recovery.sql", "launch.py",
    "requirements.lock", "requirements-dev.lock", "pyproject.toml", "frontend/src/App.tsx",
    "frontend/public/pine.svg", "frontend/package-lock.json", "frontend/vite.config.ts",
])
def test_changed_shipped_input_changes_build_identity(tmp_path: Path, name: str):
    root = source_fixture(tmp_path)
    before = current_build(root)
    (root / name).write_text("changed source input")
    assert current_build(root).build_fingerprint != before.build_fingerprint


def test_identical_source_in_another_checkout_has_separate_location(tmp_path: Path):
    first = current_build(source_fixture(tmp_path / "one"))
    second = current_build(source_fixture(tmp_path / "two"))
    assert first.build_fingerprint == second.build_fingerprint
    assert first.source_root != second.source_root


def test_record_retains_pid_url_and_adds_non_content_build_metadata(tmp_path: Path, monkeypatch):
    build = current_build(source_fixture(tmp_path / "source"))
    monkeypatch.setattr(instances, "current_build", lambda: build)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    lock = instances.acquire_instance_lock(data_dir)
    assert lock is not None
    try:
        lock.record("http://127.0.0.1:18789/")
        value = json.loads((data_dir / instances.INSTANCE_FILENAME).read_text())
        assert set(value) == {"pid", "url", "build_fingerprint", "source_root", "supported_schema", "started_at"}
        assert value["pid"] == os.getpid() and value["url"] == "http://127.0.0.1:18789/"
        assert value["build_fingerprint"] == build.build_fingerprint
        assert value["source_root"] == build.source_root and value["supported_schema"] == 8
        assert value["started_at"].endswith("Z")
    finally:
        lock.release()


@pytest.mark.parametrize("change", [
    {"build_fingerprint": "f" * 64}, {"source_root": "/another/checkout"}, {"supported_schema": 7},
])
def test_different_running_identity_requires_deliberate_restart(tmp_path: Path, change):
    build = current_build(source_fixture(tmp_path / "source"))
    data = tmp_path / "data"
    data.mkdir()
    write_info(data, metadata(build, **change))
    status = instances.describe_running_instance(data, build)
    assert status.identity == "different"
    assert "deliberately stop" in status.message and "No service was restarted" in status.message


@pytest.mark.parametrize("value", [None, [], {"pid": 123, "url": "http://127.0.0.1:18789/"}, {"url": "https://example.com/"}])
def test_unknown_or_legacy_instance_metadata_is_not_auto_opened(tmp_path: Path, monkeypatch, capsys, value):
    (tmp_path / instances.INSTANCE_FILENAME).write_text(json.dumps(value))
    monkeypatch.setattr(instances.webbrowser, "open", lambda url: pytest.fail("Unknown instances must not auto-open"))
    status = instances.describe_running_instance(tmp_path, BuildInfo("a" * 64, "/source", 11))
    assert status.identity == "unknown"
    assert instances.report_running_instance(status, open_browser=True) == 1
    assert "build identity is unavailable" in capsys.readouterr().out


def test_same_identity_reuses_only_valid_loopback_url(tmp_path: Path, monkeypatch):
    build = BuildInfo("a" * 64, "/source", 11)
    write_info(tmp_path, metadata(build))
    opened = []
    monkeypatch.setattr(instances.webbrowser, "open", opened.append)
    status = instances.describe_running_instance(tmp_path, build)
    assert status.identity == "same"
    assert instances.report_running_instance(status, open_browser=True) == 0
    assert opened == ["http://127.0.0.1:18789/"]
    write_info(tmp_path, metadata(build, url="javascript:alert(1)"))
    invalid = instances.describe_running_instance(tmp_path, build)
    assert invalid.identity == "unknown"
    assert instances.report_running_instance(invalid, open_browser=True) == 1
    assert opened == ["http://127.0.0.1:18789/"]


def test_free_lock_with_stale_metadata_is_not_reused(tmp_path: Path, monkeypatch):
    build = BuildInfo("a" * 64, "/source", 11)
    write_info(tmp_path, metadata(build))
    monkeypatch.setattr(instances, "current_build", lambda: build)
    assert instances.probe_running_instance(tmp_path) is None
    assert not (tmp_path / instances.INSTANCE_FILENAME).exists()
    lock = instances.acquire_instance_lock(tmp_path)
    assert lock is not None
    lock.release()


def test_probe_missing_or_invalid_data_directory_creates_nothing(tmp_path: Path):
    missing = tmp_path / "missing"
    assert instances.probe_running_instance(missing) is None and not missing.exists()
    file = tmp_path / "file"
    file.write_text("not a directory")
    assert instances.probe_running_instance(file) is None
    assert list(tmp_path.iterdir()) == [file]


@pytest.mark.parametrize("identity,expected", [("same", 0), ("different", 1), ("unknown", 1)])
def test_launcher_checks_held_instance_before_dependency_or_interface_changes(tmp_path: Path, monkeypatch, identity, expected):
    build = BuildInfo("a" * 64, "/source", 11)
    info = metadata(build) if identity != "unknown" else {"pid": 123, "url": "http://127.0.0.1:18789/"}
    if identity == "different":
        info["build_fingerprint"] = "b" * 64
    write_info(tmp_path, info)
    monkeypatch.setattr(launch, "resolve_data_dir", lambda: tmp_path)
    monkeypatch.setattr(instances, "acquire_instance_lock", lambda path: None)
    monkeypatch.setattr(instances, "current_build", lambda: build)
    monkeypatch.setattr(launch, "ensure_python_env", lambda: pytest.fail("No dependency preparation for held instance"))
    monkeypatch.setattr(launch, "ensure_frontend", lambda: pytest.fail("No frontend rebuild for held instance"))
    monkeypatch.setattr(launch.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("Do not spawn another backend"))
    monkeypatch.setattr(instances.webbrowser, "open", lambda url: pytest.fail("--no-browser must be respected"))
    assert launch.main(["--no-browser"]) == expected


def test_launcher_ignores_free_stale_info_and_continues_normal_preparation(tmp_path: Path, monkeypatch):
    write_info(tmp_path, metadata(BuildInfo("a" * 64, "/source", 11)))
    calls = []
    monkeypatch.setattr(launch, "resolve_data_dir", lambda: tmp_path)
    monkeypatch.setattr(launch, "ensure_python_env", lambda: calls.append("python") or Path(sys.executable))
    monkeypatch.setattr(launch, "ensure_frontend", lambda: calls.append("frontend"))
    monkeypatch.setattr(launch.signal, "signal", lambda *args: None)
    monkeypatch.setattr(launch.subprocess, "Popen", lambda *args, **kwargs: calls.append("backend") or SimpleNamespace(wait=lambda: 0))
    assert launch.main(["--no-browser"]) == 0
    assert calls == ["python", "frontend", "backend"]


@pytest.mark.parametrize("identity,expected", [("same", 0), ("different", 1), ("unknown", 1)])
def test_direct_backend_held_instance_uses_same_safe_reuse_behavior(tmp_path: Path, monkeypatch, identity, expected):
    status = instances.RunningInstance(identity, "http://127.0.0.1:18789/", "synthetic instance status")
    monkeypatch.setattr(entry, "_treat_stop_signals_as_interrupt", lambda: None)
    monkeypatch.setattr(entry, "resolve_data_dir", lambda: tmp_path)
    monkeypatch.setattr(entry, "ensure_data_dir", lambda path: path)
    monkeypatch.setattr(entry, "acquire_instance_lock", lambda path: None)
    monkeypatch.setattr(entry, "describe_running_instance", lambda path: status)
    monkeypatch.setattr(entry, "open_database", lambda path: pytest.fail("Held instance must not open the database"))
    monkeypatch.setattr(entry.webbrowser, "open", lambda url: pytest.fail("--no-browser must be respected"))
    assert entry.main(["--no-browser"]) == expected


def test_launcher_identity_imports_without_site_packages():
    result = subprocess.run(
        [sys.executable, "-S", "-c", "import sys; import launch; from backend.platform.build_info import current_build; assert len(current_build().build_fingerprint) == 64; assert 'pydantic' not in sys.modules; assert 'uvicorn' not in sys.modules; print('stdlib bootstrap passed')"],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "stdlib bootstrap passed"
