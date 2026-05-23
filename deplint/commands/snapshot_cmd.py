"""CLI sub-commands for snapshot management: take, diff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from deplint.snapshotter import (
    diff_snapshots,
    load_snapshot,
    save_snapshot,
    take_snapshot,
)

_CHANGE_SYMBOL = {
    "added": "+",
    "removed": "-",
    "upgraded": "^",
    "downgraded": "v",
    "unpinned": "~",
    "repinned": "=",
    "changed": "?",
}


def add_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "snapshot",
        help="Take or compare snapshots of a requirements file",
    )
    sub = p.add_subparsers(dest="snapshot_action", required=True)

    take_p = sub.add_parser("take", help="Capture current state of a requirements file")
    take_p.add_argument("req_file", help="Path to requirements file")
    take_p.add_argument(
        "-o", "--output", default=".deplint_snapshot.json",
        help="Where to write the snapshot (default: .deplint_snapshot.json)",
    )

    diff_p = sub.add_parser("diff", help="Diff two snapshots or a snapshot vs a live file")
    diff_p.add_argument("old_snapshot", help="Path to the old snapshot JSON file")
    diff_p.add_argument(
        "new",
        help="Path to a new snapshot JSON file OR a requirements file to snapshot on-the-fly",
    )

    p.set_defaults(func=run_snapshot)


def run_snapshot(args: argparse.Namespace) -> int:
    if args.snapshot_action == "take":
        return _cmd_take(args)
    if args.snapshot_action == "diff":
        return _cmd_diff(args)
    return 1


def _cmd_take(args: argparse.Namespace) -> int:
    try:
        snap = take_snapshot(args.req_file)
        save_snapshot(snap, args.output)
        print(f"Snapshot saved to {args.output} ({len(snap.packages)} packages)")
        return 0
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _cmd_diff(args: argparse.Namespace) -> int:
    try:
        old_snap = load_snapshot(args.old_snapshot)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"error loading old snapshot: {exc}", file=sys.stderr)
        return 1

    new_path = Path(args.new)
    try:
        if new_path.suffix in (".txt", ".in", ""):
            new_snap = take_snapshot(args.new)
        else:
            new_snap = load_snapshot(args.new)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"error loading new snapshot/file: {exc}", file=sys.stderr)
        return 1

    changes = diff_snapshots(old_snap, new_snap)
    if not changes:
        print("No changes detected.")
        return 0

    print(f"{len(changes)} package(s) changed:\n")
    for name, info in changes.items():
        sym = _CHANGE_SYMBOL.get(info["change"], "?")
        old_v = info["old"] or "(none)"
        new_v = info["new"] or "(none)"
        print(f"  [{sym}] {name}: {old_v} -> {new_v}  ({info['change']})")

    return 0
