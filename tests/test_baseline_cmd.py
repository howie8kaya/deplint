"""Integration-style tests for the baseline sub-command."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from deplint.commands.baseline_cmd import run_baseline
from deplint.models import AnalysisResult, Issue, IssueCode, IssueSeverity


def _make_issue(pkg: str = "requests") -> Issue:
    return Issue(
        code=IssueCode.UNPINNED,
        severity=IssueSeverity.WARNING,
        package=pkg,
        message=f"{pkg} is unpinned",
        filename="requirements.txt",
    )


def _args(tmp_path: Path, diff: bool = False, paths: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        paths=paths or [str(tmp_path)],
        baseline_file=str(tmp_path / ".deplint-baseline.json"),
        diff=diff,
    )


# ---------------------------------------------------------------------------

def test_no_req_files_returns_1(tmp_path):
    args = _args(tmp_path)
    with patch("deplint.commands.baseline_cmd._collect_req_files", return_value=[]):
        rc = run_baseline(args)
    assert rc == 1


def test_save_creates_baseline_file(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("requests\n")
    issue = _make_issue()
    mock_result = AnalysisResult(filename=str(req), issues=[issue])

    args = _args(tmp_path)
    with patch("deplint.commands.baseline_cmd._collect_req_files", return_value=[req]), \
         patch("deplint.commands.baseline_cmd.Analyzer") as MockAnalyzer:
        MockAnalyzer.return_value.analyze_file.return_value = mock_result
        rc = run_baseline(args)

    assert rc == 0
    baseline_path = Path(args.baseline_file)
    assert baseline_path.exists()
    data = json.loads(baseline_path.read_text())
    assert len(data["baseline"]) == 1


def test_diff_no_new_issues_returns_0(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("requests==2.0.0\n")
    issue = _make_issue()
    mock_result = AnalysisResult(filename=str(req), issues=[issue])

    # pre-populate baseline with that issue
    from deplint.baseline import save_baseline
    save_baseline([issue], path=tmp_path / ".deplint-baseline.json")

    args = _args(tmp_path, diff=True)
    with patch("deplint.commands.baseline_cmd._collect_req_files", return_value=[req]), \
         patch("deplint.commands.baseline_cmd.Analyzer") as MockAnalyzer:
        MockAnalyzer.return_value.analyze_file.return_value = mock_result
        rc = run_baseline(args)

    assert rc == 0


def test_diff_new_issues_returns_1(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("flask\n")
    new_issue = _make_issue(pkg="flask")
    mock_result = AnalysisResult(filename=str(req), issues=[new_issue])

    # baseline is empty
    args = _args(tmp_path, diff=True)
    with patch("deplint.commands.baseline_cmd._collect_req_files", return_value=[req]), \
         patch("deplint.commands.baseline_cmd.Analyzer") as MockAnalyzer:
        MockAnalyzer.return_value.analyze_file.return_value = mock_result
        rc = run_baseline(args)

    assert rc == 1
