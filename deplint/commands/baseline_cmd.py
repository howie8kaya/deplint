"""CLI sub-command: manage the deplint baseline file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from deplint.analyzer import Analyzer
from deplint.baseline import filter_baseline, load_baseline, save_baseline
from deplint.multi import _collect_req_files

_DEFAULT_BASELINE = ".deplint-baseline.json"


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "baseline",
        help="Create or update the baseline snapshot of known issues.",
    )
    p.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Requirement files or directories to scan (default: current dir).",
    )
    p.add_argument(
        "--baseline-file",
        default=_DEFAULT_BASELINE,
        metavar="FILE",
        help=f"Path to the baseline JSON file (default: {_DEFAULT_BASELINE}).",
    )
    p.add_argument(
        "--diff",
        action="store_true",
        help="Show issues not yet in the baseline instead of saving.",
    )
    p.set_defaults(func=run_baseline)


def run_baseline(args: argparse.Namespace) -> int:
    """Entry-point called by the CLI dispatcher."""
    req_files: list[Path] = []
    for raw in args.paths:
        p = Path(raw)
        if p.is_file():
            req_files.append(p)
        else:
            req_files.extend(_collect_req_files(p))

    if not req_files:
        print("deplint baseline: no requirement files found.", file=sys.stderr)
        return 1

    analyzer = Analyzer()
    all_issues = []
    for rf in req_files:
        result = analyzer.analyze_file(str(rf))
        all_issues.extend(result.issues)

    if args.diff:
        baseline = load_baseline(args.baseline_file)
        new_issues = filter_baseline(all_issues, baseline)
        if new_issues:
            print(f"{len(new_issues)} new issue(s) not in baseline:")
            for issue in new_issues:
                print(f"  [{issue.severity.value}] {issue.code.value}: {issue.message}")
            return 1
        print("No new issues beyond baseline.")
        return 0

    save_baseline(all_issues, path=args.baseline_file)
    print(
        f"Baseline saved to {args.baseline_file} "
        f"({len(all_issues)} issue(s) recorded)."
    )
    return 0
