"""Track and report issue trends across multiple analysis runs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from deplint.models import AnalysisResult


@dataclass
class TrendEntry:
    timestamp: str
    total_issues: int
    error_count: int
    warning_count: int
    info_count: int
    file_count: int

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "total_issues": self.total_issues,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "file_count": self.file_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrendEntry":
        return cls(
            timestamp=data["timestamp"],
            total_issues=data["total_issues"],
            error_count=data["error_count"],
            warning_count=data["warning_count"],
            info_count=data["info_count"],
            file_count=data["file_count"],
        )


@dataclass
class TrendReport:
    entries: List[TrendEntry] = field(default_factory=list)

    @property
    def is_improving(self) -> Optional[bool]:
        if len(self.entries) < 2:
            return None
        return self.entries[-1].total_issues < self.entries[-2].total_issues

    @property
    def delta(self) -> Optional[int]:
        if len(self.entries) < 2:
            return None
        return self.entries[-1].total_issues - self.entries[-2].total_issues


def _make_entry(results: List[AnalysisResult]) -> TrendEntry:
    from deplint.models import IssueSeverity

    all_issues = [issue for r in results for issue in r.issues]
    return TrendEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_issues=len(all_issues),
        error_count=sum(1 for i in all_issues if i.severity == IssueSeverity.ERROR),
        warning_count=sum(1 for i in all_issues if i.severity == IssueSeverity.WARNING),
        info_count=sum(1 for i in all_issues if i.severity == IssueSeverity.INFO),
        file_count=len(results),
    )


def record_trend(results: List[AnalysisResult], path: Path) -> TrendEntry:
    report = load_trend(path)
    entry = _make_entry(results)
    report.entries.append(entry)
    path.write_text(json.dumps([e.to_dict() for e in report.entries], indent=2))
    return entry


def load_trend(path: Path) -> TrendReport:
    if not path.exists():
        return TrendReport()
    data = json.loads(path.read_text())
    return TrendReport(entries=[TrendEntry.from_dict(d) for d in data])


def format_trend(report: TrendReport) -> str:
    if not report.entries:
        return "No trend data available."
    lines = [f"{'Timestamp':<35} {'Total':>6} {'Errors':>7} {'Warnings':>9} {'Info':>6}"]
    lines.append("-" * 70)
    for e in report.entries:
        lines.append(
            f"{e.timestamp:<35} {e.total_issues:>6} {e.error_count:>7} "
            f"{e.warning_count:>9} {e.info_count:>6}"
        )
    if report.delta is not None:
        direction = "improved" if report.is_improving else "worsened"
        lines.append(f"\nTrend: {direction} by {abs(report.delta)} issue(s)")
    return "\n".join(lines)
