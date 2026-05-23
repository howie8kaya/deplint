"""Score a set of analysis results to produce a health metric for a project."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from deplint.models import AnalysisResult, IssueSeverity

# Weight applied to each severity level when computing the raw penalty.
_SEVERITY_WEIGHT: dict[IssueSeverity, int] = {
    IssueSeverity.ERROR: 10,
    IssueSeverity.WARNING: 3,
    IssueSeverity.INFO: 1,
}

_MAX_SCORE = 100


@dataclass
class HealthScore:
    score: int          # 0-100
    penalty: int        # raw penalty points deducted
    total_issues: int
    errors: int
    warnings: int
    infos: int
    grade: str          # A-F

    def __repr__(self) -> str:  # pragma: no cover
        return f"HealthScore(score={self.score}, grade={self.grade!r})"


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_results(results: List[AnalysisResult]) -> HealthScore:
    """Return a HealthScore computed from *results*.

    The penalty grows with the number and severity of issues.  The final
    score is clamped to [0, 100].
    """
    errors = warnings = infos = 0

    for result in results:
        for issue in result.issues:
            if issue.severity == IssueSeverity.ERROR:
                errors += 1
            elif issue.severity == IssueSeverity.WARNING:
                warnings += 1
            else:
                infos += 1

    penalty = (
        errors * _SEVERITY_WEIGHT[IssueSeverity.ERROR]
        + warnings * _SEVERITY_WEIGHT[IssueSeverity.WARNING]
        + infos * _SEVERITY_WEIGHT[IssueSeverity.INFO]
    )

    score = max(0, _MAX_SCORE - penalty)
    total = errors + warnings + infos

    return HealthScore(
        score=score,
        penalty=penalty,
        total_issues=total,
        errors=errors,
        warnings=warnings,
        infos=infos,
        grade=_grade(score),
    )


def format_score(hs: HealthScore) -> str:
    """Return a human-readable one-liner for *hs*."""
    return (
        f"Health score: {hs.score}/100 (grade {hs.grade}) — "
        f"{hs.errors} error(s), {hs.warnings} warning(s), {hs.infos} info(s)"
    )
