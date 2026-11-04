"""Credentials live in the data folder and are copied once from the code folder's .secrets/."""

from __future__ import annotations

import os
import stat

from backend.platform import secrets
from backend.platform.google import client_file, token_file


def _use_data_dir(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setenv("BEARPLANS_DATA_DIR", str(data))
    monkeypatch.delenv("BEARPLANS_SECRETS_FILE", raising=False)
    return data / "secrets"


def _legacy(tmp_path, **files):
    folder = tmp_path / "code" / ".secrets"
    folder.mkdir(parents=True)
    for name, text in files.items():
        (folder / name).write_text(text)
        (folder / name).chmod(0o644)
    return folder


def test_default_location_is_the_data_folder(monkeypatch, tmp_path):
    target = _use_data_dir(monkeypatch, tmp_path)
    assert secrets.secrets_file() == target.resolve() / "bearplans.secrets.env"
    assert client_file().parent == token_file().parent == target.resolve()


def test_old_files_are_copied_once_owner_only_and_left_in_place(monkeypatch, tmp_path):
    target = _use_data_dir(monkeypatch, tmp_path)
    legacy = _legacy(tmp_path, **{"bearplans.secrets.env": "BCOURSES_TOKEN=abc\n",
                                  "google_oauth_client.json": "{}", "google_token.json": "{}", "notes.txt": "x"})
    copied = secrets.move_legacy_secrets(legacy)
    assert sorted(copied) == ["bearplans.secrets.env", "google_oauth_client.json", "google_token.json"]
    assert not (target / "notes.txt").exists()  # Only known credential files move.
    assert secrets.read_secret("BCOURSES_TOKEN") == "abc"
    assert stat.S_IMODE(target.stat().st_mode) == 0o700
    assert all(stat.S_IMODE((target / name).stat().st_mode) == 0o600 for name in copied)
    assert (legacy / "bearplans.secrets.env").read_text() == "BCOURSES_TOKEN=abc\n"  # Old folder untouched.
    assert not list(target.glob("*.tmp"))

    # A credential removed later (for example in the app) is not copied back.
    (target / "bearplans.secrets.env").unlink()
    assert secrets.move_legacy_secrets(legacy) == []
    assert secrets.read_secret("BCOURSES_TOKEN") is None


def test_existing_new_files_are_never_overwritten(monkeypatch, tmp_path):
    target = _use_data_dir(monkeypatch, tmp_path)
    target.mkdir(parents=True)
    (target / "bearplans.secrets.env").write_text("BCOURSES_TOKEN=new\n")
    legacy = _legacy(tmp_path, **{"bearplans.secrets.env": "BCOURSES_TOKEN=old\n", "google_token.json": "{}"})
    assert secrets.move_legacy_secrets(legacy) == ["google_token.json"]
    assert secrets.read_secret("BCOURSES_TOKEN") == "new"


def test_nothing_happens_without_an_old_folder_or_with_the_test_override(monkeypatch, tmp_path):
    target = _use_data_dir(monkeypatch, tmp_path)
    assert secrets.move_legacy_secrets(tmp_path / "missing") == []
    assert not target.exists()
    legacy = _legacy(tmp_path, **{"bearplans.secrets.env": "BCOURSES_TOKEN=abc\n"})
    monkeypatch.setenv("BEARPLANS_SECRETS_FILE", str(tmp_path / "elsewhere" / "s.env"))
    assert secrets.move_legacy_secrets(legacy) == []
    assert not (tmp_path / "elsewhere").exists() and not target.exists()


def test_the_real_old_folder_is_not_touched_by_tests():
    assert os.environ["BEARPLANS_SECRETS_FILE"].endswith("none.env")
