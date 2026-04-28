#!/usr/bin/env python3
"""Discover new publications via ORCID + Semantic Scholar, propose BibTeX PRs.

Compares ORCID works against papers.bib. For new DOIs, fetches metadata from
Semantic Scholar and generates draft BibTeX entries. Creates a PR via `gh`.

Usage:
    python3 scripts/update_publications.py          # dry-run: print new entries
    python3 scripts/update_publications.py --pr     # create a PR with new entries
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")

ORCID_ID = "0000-0002-4618-0647"
ORCID_API = f"https://pub.orcid.org/v3.0/{ORCID_ID}/works"
S2_API = "https://api.semanticscholar.org/graph/v1/paper"

BIB_PATH = Path(__file__).resolve().parent.parent / "_bibliography" / "papers.bib"


def extract_existing_dois(bib_path: Path) -> set[str]:
    text = bib_path.read_text()
    dois = set()
    for m in re.finditer(r"doi\s*=\s*\{([^}]+)\}", text, re.IGNORECASE):
        dois.add(m.group(1).strip().lower())
    return dois


def fetch_orcid_works() -> list[dict]:
    headers = {"Accept": "application/json"}
    resp = requests.get(ORCID_API, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    works = []
    for group in data.get("group", []):
        summaries = group.get("work-summary", [])
        if not summaries:
            continue
        summary = summaries[0]
        title = summary.get("title", {}).get("title", {}).get("value", "")
        year = summary.get("publication-date", {}).get("year", {}).get("value", "")
        journal = summary.get("journal-title", {}).get("value", "") if summary.get("journal-title") else ""

        doi = None
        for eid in summary.get("external-ids", {}).get("external-id", []):
            if eid.get("external-id-type") == "doi":
                doi = eid.get("external-id-value", "").strip()
                break

        if doi:
            works.append({"doi": doi.lower(), "title": title, "year": year, "journal": journal})

    return works


def fetch_s2_metadata(doi: str) -> dict | None:
    url = f"{S2_API}/DOI:{doi}?fields=title,authors,venue,year,externalIds,abstract"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  S2 lookup failed for {doi}: {e}")
        return None


def make_bib_key(authors: list[dict], year: str, title: str) -> str:
    last = "unknown"
    if authors:
        name = authors[0].get("name", "")
        parts = name.split()
        if parts:
            last = re.sub(r"[^a-z]", "", parts[-1].lower())
    first_word = re.sub(r"[^a-z]", "", title.split()[0].lower()) if title else "untitled"
    return f"{last}{year}{first_word}"


def format_bibtex(key: str, meta: dict, doi: str) -> str:
    authors = " and ".join(a.get("name", "") for a in meta.get("authors", []))
    title = meta.get("title", "")
    venue = meta.get("venue", "")
    year = str(meta.get("year", ""))

    lines = [
        f"@article{{{key},",
        f"  author = {{{authors}}},",
        f"  title = {{{title}}},",
    ]
    if venue:
        lines.append(f"  journal = {{{venue}}},")
    if year:
        lines.append(f"  year = {{{year}}},")
    lines.append(f"  doi = {{{doi}}},")
    lines.append(f"  selected = {{false}}")
    lines.append("}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", action="store_true", help="Create a PR with new entries")
    args = parser.parse_args()

    print(f"Fetching ORCID works for {ORCID_ID}...")
    orcid_works = fetch_orcid_works()
    print(f"  Found {len(orcid_works)} works on ORCID")

    existing_dois = extract_existing_dois(BIB_PATH)
    print(f"  {len(existing_dois)} DOIs already in papers.bib")

    new_works = [w for w in orcid_works if w["doi"] not in existing_dois]
    print(f"  {len(new_works)} new DOIs to process")

    if not new_works:
        print("No new publications found.")
        return

    new_entries = []
    for work in new_works:
        print(f"\n  Processing: {work['doi']}")
        time.sleep(1)
        meta = fetch_s2_metadata(work["doi"])
        if meta is None:
            print(f"    Skipped (not found on Semantic Scholar)")
            continue

        key = make_bib_key(meta.get("authors", []), str(meta.get("year", work["year"])), meta.get("title", work["title"]))
        bib = format_bibtex(key, meta, work["doi"])
        new_entries.append({"key": key, "title": meta.get("title", work["title"]), "bib": bib})
        print(f"    → {key}: {meta.get('title', '')[:60]}")

    if not new_entries:
        print("\nNo new entries could be generated (all skipped).")
        return

    print(f"\n{len(new_entries)} new BibTeX entries generated.")

    if not args.pr:
        print("\nDry run — entries not written. Use --pr to create a PR.")
        for entry in new_entries:
            print(f"\n{entry['bib']}")
        return

    bib_text = BIB_PATH.read_text()
    additions = "\n\n".join(e["bib"] for e in new_entries)
    BIB_PATH.write_text(bib_text.rstrip() + "\n\n" + additions + "\n")
    print(f"Appended {len(new_entries)} entries to {BIB_PATH}")

    branch = f"auto/new-publications-{int(time.time())}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    subprocess.run(["git", "add", str(BIB_PATH)], check=True)

    titles = "\n".join(f"- {e['title']}" for e in new_entries)
    msg = f"feat: add {len(new_entries)} new publication(s) from ORCID\n\n{titles}"
    subprocess.run(["git", "commit", "-m", msg], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch], check=True)

    body = f"## New publications discovered via ORCID\n\n{titles}\n\nReview the BibTeX entries and add `selected`, `cv_order`, `altmetric`, and `preview` fields as needed."
    subprocess.run([
        "gh", "pr", "create",
        "--title", f"Add {len(new_entries)} new publication(s)",
        "--body", body,
        "--base", "master",
    ], check=True)

    print(f"\nPR created on branch {branch}")


if __name__ == "__main__":
    main()
