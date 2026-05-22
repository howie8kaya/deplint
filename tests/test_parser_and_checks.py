"""Tests for the requirements parser and built-in checks."""

import pytest

from deplint.analyzer import Analyzer
from deplint.checks import check_conflicts, check_duplicates, check_unpinned
from deplint.models import IssueCode
from deplint.parser import parse_requirements


SAMPLE = """\
# production deps
requests==2.31.0
flask>=2.0
numpy
boto3==1.26.0
"""


def test_parse_basic():
    reqs = parse_requirements(SAMPLE)
    assert len(reqs) == 4
    names = [r.name for r in reqs]
    assert "requests" in names
    assert "numpy" in names


def test_pinned_detection():
    reqs = parse_requirements(SAMPLE)
    by_name = {r.name: r for r in reqs}
    assert by_name["requests"].is_pinned() is True
    assert by_name["flask"].is_pinned() is False
    assert by_name["numpy"].is_pinned() is False


def test_parse_extras():
    reqs = parse_requirements("uvicorn[standard]==0.23.0")
    assert reqs[0].extras == ["standard"]
    assert reqs[0].is_pinned() is True


def test_check_unpinned():
    reqs = parse_requirements(SAMPLE)
    issues = check_unpinned(reqs)
    codes = [i.code for i in issues]
    assert IssueCode.UNPINNED_DEPENDENCY in codes
    unpinned_names = {i.package for i in issues}
    assert "flask" in unpinned_names
    assert "numpy" in unpinned_names
    assert "requests" not in unpinned_names


def test_check_duplicates():
    content = "requests==2.31.0\nrequests==2.28.0\n"
    reqs = parse_requirements(content)
    issues = check_duplicates(reqs)
    assert len(issues) == 1
    assert issues[0].code == IssueCode.DUPLICATE_DEPENDENCY


def test_check_conflicts():
    content = "django==3.2\ndjango==4.2\n"
    reqs = parse_requirements(content)
    issues = check_conflicts(reqs)
    assert any(i.code == IssueCode.CONFLICTING_VERSIONS for i in issues)


def test_no_false_positive_conflicts():
    content = "flask==2.3.0\nrequests==2.31.0\n"
    reqs = parse_requirements(content)
    assert check_conflicts(reqs) == []


def test_analyzer_end_to_end():
    analyzer = Analyzer()
    result = analyzer.analyze_content(SAMPLE, filepath="requirements.txt")
    assert result.filepath == "requirements.txt"
    assert result.has_issues
    assert len(result.warnings) > 0


def test_analyzer_clean_file():
    content = "requests==2.31.0\nflask==2.3.3\n"
    analyzer = Analyzer()
    result = analyzer.analyze_content(content)
    assert not result.has_issues
