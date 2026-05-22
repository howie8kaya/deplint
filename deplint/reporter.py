"""Aggregates analysis results across multiple files and produces a combined report."""

from dataclasses import dataclass, field
from typing import List, Optional

from deplint.models import AnalysisResult, IssueSeverity
from deplint.formatter import TextFormatter, JsonFormatter


@dataclass
class Report:
    """Combined report for one or more analysed requirement files."""

    results: List[AnalysisResult] = field(default_factory=list)

    def add(self, result: AnalysisResult) -> None:
        self.results.append(result)

    @property
    def total_issues(self) -> int:
        return sum(len(r.issues) for r in self.results)

    @property
    def has_errors(self) -> bool:
        return any(
            issue.severity == IssueSeverity.ERROR
            for r in self.results
            for issue in r.issues
        )

    @property
    def has_warnings(self) -> bool:
        return any(
            issue.severity == IssueSeverity.WARNING
            for r in self.results
            for issue in r.issues
        )

    def exit_code(self, fail_on_warning: bool = False) -> int:
        if self.has_errors:
            return 1
        if fail_on_warning and self.has_warnings:
            return 1
        return 0


def build_report(results: List[AnalysisResult]) -> Report:
    """Construct a Report from a list of AnalysisResult objects."""
    report = Report()
    for result in results:
        report.add(result)
    return report


def render_report(report: Report, fmt: str = "text", color: bool = True) -> str:
    """Render a Report to a string using the specified format."""
    lines: List[str] = []
    if fmt == "json":
        formatter = JsonFormatter()
        parts = [formatter.format(r) for r in report.results]
        # Wrap multiple results in a JSON array
        if len(parts) == 1:
            return parts[0]
        inner = ",\n".join(parts)
        return f"[{inner}]"
    else:
        formatter = TextFormatter(color=color)
        for result in report.results:
            lines.append(formatter.format(result))
        lines.append(f"\nTotal: {report.total_issues} issue(s) across {len(report.results)} file(s).")
        return "\n".join(lines)
