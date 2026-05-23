"""CLI sub-command: ``deplint score`` — print a project health score."""
from __future__ import annotations

import argparse
import sys
from typing import List

from deplint.analyzer import Analyzer
from deplint.multi import _collect_req_files
from deplint.scorer import format_score, score_results


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "score",
        help="Compute a 0-100 health score for dependency files.",
    )
    p.add_argument(
        "paths",
        nargs="*",
        default=["."],
        metavar="PATH",
        help="Files or directories to scan (default: current directory).",
    )
    p.add_argument(
        "--fail-under",
        type=int,
        default=0,
        metavar="N",
        dest="fail_under",
        help="Exit with code 1 if the score is below N.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Emit result as JSON.",
    )
    p.set_defaults(func=run_score)


def run_score(args: argparse.Namespace) -> int:
    """Entry point for the *score* sub-command.

    Returns the process exit code.
    """
    req_files: List[str] = []
    for path in args.paths:
        req_files.extend(_collect_req_files(path))

    if not req_files:
        print("deplint score: no requirement files found.", file=sys.stderr)
        return 1

    analyzer = Analyzer()
    results = [analyzer.analyze_file(f) for f in req_files]

    hs = score_results(results)

    if getattr(args, "json", False):
        import json

        payload = {
            "score": hs.score,
            "grade": hs.grade,
            "penalty": hs.penalty,
            "total_issues": hs.total_issues,
            "errors": hs.errors,
            "warnings": hs.warnings,
            "infos": hs.infos,
        }
        print(json.dumps(payload))
    else:
        print(format_score(hs))

    if args.fail_under and hs.score < args.fail_under:
        return 1

    return 0
