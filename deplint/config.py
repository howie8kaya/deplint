"""Configuration loading for deplint.

Supports reading settings from pyproject.toml or a .deplint.toml file.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

try:
    import tomllib
except ImportError:  # Python < 3.11
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


@dataclass
class DeplintConfig:
    """Resolved configuration for a deplint run."""

    ignore_codes: List[str] = field(default_factory=list)
    fail_on: str = "error"  # error | warning | info
    check_outdated: bool = False
    exclude: List[str] = field(default_factory=list)


_DEFAULTS = DeplintConfig()


def _find_config_file(start: Path) -> Optional[Path]:
    """Walk up from *start* looking for a config file."""
    candidates = [".deplint.toml", "pyproject.toml"]
    for directory in [start, *start.parents]:
        for name in candidates:
            path = directory / name
            if path.is_file():
                return path
    return None


def load_config(start_dir: Optional[str] = None) -> DeplintConfig:
    """Load configuration from the nearest config file, or return defaults."""
    if tomllib is None:
        return DeplintConfig()

    base = Path(start_dir) if start_dir else Path(os.getcwd())
    config_path = _find_config_file(base)
    if config_path is None:
        return DeplintConfig()

    with config_path.open("rb") as fh:
        data = tomllib.load(fh)

    # Support both [tool.deplint] (pyproject.toml) and top-level [deplint]
    section = data.get("tool", {}).get("deplint") or data.get("deplint") or {}

    return DeplintConfig(
        ignore_codes=section.get("ignore", []),
        fail_on=section.get("fail_on", _DEFAULTS.fail_on),
        check_outdated=section.get("check_outdated", _DEFAULTS.check_outdated),
        exclude=section.get("exclude", []),
    )
