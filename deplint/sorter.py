"""Utilities for sorting requirements and issues in various orders."""

from __future__ import annotations

from typing import List

from deplint.models import Issue, IssueSeverity, AnalysisResult


_SEVERITY_ORDER = {
    IssueSeverity.ERROR: 0,
    IssueSeverity.WARNING: 1,
    IssueSeverity.INFO: 2,
}


def sort_issues_by_severity(issues: List[Issue]) -> List[Issue]:
    """Return issues sorted by severity (errors first, then warnings, then info)."""
    return sorted(issues, key=lambda i: _SEVERITY_ORDER.get(i.severity, 99))


def sort_issues_by_package(issues: List[Issue]) -> List[Issue]:
    """Return issues sorted alphabetically by package name (case-insensitive)."""
    return sorted(issues, key=lambda i: (i.package or "").lower())


def sort_issues_by_code(issues: List[Issue]) -> List[Issue]:
    """Return issues sorted by issue code string."""
    return sorted(issues, key=lambda i: i.code.value)


def sort_results_by_file(results: List[AnalysisResult]) -> List[AnalysisResult]:
    """Return analysis results sorted alphabetically by filename."""
    return sorted(results, key=lambda r: (r.filename or "").lower())


def sort_results_by_issue_count(results: List[AnalysisResult]) -> List[AnalysisResult]:
    """Return analysis results sorted by number of issues, descending."""
    return sorted(results, key=lambda r: len(r.issues), reverse=True)


def sort_issues_multi(
    issues: List[Issue],
    primary: str = "severity",
    secondary: str = "package",
) -> List[Issue]:
    """Sort issues by two keys.

    Supported key names: 'severity', 'package', 'code'.
    """
    _key_fns = {
        "severity": lambda i: _SEVERITY_ORDER.get(i.severity, 99),
        "package": lambda i: (i.package or "").lower(),
        "code": lambda i: i.code.value,
    }
    pk = _key_fns.get(primary)
    sk = _key_fns.get(secondary)
    if pk is None:
        raise ValueError(f"Unknown sort key: {primary!r}")
    if sk is None:
        raise ValueError(f"Unknown sort key: {secondary!r}")
    return sorted(issues, key=lambda i: (pk(i), sk(i)))
