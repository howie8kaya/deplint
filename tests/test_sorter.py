"""Tests for deplint.sorter."""

from __future__ import annotations

import pytest

from deplint.models import Issue, IssueSeverity, IssueCode, AnalysisResult
from deplint.sorter import (
    sort_issues_by_severity,
    sort_issues_by_package,
    sort_issues_by_code,
    sort_results_by_file,
    sort_results_by_issue_count,
    sort_issues_multi,
)


def _issue(code: IssueCode, severity: IssueSeverity, package: str) -> Issue:
    return Issue(code=code, severity=severity, package=package, message="test")


def _result(filename: str, issues: list) -> AnalysisResult:
    return AnalysisResult(filename=filename, issues=issues)


# --- sort_issues_by_severity ---

def test_sort_by_severity_errors_first():
    issues = [
        _issue(IssueCode.UNPINNED, IssueSeverity.INFO, "z-pkg"),
        _issue(IssueCode.CONFLICT, IssueSeverity.ERROR, "a-pkg"),
        _issue(IssueCode.DUPLICATE, IssueSeverity.WARNING, "m-pkg"),
    ]
    result = sort_issues_by_severity(issues)
    assert result[0].severity == IssueSeverity.ERROR
    assert result[1].severity == IssueSeverity.WARNING
    assert result[2].severity == IssueSeverity.INFO


def test_sort_by_severity_stable_within_same_level():
    issues = [
        _issue(IssueCode.UNPINNED, IssueSeverity.WARNING, "b"),
        _issue(IssueCode.DUPLICATE, IssueSeverity.WARNING, "a"),
    ]
    result = sort_issues_by_severity(issues)
    # Both are WARNING; original relative order preserved
    assert [i.package for i in result] == ["b", "a"]


# --- sort_issues_by_package ---

def test_sort_by_package_alphabetical():
    issues = [
        _issue(IssueCode.UNPINNED, IssueSeverity.WARNING, "Zlib"),
        _issue(IssueCode.UNPINNED, IssueSeverity.WARNING, "alpha"),
        _issue(IssueCode.UNPINNED, IssueSeverity.WARNING, "Beta"),
    ]
    result = sort_issues_by_package(issues)
    assert [i.package for i in result] == ["alpha", "Beta", "Zlib"]


def test_sort_by_package_none_treated_as_empty():
    issues = [
        _issue(IssueCode.UNPINNED, IssueSeverity.WARNING, "requests"),
        Issue(code=IssueCode.CONFLICT, severity=IssueSeverity.ERROR, package=None, message="x"),
    ]
    result = sort_issues_by_package(issues)
    assert result[0].package is None


# --- sort_issues_by_code ---

def test_sort_by_code():
    issues = [
        _issue(IssueCode.OUTDATED, IssueSeverity.INFO, "a"),
        _issue(IssueCode.CONFLICT, IssueSeverity.ERROR, "b"),
        _issue(IssueCode.UNPINNED, IssueSeverity.WARNING, "c"),
    ]
    result = sort_issues_by_code(issues)
    codes = [i.code.value for i in result]
    assert codes == sorted(codes)


# --- sort_results_by_file ---

def test_sort_results_by_file():
    results = [_result("z.txt", []), _result("a.txt", []), _result("m.txt", [])]
    sorted_r = sort_results_by_file(results)
    assert [r.filename for r in sorted_r] == ["a.txt", "m.txt", "z.txt"]


# --- sort_results_by_issue_count ---

def test_sort_results_by_issue_count_descending():
    i = _issue(IssueCode.UNPINNED, IssueSeverity.WARNING, "p")
    results = [_result("a.txt", [i]), _result("b.txt", [i, i, i]), _result("c.txt", [i, i])]
    sorted_r = sort_results_by_issue_count(results)
    assert [len(r.issues) for r in sorted_r] == [3, 2, 1]


# --- sort_issues_multi ---

def test_sort_multi_severity_then_package():
    issues = [
        _issue(IssueCode.UNPINNED, IssueSeverity.WARNING, "z"),
        _issue(IssueCode.CONFLICT, IssueSeverity.ERROR, "b"),
        _issue(IssueCode.DUPLICATE, IssueSeverity.WARNING, "a"),
    ]
    result = sort_issues_multi(issues, primary="severity", secondary="package")
    assert result[0].severity == IssueSeverity.ERROR
    assert result[1].package == "a"
    assert result[2].package == "z"


def test_sort_multi_invalid_key_raises():
    with pytest.raises(ValueError, match="Unknown sort key"):
        sort_issues_multi([], primary="bogus")
