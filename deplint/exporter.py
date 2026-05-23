"""Export analysis results to various file formats (CSV, Markdown)."""
from __future__ import annotations

import csv
import io
from typing import List

from deplint.models import AnalysisResult, Issue


def _all_issues(results: List[AnalysisResult]) -> List[tuple[str, Issue]]:
    """Flatten results into (filename, issue) pairs."""
    pairs = []
    for result in results:
        fname = result.filename or ""
        for issue in result.issues:
            pairs.append((fname, issue))
    return pairs


def export_csv(results: List[AnalysisResult]) -> str:
    """Return a CSV string of all issues across the given results."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["file", "severity", "code", "package", "message"])
    for fname, issue in _all_issues(results):
        writer.writerow([
            fname,
            issue.severity.value,
            issue.code.value,
            issue.package or "",
            issue.message,
        ])
    return output.getvalue()


def export_markdown(results: List[AnalysisResult]) -> str:
    """Return a Markdown table string of all issues across the given results."""
    lines: List[str] = []
    lines.append("| File | Severity | Code | Package | Message |")
    lines.append("|------|----------|------|---------|---------|")
    pairs = _all_issues(results)
    if not pairs:
        lines.append("| — | — | — | — | No issues found |")
    else:
        for fname, issue in pairs:
            lines.append(
                f"| {fname} "
                f"| {issue.severity.value} "
                f"| {issue.code.value} "
                f"| {issue.package or ''} "
                f"| {issue.message} |"
            )
    return "\n".join(lines) + "\n"


def export_results(results: List[AnalysisResult], fmt: str) -> str:
    """Dispatch to the appropriate exporter by format name.

    Supported formats: ``csv``, ``markdown`` / ``md``.
    Raises ``ValueError`` for unknown formats.
    """
    fmt = fmt.lower().strip()
    if fmt == "csv":
        return export_csv(results)
    if fmt in ("markdown", "md"):
        return export_markdown(results)
    raise ValueError(f"Unknown export format: {fmt!r}")
