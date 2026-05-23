"""CLI sub-command: deplint watch — re-lint on file changes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from deplint.formatter import TextFormatter
from deplint.linter import LintResult
from deplint.watchdog import Watchdog


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "watch",
        help="Watch requirement files and re-lint on changes.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Requirement file(s) to watch.",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 1.0).",
    )
    p.set_defaults(func=run_watch)


def _on_change(path: Path, result: LintResult) -> None:
    formatter = TextFormatter()
    # Re-use the text formatter by wrapping the LintResult lightly.
    print(f"\n[deplint] {path} changed — re-linting...", flush=True)
    if not result.issues:
        print(f"  ✓ No issues found in {path.name}", flush=True)
        return
    for issue in result.issues:
        print(f"  {issue}", flush=True)
    total = len(result.issues)
    print(f"  {total} issue(s) found.", flush=True)


def run_watch(args: argparse.Namespace) -> int:
    paths: List[Path] = []
    for raw in args.files:
        p = Path(raw)
        if not p.exists():
            print(f"deplint watch: file not found: {raw}", file=sys.stderr)
            return 1
        paths.append(p)

    print(
        f"Watching {len(paths)} file(s) — press Ctrl+C to stop.",
        flush=True,
    )
    wd = Watchdog(paths=paths, on_change=_on_change, interval=args.interval)
    try:
        wd.run()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    return 0
