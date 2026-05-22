"""Output formatters for deplint analysis results."""

from typing import List
from deplint.models import AnalysisResult, Issue, IssueSeverity


class TextFormatter:
    """Plain text formatter for terminal output."""

    SEVERITY_PREFIX = {
        IssueSeverity.ERROR: "[ERROR]",
        IssueSeverity.WARNING: "[WARN] ",
        IssueSeverity.INFO: "[INFO] ",
    }

    def format(self, result: AnalysisResult) -> str:
        lines = []

        if not result.issues:
            lines.append("✓ No issues found.")
            return "\n".join(lines)

        for issue in result.issues:
            prefix = self.SEVERITY_PREFIX.get(issue.severity, "[?]   ")
            location = f"line {issue.line}" if issue.line is not None else "global"
            lines.append(f"{prefix} ({location}) [{issue.code.value}] {issue.message}")

        summary = self._summary(result.issues)
        lines.append("")
        lines.append(summary)
        return "\n".join(lines)

    def _summary(self, issues: List[Issue]) -> str:
        errors = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
        infos = sum(1 for i in issues if i.severity == IssueSeverity.INFO)
        parts = []
        if errors:
            parts.append(f"{errors} error(s)")
        if warnings:
            parts.append(f"{warnings} warning(s)")
        if infos:
            parts.append(f"{infos} info(s)")
        return "Found: " + ", ".join(parts)


class JsonFormatter:
    """JSON formatter for machine-readable output."""

    def format(self, result: AnalysisResult) -> str:
        import json

        data = {
            "source": result.source,
            "issue_count": len(result.issues),
            "issues": [
                {
                    "line": issue.line,
                    "severity": issue.severity.value,
                    "code": issue.code.value,
                    "message": issue.message,
                    "package": issue.package,
                }
                for issue in result.issues
            ],
        }
        return json.dumps(data, indent=2)


def get_formatter(fmt: str):
    """Return a formatter instance by name."""
    formatters = {
        "text": TextFormatter,
        "json": JsonFormatter,
    }
    cls = formatters.get(fmt)
    if cls is None:
        raise ValueError(f"Unknown formatter: {fmt!r}. Choose from: {list(formatters)}")
    return cls()
