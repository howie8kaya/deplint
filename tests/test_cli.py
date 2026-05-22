"""Tests for the deplint CLI."""

import json
import textwrap
from pathlib import Path

import pytest

from deplint.cli import run


@pytest.fixture()
def req_file(tmp_path):
    """Factory that writes a requirements file and returns its path string."""
    def _write(content: str) -> str:
        p = tmp_path / "requirements.txt"
        p.write_text(textwrap.dedent(content))
        return str(p)
    return _write


def test_clean_file_exits_zero(req_file):
    path = req_file("""
        requests==2.31.0
        flask==3.0.0
    """)
    assert run([path]) == 0


def test_unpinned_exits_nonzero_on_error(req_file):
    path = req_file("""
        requests
        flask==3.0.0
    """)
    assert run([path, "--fail-on", "error"]) == 1


def test_fail_on_warning_triggers(req_file):
    # duplicate triggers a warning-level issue
    path = req_file("""
        requests==2.31.0
        requests==2.28.0
    """)
    assert run([path, "--fail-on", "warning"]) == 1


def test_fail_on_warning_passes_for_info(req_file, capsys):
    path = req_file("""
        requests==2.31.0
    """)
    # no warnings or errors — should pass even with --fail-on warning
    code = run([path, "--fail-on", "warning"])
    assert code == 0


def test_json_output_is_valid(req_file, capsys):
    path = req_file("""
        requests==2.31.0
    """)
    run([path, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "issues" in data
    assert "summary" in data


def test_missing_file_exits_2(capsys):
    code = run(["/nonexistent/requirements.txt"])
    assert code == 2
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_multiple_files(req_file, tmp_path):
    p1 = req_file("requests==2.31.0\n")
    p2 = tmp_path / "other.txt"
    p2.write_text("flask==3.0.0\n")
    assert run([p1, str(p2)]) == 0


def test_text_output_contains_filename(req_file, capsys):
    path = req_file("requests\n")
    run([path])
    captured = capsys.readouterr()
    assert "requirements.txt" in captured.out or "UNPINNED" in captured.out
