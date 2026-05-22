"""Tests for the outdated-pin check."""

from __future__ import annotations

import pytest

from deplint.parser import Requirement
from deplint.models import IssueCode, IssueSeverity
from deplint.outdated import check_outdated


def _req(name: str, version: str | None, line: int = 1) -> Requirement:
    return Requirement(name=name, version=version, extras=[], line_number=line)


def _fake_pypi(versions: dict[str, str | None]):
    """Return a fetch function that returns from a fixed mapping."""
    def fetch(package_name: str):
        return versions.get(package_name)
    return fetch


def test_no_issues_when_up_to_date():
    reqs = [_req("requests", "2.31.0")]
    fetch = _fake_pypi({"requests": "2.31.0"})
    issues = check_outdated(reqs, fetch_fn=fetch)
    assert issues == []


def test_outdated_pin_raises_info_issue():
    reqs = [_req("requests", "2.28.0", line=3)]
    fetch = _fake_pypi({"requests": "2.31.0"})
    issues = check_outdated(reqs, fetch_fn=fetch)
    assert len(issues) == 1
    issue = issues[0]
    assert issue.code == IssueCode.OUTDATED_PIN
    assert issue.severity == IssueSeverity.INFO
    assert issue.package == "requests"
    assert "2.28.0" in issue.message
    assert "2.31.0" in issue.message
    assert issue.line == 3


def test_unpinned_requirements_are_skipped():
    reqs = [_req("flask", None)]
    fetch = _fake_pypi({"flask": "3.0.0"})
    issues = check_outdated(reqs, fetch_fn=fetch)
    assert issues == []


def test_pypi_unavailable_skips_package():
    reqs = [_req("mypackage", "1.0.0")]
    fetch = _fake_pypi({})  # returns None for everything
    issues = check_outdated(reqs, fetch_fn=fetch)
    assert issues == []


def test_multiple_packages_mixed():
    reqs = [
        _req("requests", "2.28.0", line=1),
        _req("flask", "2.3.0", line=2),
        _req("click", "8.1.0", line=3),
    ]
    fetch = _fake_pypi({
        "requests": "2.31.0",  # outdated
        "flask": "2.3.0",      # up to date
        "click": "8.1.7",      # outdated
    })
    issues = check_outdated(reqs, fetch_fn=fetch)
    assert len(issues) == 2
    packages = {i.package for i in issues}
    assert packages == {"requests", "click"}
