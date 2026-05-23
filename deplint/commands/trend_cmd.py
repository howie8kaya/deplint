"""CLI subcommand: trend — record and display issue trends."""

from __future__ import annotations

import argparse
from pathlib import Path

from deplint.multi import analyze_many
from deplint.trender import format_trend, load_trend, record_trend

_DEFAULT_TREND_FILE = ".deplint_trend.json"


def add_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "trend",
        help="Record and display issue count trends over time.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="requirements file(s) to analyse (omit to just show history)",
    )
    p.add_argument(
        "--trend-file",
        default=_DEFAULT_TREND_FILE,
        metavar="PATH",
        help=f"path to trend history file (default: {_DEFAULT_TREND_FILE})",
    )
    p.add_argument(
        "--show",
        action="store_true",
        help="print the trend table and exit without recording a new entry",
    )
    p.set_defaults(func=run_trend)


def run_trend(args: argparse.Namespace) -> int:
    trend_path = Path(args.trend_file)

    if args.show or not args.files:
        report = load_trend(trend_path)
        print(format_trend(report))
        return 0

    results = analyze_many(args.files)
    entry = record_trend(results, trend_path)

    print(
        f"Recorded: {entry.total_issues} total issue(s) "
        f"({entry.error_count} errors, {entry.warning_count} warnings, "
        f"{entry.info_count} info) across {entry.file_count} file(s)."
    )

    report = load_trend(trend_path)
    if report.delta is not None:
        direction = "▼ improved" if report.is_improving else "▲ worsened"
        print(f"Trend vs previous run: {direction} by {abs(report.delta)} issue(s)")

    return 0
