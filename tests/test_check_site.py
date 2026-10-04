"""Tests for scripts/check_site.py: the bib reader, the data checks, and the built-site checks.

Run with `python3 -m pytest tests/`. The built-site tests use _site and are skipped when it
hasn't been built.
"""

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_site  # noqa: E402


@pytest.fixture(autouse=True)
def reset_results():
    check_site.failures.clear()
    check_site.warnings.clear()
    yield
    check_site.failures.clear()
    check_site.warnings.clear()


def bib(tmp_path, text):
    path = tmp_path / "papers.bib"
    path.write_text(text, encoding="utf-8")
    return check_site.parse_bib(path)


ENTRY = """@article{{{key},
  author = {{Chiou, Joshua and Krämer, Dana}},
  title = {{A {{Nested}} title}},
  journal = {{{journal}}},
  year = {{2021}},
  doi = {{{doi}}},
  selected = {{{selected}}}
}}
"""


def make(key="a2021", journal="Nature", doi="10.1/a", selected="false"):
    return ENTRY.format(key=key, journal=journal, doi=doi, selected=selected)


def test_parse_bib_reads_nested_braces_and_unicode(tmp_path):
    [entry] = bib(tmp_path, make())
    assert entry["key"] == "a2021"
    assert entry["title"] == "A {Nested} title"
    assert "Krämer" in entry["author"]
    assert entry["journal"] == "Nature"


def test_parse_bib_counts_every_entry(tmp_path):
    entries = bib(tmp_path, make("a", doi="1") + make("b", doi="2") + make("c", doi="3"))
    assert [e["key"] for e in entries] == ["a", "b", "c"]


def test_real_bib_matches_entry_count():
    text = (ROOT / "_bibliography" / "papers.bib").read_text(encoding="utf-8")
    entries = check_site.parse_bib(ROOT / "_bibliography" / "papers.bib")
    assert len(entries) == text.count("\n@") + text.startswith("@")


def test_duplicate_key_and_doi_fail(tmp_path):
    entries = bib(tmp_path, make("a", doi="10.1/X") + make("a", doi="10.1/x"))
    check_site.check_bib(entries, {})
    assert any("duplicate key a" in f for f in check_site.failures)
    assert any("duplicate DOI" in f for f in check_site.failures)


def test_top_journal_misspelling_fails(tmp_path):
    entries = bib(tmp_path, make(journal="Nature genetics"))
    check_site.check_bib(entries, {"top_journals": ["Nature Genetics"]})
    assert any("should be spelled 'Nature Genetics'" in f for f in check_site.failures)


def test_scholar_h_index_needs_enough_citations():
    check_site.check_scholar({"citations": 100, "h_index": 28, "i10_index": 36})
    assert any("h-index 28" in f for f in check_site.failures)


def test_scholar_current_values_pass():
    check_site.check_scholar(check_site.load_json("scholar_stats.json"))
    assert check_site.failures == []


def test_strava_monthly_must_sum_to_total():
    check_site.check_strava({"total_distance_km": 500, "monthly": [{"distance_km": 100}]})
    assert check_site.failures


def test_travel_city_needs_known_country():
    check_site.check_travel(
        [{"name": "France", "continent": "Europe", "flag": "x"}],
        [{"name": "Rome", "country": "Italy"}],
    )
    assert any("Rome" in f for f in check_site.failures)


def test_real_data_files_pass():
    config = check_site.load_yaml(ROOT / "_config.yml")
    check_site.check_bib(check_site.parse_bib(ROOT / "_bibliography" / "papers.bib"), config)
    check_site.check_strava(check_site.load_json("strava_stats.json"))
    check_site.check_travel(
        check_site.load_yaml(ROOT / "_data" / "travel_countries.yml"),
        check_site.load_yaml(ROOT / "_data" / "travel_cities.yml"),
    )
    assert check_site.failures == []


# ---------------------------------------------------------------- built site

needs_site = pytest.mark.skipif(not (ROOT / "_site" / "index.html").exists(), reason="site not built")


def run_site_checks(site):
    config = check_site.load_yaml(ROOT / "_config.yml")
    entries = check_site.parse_bib(ROOT / "_bibliography" / "papers.bib")
    check_site.check_site(site, entries, config, check_site.load_json("scholar_stats.json"))


@pytest.fixture
def site_copy(tmp_path):
    dest = tmp_path / "site"
    for rel in ["index.html", "publications/index.html", "code/index.html",
                "projects/fun_travel/index.html", "projects/fun_cycling/index.html"]:
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / "_site" / rel, dest / rel)
    return dest


def edit(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not found in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


@needs_site
def test_built_site_passes(site_copy):
    run_site_checks(site_copy)
    assert check_site.failures == []


@needs_site
def test_hardcoded_publication_count_is_caught(site_copy):
    page = site_copy / "publications" / "index.html"
    total = len(check_site.parse_bib(ROOT / "_bibliography" / "papers.bib"))
    edit(page, f'publication-count">{total} publications', 'publication-count">38 publications')
    run_site_checks(site_copy)
    assert any("publications page count" in f for f in check_site.failures)


@needs_site
def test_missing_entry_on_publications_page_is_caught(site_copy):
    page = site_copy / "publications" / "index.html"
    text = page.read_text(encoding="utf-8")
    split = text.find("all-heading")
    head, tail = text[:split], text[split:]
    page.write_text(head + tail.replace('<div id="sun2023plasma" class="col-sm', '<div class="col-sm', 1))
    run_site_checks(site_copy)
    assert any("sun2023plasma" in f for f in check_site.failures)


@needs_site
def test_stale_citation_stat_is_caught(site_copy):
    citations = check_site.load_json("scholar_stats.json")["citations"]
    edit(site_copy / "index.html", f'id="stat-citations">{citations}', 'id="stat-citations">1')
    run_site_checks(site_copy)
    assert any("citations stat" in f for f in check_site.failures)
