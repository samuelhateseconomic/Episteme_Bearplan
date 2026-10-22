"""Startup failures release resources and never advertise an unready app."""

from __future__ import annotations

import asyncio
import errno
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest
import uvicorn

from backend import __main__ as entry
from backend.storage.db import StorageError
from backend.storage.migrations import current_version


@pytest.fixture
def startup(monkeypatch, db):
    events = []

    class Socket:
        closed = False

        def close(self):
            events.append("socket-close")
            self.closed = True

    class Lock:
        recorded = []
        released = False

        def record(self, url):
            events.append("record-ready")
            self.recorded.append(url)

        def release(self):
            events.append("lock-release")
            self.released = True

    sock, lock = Socket(), Lock()
    app = object()
    state = SimpleNamespace(
        events=events, sock=sock, lock=lock, app=app, db=db,
        run_error=None, ready=True, interrupt=False, config=None,
    )

    def open_database(path):
        events.append("database")
        return db

    def bind(port):
        events.append("bind")
        return sock

    def create_app(*args, **kwargs):
        events.append("app")
        return app

    class Server:
        def __init__(self, config, on_ready):
            events.append("server")
            state.config = config
            self.on_ready = on_ready
            self.started = False

        def run(self, sockets):
            assert sockets == [sock] and not sock.closed
            if state.run_error:
                raise state.run_error
            if state.ready:
                events.append("lifespan-ready")
                self.started = True
                self.on_ready()
            if state.interrupt:
                raise KeyboardInterrupt

    monkeypatch.setattr(entry, "_treat_stop_signals_as_interrupt", lambda: None)
    monkeypatch.setattr(entry, "resolve_data_dir", lambda: db.path.parent)
    monkeypatch.setattr(entry, "ensure_data_dir", lambda path: path)
    monkeypatch.setattr(entry, "acquire_instance_lock", lambda path: lock)
    monkeypatch.setattr(entry, "open_database", open_database)
    monkeypatch.setattr(entry, "_bind", bind)
    monkeypatch.setattr(entry, "create_app", create_app)
    monkeypatch.setattr(entry, "_ReadyServer", Server)
    return state


@pytest.mark.parametrize("failure", [
    StorageError("Required timer recovery schema is missing."),
    sqlite3.OperationalError("no such table: timer_interruptions"),
])
def test_app_construction_failure_is_readable_and_closes_socket_and_lock(startup, monkeypatch, capsys, failure):
    def fail(*args, **kwargs):
        startup.events.append("app-failed")
        raise failure

    monkeypatch.setattr(entry, "create_app", fail)
    assert entry.main(["--no-browser"]) == 1
    output = capsys.readouterr()
    assert "cannot start" in output.err and str(failure) in output.err
    assert "Saved data was not reset" in output.err and "Traceback" not in output.err
    assert "open:" not in output.out and "schema:" not in output.out
    assert startup.events == ["database", "bind", "app-failed", "socket-close", "lock-release"]
    assert startup.sock.closed and startup.lock.released and startup.lock.recorded == []


def test_busy_port_never_constructs_timer_or_announces_readiness(startup, monkeypatch, capsys):
    def busy(port):
        startup.events.append("busy-bind")
        raise OSError(errno.EADDRINUSE, "Address already in use")

    monkeypatch.setattr(entry, "_bind", busy)
    assert entry.main(["--no-browser", "--port", "18789"]) == 1
    output = capsys.readouterr()
    assert "port 18789 is unavailable" in output.err and "--port N" in output.err
    assert "open:" not in output.out and "Traceback" not in output.err
    assert startup.events == ["database", "busy-bind", "lock-release"]
    assert startup.lock.released and startup.lock.recorded == []


@pytest.mark.parametrize("failure", [StorageError("startup checkpoint failed"), sqlite3.OperationalError("disk I/O error")])
def test_server_startup_storage_failure_releases_claimed_resources(startup, capsys, failure):
    startup.run_error = failure
    assert entry.main(["--no-browser"]) == 1
    output = capsys.readouterr()
    assert str(failure) in output.err and "Traceback" not in output.err
    assert "open:" not in output.out and startup.lock.recorded == []
    assert startup.sock.closed and startup.lock.released


