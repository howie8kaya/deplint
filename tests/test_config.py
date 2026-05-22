"""Tests for deplint.config."""
from __future__ import annotations

import pytest

from deplint.config import DeplintConfig, load_config


@pytest.fixture()
def tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_defaults_when_no_file(tmp_cwd):
    cfg = load_config(str(tmp_cwd))
    assert cfg.ignore_codes == []
    assert cfg.fail_on == "error"
    assert cfg.check_outdated is False
    assert cfg.exclude == []


def test_pyproject_toml_tool_section(tmp_cwd):
    (tmp_cwd / "pyproject.toml").write_text(
        "[tool.deplint]\n"
        'ignore = ["W001"]\n'
        'fail_on = "warning"\n'
        "check_outdated = true\n"
        'exclude = ["requirements-dev.txt"]\n',
        encoding="utf-8",
    )
    cfg = load_config(str(tmp_cwd))
    assert cfg.ignore_codes == ["W001"]
    assert cfg.fail_on == "warning"
    assert cfg.check_outdated is True
    assert cfg.exclude == ["requirements-dev.txt"]


def test_deplint_toml_top_level(tmp_cwd):
    (tmp_cwd / ".deplint.toml").write_text(
        "[deplint]\n"
        'ignore = ["E002", "E003"]\n'
        'fail_on = "info"\n',
        encoding="utf-8",
    )
    cfg = load_config(str(tmp_cwd))
    assert cfg.ignore_codes == ["E002", "E003"]
    assert cfg.fail_on == "info"


def test_deplint_toml_preferred_over_pyproject(tmp_cwd):
    """A .deplint.toml in the same directory should win over pyproject.toml."""
    (tmp_cwd / "pyproject.toml").write_text(
        "[tool.deplint]\nfail_on = \"error\"\n", encoding="utf-8"
    )
    (tmp_cwd / ".deplint.toml").write_text(
        "[deplint]\nfail_on = \"warning\"\n", encoding="utf-8"
    )
    cfg = load_config(str(tmp_cwd))
    assert cfg.fail_on == "warning"


def test_walks_up_to_parent(tmp_cwd):
    (tmp_cwd / "pyproject.toml").write_text(
        "[tool.deplint]\ncheck_outdated = true\n", encoding="utf-8"
    )
    subdir = tmp_cwd / "src" / "mypackage"
    subdir.mkdir(parents=True)
    cfg = load_config(str(subdir))
    assert cfg.check_outdated is True


def test_empty_toml_section_returns_defaults(tmp_cwd):
    (tmp_cwd / ".deplint.toml").write_text("", encoding="utf-8")
    cfg = load_config(str(tmp_cwd))
    assert cfg == DeplintConfig()
