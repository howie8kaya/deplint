"""Tests for deplint.scorer."""
from __future__ import annotations

import pytest

from deplint.models import AnalysisResult, Issue, IssueCode, IssueSeverity
from deplint.scorer import HealthScore, format_score, score_results


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _issue(severity: IssueSeverity, pkg: str = "pkg") -> Issue:
    return Issue(
        code=IssueCode.UNPINNED,
        severity=severity,
        package=pkg,
        message="test",
        filename=None,
    )


def _result(*issues: Issue, filename: str = "req.txt") -> AnalysisResult:
    return AnalysisResult(filename=filename, issues=list(issues))


# ---------------------------------------------------------------------------
# score_results
# ---------------------------------------------------------------------------

def test_no_results_gives_perfect_score():
    hs = score_results([])
    assert hs.score == 100
    assert hs.penalty == 0
    assert hs.total_issues == 0
    assert hs.grade == "A"


def test_clean_result_gives_perfect_score():
    hs = score_results([_result()])
    assert hs.score == 100
    assert hs.grade == "A"


def test_single_error_deducts_ten_points():
    hs = score_results([_result(_issue(IssueSeverity.ERROR))])
    assert hs.score == 90
    assert hs.errors == 1
    assert hs.warnings == 0
    assert hs.infos == 0
    assert hs.grade == "A"


def test_single_warning_deducts_three_points():
    hs = score_results([_result(_issue(IssueSeverity.WARNING))])
    assert hs.score == 97
    assert hs.warnings == 1


def test_single_info_deducts_one_point():
    hs = score_results([_result(_issue(IssueSeverity.INFO))])
    assert hs.score == 99
    assert hs.infos == 1


def test_score_clamped_at_zero():
    errors = [_issue(IssueSeverity.ERROR, pkg=f"pkg{i}") for i in range(20)]
    hs = score_results([_result(*errors)])
    assert hs.score == 0
    assert hs.penalty == 200


def test_multiple_files_aggregated():
    r1 = _result(_issue(IssueSeverity.ERROR), filename="a.txt")
    r2 = _result(_issue(IssueSeverity.WARNING), filename="b.txt")
    hs = score_results([r1, r2])
    assert hs.errors == 1
    assert hs.warnings == 1
    assert hs.penalty == 13
    assert hs.score == 87
    assert hs.total_issues == 2


@pytest.mark.parametrize("score,expected_grade", [
    (100, "A"),
    (90, "A"),
    (89, "B"),
    (75, "B"),
    (74, "C"),
    (60, "C"),
    (59, "D"),
    (40, "D"),
    (39, "F"),
    (0, "F"),
])
def test_grade_boundaries(score, expected_grade):
    from deplint.scorer import _grade
    assert _grade(score) == expected_grade


# ---------------------------------------------------------------------------
# format_score
# ---------------------------------------------------------------------------

def test_format_score_contains_key_fields():
    hs = score_results([_result(_issue(IssueSeverity.ERROR))])
    text = format_score(hs)
    assert "90/100" in text
    assert "grade A" in text
    assert "1 error" in text
    assert "0 warning" in text
