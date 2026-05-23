"""Tests for deplint.trender."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deplint.models import Issue, IssueCode, IssueSeverity, AnalysisResult
from deplint.trender import (
    TrendEntry,
    TrendReport,
    _make_entry,
    format_trend,
    load_trend,
    record_trend,
)


def _issue(severity: IssueSeverity) -> Issue:
    return Issue(
        severity=severity,
        code=IssueCode.UNPINNED,
        package="pkg",
        message="msg",
        filename=None,
    )


def _result(*severities: IssueSeverity) -> AnalysisResult:
    return AnalysisResult(
        filename="req.txt",
        issues=[_issue(s) for s in severities],
    )


def test_make_entry_counts_by_severity():
    results = [
        _result(IssueSeverity.ERROR, IssueSeverity.WARNING, IssueSeverity.INFO),
        _result(IssueSeverity.ERROR),
    ]
    entry = _make_entry(results)
    assert entry.total_issues == 4
    assert entry.error_count == 2
    assert entry.warning_count == 1
    assert entry.info_count == 1
    assert entry.file_count == 2


def test_make_entry_empty_results():
    entry = _make_entry([])
    assert entry.total_issues == 0
    assert entry.file_count == 0


def test_trend_entry_round_trip():
    entry = TrendEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        total_issues=3,
        error_count=1,
        warning_count=1,
        info_count=1,
        file_count=2,
    )
    restored = TrendEntry.from_dict(entry.to_dict())
    assert restored.timestamp == entry.timestamp
    assert restored.total_issues == entry.total_issues


def test_load_trend_missing_file_returns_empty(tmp_path):
    report = load_trend(tmp_path / "nonexistent.json")
    assert report.entries == []


def test_record_trend_creates_file(tmp_path):
    path = tmp_path / "trend.json"
    results = [_result(IssueSeverity.ERROR)]
    record_trend(results, path)
    assert path.exists()
    data = json.loads(path.read_text())
    assert len(data) == 1
    assert data[0]["total_issues"] == 1


def test_record_trend_appends_entries(tmp_path):
    path = tmp_path / "trend.json"
    record_trend([_result(IssueSeverity.ERROR)], path)
    record_trend([_result(IssueSeverity.WARNING)], path)
    report = load_trend(path)
    assert len(report.entries) == 2


def test_trend_report_delta_and_direction(tmp_path):
    path = tmp_path / "trend.json"
    record_trend([_result(IssueSeverity.ERROR, IssueSeverity.ERROR)], path)
    record_trend([_result(IssueSeverity.ERROR)], path)
    report = load_trend(path)
    assert report.delta == -1
    assert report.is_improving is True


def test_trend_report_single_entry_has_no_delta():
    report = TrendReport(entries=[
        TrendEntry("ts", 5, 1, 2, 2, 1)
    ])
    assert report.delta is None
    assert report.is_improving is None


def test_format_trend_no_data():
    report = TrendReport()
    output = format_trend(report)
    assert "No trend data" in output


def test_format_trend_shows_entries(tmp_path):
    path = tmp_path / "trend.json"
    record_trend([_result(IssueSeverity.ERROR)], path)
    record_trend([], path)
    report = load_trend(path)
    output = format_trend(report)
    assert "improved" in output
    assert "Trend" in output
