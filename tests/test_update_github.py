"""Tests for the language list on repo cards (scripts/update_github.py)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
pytest.importorskip("requests")
import update_github  # noqa: E402


def test_lists_every_language_above_the_threshold():
    assert update_github.main_languages({"Python": 70, "R": 25, "HTML": 3, "Shell": 2}) == ["Python", "R"]


def test_caps_the_list_and_orders_by_size():
    counts = {"R": 30, "Python": 40, "Shell": 15, "HTML": 15}
    assert update_github.main_languages(counts) == ["Python", "R", "Shell"]


def test_no_breakdown_means_no_languages():
    assert update_github.main_languages({}) == []
    assert update_github.main_languages(None) == []
