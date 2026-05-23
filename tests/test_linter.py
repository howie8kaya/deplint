"""Tests for deplint.linter — Linter pipeline."""

import pytest

from deplint.linter import Linter, LintResult
from deplint.config import DeplintConfig


CLEAN_REQS = "requests==2.31.0\nflask==3.0.0\n"
UNPINNED_REQS = "requests\nflask>=2.0\n"
DUPLICATE_REQS = "requests==2.31.0\nrequests==2.28.0\n"


@pytest.fixture
def linter():
    return Linter()


def test_lint_content_clean_has_no_issues(linter):
    result = linter.lint_content(CLEAN_REQS)
    assert isinstance(result, LintResult)
    assert result.total_issues == 0


def test_lint_content_unpinned_produces_issues(linter):
    result = linter.lint_content(UNPINNED_REQS)
    assert result.total_issues > 0


def test_lint_content_duplicate_produces_issues(linter):
    result = linter.lint_content(DUPLICATE_REQS)
    assert result.total_issues > 0


def test_lint_result_has_stats(linter):
    result = linter.lint_content(CLEAN_REQS)
    assert result.stats is not None
    assert result.stats.total_files == 1


def test_lint_result_has_score(linter):
    result = linter.lint_content(CLEAN_REQS)
    assert result.score is not None
    assert result.score.value == 100


def test_has_errors_false_for_clean(linter):
    result = linter.lint_content(CLEAN_REQS)
    assert result.has_errors is False


def test_has_warnings_false_for_clean(linter):
    result = linter.lint_content(CLEAN_REQS)
    assert result.has_warnings is False


def test_ignore_config_filters_codes():
    config = DeplintConfig(ignore=["DEP001"])
    linter = Linter(config=config)
    result = linter.lint_content(UNPINNED_REQS)
    codes = {i.code.value for r in result.results for i in r.issues}
    assert "DEP001" not in codes


def test_lint_file_reads_from_disk(tmp_path, linter):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text(CLEAN_REQS)
    result = linter.lint_file(str(req_file))
    assert result.total_issues == 0


def test_lint_many_aggregates_files(tmp_path, linter):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text(CLEAN_REQS)
    f2.write_text(UNPINNED_REQS)
    result = linter.lint_many([str(f1), str(f2)])
    assert len(result.results) == 2
    assert result.total_issues > 0


def test_lint_many_stats_counts_all_files(tmp_path, linter):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text(CLEAN_REQS)
    f2.write_text(CLEAN_REQS)
    result = linter.lint_many([str(f1), str(f2)])
    assert result.stats.total_files == 2
    assert result.stats.clean_files == 2
