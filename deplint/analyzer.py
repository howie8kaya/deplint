"""Main analyzer that wires together parsing and checks."""

from .checks import ALL_CHECKS
from .models import AnalysisResult
from .parser import parse_requirements, parse_requirements_file


class Analyzer:
    """Run all registered checks against a requirements file or content string."""

    def __init__(self, checks=None):
        self.checks = checks if checks is not None else ALL_CHECKS

    def analyze_content(self, content: str, filepath: str = "<stdin>") -> AnalysisResult:
        """Analyze requirements from a string."""
        requirements = parse_requirements(content)
        return self._run_checks(requirements, filepath)

    def analyze_file(self, filepath: str) -> AnalysisResult:
        """Analyze a requirements file on disk."""
        requirements = parse_requirements_file(filepath)
        return self._run_checks(requirements, filepath)

    def _run_checks(self, requirements, filepath: str) -> AnalysisResult:
        result = AnalysisResult(filepath=filepath)
        for check in self.checks:
            result.issues.extend(check(requirements))
        # Sort issues by line number for readable output
        result.issues.sort(key=lambda i: i.line_number)
        return result
