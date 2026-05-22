"""Tests for deplint.filter."""
from __future__ import annotations

import pytest

from deplint.config import DeplintConfig
from deplint.filter import apply_exclude, apply_ignore, filter_results
from deplint.models import AnalysisResult, Issue, IssueCode, IssueSeverity


def _issue(code: IssueCode, line: int = 1) -> Issue:
    return Issue(
        code=code,
        severity=IssueSeverity.ERROR,
        line=line,
        message="test",
        package="pkg",
    )


def _result(filename: str, *codes: IssueCode) -> AnalysisResult:
    return AnalysisResult(filename=filename, issues=[_issue(c) for c in codes])


# --- apply_ignore ---

def test_apply_ignore_empty_list_keeps_all():
    issues = [_issue(IssueCode.UNPINNED), _issue(IssueCode.DUPLICATE)]
    assert apply_ignore(issues, []) == issues


def test_apply_ignore_removes_matching_code():
    issues = [_issue(IssueCode.UNPINNED), _issue(IssueCode.DUPLICATE)]
    result = apply_ignore(issues, [IssueCode.UNPINNED.value])
    assert len(result) == 1
    assert result[0].code == IssueCode.DUPLICATE


def test_apply_ignore_case_insensitive():
    issues = [_issue(IssueCode.UNPINNED)]
    assert apply_ignore(issues, [IssueCode.UNPINNED.value.lower()]) == []


def test_apply_ignore_unknown_code_is_harmless():
    issues = [_issue(IssueCode.UNPINNED)]
    assert len(apply_ignore(issues, ["ZZZZ"])) == 1


# --- apply_exclude ---

def test_apply_exclude_no_patterns():
    r = _result("requirements.txt")
    assert apply_exclude(r, []) is False


def test_apply_exclude_substring_match():
    r = _result("requirements-dev.txt")
    assert apply_exclude(r, ["requirements-dev"]) is True


def test_apply_exclude_no_match():
    r = _result("requirements.txt")
    assert apply_exclude(r, ["requirements-dev.txt"]) is False


# --- filter_results ---

def test_filter_results_excludes_file():
    results = [
        _result("requirements.txt", IssueCode.UNPINNED),
        _result("requirements-dev.txt", IssueCode.DUPLICATE),
    ]
    cfg = DeplintConfig(exclude=["requirements-dev"])
    out = filter_results(results, cfg)
    assert len(out) == 1
    assert out[0].filename == "requirements.txt"


def test_filter_results_ignores_codes():
    results = [
        _result("requirements.txt", IssueCode.UNPINNED, IssueCode.DUPLICATE),
    ]
    cfg = DeplintConfig(ignore_codes=[IssueCode.UNPINNED.value])
    out = filter_results(results, cfg)
    assert len(out[0].issues) == 1
    assert out[0].issues[0].code == IssueCode.DUPLICATE


def test_filter_results_no_config_returns_all():
    results = [
        _result("requirements.txt", IssueCode.UNPINNED),
        _result("requirements-dev.txt", IssueCode.DUPLICATE),
    ]
    cfg = DeplintConfig()
    out = filter_results(results, cfg)
    assert len(out) == 2
