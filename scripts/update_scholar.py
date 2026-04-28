#!/usr/bin/python3.12
"""Fetch Google Scholar stats and count publications from papers.bib.

Writes _data/scholar_stats.json with citation count, h-index, paper counts,
and top-journal counts. Run manually or via GitHub Actions.

Usage:
    python3 scripts/update_scholar.py
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

SCHOLAR_ID = "cIiNWmYAAAAJ"
BIB_PATH = Path(__file__).resolve().parent.parent / "_bibliography" / "papers.bib"
OUT_PATH = Path(__file__).resolve().parent.parent / "_data" / "scholar_stats.json"

TOP_JOURNALS = {"Nature", "Cell", "Nature Genetics"}
GOOGLE_SCHOLAR_TIMEOUT = 30


def count_bib_entries(bib_path: Path) -> tuple[int, int]:
    text = bib_path.read_text()
    total = len(re.findall(r"^@\w+\{", text, re.MULTILINE))
    top = 0
    for m in re.finditer(r"journal\s*=\s*\{([^}]+)\}", text):
        if m.group(1).strip() in TOP_JOURNALS:
            top += 1
    return total, top


def fetch_google_scholar(scholar_id: str) -> dict | None:
    import subprocess, sys
    code = f"""
import json
from scholarly import scholarly
a = scholarly.search_author_id('{scholar_id}')
a = scholarly.fill(a, sections=['indices'])
print(json.dumps({{"citations": a.get("citedby", 0), "h_index": a.get("hindex", 0), "i10_index": a.get("i10index", 0)}}))
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=GOOGLE_SCHOLAR_TIMEOUT,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout.strip())
            data["source"] = "google_scholar"
            return data
        print(f"Google Scholar failed: {result.stderr.strip()}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Google Scholar timed out after {GOOGLE_SCHOLAR_TIMEOUT}s")
        return None
    except Exception as e:
        print(f"Google Scholar failed: {e}")
        return None


def fetch_semantic_scholar() -> dict | None:
    import urllib.request
    url = "https://api.semanticscholar.org/graph/v1/author/29873803?fields=citationCount,hIndex"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        return {
            "citations": data.get("citationCount", 0),
            "h_index": data.get("hIndex", 0),
            "i10_index": 0,
            "source": "semantic_scholar",
        }
    except Exception as e:
        print(f"Semantic Scholar failed: {e}")
        return None


def main():
    total_papers, top_journal_papers = count_bib_entries(BIB_PATH)
    print(f"Bib: {total_papers} papers, {top_journal_papers} in top journals")

    scholar = fetch_google_scholar(SCHOLAR_ID)
    if scholar is None:
        print("Falling back to Semantic Scholar...")
        scholar = fetch_semantic_scholar()
    if scholar is None:
        print("All sources failed — using zeros")
        scholar = {"citations": 0, "h_index": 0, "i10_index": 0, "source": "none"}

    print(f"{scholar['source']}: {scholar['citations']} citations, h-index {scholar['h_index']}")

    stats = {
        "total_papers": total_papers,
        "top_journal_papers": top_journal_papers,
        "citations": scholar["citations"],
        "h_index": scholar["h_index"],
        "i10_index": scholar["i10_index"],
        "source": scholar["source"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    OUT_PATH.write_text(json.dumps(stats, indent=2) + "\n")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
