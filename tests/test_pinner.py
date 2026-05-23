"""Tests for deplint.pinner — pin_requirements and apply_pins."""

from __future__ import annotations

from deplint.parser import Requirement
from deplint.pinner import PinResult, apply_pins, pin_requirements


def _req(name: str, version: str | None = None, raw: str | None = None) -> Requirement:
    return Requirement(
        name=name,
        version=version,
        extras=[],
        raw=raw or (f"{name}=={version}" if version else name),
    )


def _fake_fetch(versions: dict):
    def fetch(name: str):
        return versions.get(name.lower())
    return fetch


# ---------------------------------------------------------------------------
# pin_requirements
# ---------------------------------------------------------------------------

def test_already_pinned_is_skipped():
    req = _req("requests", "2.31.0")
    results = pin_requirements([req], fetch_latest=_fake_fetch({"requests": "2.32.0"}))
    assert len(results) == 1
    r = results[0]
    assert r.skipped is True
    assert r.pinned == req.raw


def test_unpinned_gets_latest_version():
    req = _req("flask", raw="flask")
    results = pin_requirements([req], fetch_latest=_fake_fetch({"flask": "3.0.1"}))
    assert len(results) == 1
    r = results[0]
    assert r.skipped is False
    assert r.pinned == "flask==3.0.1"
    assert r.original == "flask"


def test_unknown_package_skipped_with_none_pinned():
    req = _req("nosuchpkg", raw="nosuchpkg")
    results = pin_requirements([req], fetch_latest=_fake_fetch({}))
    assert len(results) == 1
    r = results[0]
    assert r.skipped is True
    assert r.pinned is None


def test_mixed_list():
    reqs = [
        _req("requests", "2.31.0"),
        _req("flask", raw="flask"),
        _req("unknown", raw="unknown"),
    ]
    fetch = _fake_fetch({"flask": "3.0.1"})
    results = pin_requirements(reqs, fetch_latest=fetch)
    assert len(results) == 3
    assert results[0].skipped is True   # already pinned
    assert results[1].pinned == "flask==3.0.1"
    assert results[2].pinned is None


# ---------------------------------------------------------------------------
# apply_pins
# ---------------------------------------------------------------------------

def test_apply_pins_rewrites_unpinned_line():
    content = "flask\nrequests==2.31.0\n"
    pin_results = [
        PinResult("flask", "flask", "flask==3.0.1", skipped=False),
        PinResult("requests", "requests==2.31.0", "requests==2.31.0", skipped=True),
    ]
    result = apply_pins(content, pin_results)
    assert result == "flask==3.0.1\nrequests==2.31.0\n"


def test_apply_pins_preserves_comments_and_blanks():
    content = "# top comment\nflask\n\n# another\nclick\n"
    pin_results = [
        PinResult("flask", "flask", "flask==3.0.1", skipped=False),
        PinResult("click", "click", "click==8.1.7", skipped=False),
    ]
    result = apply_pins(content, pin_results)
    assert "# top comment\n" in result
    assert "flask==3.0.1\n" in result
    assert "\n" in result
    assert "click==8.1.7\n" in result


def test_apply_pins_no_changes_when_all_skipped():
    content = "requests==2.31.0\n"
    pin_results = [
        PinResult("requests", "requests==2.31.0", "requests==2.31.0", skipped=True),
    ]
    assert apply_pins(content, pin_results) == content
