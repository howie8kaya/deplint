"""Group analysis results by package name or issue code."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from deplint.models import AnalysisResult, Issue


def group_by_package(results: List[AnalysisResult]) -> Dict[str, List[Issue]]:
    """Return a mapping of package name -> list of issues across all results."""
    grouped: Dict[str, List[Issue]] = defaultdict(list)
    for result in results:
        for issue in result.issues:
            pkg = issue.package_name or "<unknown>"
            grouped[pkg].append(issue)
    return dict(grouped)


def group_by_code(results: List[AnalysisResult]) -> Dict[str, List[Issue]]:
    """Return a mapping of issue code -> list of issues across all results."""
    grouped: Dict[str, List[Issue]] = defaultdict(list)
    for result in results:
        for issue in result.issues:
            code = issue.code.value if hasattr(issue.code, "value") else str(issue.code)
            grouped[code].append(issue)
    return dict(grouped)


def group_by_file(results: List[AnalysisResult]) -> Dict[str, List[Issue]]:
    """Return a mapping of file path -> list of issues."""
    return {result.path: list(result.issues) for result in results}


def summary_by_package(results: List[AnalysisResult]) -> Dict[str, int]:
    """Return a mapping of package name -> total issue count."""
    grouped = group_by_package(results)
    return {pkg: len(issues) for pkg, issues in grouped.items()}


def summary_by_code(results: List[AnalysisResult]) -> Dict[str, int]:
    """Return a mapping of issue code -> total issue count."""
    grouped = group_by_code(results)
    return {code: len(issues) for code, issues in grouped.items()}
