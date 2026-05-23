"""Tests for deplint.summarizer."""

from deplint.models import IssueSeverity, IssueCode, Issue, AnalysisResult
from deplint.summarizer import summarize, format_summary, SummaryStats


def _issue(code=IssueCode.UNPINNED, severity=IssueSeverity.WARNING, package="requests"):
    return Issue(code=code, severity=severity, package=package, message="test")


def _result(filename="req.txt", issues=None):
    return AnalysisResult(filename=filename, issues=issues or [])


def test_empty_results_give_zero_stats():
    stats = summarize([])
    assert stats.total_files == 0
    assert stats.total_issues == 0
    assert stats.is_clean


def test_clean_result_counts_file_but_no_issues():
    stats = summarize([_result()])
    assert stats.total_files == 1
    assert stats.files_with_issues == 0
    assert stats.clean_files == 1
    assert stats.is_clean


def test_result_with_issues_increments_counters():
    issues = [_issue(severity=IssueSeverity.ERROR), _issue(severity=IssueSeverity.WARNING)]
    stats = summarize([_result(issues=issues)])
    assert stats.total_issues == 2
    assert stats.errors == 1
    assert stats.warnings == 1
    assert stats.infos == 0
    assert stats.files_with_issues == 1


def test_info_severity_counted_separately():
    stats = summarize([_result(issues=[_issue(severity=IssueSeverity.INFO)])])
    assert stats.infos == 1
    assert stats.errors == 0
    assert stats.warnings == 0


def test_by_code_aggregated():
    issues = [
        _issue(code=IssueCode.UNPINNED),
        _issue(code=IssueCode.UNPINNED),
        _issue(code=IssueCode.DUPLICATE),
    ]
    stats = summarize([_result(issues=issues)])
    code_unpinned = IssueCode.UNPINNED.value
    code_dup = IssueCode.DUPLICATE.value
    assert stats.by_code[code_unpinned] == 2
    assert stats.by_code[code_dup] == 1


def test_by_package_aggregated_across_results():
    r1 = _result("a.txt", [_issue(package="flask"), _issue(package="flask")])
    r2 = _result("b.txt", [_issue(package="flask"), _issue(package="django")])
    stats = summarize([r1, r2])
    assert stats.by_package["flask"] == 3
    assert stats.by_package["django"] == 1


def test_format_summary_clean():
    stats = SummaryStats(total_files=3, files_with_issues=0, total_issues=0)
    text = format_summary(stats)
    assert "No issues found" in text
    assert "3 file" in text


def test_format_summary_with_issues():
    issues = [_issue(severity=IssueSeverity.ERROR), _issue(severity=IssueSeverity.WARNING)]
    stats = summarize([_result(issues=issues)])
    text = format_summary(stats)
    assert "1 error" in text
    assert "1 warning" in text


def test_format_summary_shows_top_codes():
    issues = [_issue(code=IssueCode.UNPINNED)] * 3 + [_issue(code=IssueCode.DUPLICATE)]
    stats = summarize([_result(issues=issues)])
    text = format_summary(stats)
    assert "Top codes" in text
