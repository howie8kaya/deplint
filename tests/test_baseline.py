"""Tests for deplint.baseline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from deplint.baseline import (
    _issue_key,
    filter_baseline,
    load_baseline,
    save_baseline,
)
from deplint.models import Issue, IssueCode, IssueSeverity


def _issue(
    code: IssueCode = IssueCode.UNPINNED,
    package: str = "requests",
    filename: str | None = "requirements.txt",
) -> Issue:
    return Issue(
        code=code,
        severity=IssueSeverity.WARNING,
        package=package,
        message=f"{package} has issue {code.value}",
        filename=filename,
    )


# ---------------------------------------------------------------------------
# _issue_key
# ---------------------------------------------------------------------------

def test_issue_key_includes_code_package_filename():
    i = _issue(package="flask", filename="req.txt")
    key = _issue_key(i)
    assert "flask" in key
    assert "req.txt" in key
    assert i.code.value in key


def test_issue_key_none_filename():
    i = _issue(filename=None)
    key = _issue_key(i)
    assert key.endswith(":")


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path):
    p = tmp_path / "baseline.json"
    issues = [_issue(package="flask"), _issue(package="django")]
    save_baseline(issues, path=p)
    assert p.exists()
    data = json.loads(p.read_text())
    assert "baseline" in data
    assert len(data["baseline"]) == 2


def test_round_trip_restores_keys(tmp_path):
    p = tmp_path / "baseline.json"
    issues = [_issue(package="requests")]
    save_baseline(issues, path=p)
    baseline = load_baseline(path=p)
    assert _issue_key(issues[0]) in baseline


def test_load_missing_file_returns_empty(tmp_path):
    result = load_baseline(path=tmp_path / "nonexistent.json")
    assert result == {}


def test_load_corrupt_file_returns_empty(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json at all")
    assert load_baseline(path=p) == {}


# ---------------------------------------------------------------------------
# filter_baseline
# ---------------------------------------------------------------------------

def test_filter_baseline_removes_known_issues():
    issues = [_issue(package="requests"), _issue(package="flask")]
    baseline = {_issue_key(issues[0]): True}
    result = filter_baseline(issues, baseline)
    assert len(result) == 1
    assert result[0].package == "flask"


def test_filter_baseline_empty_baseline_keeps_all():
    issues = [_issue(package="a"), _issue(package="b")]
    assert filter_baseline(issues, {}) == issues


def test_filter_baseline_all_known_returns_empty():
    issues = [_issue(package="x")]
    baseline = {_issue_key(i): True for i in issues}
    assert filter_baseline(issues, baseline) == []
