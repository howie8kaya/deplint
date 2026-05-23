"""Tests for deplint.watchdog."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
from unittest.mock import MagicMock, patch

import pytest

from deplint.linter import LintResult
from deplint.watchdog import Watchdog, WatchState, _file_hash, _changed


@pytest.fixture()
def req_file(tmp_path: Path) -> Path:
    p = tmp_path / "requirements.txt"
    p.write_text("requests==2.31.0\n")
    return p


def _dummy_lint(path: Path) -> LintResult:
    return LintResult(path=path, issues=[], stats={})


def test_file_hash_returns_string(req_file: Path) -> None:
    h = _file_hash(req_file)
    assert isinstance(h, str) and len(h) == 32


def test_file_hash_missing_file_returns_none(tmp_path: Path) -> None:
    assert _file_hash(tmp_path / "nope.txt") is None


def test_file_hash_changes_when_content_changes(req_file: Path) -> None:
    h1 = _file_hash(req_file)
    req_file.write_text("flask==3.0.0\n")
    h2 = _file_hash(req_file)
    assert h1 != h2


def test_changed_detects_modification(req_file: Path) -> None:
    state = WatchState(path=req_file, last_hash=_file_hash(req_file))
    assert not _changed(state)  # nothing changed yet
    req_file.write_text("flask==3.0.0\n")
    assert _changed(state)  # now it changed


def test_changed_missing_file_returns_false(tmp_path: Path) -> None:
    state = WatchState(path=tmp_path / "ghost.txt", last_hash="abc")
    assert not _changed(state)


def test_watchdog_calls_on_change_when_file_modified(req_file: Path) -> None:
    calls: List[Tuple[Path, LintResult]] = []

    def handler(p: Path, r: LintResult) -> None:
        calls.append((p, r))

    with patch("deplint.watchdog.lint_file", side_effect=_dummy_lint):
        wd = Watchdog(paths=[req_file], on_change=handler)
        req_file.write_text("flask==3.0.0\n")
        changed = wd.poll_once()

    assert req_file in changed
    assert len(calls) == 1
    assert calls[0][0] == req_file


def test_watchdog_no_callback_when_unchanged(req_file: Path) -> None:
    calls: List[Path] = []

    with patch("deplint.watchdog.lint_file", side_effect=_dummy_lint):
        wd = Watchdog(paths=[req_file], on_change=lambda p, r: calls.append(p))
        wd.poll_once()  # no changes

    assert calls == []


def test_watchdog_run_respects_max_iterations(req_file: Path) -> None:
    poll_mock = MagicMock(return_value=[])
    with patch("deplint.watchdog.lint_file", side_effect=_dummy_lint):
        wd = Watchdog(paths=[req_file], on_change=lambda p, r: None, interval=0)
        wd.poll_once = poll_mock  # type: ignore[method-assign]
        wd.run(max_iterations=3)

    assert poll_mock.call_count == 3
