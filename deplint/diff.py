"""Compare two requirements files and report added/removed/changed packages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from deplint.parser import Requirement, parse_requirements


@dataclass
class DiffEntry:
    package: str
    old_version: Optional[str]  # None if added
    new_version: Optional[str]  # None if removed

    @property
    def kind(self) -> str:
        if self.old_version is None:
            return "added"
        if self.new_version is None:
            return "removed"
        return "changed"

    def __repr__(self) -> str:  # pragma: no cover
        return f"DiffEntry({self.package!r}, {self.old_version!r} -> {self.new_version!r})"


def _req_map(reqs: List[Requirement]) -> Dict[str, Optional[str]]:
    """Return {name_lower: version_or_None} for a list of requirements."""
    result: Dict[str, Optional[str]] = {}
    for req in reqs:
        version: Optional[str] = None
        if req.specifier and req.specifier.startswith("=="):
            version = req.specifier[2:].strip()
        result[req.name.lower()] = version
    return result


def diff_requirements(
    old_content: str,
    new_content: str,
) -> List[DiffEntry]:
    """Diff two requirements file contents and return a list of DiffEntry objects."""
    old_reqs = parse_requirements(old_content)
    new_reqs = parse_requirements(new_content)

    old_map = _req_map(old_reqs)
    new_map = _req_map(new_reqs)

    entries: List[DiffEntry] = []

    all_keys = sorted(set(old_map) | set(new_map))
    for key in all_keys:
        in_old = key in old_map
        in_new = key in new_map
        if in_old and not in_new:
            entries.append(DiffEntry(package=key, old_version=old_map[key], new_version=None))
        elif in_new and not in_old:
            entries.append(DiffEntry(package=key, old_version=None, new_version=new_map[key]))
        elif old_map[key] != new_map[key]:
            entries.append(DiffEntry(package=key, old_version=old_map[key], new_version=new_map[key]))

    return entries
