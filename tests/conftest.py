from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.storage.db import Database, open_database

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return open_database(tmp_path / "test.sqlite3")


@pytest.fixture
def client(db: Database) -> TestClient:
    # TestClient sends Host: testserver; use the address a real browser would.
    return TestClient(create_app(db), base_url="http://127.0.0.1:8765")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def http_json(method: str, url: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"null")


class Service:
    """A real `python -m backend` process, as launch.py starts it."""

    def __init__(self, data_dir: Path, port: int, *, via_launcher: bool = False) -> None:
        self.data_dir = data_dir
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self.process: subprocess.Popen[str] | None = None
        self.output = ""
        self.via_launcher = via_launcher

    def start(self) -> Service:
        env = {**os.environ, "BEARPLANS_DATA_DIR": str(self.data_dir), "PYTHONUNBUFFERED": "1"}
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        entry = [str(ROOT / "launch.py")] if self.via_launcher else ["-m", "backend"]
        self.process = subprocess.Popen(
            [sys.executable, *entry, "--no-browser", "--port", str(self.port)],
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=flags,
        )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.output = self.process.stdout.read()
                raise AssertionError(f"service exited early ({self.process.returncode}):\n{self.output}")
            try:
                if http_json("GET", f"{self.url}/api/health")[0] == 200:
                    return self
            except OSError:
                pass
            time.sleep(0.1)
        self.kill()
        raise AssertionError("service did not become healthy within 30s")

    def stop(self) -> int:
        """Graceful stop, as Ctrl+C would do."""
        assert self.process is not None
        self.process.send_signal(signal.CTRL_BREAK_EVENT if sys.platform == "win32" else signal.SIGINT)
        try:
            code = self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.kill()
            raise AssertionError("service did not stop within 15s")
        self.output = self.process.stdout.read()
        return code

    def kill(self) -> None:
        """Abrupt termination, as a crash or force-quit would do."""
        if self.process and self.process.poll() is None:
            self.process.kill()
            self.process.wait(timeout=15)
        if self.process and self.process.stdout:
            self.output = self.process.stdout.read()


@contextmanager
def running_service(data_dir: Path, port: int | None = None) -> Iterator[Service]:
    service = Service(data_dir, port or free_port()).start()
    try:
        yield service
    finally:
        service.kill()
