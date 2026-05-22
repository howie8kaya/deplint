"""Utilities for running deplint analysis over multiple requirement files at once."""

from pathlib import Path
from typing import List, Optional

from deplint.analyzer import Analyzer
from deplint.config import DeplintConfig
from deplint.filter import filter_results
from deplint.models import AnalysisResult
from deplint.reporter import Report, build_report


def _collect_req_files(paths: List[str]) -> List[Path]:
    """Expand directories to *.txt / *.in files; keep explicit file paths as-is."""
    collected: List[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            collected.extend(sorted(p.glob("requirements*.txt")))
            collected.extend(sorted(p.glob("requirements*.in")))
        else:
            collected.append(p)
    return collected


def analyze_many(
    paths: List[str],
    config: Optional[DeplintConfig] = None,
    check_outdated: bool = False,
) -> Report:
    """Analyse every requirements file in *paths* and return a combined Report.

    Args:
        paths: File paths or directories to scan.
        config: Optional configuration; defaults are used when *None*.
        check_outdated: When True the outdated-pin check is also executed.

    Returns:
        A :class:`~deplint.reporter.Report` aggregating all findings.
    """
    if config is None:
        config = DeplintConfig()

    analyzer = Analyzer(check_outdated=check_outdated)
    results: List[AnalysisResult] = []

    for file_path in _collect_req_files(paths):
        result = analyzer.analyze_file(str(file_path))
        filtered = filter_results(
            result,
            ignore_codes=config.ignore,
            exclude_packages=config.exclude,
        )
        results.append(filtered)

    return build_report(results)
