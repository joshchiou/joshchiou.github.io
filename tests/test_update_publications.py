"""Tests for the DOI ignore list (scripts/update_publications.py)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
pytest.importorskip("requests")
import update_publications  # noqa: E402


def test_reads_dois_and_drops_comments(tmp_path):
    f = tmp_path / "ignore.txt"
    f.write_text("# header\n\n10.1101/ABC.1  # preprint\n  10.2210/pdb3jb5/pdb\n")
    assert update_publications.load_ignored_dois(f) == {"10.1101/abc.1", "10.2210/pdb3jb5/pdb"}


def test_missing_file_ignores_nothing(tmp_path):
    assert update_publications.load_ignored_dois(tmp_path / "absent.txt") == set()


def test_committed_list_holds_the_rejected_preprints():
    ignored = update_publications.load_ignored_dois()
    assert "10.1101/2022.06.17.496443" in ignored  # UKB-PPP preprint of sun2023plasma
