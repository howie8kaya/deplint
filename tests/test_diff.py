"""Tests for deplint.diff module."""

import pytest

from deplint.diff import DiffEntry, diff_requirements


OLD = """\
requests==2.28.0
flask==2.2.0
numpy==1.24.0
"""

NEW = """\
requests==2.31.0
flask==2.2.0
pandas==2.0.0
"""


def test_no_diff_identical_files():
    entries = diff_requirements(OLD, OLD)
    assert entries == []


def test_changed_version():
    entries = diff_requirements(OLD, NEW)
    changed = [e for e in entries if e.kind == "changed"]
    assert len(changed) == 1
    assert changed[0].package == "requests"
    assert changed[0].old_version == "2.28.0"
    assert changed[0].new_version == "2.31.0"


def test_removed_package():
    entries = diff_requirements(OLD, NEW)
    removed = [e for e in entries if e.kind == "removed"]
    assert len(removed) == 1
    assert removed[0].package == "numpy"
    assert removed[0].new_version is None


def test_added_package():
    entries = diff_requirements(OLD, NEW)
    added = [e for e in entries if e.kind == "added"]
    assert len(added) == 1
    assert added[0].package == "pandas"
    assert added[0].old_version is None


def test_unpinned_shows_none_version():
    old = "requests\n"
    new = "requests==2.31.0\n"
    entries = diff_requirements(old, new)
    assert len(entries) == 1
    assert entries[0].kind == "changed"
    assert entries[0].old_version is None
    assert entries[0].new_version == "2.31.0"


def test_case_insensitive_package_names():
    old = "Flask==2.2.0\n"
    new = "flask==2.3.0\n"
    entries = diff_requirements(old, new)
    assert len(entries) == 1
    assert entries[0].package == "flask"
    assert entries[0].old_version == "2.2.0"
    assert entries[0].new_version == "2.3.0"


def test_empty_old_file():
    entries = diff_requirements("", NEW)
    assert all(e.kind == "added" for e in entries)
    packages = {e.package for e in entries}
    assert packages == {"requests", "flask", "pandas"}


def test_empty_new_file():
    entries = diff_requirements(OLD, "")
    assert all(e.kind == "removed" for e in entries)


def test_diff_entry_kind_unchanged_not_returned():
    same = "boto3==1.26.0\n"
    entries = diff_requirements(same, same)
    assert entries == []
