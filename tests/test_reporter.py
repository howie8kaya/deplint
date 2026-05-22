"""Tests for deplint.reporter."""

import pytest

from deplint.models import AnalysisResult, Issue, IssueCode, IssueSeverity
from deplint.reporter import Report, build_report, render_report


def _issue(severity: IssueSeverity, code: IssueCode = IssueCode.UNPINNED) -> Issue:
    return Issue(
        severity=severity,
        code=code,
        message="test issue",
        package="pkg",
        line=1,
    )


def _result(filename: str, *issues: Issue) -> AnalysisResult:
    return AnalysisResult(filename=filename, issues=list(issues))


class TestReport:
    def test_empty_report(self):
        r = Report()
        assert r.total_issues == 0
        assert not r.has_errors
        assert not r.has_warnings
        assert r.exit_code() == 0

    def test_add_result(self):
        r = Report()
        r.add(_result("a.txt", _issue(IssueSeverity.ERROR)))
        assert r.total_issues == 1
        assert r.has_errors

    def test_exit_code_error(self):
        r = Report()
        r.add(_result("a.txt", _issue(IssueSeverity.ERROR)))
        assert r.exit_code() == 1

    def test_exit_code_warning_default(self):
        r = Report()
        r.add(_result("a.txt", _issue(IssueSeverity.WARNING)))
        assert r.exit_code(fail_on_warning=False) == 0

    def test_exit_code_warning_strict(self):
        r = Report()
        r.add(_result("a.txt", _issue(IssueSeverity.WARNING)))
        assert r.exit_code(fail_on_warning=True) == 1

    def test_exit_code_info_only(self):
        r = Report()
        r.add(_result("a.txt", _issue(IssueSeverity.INFO)))
        assert r.exit_code(fail_on_warning=True) == 0


class TestBuildReport:
    def test_build_from_list(self):
        results = [
            _result("a.txt", _issue(IssueSeverity.ERROR)),
            _result("b.txt", _issue(IssueSeverity.WARNING)),
        ]
        report = build_report(results)
        assert len(report.results) == 2
        assert report.total_issues == 2

    def test_build_empty(self):
        report = build_report([])
        assert report.total_issues == 0


class TestRenderReport:
    def test_text_render_contains_summary(self):
        results = [_result("req.txt", _issue(IssueSeverity.ERROR))]
        report = build_report(results)
        output = render_report(report, fmt="text", color=False)
        assert "Total:" in output
        assert "1 issue(s)" in output
        assert "1 file(s)" in output

    def test_json_render_single(self):
        results = [_result("req.txt")]
        report = build_report(results)
        output = render_report(report, fmt="json")
        assert "req.txt" in output

    def test_json_render_multiple(self):
        results = [_result("a.txt"), _result("b.txt")]
        report = build_report(results)
        output = render_report(report, fmt="json")
        assert output.startswith("[")
        assert output.endswith("]")
