"""Tests for deplint.grouper."""
from __future__ import annotations

import pytest

from deplint.models import AnalysisResult, Issue, IssueCode, IssueSeverity
from deplint.grouper import (
    group_by_code,
    group_by_file,
    group_by_package,
    summary_by_code,
    summary_by_package,
)


def _issue(code: IssueCode, package: str, severity: IssueSeverity = IssueSeverity.ERROR) -> Issue:
    return Issue(code=code, severity=severity, package_name=package, message=f"{package} issue")


def _result(path: str, issues: list) -> AnalysisResult:
    return AnalysisResult(path=path, issues=issues)


@pytest.fixture()
def results():
    return [
        _result(
            "reqs/base.txt",
            [
                _issue(IssueCode.UNPINNED, "requests"),
                _issue(IssueCode.DUPLICATE, "flask"),
            ],
        ),
        _result(
            "reqs/dev.txt",
            [
                _issue(IssueCode.UNPINNED, "pytest"),
                _issue(IssueCode.CONFLICT, "requests", IssueSeverity.WARNING),
            ],
        ),
    ]


def test_group_by_package_merges_across_files(results):
    grouped = group_by_package(results)
    assert "requests" in grouped
    assert len(grouped["requests"]) == 2
    assert len(grouped["flask"]) == 1
    assert len(grouped["pytest"]) == 1


def test_group_by_code_aggregates_codes(results):
    grouped = group_by_code(results)
    unpinned_code = IssueCode.UNPINNED.value
    assert unpinned_code in grouped
    assert len(grouped[unpinned_code]) == 2


def test_group_by_file_maps_path_to_issues(results):
    grouped = group_by_file(results)
    assert "reqs/base.txt" in grouped
    assert len(grouped["reqs/base.txt"]) == 2
    assert len(grouped["reqs/dev.txt"]) == 2


def test_group_by_file_empty_results():
    grouped = group_by_file([])
    assert grouped == {}


def test_summary_by_package(results):
    summary = summary_by_package(results)
    assert summary["requests"] == 2
    assert summary["flask"] == 1


def test_summary_by_code(results):
    summary = summary_by_code(results)
    assert summary[IssueCode.UNPINNED.value] == 2
    assert summary[IssueCode.DUPLICATE.value] == 1
    assert summary[IssueCode.CONFLICT.value] == 1


def test_group_by_package_unknown_package():
    issue = Issue(code=IssueCode.UNPINNED, severity=IssueSeverity.ERROR, package_name=None, message="no pkg")
    result = _result("req.txt", [issue])
    grouped = group_by_package([result])
    assert "<unknown>" in grouped
    assert len(grouped["<unknown>"]) == 1
