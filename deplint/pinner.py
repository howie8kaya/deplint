"""Utilities for auto-pinning unpinned requirements to their latest versions."""

from __future__ import annotations

from typing import List, Optional

from deplint.parser import Requirement, is_pinned
from deplint.outdated import get_latest_version


class PinResult:
    """Outcome of attempting to pin a single requirement."""

    def __init__(self, name: str, original: str, pinned: Optional[str], skipped: bool = False) -> None:
        self.name = name
        self.original = original
        self.pinned = pinned
        self.skipped = skipped

    def __repr__(self) -> str:  # pragma: no cover
        return f"PinResult(name={self.name!r}, pinned={self.pinned!r}, skipped={self.skipped})"


def pin_requirements(
    requirements: List[Requirement],
    fetch_latest=None,
) -> List[PinResult]:
    """Return PinResult for each requirement, resolving unpinned ones.

    Args:
        requirements: parsed Requirement objects.
        fetch_latest: callable(name) -> version string, defaults to get_latest_version.
    """
    if fetch_latest is None:
        fetch_latest = get_latest_version

    results: List[PinResult] = []
    for req in requirements:
        if is_pinned(req):
            results.append(PinResult(req.name, req.raw, req.raw, skipped=True))
            continue

        latest = fetch_latest(req.name)
        if latest is None:
            results.append(PinResult(req.name, req.raw, None, skipped=True))
        else:
            pinned_line = f"{req.name}=={latest}"
            results.append(PinResult(req.name, req.raw, pinned_line))

    return results


def apply_pins(content: str, pin_results: List[PinResult]) -> str:
    """Rewrite a requirements file string, replacing unpinned lines with pinned versions.

    Lines that could not be resolved or were already pinned are left unchanged.
    """
    lines = content.splitlines(keepends=True)
    pin_map = {
        pr.original.strip(): pr.pinned
        for pr in pin_results
        if not pr.skipped and pr.pinned is not None
    }

    output = []
    for line in lines:
        stripped = line.strip()
        if stripped in pin_map:
            # Preserve trailing newline style
            ending = line[len(line.rstrip()):] or "\n"
            output.append(pin_map[stripped] + ending)
        else:
            output.append(line)

    return "".join(output)
