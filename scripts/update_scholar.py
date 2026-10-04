#!/usr/bin/env python3
"""Fetch Google Scholar stats.

Writes _data/scholar_stats.json with citation count, h-index, i10-index, and
update metadata. Publication counts are not stored here: the site counts
papers.bib at build time (_plugins/publication-stats.rb). If the Scholar fetch fails, exits
non-zero and leaves the file untouched, so the workflow run turns red instead
of committing stale numbers with a fresh timestamp.

Google Scholar blocks GitHub Actions runners, so the workflow reads the profile
through SerpAPI's Google Scholar Author API when SERPAPI_KEY is set (repo secret).
Without the key, it falls back to scraping Scholar directly with scholarly, which
works from a home connection but not from CI.

Usage:
    SERPAPI_KEY=... python3 scripts/update_scholar.py
    python3 scripts/update_scholar.py            # scholarly fallback
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCHOLAR_ID = "cIiNWmYAAAAJ"
OUT_PATH = Path(__file__).resolve().parent.parent / "_data" / "scholar_stats.json"

GOOGLE_SCHOLAR_TIMEOUT = 60
SERPAPI_URL = "https://serpapi.com/search.json"


def load_existing_stats() -> dict:
    if OUT_PATH.exists():
        try:
            return json.loads(OUT_PATH.read_text())
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


def fetch_serpapi(scholar_id: str, api_key: str) -> dict | None:
    """Read citations, h-index, and i10-index from SerpAPI's google_scholar_author engine."""
    query = urllib.parse.urlencode({"engine": "google_scholar_author", "author_id": scholar_id, "hl": "en", "api_key": api_key})
    try:
        with urllib.request.urlopen(f"{SERPAPI_URL}?{query}", timeout=GOOGLE_SCHOLAR_TIMEOUT) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        # Don't echo the request URL: it contains the API key.
        print(f"SerpAPI request failed with HTTP {e.code}")
        return None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"SerpAPI request failed: {type(e).__name__}")
        return None
    if "error" in data:
        print(f"SerpAPI error: {data['error']}")
        return None
    metrics = {}
    for row in data.get("cited_by", {}).get("table", []):
        for name, values in row.items():
            metrics[name] = values.get("all")
    if not metrics.get("citations"):
        print("SerpAPI response had no citation table")
        return None
    return {
        "citations": int(metrics["citations"]),
        "h_index": int(metrics.get("h_index") or 0),
        "i10_index": int(metrics.get("i10_index") or 0),
        "source": "google_scholar",
    }


def fetch_google_scholar(scholar_id: str) -> dict | None:
    import subprocess
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
    existing = load_existing_stats()
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if api_key:
        scholar = fetch_serpapi(SCHOLAR_ID, api_key)
    else:
        print("SERPAPI_KEY not set; trying Google Scholar directly")
        scholar = fetch_google_scholar(SCHOLAR_ID)

    if scholar is None:
        sys.exit(f"Google Scholar fetch failed; leaving {OUT_PATH.name} unchanged")
    else:
        prev_citations = existing.get("citations", 0)
        if scholar["citations"] < prev_citations:
            print(f"WARNING: New citations ({scholar['citations']}) < previous ({prev_citations})")
            print("Keeping previous values (citations should not decrease)")
            scholar["citations"] = prev_citations
            scholar["h_index"] = max(scholar["h_index"], existing.get("h_index", 0))

    print(f"{scholar['source']}: {scholar['citations']} citations, h-index {scholar['h_index']}")

    stats = {
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
