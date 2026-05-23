"""Upgrade suggestions: given current requirements, propose newer pinned versions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from deplint.parser import Requirement


@dataclass
class UpgradeProposal:
    package: str
    current_version: Optional[str]  # None if unpinned
    proposed_version: str

    def __repr__(self) -> str:  # pragma: no cover
        current = self.current_version or "(unpinned)"
        return f"<UpgradeProposal {self.package} {current} -> {self.proposed_version}>"


@dataclass
class UpgradeReport:
    proposals: List[UpgradeProposal] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)  # packages already up-to-date
    errors: List[str] = field(default_factory=list)   # packages where fetch failed

    @property
    def has_upgrades(self) -> bool:
        return bool(self.proposals)


FetchFn = Callable[[str], Optional[str]]


def _is_newer(current: str, candidate: str) -> bool:
    """Return True if candidate version is strictly newer than current."""
    from packaging.version import Version, InvalidVersion
    try:
        return Version(candidate) > Version(current)
    except InvalidVersion:
        return False


def propose_upgrades(
    requirements: List[Requirement],
    fetch_latest: FetchFn,
) -> UpgradeReport:
    """Check each requirement against the latest available version.

    Args:
        requirements: parsed Requirement objects.
        fetch_latest: callable(package_name) -> latest version string or None.

    Returns:
        UpgradeReport with proposals, skipped, and error lists.
    """
    report = UpgradeReport()
    seen: set[str] = set()

    for req in requirements:
        name_lower = req.name.lower()
        if name_lower in seen:
            continue
        seen.add(name_lower)

        try:
            latest = fetch_latest(req.name)
        except Exception as exc:  # noqa: BLE001
            report.errors.append(f"{req.name}: {exc}")
            continue

        if latest is None:
            report.errors.append(f"{req.name}: could not fetch latest version")
            continue

        current = req.version  # may be None for unpinned
        if current is None or _is_newer(current, latest):
            report.proposals.append(
                UpgradeProposal(
                    package=req.name,
                    current_version=current,
                    proposed_version=latest,
                )
            )
        else:
            report.skipped.append(req.name)

    return report
