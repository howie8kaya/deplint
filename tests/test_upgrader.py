"""Tests for deplint.upgrader."""
from __future__ import annotations

from typing import Dict, Optional

import pytest

from deplint.parser import Requirement
from deplint.upgrader import UpgradeProposal, UpgradeReport, propose_upgrades


def _req(name: str, version: Optional[str] = None) -> Requirement:
    specifier = f"=={version}" if version else ""
    return Requirement(name=name, specifier=specifier, version=version, extras=[])


def _fake_fetch(versions: Dict[str, Optional[str]]):
    """Return a fetch callable backed by a dict."""
    def fetch(package: str) -> Optional[str]:
        key = package.lower()
        if key not in versions:
            raise ValueError(f"unknown package: {package}")
        return versions[key]
    return fetch


def test_already_up_to_date_goes_to_skipped():
    reqs = [_req("requests", "2.31.0")]
    fetch = _fake_fetch({"requests": "2.31.0"})
    report = propose_upgrades(reqs, fetch)
    assert report.proposals == []
    assert "requests" in report.skipped
    assert report.errors == []


def test_outdated_pin_creates_proposal():
    reqs = [_req("flask", "2.2.0")]
    fetch = _fake_fetch({"flask": "3.0.1"})
    report = propose_upgrades(reqs, fetch)
    assert len(report.proposals) == 1
    p = report.proposals[0]
    assert p.package == "flask"
    assert p.current_version == "2.2.0"
    assert p.proposed_version == "3.0.1"
    assert not report.has_upgrades is False  # i.e. has_upgrades is True
    assert report.has_upgrades


def test_unpinned_always_gets_proposal():
    reqs = [_req("numpy")]  # no version pinned
    fetch = _fake_fetch({"numpy": "1.26.4"})
    report = propose_upgrades(reqs, fetch)
    assert len(report.proposals) == 1
    assert report.proposals[0].current_version is None
    assert report.proposals[0].proposed_version == "1.26.4"


def test_fetch_returns_none_goes_to_errors():
    reqs = [_req("mystery", "1.0.0")]
    fetch = _fake_fetch({"mystery": None})
    report = propose_upgrades(reqs, fetch)
    assert report.proposals == []
    assert any("mystery" in e for e in report.errors)


def test_fetch_raises_exception_goes_to_errors():
    reqs = [_req("broken", "0.1")]

    def bad_fetch(name: str):
        raise ConnectionError("timeout")

    report = propose_upgrades(reqs, bad_fetch)
    assert report.proposals == []
    assert any("broken" in e for e in report.errors)


def test_duplicate_packages_deduplicated():
    reqs = [
        _req("django", "4.2.0"),
        _req("Django", "4.2.0"),  # same package, different casing
    ]
    fetch = _fake_fetch({"django": "5.0.3"})
    report = propose_upgrades(reqs, fetch)
    # Only one proposal, not two
    assert len(report.proposals) == 1


def test_mixed_results():
    reqs = [
        _req("click", "8.0.0"),   # outdated
        _req("rich", "13.7.1"),   # up to date
        _req("missing", "1.0"),   # fetch returns None
    ]
    fetch = _fake_fetch({"click": "8.1.7", "rich": "13.7.1", "missing": None})
    report = propose_upgrades(reqs, fetch)
    assert len(report.proposals) == 1
    assert report.proposals[0].package == "click"
    assert "rich" in report.skipped
    assert any("missing" in e for e in report.errors)
