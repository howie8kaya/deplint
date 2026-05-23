"""Snapshot the current state of a requirements file for later comparison."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from deplint.parser import Requirement, parse_requirements


@dataclass
class Snapshot:
    created_at: str
    source_file: str
    packages: Dict[str, Optional[str]]  # name -> pinned version or None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            created_at=data["created_at"],
            source_file=data["source_file"],
            packages=data["packages"],
        )


def take_snapshot(req_file: str) -> Snapshot:
    """Parse a requirements file and capture its current package versions."""
    path = Path(req_file)
    with path.open() as fh:
        content = fh.read()

    reqs: List[Requirement] = parse_requirements(content)
    packages = {r.name: r.version for r in reqs}

    return Snapshot(
        created_at=datetime.now(timezone.utc).isoformat(),
        source_file=str(path.resolve()),
        packages=packages,
    )


def save_snapshot(snapshot: Snapshot, output_path: str) -> None:
    """Write a snapshot to a JSON file."""
    with open(output_path, "w") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(path: str) -> Snapshot:
    """Load a previously saved snapshot from a JSON file."""
    with open(path) as fh:
        data = json.load(fh)
    return Snapshot.from_dict(data)


def diff_snapshots(
    old: Snapshot, new: Snapshot
) -> Dict[str, dict]:
    """Compare two snapshots and return a mapping of changed packages.

    Returns a dict keyed by package name with values like:
        {"old": "1.0", "new": "2.0", "change": "upgraded"}
    Change values: "added", "removed", "upgraded", "downgraded", "unpinned", "repinned"
    """
    changes: Dict[str, dict] = {}
    all_names = set(old.packages) | set(new.packages)

    for name in sorted(all_names):
        old_ver = old.packages.get(name)
        new_ver = new.packages.get(name)

        if old_ver == new_ver:
            continue

        if name not in old.packages:
            changes[name] = {"old": None, "new": new_ver, "change": "added"}
        elif name not in new.packages:
            changes[name] = {"old": old_ver, "new": None, "change": "removed"}
        elif old_ver is not None and new_ver is None:
            changes[name] = {"old": old_ver, "new": None, "change": "unpinned"}
        elif old_ver is None and new_ver is not None:
            changes[name] = {"old": None, "new": new_ver, "change": "repinned"}
        else:
            from packaging.version import Version
            try:
                change = "upgraded" if Version(new_ver) > Version(old_ver) else "downgraded"
            except Exception:
                change = "changed"
            changes[name] = {"old": old_ver, "new": new_ver, "change": change}

    return changes
