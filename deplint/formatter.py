"""Output formatters for deplint analysis results."""
from __future__ import annotations

import json
from typing import List

from deplint.models import AnalysisResult, Issue
from deplint.grouper import group_by_package, summary_by_code


class TextFormatter:
    """Human-readable text output."""

    def format(self, results: List[AnalysisResult]) -> str:
        lines: List[str] = []
        for result in results:
            if not result.issues:
                continue
            lines.append(f"==> {result.path}")
            for issue in result.issues:
                sev = issue.severity.value.upper()
                code = issue.code.value if hasattr(issue.code, "value") else str(issue.code)
                pkg = issue.package_name or ""
                lines.append(f"  [{sev}] {code}: {pkg} — {issue.message}")
        lines.append("")
        lines.append(self._summary(results))
        return "\n".join(lines)

    def _summary(self, results: List[AnalysisResult]) -> str:
        total = sum(len(r.issues) for r in results)
        files = len(results)
        return f"{total} issue(s) found across {files} file(s)."


class JsonFormatter:
    """Machine-readable JSON output."""

    def format(self, results: List[AnalysisResult]) -> str:
        payload = {
            "files": [
                {
                    "path": r.path,
                    "issues": [
                        {
                            "code": issue.code.value if hasattr(issue.code, "value") else str(issue.code),
                            "severity": issue.severity.value,
                            "package": issue.package_name,
                            "message": issue.message,
                        }
                        for issue in r.issues
                    ],
                }
                for r in results
            ],
            "summary": {
                "total_issues": sum(len(r.issues) for r in results),
                "by_code": summary_by_code(results),
                "by_package": {
                    pkg: len(issues)
                    for pkg, issues in group_by_package(results).items()
                },
            },
        }
        return json.dumps(payload, indent=2)


class GroupedTextFormatter:
    """Text output grouped by package name."""

    def format(self, results: List[AnalysisResult]) -> str:
        lines: List[str] = []
        grouped = group_by_package(results)
        for pkg, issues in sorted(grouped.items()):
            lines.append(f"Package: {pkg}")
            for issue in issues:
                sev = issue.severity.value.upper()
                code = issue.code.value if hasattr(issue.code, "value") else str(issue.code)
                lines.append(f"  [{sev}] {code}: {issue.message}")
        lines.append("")
        total = sum(len(v) for v in grouped.values())
        lines.append(f"{total} issue(s) across {len(grouped)} package(s).")
        return "\n".join(lines)
