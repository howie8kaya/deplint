"""Tests for deplint.exporter."""
from __future__ import annotations

import pytest

from deplint.models import AnalysisResult, Issue, IssueCode, IssueSeverity
from deplint.exporter import export_csv, export_markdown, export_results


def _issue(
    code: IssueCode = IssueCode.UNPINNED,
    severity: IssueSeverity = IssueSeverity.WARNING,
    package: str = "requests",
    message: str = "not pinned",
) -> Issue:
    return Issue(code=code, severity=severity, package=package, message=message)


def _result(filename: str, *issues: Issue) -> AnalysisResult:
    return AnalysisResult(filename=filename, issues=list(issues))


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

class TestExportCsv:
    def test_header_always_present(self):
        csv_text = export_csv([])
        assert csv_text.startswith("file,severity,code,package,message")

    def test_empty_results_only_header(self):
        csv_text = export_csv([])
        lines = [l for l in csv_text.splitlines() if l]
        assert len(lines) == 1

    def test_single_issue_row(self):
        issue = _issue(message="needs pin")
        result = _result("req.txt", issue)
        csv_text = export_csv([result])
        lines = csv_text.splitlines()
        assert len(lines) == 2
        assert "req.txt" in lines[1]
        assert "needs pin" in lines[1]

    def test_multiple_results_flattened(self):
        r1 = _result("a.txt", _issue(package="flask"))
        r2 = _result("b.txt", _issue(package="django"), _issue(package="celery"))
        csv_text = export_csv([r1, r2])
        lines = [l for l in csv_text.splitlines() if l]
        assert len(lines) == 4  # header + 3 issues

    def test_none_filename_becomes_empty_string(self):
        result = AnalysisResult(filename=None, issues=[_issue()])
        csv_text = export_csv([result])
        first_data_line = csv_text.splitlines()[1]
        assert first_data_line.startswith(",")


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

class TestExportMarkdown:
    def test_table_header_present(self):
        md = export_markdown([])
        assert "| File |" in md
        assert "|------|" in md

    def test_empty_results_shows_no_issues_row(self):
        md = export_markdown([])
        assert "No issues found" in md

    def test_issue_row_contains_package(self):
        result = _result("requirements.txt", _issue(package="boto3"))
        md = export_markdown([result])
        assert "boto3" in md
        assert "requirements.txt" in md

    def test_ends_with_newline(self):
        md = export_markdown([])
        assert md.endswith("\n")


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

class TestExportResults:
    def test_csv_dispatch(self):
        text = export_results([], "csv")
        assert "severity" in text

    def test_markdown_dispatch(self):
        text = export_results([], "markdown")
        assert "| File |" in text

    def test_md_alias(self):
        text = export_results([], "md")
        assert "| File |" in text

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError, match="Unknown export format"):
            export_results([], "xml")

    def test_case_insensitive_format(self):
        text = export_results([], "CSV")
        assert "severity" in text
