"""Summarize analysis results into human-readable statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from deplint.models import AnalysisResult, IssueSeverity


@dataclass
class SummaryStats:
    total_files: int = 0
    files_with_issues: int = 0
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0
    by_code: Dict[str, int] = field(default_factory=dict)
    by_package: Dict[str, int] = field(default_factory=dict)

    @property
    def clean_files(self) -> int:
        return self.total_files - self.files_with_issues

    @property
    def is_clean(self) -> bool:
        return self.total_issues == 0


def summarize(results: List[AnalysisResult]) -> SummaryStats:
    """Compute summary statistics across all analysis results."""
    stats = SummaryStats(total_files=len(results))

    for result in results:
        if result.issues:
            stats.files_with_issues += 1

        for issue in result.issues:
            stats.total_issues += 1

            if issue.severity == IssueSeverity.ERROR:
                stats.errors += 1
            elif issue.severity == IssueSeverity.WARNING:
                stats.warnings += 1
            else:
                stats.infos += 1

            code = issue.code.value if hasattr(issue.code, "value") else str(issue.code)
            stats.by_code[code] = stats.by_code.get(code, 0) + 1

            if issue.package:
                stats.by_package[issue.package] = (
                    stats.by_package.get(issue.package, 0) + 1
                )

    return stats


def format_summary(stats: SummaryStats) -> str:
    """Return a compact text summary suitable for CLI output."""
    lines: List[str] = []
    lines.append(
        f"Scanned {stats.total_files} file(s): "
        f"{stats.clean_files} clean, {stats.files_with_issues} with issues."
    )
    if stats.is_clean:
        lines.append("No issues found.")
        return "\n".join(lines)

    parts = []
    if stats.errors:
        parts.append(f"{stats.errors} error(s)")
    if stats.warnings:
        parts.append(f"{stats.warnings} warning(s)")
    if stats.infos:
        parts.append(f"{stats.infos} info(s)")
    lines.append("Issues: " + ", ".join(parts) + ".")

    if stats.by_code:
        top = sorted(stats.by_code.items(), key=lambda x: -x[1])[:5]
        lines.append("Top codes: " + ", ".join(f"{c}({n})" for c, n in top))

    return "\n".join(lines)
