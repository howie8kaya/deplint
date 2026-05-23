"""Linter: combines analysis, filtering, and scoring into a single pipeline result."""

from dataclasses import dataclass, field
from typing import List, Optional

from deplint.analyzer import Analyzer
from deplint.filter import filter_results
from deplint.scorer import score_results, HealthScore, format_score
from deplint.summarizer import summarize, SummaryStats
from deplint.models import AnalysisResult
from deplint.config import DeplintConfig


@dataclass
class LintResult:
    """Aggregated output from a full lint run."""

    results: List[AnalysisResult] = field(default_factory=list)
    stats: Optional[SummaryStats] = None
    score: Optional[HealthScore] = None

    @property
    def has_errors(self) -> bool:
        return any(
            any(i.severity.name == "ERROR" for i in r.issues)
            for r in self.results
        )

    @property
    def has_warnings(self) -> bool:
        return any(
            any(i.severity.name == "WARNING" for i in r.issues)
            for r in self.results
        )

    @property
    def total_issues(self) -> int:
        return sum(len(r.issues) for r in self.results)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"LintResult(files={len(self.results)}, "
            f"issues={self.total_issues}, "
            f"score={self.score})"
        )


class Linter:
    """High-level entry point that runs analysis and post-processing."""

    def __init__(self, config: Optional[DeplintConfig] = None) -> None:
        self.config = config or DeplintConfig()
        self._analyzer = Analyzer()

    def lint_content(self, content: str, filename: str = "<string>") -> LintResult:
        """Lint raw requirements text."""
        raw = self._analyzer.analyze_content(content, filename=filename)
        return self._build(raw)

    def lint_file(self, path: str) -> LintResult:
        """Lint a requirements file on disk."""
        raw = self._analyzer.analyze_file(path)
        return self._build(raw)

    def lint_many(self, paths: List[str]) -> LintResult:
        """Lint multiple requirements files."""
        results = [self._analyzer.analyze_file(p) for p in paths]
        return self._build(*results)

    def _build(self, *raw_results: AnalysisResult) -> LintResult:
        filtered = filter_results(
            list(raw_results),
            ignore_codes=self.config.ignore,
            exclude_packages=self.config.exclude,
        )
        stats = summarize(filtered)
        score = score_results(filtered)
        return LintResult(results=filtered, stats=stats, score=score)
