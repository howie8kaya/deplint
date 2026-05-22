"""Data models for deplint issues and analysis results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCode(str, Enum):
    UNPINNED = "UNPINNED"
    DUPLICATE = "DUPLICATE"
    CONFLICT = "CONFLICT"
    OUTDATED_PIN = "OUTDATED_PIN"


@dataclass
class Issue:
    code: IssueCode
    severity: IssueSeverity
    package: str
    message: str
    line: Optional[int] = None

    def __str__(self) -> str:
        location = f"line {self.line}: " if self.line is not None else ""
        return f"[{self.severity.value.upper()}] {location}{self.code.value}: {self.message}"


@dataclass
class AnalysisResult:
    issues: list[Issue] = field(default_factory=list)
    package_count: int = 0
    source: str = ""

    @property
    def has_errors(self) -> bool:
        return any(i.severity == IssueSeverity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == IssueSeverity.WARNING for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.INFO)
