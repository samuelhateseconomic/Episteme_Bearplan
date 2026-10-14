from pathlib import Path

import pytest

from backend.platform.paths import (
    DATA_DIR_ENV,
    SOURCE_ROOT,
    DataDirError,
    default_data_dir,
    ensure_data_dir,
    resolve_data_dir,
)


def test_mac_default_is_application_support(tmp_path: Path) -> None:
    assert default_data_dir("darwin", {}, tmp_path) == tmp_path / "Library" / "Application Support" / "BearPlans"


def test_windows_default_uses_local_app_data(tmp_path: Path) -> None:
    assert default_data_dir("win32", {"LOCALAPPDATA": str(tmp_path)}, tmp_path) == tmp_path / "BearPlans"


def test_linux_default_honours_xdg(tmp_path: Path) -> None:
    assert default_data_dir("linux", {"XDG_DATA_HOME": str(tmp_path)}, tmp_path) == tmp_path / "bearplans"


def test_platform_default_is_outside_the_source_tree() -> None:
    path = resolve_data_dir({})
    assert SOURCE_ROOT not in path.parents and path != SOURCE_ROOT


def test_environment_override(tmp_path: Path) -> None:
    assert resolve_data_dir({DATA_DIR_ENV: str(tmp_path / "data")}) == (tmp_path / "data").resolve()


@pytest.mark.parametrize("inside", [".", "backend", "frontend/dist", "data"])
def test_rejects_data_dir_inside_source_tree(inside: str) -> None:
    with pytest.raises(DataDirError, match="inside the source tree"):
        resolve_data_dir({DATA_DIR_ENV: str(SOURCE_ROOT / inside)})


def test_rejects_source_tree_with_different_case_or_relative_spelling(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(SOURCE_ROOT / "backend")
    with pytest.raises(DataDirError):
        resolve_data_dir({DATA_DIR_ENV: "../somewhere"})


def test_ensure_creates_nested_directory(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b"
    assert ensure_data_dir(target).is_dir()


def test_ensure_rejects_a_file(tmp_path: Path) -> None:
    target = tmp_path / "file"
    target.write_text("x")
    with pytest.raises(DataDirError):
        ensure_data_dir(target)
