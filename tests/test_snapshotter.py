"""Tests for deplint.snapshotter and the snapshot CLI command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deplint.snapshotter import (
    Snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
    take_snapshot,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_reqs(tmp_path: Path, content: str, name: str = "requirements.txt") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# take_snapshot
# ---------------------------------------------------------------------------

def test_take_snapshot_pinned(tmp_path: Path) -> None:
    req = _write_reqs(tmp_path, "requests==2.31.0\nflask==3.0.0\n")
    snap = take_snapshot(str(req))
    assert snap.packages["requests"] == "2.31.0"
    assert snap.packages["flask"] == "3.0.0"
    assert snap.source_file.endswith("requirements.txt")


def test_take_snapshot_unpinned_has_none_version(tmp_path: Path) -> None:
    req = _write_reqs(tmp_path, "requests\nflask>=2.0\n")
    snap = take_snapshot(str(req))
    assert snap.packages["requests"] is None
    assert snap.packages["flask"] is None


def test_take_snapshot_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        take_snapshot(str(tmp_path / "nonexistent.txt"))


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_round_trip(tmp_path: Path) -> None:
    snap = Snapshot(
        created_at="2024-01-01T00:00:00+00:00",
        source_file="/some/requirements.txt",
        packages={"requests": "2.31.0", "boto3": None},
    )
    out = tmp_path / "snap.json"
    save_snapshot(snap, str(out))
    loaded = load_snapshot(str(out))
    assert loaded.packages == snap.packages
    assert loaded.source_file == snap.source_file
    assert loaded.created_at == snap.created_at


def test_save_produces_valid_json(tmp_path: Path) -> None:
    snap = Snapshot(created_at="t", source_file="f", packages={"x": "1.0"})
    out = tmp_path / "snap.json"
    save_snapshot(snap, str(out))
    data = json.loads(out.read_text())
    assert data["packages"]["x"] == "1.0"


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def _snap(packages: dict) -> Snapshot:
    return Snapshot(created_at="t", source_file="f", packages=packages)


def test_no_changes_when_identical() -> None:
    s = _snap({"requests": "2.31.0"})
    assert diff_snapshots(s, s) == {}


def test_added_package() -> None:
    old = _snap({"requests": "2.31.0"})
    new = _snap({"requests": "2.31.0", "flask": "3.0.0"})
    changes = diff_snapshots(old, new)
    assert changes["flask"]["change"] == "added"
    assert changes["flask"]["new"] == "3.0.0"


def test_removed_package() -> None:
    old = _snap({"requests": "2.31.0", "flask": "3.0.0"})
    new = _snap({"requests": "2.31.0"})
    changes = diff_snapshots(old, new)
    assert changes["flask"]["change"] == "removed"


def test_upgraded_package() -> None:
    old = _snap({"requests": "2.28.0"})
    new = _snap({"requests": "2.31.0"})
    changes = diff_snapshots(old, new)
    assert changes["requests"]["change"] == "upgraded"


def test_downgraded_package() -> None:
    old = _snap({"requests": "2.31.0"})
    new = _snap({"requests": "2.28.0"})
    changes = diff_snapshots(old, new)
    assert changes["requests"]["change"] == "downgraded"


def test_unpinned_package() -> None:
    old = _snap({"requests": "2.31.0"})
    new = _snap({"requests": None})
    changes = diff_snapshots(old, new)
    assert changes["requests"]["change"] == "unpinned"


def test_repinned_package() -> None:
    old = _snap({"requests": None})
    new = _snap({"requests": "2.31.0"})
    changes = diff_snapshots(old, new)
    assert changes["requests"]["change"] == "repinned"
