"""Filtering utilities that apply config-level rules to analysis results."""
from __future__ import annotations

from typing import List

from deplint.config import DeplintConfig
from deplint.models import AnalysisResult, Issue


def apply_ignore(issues: List[Issue], ignore_codes: List[str]) -> List[Issue]:
    """Return a new list with issues whose code is in *ignore_codes* removed."""
    if not ignore_codes:
        return list(issues)
    ignored = {c.upper() for c in ignore_codes}
    return [i for i in issues if i.code.value not in ignored]


def apply_exclude(result: AnalysisResult, exclude_patterns: List[str]) -> bool:
    """Return True if *result* should be excluded based on filename patterns.

    Simple substring / glob-style matching: an entry in *exclude_patterns* is
    considered a match if the pattern appears anywhere in the file path.
    """
    if not exclude_patterns:
        return False
    path = result.filename or ""
    for pattern in exclude_patterns:
        if pattern in path:
            return True
    return False


def filter_results(
    results: List[AnalysisResult], config: DeplintConfig
) -> List[AnalysisResult]:
    """Apply all config-driven filters to a list of *AnalysisResult* objects."""
    filtered: List[AnalysisResult] = []
    for result in results:
        if apply_exclude(result, config.exclude):
            continue
        kept_issues = apply_ignore(result.issues, config.ignore_codes)
        filtered.append(
            AnalysisResult(filename=result.filename, issues=kept_issues)
        )
    return filtered
