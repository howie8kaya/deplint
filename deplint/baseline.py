"""Baseline support: snapshot current issues to suppress them in future runs."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from deplint.models import Issue

_DEFAULT_BASELINE_FILE = ".deplint-baseline.json"


def _issue_key(issue: Issue) -> str:
    """Stable string key that uniquely identifies an issue instance."""
    return f"{issue.code.value}:{issue.package}:{issue.filename or ''}"


def save_baseline(issues: List[Issue], path: str | Path = _DEFAULT_BASELINE_FILE) -> None:
    """Persist a list of issues as the new baseline."""
    path = Path(path)
    keys = sorted({_issue_key(i) for i in issues})
    path.write_text(json.dumps({"baseline": keys}, indent=2))


def load_baseline(path: str | Path = _DEFAULT_BASELINE_FILE) -> Dict[str, bool]:
    """Return a set-like dict of baseline issue keys (empty if file missing)."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return {k: True for k in data.get("baseline", [])}
    except (json.JSONDecodeError, KeyError):
        return {}


def filter_baseline(issues: List[Issue], baseline: Dict[str, bool]) -> List[Issue]:
    """Remove issues that are already captured in *baseline*."""
    if not baseline:
        return issues
    return [i for i in issues if _issue_key(i) not in baseline]
