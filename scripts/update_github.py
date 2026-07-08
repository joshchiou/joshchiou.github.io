#!/usr/bin/env python3
"""Fetch GitHub profile and repo stats, write _data/github_stats.json.

Uses GITHUB_TOKEN if available (5,000 req/hr), falls back to
unauthenticated (60 req/hr).

Usage:
    python3 scripts/update_github.py
    GITHUB_TOKEN=ghp_... python3 scripts/update_github.py
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")

GITHUB_USER = "joshchiou"
API_BASE = "https://api.github.com"
REPO_ROOT = Path(__file__).parent.parent
REPOS_PATH = REPO_ROOT / "_data" / "repositories.yml"
OUT_PATH = REPO_ROOT / "_data" / "github_stats.json"

MAX_RETRIES = 4
BACKOFF_BASE = 2  # seconds: 2, 4, 8, 16


def get_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        print("Using authenticated requests")
    else:
        print("WARNING: No GITHUB_TOKEN — using unauthenticated (60 req/hr limit)")
    return headers


def fetch_json(url: str, headers: dict) -> dict | list | None:
    """GET JSON, retrying on network errors, rate limits, and 5xx responses.

    Returns None once retries are exhausted so callers can degrade gracefully
    (e.g. skip one repo) rather than crashing the whole run.
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException as e:
            if attempt == MAX_RETRIES:
                print(f"  Failed: {url} — {e}")
                return None
            wait = BACKOFF_BASE ** (attempt + 1)
            print(f"  Network error ({e}); retrying in {wait}s")
            time.sleep(wait)
            continue

        # GitHub signals rate limiting with 403/429 + a zero remaining header.
        rate_limited = resp.status_code in (429, 403) and \
            resp.headers.get("X-RateLimit-Remaining") == "0"
        if rate_limited or resp.status_code >= 500:
            if attempt == MAX_RETRIES:
                print(f"  Failed: {url} — HTTP {resp.status_code}")
                return None
            reset = resp.headers.get("X-RateLimit-Reset")
            wait = BACKOFF_BASE ** (attempt + 1)
            if rate_limited and reset and reset.isdigit():
                wait = max(wait, min(int(reset) - int(time.time()) + 1, 300))
            print(f"  HTTP {resp.status_code}; retrying in {wait}s")
            time.sleep(wait)
            continue

        try:
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"  Failed: {url} — {e}")
            return None
    return None


def get_featured_repos() -> list[str]:
    """Read featured repo slugs from _data/repositories.yml."""
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML not installed. Run: pip install pyyaml")
    data = yaml.safe_load(REPOS_PATH.read_text())
    return [r["repo"] for r in data.get("github_repos", [])]


def load_existing_stats() -> dict:
    if OUT_PATH.exists():
        try:
            return json.loads(OUT_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def main():
    headers = get_headers()
    existing = load_existing_stats()

    print(f"Fetching profile for {GITHUB_USER}...")
    profile = fetch_json(f"{API_BASE}/users/{GITHUB_USER}", headers)
    if not profile:
        # Don't clobber good data on a transient failure; leave the file as-is.
        print("Failed to fetch GitHub profile — keeping existing github_stats.json")
        return

    print("Fetching all repos for star count...")
    all_repos = []
    page = 1
    stars_ok = True
    while True:
        batch = fetch_json(
            f"{API_BASE}/users/{GITHUB_USER}/repos?per_page=100&page={page}",
            headers,
        )
        if batch is None:
            # A page failed: the star total would be undercounted, so mark it
            # unreliable and fall back to the last known value below.
            stars_ok = False
            break
        if not batch:
            break
        all_repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in all_repos)
    if not stars_ok and existing.get("total_stars"):
        print(f"  Star count incomplete — preserving previous total ({existing['total_stars']})")
        total_stars = existing["total_stars"]
    else:
        print(f"  {len(all_repos)} repos, {total_stars} total stars")

    featured = get_featured_repos()
    print(f"Fetching metadata for {len(featured)} featured repos...")
    existing_repos = existing.get("repos", {})
    repos = {}
    for slug in featured:
        data = fetch_json(f"{API_BASE}/repos/{slug}", headers)
        if data:
            repos[slug] = {
                "language": data.get("language"),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "description": data.get("description", ""),
            }
            print(f"  {slug}: {repos[slug]['language']}, "
                  f"{repos[slug]['stars']} stars, {repos[slug]['forks']} forks")
        elif slug in existing_repos:
            # Keep the last known metadata for this repo rather than dropping it.
            repos[slug] = existing_repos[slug]
            print(f"  {slug}: fetch failed — preserving previous data")

    stats = {
        "avatar_url": profile.get("avatar_url", ""),
        "name": profile.get("name", GITHUB_USER),
        "public_repos": profile.get("public_repos", 0),
        "followers": profile.get("followers", 0),
        "total_stars": total_stars,
        "repos": repos,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    OUT_PATH.write_text(json.dumps(stats, indent=2) + "\n")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
