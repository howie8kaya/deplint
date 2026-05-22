"""Simple file-based cache for PyPI version lookups."""

import json
import os
import time
from pathlib import Path
from typing import Optional

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "deplint"
DEFAULT_TTL = 3600  # seconds


class VersionCache:
    """Caches latest-version responses from PyPI to avoid redundant network calls."""

    def __init__(self, cache_dir: Path = DEFAULT_CACHE_DIR, ttl: int = DEFAULT_TTL):
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, package: str) -> Path:
        safe = package.lower().replace("-", "_")
        return self.cache_dir / f"{safe}.json"

    def get(self, package: str) -> Optional[str]:
        """Return cached version string, or None if missing/expired."""
        p = self._path(package)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text())
            if time.time() - data["ts"] > self.ttl:
                p.unlink(missing_ok=True)
                return None
            return data["version"]
        except (KeyError, json.JSONDecodeError, OSError):
            return None

    def set(self, package: str, version: str) -> None:
        """Store a version string for the given package."""
        p = self._path(package)
        try:
            p.write_text(json.dumps({"version": version, "ts": time.time()}))
        except OSError:
            pass  # cache write failure is non-fatal

    def invalidate(self, package: str) -> None:
        """Remove cached entry for a package."""
        self._path(package).unlink(missing_ok=True)

    def clear(self) -> int:
        """Remove all cached entries. Returns number of files removed."""
        removed = 0
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
        return removed


_default_cache: Optional[VersionCache] = None


def get_default_cache() -> VersionCache:
    global _default_cache
    if _default_cache is None:
        _default_cache = VersionCache()
    return _default_cache