def test_failed_lifespan_does_not_print_ready_banner_or_record_instance(startup, capsys):
    startup.ready = False
    assert entry.main(["--no-browser"]) == 1
    output = capsys.readouterr()
    assert "did not finish starting" in output.err
    assert "open:" not in output.out and "schema:" not in output.out
    assert startup.lock.recorded == [] and startup.sock.closed and startup.lock.released


def test_ready_banner_and_instance_record_follow_lifespan_success(startup, capsys):
    assert entry.main(["--no-browser", "--port", "18789"]) == 0
    output = capsys.readouterr()
    assert f"data:   {startup.db.path.parent}" in output.out
    assert f"schema: version {current_version(startup.db)}" in output.out
    assert "open:   http://127.0.0.1:18789/" in output.out and "BearPlans stopped." in output.out
    assert startup.events.index("lifespan-ready") < startup.events.index("record-ready")
    assert startup.lock.recorded == ["http://127.0.0.1:18789/"]
    assert startup.config.app is startup.app and startup.config.host == "127.0.0.1"
    assert startup.config.workers == 1
    assert startup.sock.closed and startup.lock.released


def test_graceful_interrupt_after_ready_keeps_existing_exit_behavior(startup, capsys):
    startup.interrupt = True
    assert entry.main(["--no-browser"]) == 0
    assert "BearPlans stopped." in capsys.readouterr().out
    assert startup.sock.closed and startup.lock.released


def test_instance_record_failure_is_reported_before_banner(startup, monkeypatch, capsys):
    def fail(url):
        raise OSError("instance metadata is not writable")

    monkeypatch.setattr(startup.lock, "record", fail)
    assert entry.main(["--no-browser"]) == 1
    output = capsys.readouterr()
    assert "instance metadata is not writable" in output.err and "Traceback" not in output.err
    assert "open:" not in output.out
    assert startup.sock.closed and startup.lock.released


@pytest.mark.parametrize("ready", [True, False])
def test_ready_server_hook_waits_for_actual_uvicorn_startup(monkeypatch, ready):
    events = []

    async def startup(self, sockets=None):
        events.append("lifespan-and-listener")
        self.started = ready

    monkeypatch.setattr(uvicorn.Server, "startup", startup)
    server = entry._ReadyServer(uvicorn.Config(lambda scope, receive, send: None), lambda: events.append("ready"))
    asyncio.run(server.startup())
    assert events == (["lifespan-and-listener", "ready"] if ready else ["lifespan-and-listener"])


def test_failed_readiness_metadata_drains_started_lifespan(monkeypatch):
    events = []

    async def startup(self, sockets=None):
        self.started = True
        events.append("lifespan-ready")

    async def shutdown(self, sockets=None):
        events.append("lifespan-stopped")

    def fail():
        raise StorageError("readiness metadata failed")

    monkeypatch.setattr(uvicorn.Server, "startup", startup)
    monkeypatch.setattr(uvicorn.Server, "shutdown", shutdown)
    server = entry._ReadyServer(uvicorn.Config(lambda scope, receive, send: None), fail)
    with pytest.raises(StorageError, match="metadata failed"):
        asyncio.run(server.startup())
    assert events == ["lifespan-ready", "lifespan-stopped"]


def test_real_corrupt_database_startup_exits_without_binding_or_traceback(tmp_path: Path):
    data_dir = tmp_path / "disposable-startup"
    data_dir.mkdir()
    path = data_dir / "bearplans.sqlite3"
    original = b"synthetic invalid SQLite database" * 100
    path.write_bytes(original)
    # Corruption is rejected before the bind path. No real listener is opened.
    result = subprocess.run(
        [sys.executable, "-m", "backend", "--no-browser", "--port", "18789"],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "BEARPLANS_DATA_DIR": str(data_dir)},
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 1
    assert "cannot start" in result.stderr and "Traceback" not in result.stderr
    assert "open:" not in result.stdout and "schema:" not in result.stdout
    assert path.read_bytes() == original and not (data_dir / "instance.json").exists()
