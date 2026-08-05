#!/usr/bin/env python3
"""Fetch Google Scholar stats and count publications from papers.bib.

Writes _data/scholar_stats.json with citation count, h-index, paper counts,
top-journal breakdown, and update metadata. Preserves last-known-good values
on fetch failure.

Usage:
    python3 scripts/update_scholar.py
"""

import argparse
import json
import re
import sys
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


def check_freshness(max_age_days: int) -> int:
    """Exit status for the workflow's staleness gate.

    This job preserves last-known-good numbers and exits 0 when Scholar can't be
    reached, which is right for the site but means it never fails loudly — it
    would happily serve year-old citation counts while reporting success. The
    workflow therefore checks how long it has actually been since a live fetch.
    """
    stats = load_existing_stats()
    last = stats.get("last_success_at")
    if not last:
        print("No last_success_at recorded yet — cannot assess staleness; skipping.")
        return 0
    try:
        ts = datetime.fromisoformat(last)
    except ValueError:
        print(f"Unparseable last_success_at ({last!r}); skipping.")
        return 0
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - ts).days
    print(f"Last successful Scholar fetch: {last} ({age} days ago)")
    if age > max_age_days:
        print(f"STALE: no successful fetch for {age} days (threshold {max_age_days}).")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-freshness", type=int, metavar="DAYS",
                    help="don't fetch; exit 1 if the last successful fetch is older than DAYS")
    args = ap.parse_args()

    if args.check_freshness is not None:
        sys.exit(check_freshness(args.check_freshness))

    total_papers, top_journal_papers, top_journals = count_bib_entries(BIB_PATH)
    print(f"Bib: {total_papers} papers, {top_journal_papers} in top journals")
    print(f"  Journals: {', '.join(j['name'] + ' (' + str(j['count']) + ')' for j in top_journals)}")

    existing = load_existing_stats()
    scholar = fetch_google_scholar(SCHOLAR_ID)
    now = datetime.now(timezone.utc).isoformat()
    # Only a live fetch advances this; preserving carries the old value forward,
    # which is what makes a long stale streak visible at all.
    last_success_at = existing.get("last_success_at")

    if scholar is None:
        if existing.get("citations", 0) > 0:
            print("Google Scholar failed — preserving last known good values")
            scholar = {
                "citations": existing["citations"],
                "h_index": existing["h_index"],
                "i10_index": existing.get("i10_index", 0),
                # Deliberately not existing["source"]: claiming "google_scholar"
                # on a run that never reached Google Scholar hides the failure.
                "source": "preserved",
            }
        else:
            print("Google Scholar failed and no existing data — using zeros")
            scholar = {"citations": 0, "h_index": 0, "i10_index": 0, "source": "none"}
    else:
        last_success_at = now
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
        "updated_at": now,
    }
    if last_success_at:
        stats["last_success_at"] = last_success_at

    # Skip the write when nothing meaningful moved, so the commit log records
    # real changes instead of a daily timestamp bump. `updated_at` is excluded
    # from the comparison (it always differs) and isn't rendered anywhere; a
    # successful fetch always advances last_success_at, so successes still write
    # even when the citation count happens to be unchanged.
    def _substantive(d: dict) -> dict:
        return {k: v for k, v in d.items() if k != "updated_at"}

    if existing and _substantive(existing) == _substantive(stats):
        print("No change since last run — leaving the file untouched (no commit).")
        return

    OUT_PATH.write_text(json.dumps(stats, indent=2) + "\n")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
