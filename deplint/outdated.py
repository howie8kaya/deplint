"""Check for outdated pinned packages by querying PyPI."""

from __future__ import annotations

import urllib.request
import urllib.error
import json
from typing import Optional

from deplint.parser import Requirement
from deplint.models import Issue, IssueCode, IssueSeverity


def get_latest_version(package_name: str) -> Optional[str]:
    """Fetch the latest version of a package from PyPI.

    Returns None if the request fails or the package is not found.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except (urllib.error.URLError, KeyError, json.JSONDecodeError):
        return None


def check_outdated(
    requirements: list[Requirement],
    fetch_fn=get_latest_version,
) -> list[Issue]:
    """Check pinned requirements against the latest version on PyPI.

    Only pinned requirements (e.g. ``requests==2.28.0``) are checked.
    An INFO-level issue is raised when a newer version is available.
    """
    issues: list[Issue] = []

    for req in requirements:
        if req.version is None:
            continue
        latest = fetch_fn(req.name)
        if latest is None:
            continue
        if latest != req.version:
            issues.append(
                Issue(
                    code=IssueCode.OUTDATED_PIN,
                    severity=IssueSeverity.INFO,
                    package=req.name,
                    message=(
                        f"{req.name} is pinned to {req.version} "
                        f"but latest is {latest}"
                    ),
                    line=req.line_number,
                )
            )

    return issues
