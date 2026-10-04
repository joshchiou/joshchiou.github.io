#!/usr/bin/env python3
"""Check that every preprint in papers.bib is still unpublished.

Preprints count toward the site's publication total only until they're published (D-019). Once a
journal version exists, the bib entry should be replaced by it, or the paper is listed, and
counted, twice. This asks the bioRxiv/medRxiv API for each preprint's published DOI and fails if
one has been published. It also fails if a preprint DOI doesn't exist, which catches typos.

Runs weekly in the Site checks workflow; the API isn't reachable from every sandbox.

Usage:
    python3 scripts/check_preprints.py
"""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_site import ROOT, parse_bib  # noqa: E402

API = "https://api.biorxiv.org/details/{server}/{doi}"
PREPRINT_PREFIXES = ("10.1101/", "10.64898/")  # see D-012


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "check_preprints"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def lookup(doi: str, server: str) -> dict | None:
    """The latest version's record, or None if the server doesn't know the DOI."""
    records = fetch(API.format(server=server, doi=doi)).get("collection") or []
    return records[-1] if records else None


def check(entries: list[dict]) -> list[str]:
    problems = []
    bib_dois = {e.get("doi", "").lower() for e in entries}
    for e in entries:
        doi = e.get("doi", "")
        if not doi.startswith(PREPRINT_PREFIXES):
            continue
        server = "medrxiv" if e.get("journal", "").lower() == "medrxiv" else "biorxiv"
        record = lookup(doi, server)
        if record is None:
            problems.append(f"{e['key']}: {server} has no preprint with DOI {doi}")
            continue
        published = (record.get("published") or "NA").strip()
        if published != "NA":
            where = " (already in papers.bib, so it's listed twice)" if published.lower() in bib_dois else ""
            problems.append(f"{e['key']}: published as https://doi.org/{published}{where}; "
                            "replace the preprint entry with the published one")
    return problems


def main() -> None:
    entries = parse_bib(ROOT / "_bibliography" / "papers.bib")
    preprints = [e for e in entries if e.get("doi", "").startswith(PREPRINT_PREFIXES)]
    problems = check(entries)
    for p in problems:
        print(f"FAIL: {p}")
    if problems:
        sys.exit(f"{len(problems)} preprint problem(s)")
    print(f"All {len(preprints)} preprints are unpublished and their DOIs resolve.")


if __name__ == "__main__":
    main()
