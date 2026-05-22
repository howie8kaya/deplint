"""Tests for deplint.formatter."""
from __future__ import annotations

import json

import pytest

from deplint.models import AnalysisResult, Issue, IssueCode, IssueSeverity
from deplint.formatter import GroupedTextFormatter, JsonFormatter, TextFormatter


def make_issue(code=IssueCode.UNPINNED, pkg="requests", sev=IssueSeverity.ERROR) -> Issue:
    return Issue(code=code, severity=sev, package_name=pkg, message=f"{pkg} has an issue")


def clean_result(path="req.txt") -> AnalysisResult:
    return AnalysisResult(path=path, issues=[])


def result_with_issues(path="req.txt") -> AnalysisResult:
    return AnalysisResult(
        path=path,
        issues=[
            make_issue(IssueCode.UNPINNED, "requests"),
            make_issue(IssueCode.DUPLICATE, "flask", IssueSeverity.WARNING),
        ],
    )


class TestTextFormatter:
    def test_no_issues_shows_summary_only(self):
        fmt = TextFormatter()
        out = fmt.format([clean_result()])
        assert "0 issue(s)" in out
        assert "==>" not in out

    def test_issues_show_file_header(self):
        fmt = TextFormatter()
        out = fmt.format([result_with_issues()])
        assert "==> req.txt" in out

    def test_severity_shown_in_output(self):
        fmt = TextFormatter()
        out = fmt.format([result_with_issues()])
        assert "[ERROR]" in out
        assert "[WARNING]" in out

    def test_summary_counts_correctly(self):
        fmt = TextFormatter()
        out = fmt.format([result_with_issues(), result_with_issues("other.txt")])
        assert "4 issue(s)" in out
        assert "2 file(s)" in out


class TestJsonFormatter:
    def test_output_is_valid_json(self):
        fmt = JsonFormatter()
        out = fmt.format([result_with_issues()])
        data = json.loads(out)
        assert "files" in data
        assert "summary" in data

    def test_summary_contains_by_code(self):
        fmt = JsonFormatter()
        out = fmt.format([result_with_issues()])
        data = json.loads(out)
        assert "by_code" in data["summary"]

    def test_summary_contains_by_package(self):
        fmt = JsonFormatter()
        out = fmt.format([result_with_issues()])
        data = json.loads(out)
        assert "requests" in data["summary"]["by_package"]

    def test_empty_results_gives_zero_total(self):
        fmt = JsonFormatter()
        out = fmt.format([])
        data = json.loads(out)
        assert data["summary"]["total_issues"] == 0


class TestGroupedTextFormatter:
    def test_groups_by_package(self):
        fmt = GroupedTextFormatter()
        out = fmt.format([result_with_issues()])
        assert "Package: requests" in out
        assert "Package: flask" in out

    def test_summary_line_present(self):
        fmt = GroupedTextFormatter()
        out = fmt.format([result_with_issues()])
        assert "issue(s) across" in out

    def test_empty_results(self):
        fmt = GroupedTextFormatter()
        out = fmt.format([])
        assert "0 issue(s)" in out
