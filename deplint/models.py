"""Core data models for deplint analysis results."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueCode(str, Enum):
    UNPINNED_DEPENDENCY = "DEP001"
    DUPLICATE_DEPENDENCY = "DEP002"
    CONFLICTING_VERSIONS = "DEP003"
    OUTDATED_PINNED = "DEP004"


@dataclass
class Issue:
    code: IssueCode
    severity: IssueSeverity
    message: str
    package: str
    line_number: int = 0
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        loc = f"line {self.line_number}: " if self.line_number else ""
        hint = f" ({self.suggestion})" if self.suggestion else ""
        return f"[{self.severity.value.upper()}] {self.code.value} {loc}{self.message}{hint}"


@dataclass
class AnalysisResult:
    filepath: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == IssueSeverity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    def summary(self) -> str:
        return (
            f"{self.filepath}: "
            f"{len(self.errors)} error(s), "
            f"{len(self.warnings)} warning(s)"
        )
