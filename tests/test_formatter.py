"""Tests for deplint.formatter module."""

import json
import pytest
from deplint.formatter import TextFormatter, JsonFormatter, get_formatter
from deplint.models import Issue, IssueSeverity, IssueCode, AnalysisResult


def make_issue(severity, code, message, line=None, package="requests"):
    return Issue(severity=severity, code=code, message=message, line=line, package=package)


@pytest.fixture
def clean_result():
    return AnalysisResult(source="requirements.txt", issues=[])


@pytest.fixture
def result_with_issues():
    issues = [
        make_issue(IssueSeverity.ERROR, IssueCode.CONFLICT, "Version conflict", line=3),
        make_issue(IssueSeverity.WARNING, IssueCode.UNPINNED, "Not pinned", line=7, package="flask"),
        make_issue(IssueSeverity.INFO, IssueCode.DUPLICATE, "Duplicate entry", line=12, package="numpy"),
    ]
    return AnalysisResult(source="requirements.txt", issues=issues)


class TestTextFormatter:
    def test_no_issues(self, clean_result):
        out = TextFormatter().format(clean_result)
        assert "No issues found" in out

    def test_error_prefix(self, result_with_issues):
        out = TextFormatter().format(result_with_issues)
        assert "[ERROR]" in out

    def test_warning_prefix(self, result_with_issues):
        out = TextFormatter().format(result_with_issues)
        assert "[WARN]" in out

    def test_info_prefix(self, result_with_issues):
        out = TextFormatter().format(result_with_issues)
        assert "[INFO]" in out

    def test_summary_counts(self, result_with_issues):
        out = TextFormatter().format(result_with_issues)
        assert "1 error(s)" in out
        assert "1 warning(s)" in out
        assert "1 info(s)" in out

    def test_line_numbers_shown(self, result_with_issues):
        out = TextFormatter().format(result_with_issues)
        assert "line 3" in out
        assert "line 7" in out

    def test_global_when_no_line(self):
        result = AnalysisResult(
            source="req.txt",
            issues=[make_issue(IssueSeverity.WARNING, IssueCode.UNPINNED, "no line", line=None)],
        )
        out = TextFormatter().format(result)
        assert "global" in out


class TestJsonFormatter:
    def test_valid_json(self, result_with_issues):
        out = JsonFormatter().format(result_with_issues)
        data = json.loads(out)
        assert isinstance(data, dict)

    def test_issue_count(self, result_with_issues):
        data = json.loads(JsonFormatter().format(result_with_issues))
        assert data["issue_count"] == 3

    def test_source_field(self, result_with_issues):
        data = json.loads(JsonFormatter().format(result_with_issues))
        assert data["source"] == "requirements.txt"

    def test_issue_fields(self, result_with_issues):
        data = json.loads(JsonFormatter().format(result_with_issues))
        first = data["issues"][0]
        assert "line" in first and "severity" in first and "code" in first and "message" in first


class TestGetFormatter:
    def test_get_text(self):
        assert isinstance(get_formatter("text"), TextFormatter)

    def test_get_json(self):
        assert isinstance(get_formatter("json"), JsonFormatter)

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown formatter"):
            get_formatter("xml")
