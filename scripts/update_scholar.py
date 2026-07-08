#!/usr/bin/env python3
"""Fetch Google Scholar stats and count publications from papers.bib.

Writes _data/scholar_stats.json with citation count, h-index, paper counts,
top-journal breakdown, and update metadata. Preserves last-known-good values
on fetch failure.

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
GOOGLE_SCHOLAR_TIMEOUT = 15


def count_bib_entries(bib_path: Path) -> tuple[int, int, list[dict]]:
    text = bib_path.read_text()
    total = len(re.findall(r"^@\w+\{", text, re.MULTILINE))
    journal_counts: dict[str, int] = {}
    for m in re.finditer(r"journal\s*=\s*\{([^}]+)\}", text):
        name = m.group(1).strip()
        if name in TOP_JOURNALS:
            journal_counts[name] = journal_counts.get(name, 0) + 1
    top_journals = [
        {"name": name, "count": count}
        for name, count in sorted(journal_counts.items(), key=lambda x: -x[1])
    ]
    top_total = sum(j["count"] for j in top_journals)
    return total, top_total, top_journals


def load_existing_stats() -> dict:
    if OUT_PATH.exists():
        try:
            return json.loads(OUT_PATH.read_text())
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


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


def main():
    total_papers, top_journal_papers, top_journals = count_bib_entries(BIB_PATH)
    print(f"Bib: {total_papers} papers, {top_journal_papers} in top journals")
    print(f"  Journals: {', '.join(j['name'] + ' (' + str(j['count']) + ')' for j in top_journals)}")

    existing = load_existing_stats()
    scholar = fetch_google_scholar(SCHOLAR_ID)

    if scholar is None:
        if existing.get("citations", 0) > 0:
            print("Google Scholar failed — preserving last known good values")
            scholar = {
                "citations": existing["citations"],
                "h_index": existing["h_index"],
                "i10_index": existing.get("i10_index", 0),
                "source": existing.get("source", "preserved"),
            }
        else:
            print("Google Scholar failed and no existing data — using zeros")
            scholar = {"citations": 0, "h_index": 0, "i10_index": 0, "source": "none"}
    else:
        prev_citations = existing.get("citations", 0)
        if scholar["citations"] < prev_citations:
            print(f"WARNING: New citations ({scholar['citations']}) < previous ({prev_citations})")
            print("Keeping previous values (citations should not decrease)")
            scholar["citations"] = prev_citations
            scholar["h_index"] = max(scholar["h_index"], existing.get("h_index", 0))

    print(f"{scholar['source']}: {scholar['citations']} citations, h-index {scholar['h_index']}")

    stats = {
        "total_papers": total_papers,
        "top_journal_papers": top_journal_papers,
        "top_journals": top_journals,
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
