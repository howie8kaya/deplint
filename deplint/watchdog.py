"""Watch requirement files for changes and re-lint automatically."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from deplint.linter import LintResult, lint_file


@dataclass
class WatchState:
    path: Path
    last_hash: Optional[str] = None
    last_result: Optional[LintResult] = None


def _file_hash(path: Path) -> Optional[str]:
    """Return MD5 hex digest of file contents, or None if unreadable."""
    try:
        return hashlib.md5(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _changed(state: WatchState) -> bool:
    current = _file_hash(state.path)
    if current is None:
        return False
    if current != state.last_hash:
        state.last_hash = current
        return True
    return False


@dataclass
class Watchdog:
    paths: List[Path]
    on_change: Callable[[Path, LintResult], None]
    interval: float = 1.0
    _states: Dict[str, WatchState] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        for p in self.paths:
            self._states[str(p)] = WatchState(path=p, last_hash=_file_hash(p))

    def poll_once(self) -> List[Path]:
        """Check all watched files; trigger callback for changed ones.
        Returns list of paths that changed."""
        changed: List[Path] = []
        for key, state in self._states.items():
            if _changed(state):
                result = lint_file(state.path)
                state.last_result = result
                self.on_change(state.path, result)
                changed.append(state.path)
        return changed

    def run(self, max_iterations: Optional[int] = None) -> None:
        """Block and poll indefinitely (or up to max_iterations for testing)."""
        iterations = 0
        while True:
            self.poll_once()
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(self.interval)
