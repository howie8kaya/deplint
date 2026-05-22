"""Command-line interface for deplint."""

import sys
import argparse
from pathlib import Path

from deplint.analyzer import Analyzer
from deplint.formatter import TextFormatter, JsonFormatter
from deplint.outdated import check_outdated


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deplint",
        description="Static analysis tool for Python dependency files.",
    )
    parser.add_argument(
        "file",
        nargs="+",
        help="Path(s) to requirements file(s) to analyze.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--check-outdated",
        action="store_true",
        default=False,
        help="Query PyPI to check for outdated pinned packages.",
    )
    parser.add_argument(
        "--fail-on",
        choices=["error", "warning", "info"],
        default="error",
        help="Exit with non-zero code if issues at this level or above are found.",
    )
    return parser


def severity_rank(level: str) -> int:
    return {"info": 0, "warning": 1, "error": 2}.get(level, 2)


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    formatter = JsonFormatter() if args.format == "json" else TextFormatter()
    analyzer = Analyzer()

    exit_code = 0
    fail_rank = severity_rank(args.fail_on)

    for file_path in args.file:
        path = Path(file_path)
        if not path.exists():
            print(f"deplint: error: file not found: {file_path}", file=sys.stderr)
            exit_code = 2
            continue

        result = analyzer.analyze_file(str(path))

        if args.check_outdated:
            outdated_issues = check_outdated(result.requirements)
            result.issues.extend(outdated_issues)

        print(formatter.format(result))

        for issue in result.issues:
            if severity_rank(issue.severity.value) >= fail_rank:
                exit_code = max(exit_code, 1)

    return exit_code


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
