#!/usr/bin/env python3
"""Discover newly merged open-source PRs and propose contributions.yml entries.

Searches GitHub for merged PRs authored by GITHUB_USER, skips repositories the
user owns (those are personal projects, not contributions to other people's
software), and compares the rest against _data/contributions.yml.

New entries are appended with a provisional blurb taken from the PR title and
``needs_review: true``, then a PR is opened for curation. Nothing is ever
published without a human editing the blurb, type, and featured flag — the
values it writes are factual but terse.

By default only PRs merged after the newest date already in contributions.yml
are considered, so the first run doesn't dredge up years of old history. Use
--since to override.

Usage:
    python3 scripts/update_contributions.py                 # dry run
    python3 scripts/update_contributions.py --since 2024-01-01
    python3 scripts/update_contributions.py --pr            # open a PR
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import requests  # noqa: F401  (imported for the error message below)
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")

try:
    import yaml
except ImportError:
    sys.exit("PyYAML not installed. Run: pip install pyyaml")

from _http import get_json, request_with_retry

GITHUB_USER = "joshchiou"
API_BASE = "https://api.github.com"
# Repos under these owners are the user's own work, not contributions to others.
EXCLUDE_OWNERS = {"joshchiou"}

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRIB_PATH = REPO_ROOT / "_data" / "contributions.yml"

RATE_LIMIT_KWARGS = {
    "remaining_header": "X-RateLimit-Remaining",
    "reset_header": "X-RateLimit-Reset",
}


def headers() -> dict:
    h = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    else:
        print("WARNING: no GITHUB_TOKEN — search API allows only 10 req/min unauthenticated")
    return h


def load_existing() -> tuple[set[str], str | None]:
    """Return (known PR urls, newest date present)."""
    if not CONTRIB_PATH.exists():
        return set(), None
    data = yaml.safe_load(CONTRIB_PATH.read_text()) or []
    urls = {str(c.get("pr_url", "")).strip().rstrip("/") for c in data if c.get("pr_url")}
    dates = sorted(str(c["date"]) for c in data if c.get("date"))
    return urls, dates[-1] if dates else None


def search_merged_prs(hdrs: dict, since: str | None) -> list[dict]:
    """All merged PRs authored by the user, newest first."""
    query = f"is:pr is:merged author:{GITHUB_USER}"
    if since:
        query += f" merged:>{since}"

    items, page = [], 1
    while True:
        data = get_json(
            f"{API_BASE}/search/issues",
            headers=hdrs,
            params={"q": query, "per_page": 100, "page": page, "sort": "created", "order": "desc"},
            timeout=30,
            **RATE_LIMIT_KWARGS,
        )
        if not data or not data.get("items"):
            break
        items.extend(data["items"])
        if len(data["items"]) < 100:
            break
        page += 1
        time.sleep(1)  # search API is rate-limited more aggressively
    return items


def repo_slug(item: dict) -> str:
    """owner/repo parsed from the PR's html_url."""
    parts = item.get("html_url", "").split("/")
    return "/".join(parts[3:5]) if len(parts) >= 5 else ""


def repo_language(slug: str, hdrs: dict, cache: dict) -> str | None:
    if slug not in cache:
        data = get_json(f"{API_BASE}/repos/{slug}", headers=hdrs, timeout=30, **RATE_LIMIT_KWARGS)
        cache[slug] = (data or {}).get("language")
    return cache[slug]


def merged_date(item: dict) -> str:
    pr = item.get("pull_request") or {}
    stamp = pr.get("merged_at") or item.get("closed_at") or ""
    return stamp[:10]


def build_entry(item: dict, slug: str, language: str | None) -> dict:
    return {
        "repo": slug,
        "url": f"https://github.com/{slug}",
        "pr_title": item.get("title", "").strip(),
        "pr_url": item.get("html_url", ""),
        "date": merged_date(item),
        "type": "bug fix",  # placeholder — curate before publishing
        "language": language or "Python",
        "blurb": item.get("title", "").strip().rstrip("."),
        "needs_review": True,
    }


def to_yaml(entries: list[dict]) -> str:
    """Render entries in the hand-written style of contributions.yml."""
    out = []
    for e in entries:
        out.append(
            f"- repo: {e['repo']}\n"
            f"  url: {e['url']}\n"
            f'  pr_title: "{e["pr_title"].replace(chr(34), chr(39))}"\n'
            f"  pr_url: {e['pr_url']}\n"
            f"  date: {e['date']}\n"
            f"  type: {e['type']}\n"
            f"  language: {e['language']}\n"
            f"  blurb: {e['blurb']}\n"
            f"  needs_review: true\n"
        )
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", action="store_true", help="append entries and open a PR")
    ap.add_argument("--since", help="only consider PRs merged after this date (YYYY-MM-DD)")
    args = ap.parse_args()

    hdrs = headers()
    known_urls, newest = load_existing()
    since = args.since or newest
    print(f"{len(known_urls)} contributions already recorded; searching for PRs merged after {since or 'the beginning'}")

    items = search_merged_prs(hdrs, since)
    print(f"  {len(items)} merged PRs returned by search")

    lang_cache: dict[str, str | None] = {}
    candidates = []
    for item in items:
        slug = repo_slug(item)
        url = item.get("html_url", "").rstrip("/")
        if not slug:
            continue
        if slug.split("/")[0] in EXCLUDE_OWNERS:
            continue
        if url in known_urls:
            continue
        candidates.append(build_entry(item, slug, repo_language(slug, hdrs, lang_cache)))

    if not candidates:
        print("No new external contributions found.")
        return

    candidates.sort(key=lambda e: e["date"], reverse=True)
    block = to_yaml(candidates)
    print(f"\n{len(candidates)} new contribution(s):\n")
    print(block)

    if not args.pr:
        print("Dry run — nothing written. Use --pr to open a pull request.")
        return

    # Newest-first file: new entries go on top.
    existing_text = CONTRIB_PATH.read_text()
    lines = existing_text.split("\n")
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith("- "):
            header_end = i
            break
    merged = "\n".join(lines[:header_end]) + "\n" + block + "\n" + "\n".join(lines[header_end:])
    CONTRIB_PATH.write_text(merged)
    print(f"Prepended {len(candidates)} entries to {CONTRIB_PATH}")

    branch = f"auto/new-contributions-{int(time.time())}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    subprocess.run(["git", "add", str(CONTRIB_PATH)], check=True)
    titles = "\n".join(f"- {e['repo']}: {e['pr_title']}" for e in candidates)
    subprocess.run(
        ["git", "commit", "-m", f"chore: add {len(candidates)} discovered contribution(s)\n\n{titles}"],
        check=True,
    )
    subprocess.run(["git", "push", "-u", "origin", branch], check=True)

    body = (
        "## New merged PRs discovered\n\n"
        f"{titles}\n\n"
        "Each entry is marked `needs_review: true` and needs curation before merge:\n\n"
        "- [ ] Rewrite `blurb` to say what the change actually does (currently the PR title)\n"
        "- [ ] Set `type` (bug fix | performance | feature | packaging | compatibility)\n"
        "- [ ] Confirm `language`\n"
        "- [ ] Add `featured: true` if it belongs in the default view\n"
        "- [ ] Remove the `needs_review` key\n"
        "- [ ] Consider a matching `_news/` item\n"
    )
    subprocess.run(
        ["gh", "pr", "create", "--title",
         f"Add {len(candidates)} discovered contribution(s)", "--body", body, "--base", "master"],
        check=True,
    )
    print(f"PR opened from {branch}")


if __name__ == "__main__":
    main()
