"""Tests for deplint.cache."""

import json
import time
from pathlib import Path

import pytest

from deplint.cache import VersionCache


@pytest.fixture()
def cache(tmp_path: Path) -> VersionCache:
    return VersionCache(cache_dir=tmp_path / "cache", ttl=60)


def test_miss_on_empty_cache(cache: VersionCache) -> None:
    assert cache.get("requests") is None


def test_set_and_get(cache: VersionCache) -> None:
    cache.set("requests", "2.31.0")
    assert cache.get("requests") == "2.31.0"


def test_case_insensitive_key(cache: VersionCache) -> None:
    cache.set("Django", "4.2.0")
    assert cache.get("django") == "4.2.0"


def test_expired_entry_returns_none(cache: VersionCache, tmp_path: Path) -> None:
    short_cache = VersionCache(cache_dir=tmp_path / "short", ttl=0)
    short_cache.set("flask", "3.0.0")
    time.sleep(0.01)
    assert short_cache.get("flask") is None


def test_invalidate_removes_entry(cache: VersionCache) -> None:
    cache.set("numpy", "1.26.0")
    cache.invalidate("numpy")
    assert cache.get("numpy") is None


def test_invalidate_nonexistent_is_safe(cache: VersionCache) -> None:
    cache.invalidate("nonexistent")  # should not raise


def test_clear_removes_all(cache: VersionCache) -> None:
    cache.set("a", "1.0")
    cache.set("b", "2.0")
    cache.set("c", "3.0")
    removed = cache.clear()
    assert removed == 3
    assert cache.get("a") is None


def test_clear_empty_cache(cache: VersionCache) -> None:
    assert cache.clear() == 0


def test_corrupt_cache_file_returns_none(cache: VersionCache) -> None:
    cache.cache_dir.mkdir(parents=True, exist_ok=True)
    bad = cache.cache_dir / "broken.json"
    bad.write_text("not json!")
    # corrupt file should not crash get()
    assert cache.get("broken") is None


def test_cache_dir_created_automatically(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "c"
    c = VersionCache(cache_dir=deep)
    c.set("pkg", "0.1")
    assert c.get("pkg") == "0.1"
