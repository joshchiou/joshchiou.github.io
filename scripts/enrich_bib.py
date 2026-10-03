#!/usr/bin/env python3
"""Add abstracts, PubMed IDs, and open-access PDF links to papers.bib via Europe PMC.

For each entry with a DOI, looks the paper up on Europe PMC and adds any of
these fields the entry is missing:
  abstract  - shown behind the "Abstract" button on the publications page
  pmid      - PubMed ID
  pdf       - Europe PMC full-text PDF, only when the paper is open access

Existing fields are never overwritten. Creates a PR via `gh` for review.

Usage:
    python3 scripts/enrich_bib.py          # dry-run: print what would change
    python3 scripts/enrich_bib.py --pr     # write papers.bib and open a PR
"""

import argparse
import html
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")

EPMC_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
BIB_PATH = Path(__file__).resolve().parent.parent / "_bibliography" / "papers.bib"
ENTRY_RE = re.compile(r"@\w+\{(?P<key>[^,]+),.*?\n\}\n", re.S)


def has_field(entry: str, field: str) -> bool:
    return re.search(rf"^\s*{field}\s*=", entry, re.M | re.I) is not None


def get_field(entry: str, field: str) -> str | None:
    m = re.search(rf"^\s*{field}\s*=\s*\{{(.*?)\}},?\s*$", entry, re.M | re.I)
    return m.group(1).strip() if m else None


def clean_abstract(text: str) -> str:
    """Strip HTML from Europe PMC abstracts and make the text safe inside a BibTeX field."""
    text = re.sub(r"<h4>.*?</h4>", " ", text)  # section labels like "Background"
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("{", "(").replace("}", ")")
    return re.sub(r"\s+", " ", text).strip()


def fetch_epmc(doi: str) -> dict | None:
    resp = requests.get(
        EPMC_API,
        params={"query": f'DOI:"{doi}"', "resultType": "core", "format": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    results = resp.json().get("resultList", {}).get("result", [])
    return results[0] if results else None


def new_fields(entry: str, record: dict) -> dict[str, str]:
    fields = {}
    if not has_field(entry, "abstract") and record.get("abstractText"):
        fields["abstract"] = clean_abstract(record["abstractText"])
    if not has_field(entry, "pmid") and record.get("pmid"):
        fields["pmid"] = record["pmid"]
    pmcid = record.get("pmcid")
    if not has_field(entry, "pdf") and pmcid and record.get("isOpenAccess") == "Y":
        fields["pdf"] = f"https://europepmc.org/articles/{pmcid}?pdf=render"
    return fields


def add_fields(entry: str, fields: dict[str, str]) -> str:
    body = entry[: -len("\n}\n")].rstrip()
    if not body.endswith(","):
        body += ","
    extra = ",".join(f"\n  {k} = {{{v}}}" for k, v in fields.items())
    return body + extra + "\n}\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", action="store_true", help="Write papers.bib and create a PR")
    args = parser.parse_args()

    text = BIB_PATH.read_text()
    updated = text
    changes = []

    for m in ENTRY_RE.finditer(text):
        entry, key = m.group(0), m.group("key")
        doi = get_field(entry, "doi")
        if not doi:
            continue
        time.sleep(0.5)  # be polite to Europe PMC
        try:
            record = fetch_epmc(doi)
        except requests.RequestException as e:
            print(f"  {key}: lookup failed ({e})")
            continue
        if record is None:
            print(f"  {key}: not found on Europe PMC")
            continue
        fields = new_fields(entry, record)
        if not fields:
            continue
        updated = updated.replace(entry, add_fields(entry, fields))
        changes.append((key, sorted(fields)))
        print(f"  {key}: + {', '.join(sorted(fields))}")

    if not changes:
        print("Nothing to add.")
        return

    print(f"\n{len(changes)} entries would gain fields.")
    if not args.pr:
        print("Dry run — papers.bib not written. Use --pr to create a PR.")
        return

    BIB_PATH.write_text(updated)
    branch = f"auto/enrich-publications-{int(time.time())}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    subprocess.run(["git", "add", str(BIB_PATH)], check=True)
    summary = "\n".join(f"- `{key}`: {', '.join(fields)}" for key, fields in changes)
    subprocess.run(["git", "commit", "-m", f"feat: add abstracts/PMIDs/OA PDFs to {len(changes)} publications\n\n{summary}"], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch], check=True)
    body = (
        "## Publication metadata from Europe PMC\n\n"
        f"{summary}\n\n"
        "`pdf` links are added only for open-access papers. Spot-check abstracts for formatting before merging."
    )
    subprocess.run(
        ["gh", "pr", "create", "--title", f"Add abstracts and links to {len(changes)} publications", "--body", body, "--base", "master"],
        check=True,
    )
    print(f"\nPR created on branch {branch}")


if __name__ == "__main__":
    main()
