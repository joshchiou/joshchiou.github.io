# Site Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul joshchiou.github.io across three workstreams — performance/asset optimization, automation/data pipelines, and discoverability/UX — to reduce page weight, automate stale data, and improve search/analytics.

**Architecture:** Three independent workstreams executed in priority order. Performance work eliminates dead assets and moves client-side API calls to build-time data. Automation work adds publication auto-discovery via ORCID/Semantic Scholar and fixes scholar stats reliability. Discoverability work enables site search, adds GoatCounter analytics, and improves SEO.

**Tech Stack:** Jekyll (Ruby), Python 3 scripts, GitHub Actions, ECharts, Liquid templates, GoatCounter analytics, ORCID API, Semantic Scholar API, GitHub REST API.

---

## File Map

**New files:**
- `scripts/update_github.py` — fetches GitHub profile + repo stats, writes JSON
- `scripts/update_publications.py` — ORCID + Semantic Scholar pub discovery, creates PRs
- `.github/workflows/update-github.yml` — weekly GitHub stats Action
- `.github/workflows/update-publications.yml` — weekly pub discovery Action
- `_data/github_stats.json` — build-time GitHub stats (generated)
- `_includes/scripts/goatcounter.liquid` — analytics partial
- `assets/data/strava_calendar.json` — externalized Strava heatmap data

**Modified files:**
- `_config.yml` — enable search, add GoatCounter config
- `_includes/head.liquid` — preconnect hints, inline theme init, GoatCounter include
- `_layouts/about.liquid` — dynamic journal pills from data
- `_layouts/bib.liquid` — ScholarlyArticle JSON-LD
- `_pages/code.md` — rewrite to use build-time GitHub data
- `_pages/cv.md` — add description frontmatter
- `_pages/about.md` — add description frontmatter
- `_pages/news.md` — add description frontmatter
- `_projects/fun_cycling.md` — fetch external data, loading skeletons, theme efficiency
- `_projects/fun_cats.md` — Swiper gallery with lazy loading
- `scripts/update_scholar.py` — reliability fix + dynamic journal pills
- `scripts/update_strava.py` — also write to `assets/data/`
- `assets/js/theme.js` — extract critical init to head, defer rest
- `.github/workflows/deploy.yml` — image optimization step + Lighthouse CI

**Deleted files:**
- `assets/img/prof_pic_color.png` (14MB, unreferenced)

---

## Task 1: Dead asset cleanup + preconnect hints + enable search

Quick wins: remove the 14MB unreferenced image, add preconnect hints, flip search on.

**Files:**
- Delete: `assets/img/prof_pic_color.png`
- Modify: `_includes/head.liquid:1-11`
- Modify: `_config.yml:51`

- [ ] **Step 1: Delete the unreferenced 14MB profile image**

```bash
rm assets/img/prof_pic_color.png
```

Verify it's not referenced:
```bash
grep -r "prof_pic_color" --include="*.md" --include="*.liquid" --include="*.yml" --include="*.html" .
```
Expected: no output.

- [ ] **Step 2: Add preconnect hints to head.liquid**

In `_includes/head.liquid`, insert after line 2 (`{% include metadata.liquid %}`) and before line 4 (`<!-- Bootstrap & MDB -->`):

```html
<!-- Preconnect to external origins -->
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

- [ ] **Step 3: Enable site search in _config.yml**

Change line 51 from:
```yaml
search_enabled: false
```
to:
```yaml
search_enabled: true
```

- [ ] **Step 4: Verify the build succeeds**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: "done" with no errors.

- [ ] **Step 5: Commit**

```bash
git add -A assets/img/prof_pic_color.png _includes/head.liquid _config.yml
git commit -m "perf: remove 14MB dead asset, add preconnect hints, enable search"
```

---

## Task 2: Scholar stats reliability fix + dynamic journal pills

Make `update_scholar.py` preserve last-known-good values on failure, add plausibility checks, and output per-journal counts for dynamic pills. Update `about.liquid` to render pills from data.

**Files:**
- Modify: `scripts/update_scholar.py`
- Modify: `_layouts/about.liquid:61-68`
- Modify: `_data/scholar_stats.json`

- [ ] **Step 1: Rewrite update_scholar.py with reliability + journal pills**

Replace the entire contents of `scripts/update_scholar.py` with:

```python
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


def count_bib_entries(bib_path: Path) -> tuple[int, list[dict]]:
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
```

- [ ] **Step 2: Run the script locally to regenerate scholar_stats.json**

```bash
python3 scripts/update_scholar.py
```

Expected: prints bib counts and journal breakdown, writes `_data/scholar_stats.json` with the new `top_journals` array. If Google Scholar times out, it preserves existing values.

- [ ] **Step 3: Verify scholar_stats.json has top_journals array**

```bash
python3 -c "import json; d=json.load(open('_data/scholar_stats.json')); print(json.dumps(d['top_journals'], indent=2))"
```

Expected output like:
```json
[
  {"name": "Nature", "count": 4},
  {"name": "Nature Genetics", "count": 3},
  {"name": "Cell", "count": 2}
]
```

- [ ] **Step 4: Update about.liquid to render dynamic journal pills**

In `_layouts/about.liquid`, replace lines 61-68 (the hardcoded journal pills block):

```liquid
        {% if stats.top_journal_papers > 0 %}
        <div class="about-journals">
          <span class="about-journals-count">{{ stats.top_journal_papers }} papers in</span>
          <span class="about-journal-pill">Nature</span>
          <span class="about-journal-pill">Cell</span>
          <span class="about-journal-pill">Nature Genetics</span>
        </div>
        {% endif %}
```

with:

```liquid
        {% if stats.top_journals.size > 0 %}
        <div class="about-journals">
          <span class="about-journals-count">{{ stats.top_journal_papers }} papers in</span>
          {% for journal in stats.top_journals %}
            <span class="about-journal-pill">{{ journal.name }}</span>
          {% endfor %}
        </div>
        {% endif %}
```

- [ ] **Step 5: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds, no errors.

- [ ] **Step 6: Commit**

```bash
git add scripts/update_scholar.py _data/scholar_stats.json _layouts/about.liquid
git commit -m "feat: scholar stats reliability + dynamic journal pills from papers.bib"
```

---

## Task 3: Build-time GitHub stats

New script and workflow to fetch GitHub data at build time. Rewrite the `/code` page to use `site.data.github_stats` instead of client-side API calls.

**Files:**
- Create: `scripts/update_github.py`
- Create: `.github/workflows/update-github.yml`
- Create: `_data/github_stats.json`
- Modify: `_pages/code.md:77-133`

- [ ] **Step 1: Create scripts/update_github.py**

```python
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
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Failed: {url} — {e}")
        return None


def get_featured_repos() -> list[str]:
    """Read featured repo slugs from _data/repositories.yml."""
    try:
        import yaml
    except ImportError:
        sys.exit("PyYAML not installed. Run: pip install pyyaml")
    data = yaml.safe_load(REPOS_PATH.read_text())
    return [r["repo"] for r in data.get("github_repos", [])]


def main():
    headers = get_headers()

    print(f"Fetching profile for {GITHUB_USER}...")
    profile = fetch_json(f"{API_BASE}/users/{GITHUB_USER}", headers)
    if not profile:
        sys.exit("Failed to fetch GitHub profile")

    print("Fetching all repos for star count...")
    all_repos = []
    page = 1
    while True:
        batch = fetch_json(
            f"{API_BASE}/users/{GITHUB_USER}/repos?per_page=100&page={page}",
            headers,
        )
        if not batch:
            break
        all_repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    total_stars = sum(r.get("stargazers_count", 0) for r in all_repos)
    print(f"  {len(all_repos)} repos, {total_stars} total stars")

    featured = get_featured_repos()
    print(f"Fetching metadata for {len(featured)} featured repos...")
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
```

- [ ] **Step 2: Run the script locally to generate initial data**

```bash
python3 scripts/update_github.py
```

Expected: writes `_data/github_stats.json` with profile and repo data. May warn about unauthenticated rate limits if no `GITHUB_TOKEN` is set.

- [ ] **Step 3: Verify github_stats.json was created**

```bash
python3 -c "import json; d=json.load(open('_data/github_stats.json')); print(d['name'], d['total_stars'], 'stars', len(d['repos']), 'featured repos')"
```

Expected: something like `Josh Chiou 12 stars 3 featured repos`

- [ ] **Step 4: Create .github/workflows/update-github.yml**

```yaml
name: Update GitHub Stats

on:
  schedule:
    - cron: "41 8 * * 2" # Every Tuesday 08:41 UTC
  workflow_dispatch:

jobs:
  update-github:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install requests pyyaml

      - name: Fetch and update GitHub stats
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/update_github.py

      - name: Commit updated data files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add _data/github_stats.json
          git diff --staged --quiet || git commit -m "chore: update GitHub stats [skip ci]"
          git push
```

- [ ] **Step 5: Rewrite _pages/code.md to use build-time data**

Replace the entire `<script>` block (lines 76-133 in `_pages/code.md`) and update the profile card HTML to use Liquid data. The full replacement for `_pages/code.md`:

```markdown
---
layout: page
permalink: /code/
title: code
nav: true
nav_order: 4
description: >
  A slice of my public coding activity. Most production work lives in enterprise GitHub organizations
  (Pfizer, Lilly) and isn't reflected here.
---

{% assign gh = site.data.github_stats %}

<div class="github-profile-card mb-5" id="github-profile-card">
  <div class="github-profile-inner-d">
    <div class="github-profile-left">
      <a href="https://github.com/joshchiou" target="_blank" rel="noopener noreferrer"
         class="github-profile-identity">
        {% if gh.avatar_url %}
          <img src="{{ gh.avatar_url }}" alt="GitHub avatar" class="github-avatar">
        {% else %}
          <img src="" alt="GitHub avatar" class="github-avatar" style="display:none">
        {% endif %}
        <div>
          <div class="github-profile-name">{{ gh.name | default: "Josh Chiou" }}</div>
          <div class="github-profile-login">@joshchiou</div>
        </div>
      </a>
    </div>
    <div class="github-profile-right-d">
      <div class="github-profile-stats">
        <div class="gh-stat"><span class="gh-stat-val">{{ gh.public_repos | default: "—" }}</span><span class="gh-stat-label">repos</span></div>
        <div class="gh-stat"><span class="gh-stat-val">{{ gh.total_stars | default: "—" }}</span><span class="gh-stat-label">stars</span></div>
        <div class="gh-stat"><span class="gh-stat-val">{{ gh.followers | default: "—" }}</span><span class="gh-stat-label">followers</span></div>
      </div>
      <div class="gh-stat-divider"></div>
      <div class="github-profile-orgs-d">
        <div class="github-profile-orgs-icons">
          <a href="https://github.com/EliLillyCo" target="_blank" rel="noopener noreferrer" title="Eli Lilly & Company">
            <img src="https://avatars.githubusercontent.com/u/16001067?v=4&s=40" alt="Eli Lilly">
          </a>
          <a href="https://github.com/conda-forge" target="_blank" rel="noopener noreferrer" title="conda-forge">
            <img src="https://avatars.githubusercontent.com/u/11897326?v=4&s=40" alt="conda-forge">
          </a>
          <a href="https://github.com/noobies-tennis" target="_blank" rel="noopener noreferrer" title="Noobies Tennis">
            <img src="https://avatars.githubusercontent.com/u/97570579?v=4&s=40" alt="Noobies Tennis">
          </a>
        </div>
        <span class="github-profile-orgs-label">organizations</span>
      </div>
    </div>
  </div>
</div>

## Featured repositories

Repositories I've built or contributed to significantly.

{% assign LANG_COLORS = "Python:#3572A5,R:#198CE7,JavaScript:#f1e05a,TypeScript:#2b7489,Shell:#89e051,Ruby:#701516,HTML:#e34c26,CSS:#563d7c" | split: "," %}

<div class="repo-card-grid mb-4">
  {% for item in site.data.repositories.github_repos %}
    {% assign repo = item.repo %}
    {% assign repo_parts = repo | split: '/' %}
    {% assign owner = repo_parts[0] %}
    {% assign rname = repo_parts[1] %}
    {% assign repo_data = gh.repos[repo] %}
    <a class="repo-card" href="https://github.com/{{ repo }}" target="_blank" rel="noopener noreferrer">
      <div class="repo-card-header">
        <i class="fa-regular fa-book"></i>
        <span class="repo-card-name">
          {% if site.data.repositories.github_users contains owner %}{{ rname }}{% else %}{{ repo }}{% endif %}
        </span>
      </div>
      <div class="repo-card-desc">{{ item.desc }}</div>
      <div class="repo-card-meta">
        {% if repo_data.language %}
          {% assign lang_color = "#8a8a8a" %}
          {% for pair in LANG_COLORS %}
            {% assign kv = pair | split: ":" %}
            {% if kv[0] == repo_data.language %}
              {% assign lang_color = kv[1] %}
            {% endif %}
          {% endfor %}
          <span class="repo-card-lang">
            <span class="lang-dot" style="background:{{ lang_color }}"></span>
            {{ repo_data.language }}
          </span>
        {% endif %}
        {% if repo_data.stars > 0 %}
          <span class="repo-card-stat"><i class="fa-regular fa-star"></i> {{ repo_data.stars }}</span>
        {% endif %}
        {% if repo_data.forks > 0 %}
          <span class="repo-card-stat"><i class="fa-solid fa-code-fork"></i> {{ repo_data.forks }}</span>
        {% endif %}
      </div>
    </a>
  {% endfor %}
</div>

---

## Open-source contributions

Selected merged pull requests to community scientific software.

<ul class="list-unstyled">
  {% for c in site.data.contributions %}
  <li class="mb-4 contribution-item">
    <div class="mb-1">
      <strong>{{ c.pr_title }}</strong>
      &nbsp;&middot;&nbsp;
      <a href="{{ c.url }}" target="_blank" rel="noopener noreferrer">{{ c.repo }}</a>
      &nbsp;&middot;&nbsp;
      <span class="text-muted small">{{ c.date }}</span>
    </div>
    <div class="mb-1">
      {% if c.type %}
        {% if c.type == "bug fix" %}{% assign tc = "badge-bug" %}
        {% elsif c.type == "performance" %}{% assign tc = "badge-perf" %}
        {% elsif c.type == "feature" %}{% assign tc = "badge-feature" %}
        {% elsif c.type == "packaging" %}{% assign tc = "badge-pkg" %}
        {% elsif c.type == "compatibility" %}{% assign tc = "badge-compat" %}
        {% else %}{% assign tc = "badge-compat" %}{% endif %}
        <span class="badge-type {{ tc }}">{{ c.type }}</span>
      {% endif %}
      {% if c.language %}<span class="badge-type badge-lang">{{ c.language }}</span>{% endif %}
    </div>
    <div class="mb-1">
      <small class="text-muted">{{ c.blurb }}</small>
    </div>
    <a class="pr-link" href="{{ c.pr_url }}" target="_blank" rel="noopener noreferrer">
      <i class="fa-solid fa-code-pull-request"></i> View pull request
    </a>
  </li>
  {% endfor %}
</ul>

<div class="mt-3">
  <a href="https://github.com/search?q=author%3Ajoshchiou+is%3Apr+is%3Amerged&type=pullrequests"
     target="_blank" rel="noopener noreferrer">See all merged pull requests &rarr;</a>
</div>
```

- [ ] **Step 6: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds. The `/code` page renders GitHub stats from data file with zero `<script>` blocks.

- [ ] **Step 7: Commit**

```bash
git add scripts/update_github.py .github/workflows/update-github.yml _data/github_stats.json _pages/code.md
git commit -m "feat: build-time GitHub stats — eliminate client-side API calls on /code"
```

---

## Task 4: Image optimization (cat gallery + CI step)

Run `prep_images.py` on cat photos, add CI safety net in deploy.yml.

**Files:**
- Modify: `assets/img/projects/fun/cats/` (new WebP files)
- Modify: `.github/workflows/deploy.yml:47-54`

- [ ] **Step 1: Run prep_images.py on cat gallery images**

```bash
python3 scripts/prep_images.py assets/img/projects/fun/cats/ assets/img/projects/fun/cats/ --keep-names
```

Expected: converts 6 JPEGs to WebP, prints size savings (likely 70-80% reduction from 15MB total).

- [ ] **Step 2: Verify WebP files were created**

```bash
ls -lh assets/img/projects/fun/cats/*.webp
```

Expected: 6 `.webp` files, each much smaller than the original JPEGs.

- [ ] **Step 3: Add image optimization safety net to deploy.yml**

In `.github/workflows/deploy.yml`, add a new step after "Setup Python" (after line 46) and before "Install and Build" (line 47):

```yaml
      - name: Optimize unprocessed images 🖼️
        run: |
          pip3 install Pillow
          find assets/img -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) -size +500k | while read img; do
            webp="${img%.*}.webp"
            if [ ! -f "$webp" ]; then
              echo "Optimizing: $img"
              python3 scripts/prep_images.py "$(dirname "$img")" "$(dirname "$img")" --keep-names
            fi
          done
```

- [ ] **Step 4: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git add assets/img/projects/fun/cats/*.webp .github/workflows/deploy.yml
git commit -m "perf: optimize cat gallery images to WebP + add CI image safety net"
```

---

## Task 5: GoatCounter analytics

Add GoatCounter integration behind a config flag.

**Files:**
- Create: `_includes/scripts/goatcounter.liquid`
- Modify: `_config.yml:348-350`
- Modify: `_includes/head.liquid` (end of file)

- [ ] **Step 1: Create the GoatCounter partial**

Create `_includes/scripts/goatcounter.liquid`:

```html
{% if site.enable_goatcounter and site.goatcounter_code %}
  <script data-goatcounter="https://{{ site.goatcounter_code }}.goatcounter.com/count"
          async src="//gc.zgo.at/count.js"></script>
{% endif %}
```

- [ ] **Step 2: Add GoatCounter config to _config.yml**

After line 350 (`enable_pirsch_analytics: false`), add:

```yaml
enable_goatcounter: false # enables GoatCounter analytics (https://goatcounter.com/)
goatcounter_code: # your GoatCounter site code (the subdomain part of yourcode.goatcounter.com)
```

- [ ] **Step 3: Include the partial in head.liquid**

At the end of `_includes/head.liquid`, just before the closing line, add:

```liquid
{% include scripts/goatcounter.liquid %}
```

- [ ] **Step 4: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds. Since `enable_goatcounter` is false, no script tag is emitted.

- [ ] **Step 5: Commit**

```bash
git add _includes/scripts/goatcounter.liquid _config.yml _includes/head.liquid
git commit -m "feat: add GoatCounter analytics integration (disabled by default)"
```

> **Note:** To activate, sign up at goatcounter.com, get your site code, then set `enable_goatcounter: true` and `goatcounter_code: yourcode` in `_config.yml`.

---

## Task 6: Strava data externalization

Move calendar heatmap data from inline Liquid to an external JSON file loaded via fetch. Add loading skeleton.

**Files:**
- Modify: `scripts/update_strava.py:96-121`
- Create: `assets/data/strava_calendar.json`
- Modify: `_projects/fun_cycling.md:87-95`

- [ ] **Step 1: Update update_strava.py to also write external calendar file**

In `scripts/update_strava.py`, add after line 30 (`REPO_ROOT = Path(__file__).parent.parent`):

```python
ASSETS_DATA_DIR = REPO_ROOT / "assets" / "data"
```

Then in the `main()` function, after line 121 (`write_json(data_dir / "strava_stats.json", stats)`), add:

```python
    ASSETS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_json(ASSETS_DATA_DIR / "strava_calendar.json", calendar_data)
```

- [ ] **Step 2: Generate the initial external calendar file**

Since we can't call the Strava API without tokens, copy the existing data:

```bash
mkdir -p assets/data
cp _data/strava_calendar.json assets/data/strava_calendar.json
```

- [ ] **Step 3: Update cycling page to fetch external data**

In `_projects/fun_cycling.md`, replace lines 87-95 (the beginning of the `<script>` block that inlines data):

```javascript
<script>
(function () {
  var KM_TO_MI = 0.621371;

  var rawCalendar = {{ site.data.strava_calendar | jsonify }};
  var calendarMiles = rawCalendar.map(function (d) {
    return [d[0], Math.round(d[1] * KM_TO_MI * 10) / 10];
  });
  var maxMiles = Math.ceil(Math.max.apply(null, calendarMiles.map(function (d) { return d[1]; })) / 10) * 10;
```

with:

```javascript
<script>
(function () {
  var KM_TO_MI = 0.621371;

  var monthlyRaw = {{ site.data.strava_stats.monthly | jsonify }};
```

Then wrap the calendar-dependent code in a fetch call. Replace the full `<script>` block (lines 87 to the closing `</script>` on line 335) with the version that:
- Fetches `assets/data/strava_calendar.json` via `fetch()`
- Shows a loading skeleton on the calendar div while loading
- Keeps monthly/cumulative data inlined (small, static)
- Initializes calendar chart only after fetch completes

The full replacement `<script>` block:

```javascript
<script>
(function () {
  var KM_TO_MI = 0.621371;

  // Monthly and cumulative data are small — keep inlined
  var monthlyRaw = {{ site.data.strava_stats.monthly | jsonify }};
  var months = monthlyRaw.map(function (m) { return m.month; });
  var distMiles = monthlyRaw.map(function (m) {
    return Math.round(m.distance_km * KM_TO_MI * 10) / 10;
  });

  var byYear = {};
  monthlyRaw.forEach(function (m) {
    var parts = m.month.split('-');
    var year = parts[0];
    var monthIdx = parseInt(parts[1], 10) - 1;
    if (!byYear[year]) byYear[year] = new Array(12).fill(0);
    byYear[year][monthIdx] = Math.round(m.distance_km * KM_TO_MI * 10) / 10;
  });
  var years = Object.keys(byYear).sort();
  var monthLabels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var yearColors = ['#2980b9', '#e67e22', '#27ae60', '#8e44ad', '#e74c3c'];

  var cumMonths = [];
  var cumValues = [];
  var running = 0;
  distMiles.forEach(function (val, i) {
    running += val;
    cumMonths.push(months[i]);
    cumValues.push(Math.round(running * 10) / 10);
  });

  var calChart, barChart, cumChart;
  var calendarMiles = null;
  var maxMiles = 0;
  var currentView = 'alltime';

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  // Fetch calendar data externally (keeps page HTML lean)
  var calEl = document.getElementById('cycling-calendar');
  if (calEl) {
    calEl.innerHTML = '<div style="height:155px;display:flex;align-items:center;justify-content:center"><small class="text-muted">Loading activity data&hellip;</small></div>';
  }
  fetch('{{ "/assets/data/strava_calendar.json" | relative_url }}')
    .then(function (r) { return r.json(); })
    .then(function (rawCalendar) {
      calendarMiles = rawCalendar.map(function (d) {
        return [d[0], Math.round(d[1] * KM_TO_MI * 10) / 10];
      });
      maxMiles = Math.ceil(Math.max.apply(null, calendarMiles.map(function (d) { return d[1]; })) / 10) * 10;
      initCalChart();
    })
    .catch(function () {
      if (calEl) calEl.innerHTML = '<small class="text-muted">Activity data unavailable.</small>';
    });

  function buildCalOption() {
    if (!calendarMiles) return {};
    var mobile = window.innerWidth < 576;
    var dark = isDark();
    var textColor   = dark ? '#c8c8c8' : '#333333';
    var emptyColor  = dark ? '#1e3a4a' : '#e8f4f8';
    var borderColor = dark ? '#2d2d2d' : '#ffffff';
    return {
      tooltip: {
        formatter: function (p) { return p.data[0] + '<br/>' + p.data[1] + ' mi'; }
      },
      visualMap: {
        min: 0, max: maxMiles, show: true,
        orient: 'horizontal',
        left: mobile ? 'center' : 'right',
        bottom: 0,
        itemWidth: 10, itemHeight: 70,
        text: ['more', 'less'],
        textStyle: { fontSize: 10, color: textColor },
        inRange: { color: [emptyColor, '#74add1', '#2980b9'] }
      },
      calendar: {
        range: ['{{ "now" | date: "%Y" }}-01-01', '{{ "now" | date: "%Y-%m-%d" }}'],
        cellSize: ['auto', mobile ? 13 : 16],
        top: 20,
        left: mobile ? 30 : 40,
        right: mobile ? 10 : 115,
        bottom: mobile ? 50 : 30,
        itemStyle: { borderWidth: 2, borderColor: borderColor },
        yearLabel: { show: false },
        monthLabel: { fontSize: 11, color: textColor },
        dayLabel: { nameMap: ['S', 'M', 'T', 'W', 'T', 'F', 'S'], color: textColor }
      },
      series: [{ type: 'heatmap', coordinateSystem: 'calendar', data: calendarMiles }]
    };
  }

  function buildBarOption() {
    var dark = isDark();
    var textColor  = dark ? '#c8c8c8' : '#333333';
    var splitColor = dark ? 'rgba(200,200,200,0.15)' : 'rgba(0,0,0,0.1)';

    if (currentView === 'byyear') {
      return {
        tooltip: {
          trigger: 'axis',
          formatter: function (params) {
            var lines = params.map(function (p) {
              return '<span style="color:' + p.color + '">●</span> ' + p.seriesName + ': ' + p.value + ' mi';
            });
            return params[0].name + '<br/>' + lines.join('<br/>');
          }
        },
        legend: {
          data: years,
          textStyle: { color: textColor, fontSize: 11 },
          top: 0
        },
        grid: { left: 55, right: 20, top: 35, bottom: 30 },
        xAxis: {
          type: 'category', data: monthLabels,
          axisLabel: { fontSize: 11, color: textColor },
          axisLine:  { lineStyle: { color: textColor } },
          axisTick:  { lineStyle: { color: textColor } }
        },
        yAxis: {
          type: 'value', name: 'miles',
          nameTextStyle: { fontSize: 11, color: textColor },
          axisLabel: { color: textColor },
          splitLine: { lineStyle: { type: 'dashed', color: splitColor } }
        },
        series: years.map(function (year, i) {
          return {
            name: year, type: 'line', data: byYear[year],
            smooth: true, symbol: 'circle', symbolSize: 6,
            lineStyle: { width: 2.5 },
            itemStyle: { color: yearColors[i % yearColors.length] }
          };
        })
      };
    }

    return {
      tooltip: {
        trigger: 'axis',
        formatter: function (params) { return params[0].name + '<br/>' + params[0].value + ' mi'; }
      },
      grid: { left: 55, right: 20, top: 15, bottom: 65 },
      xAxis: {
        type: 'category', data: months,
        axisLabel: { rotate: 45, interval: 0, fontSize: 11, color: textColor },
        axisLine:  { lineStyle: { color: textColor } },
        axisTick:  { lineStyle: { color: textColor } }
      },
      yAxis: {
        type: 'value', name: 'miles',
        nameTextStyle: { fontSize: 11, color: textColor },
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { type: 'dashed', color: splitColor } }
      },
      series: [{
        type: 'bar', data: distMiles,
        itemStyle: { color: '#2980b9', borderRadius: [3, 3, 0, 0] },
        emphasis: { itemStyle: { color: '#1a5f8a' } }
      }]
    };
  }

  function buildCumOption() {
    var dark = isDark();
    var textColor  = dark ? '#c8c8c8' : '#333333';
    var splitColor = dark ? 'rgba(200,200,200,0.15)' : 'rgba(0,0,0,0.1)';
    return {
      tooltip: {
        trigger: 'axis',
        formatter: function (params) { return params[0].name + '<br/>' + params[0].value + ' mi total'; }
      },
      grid: { left: 55, right: 20, top: 15, bottom: 65 },
      xAxis: {
        type: 'category', data: cumMonths,
        axisLabel: { rotate: 45, interval: 0, fontSize: 11, color: textColor },
        axisLine:  { lineStyle: { color: textColor } },
        axisTick:  { lineStyle: { color: textColor } }
      },
      yAxis: {
        type: 'value', name: 'miles',
        nameTextStyle: { fontSize: 11, color: textColor },
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { type: 'dashed', color: splitColor } }
      },
      series: [{
        type: 'line', data: cumValues,
        smooth: true,
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
          { offset: 0, color: 'rgba(41,128,185,0.35)' },
          { offset: 1, color: 'rgba(41,128,185,0.05)' }
        ]}},
        lineStyle: { color: '#2980b9', width: 2.5 },
        itemStyle: { color: '#2980b9' },
        symbol: 'circle', symbolSize: 5
      }]
    };
  }

  function initCalChart() {
    var calEl = document.getElementById('cycling-calendar');
    if (calEl && window.echarts && calendarMiles) {
      if (calChart) { echarts.dispose(calEl); }
      var mobile = window.innerWidth < 576;
      calEl.style.height = (mobile ? 180 : 155) + 'px';
      calEl.innerHTML = '';
      calChart = echarts.init(calEl);
      calChart.setOption(buildCalOption());
    }
  }

  function initOtherCharts() {
    var barEl = document.getElementById('cycling-monthly');
    if (barEl && window.echarts) {
      if (barChart) { echarts.dispose(barEl); }
      barChart = echarts.init(barEl);
      barChart.setOption(buildBarOption());
    }
    var cumEl = document.getElementById('cycling-cumulative');
    if (cumEl && window.echarts) {
      if (cumChart) { echarts.dispose(cumEl); }
      cumChart = echarts.init(cumEl);
      cumChart.setOption(buildCumOption());
    }
  }

  function initAllCharts() {
    initCalChart();
    initOtherCharts();
  }

  document.querySelectorAll('.chart-toggle-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.chart-toggle-btn').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      currentView = btn.getAttribute('data-view');
      var barEl = document.getElementById('cycling-monthly');
      if (barEl && window.echarts) {
        if (barChart) { echarts.dispose(barEl); }
        barChart = echarts.init(barEl);
        barChart.setOption(buildBarOption());
      }
    });
  });

  window.addEventListener('resize', function () {
    if (calChart) {
      var calEl = document.getElementById('cycling-calendar');
      var mobile = window.innerWidth < 576;
      calEl.style.height = (mobile ? 180 : 155) + 'px';
      calChart.resize();
      calChart.setOption(buildCalOption());
    }
    if (barChart) { barChart.resize(); }
    if (cumChart) { cumChart.resize(); }
  });

  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-theme') { initAllCharts(); }
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  if (document.readyState === 'complete') { initOtherCharts(); }
  else { window.addEventListener('load', initOtherCharts); }
})();
</script>
```

- [ ] **Step 4: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds. The cycling page HTML no longer contains the full calendar JSON array inline.

- [ ] **Step 5: Verify calendar data is NOT inlined**

```bash
grep -c "strava_calendar" _site/projects/fun_cycling/index.html
```
Expected: 0 (no inline data reference) or only the fetch URL.

- [ ] **Step 6: Commit**

```bash
git add scripts/update_strava.py assets/data/strava_calendar.json _projects/fun_cycling.md
git commit -m "perf: externalize Strava calendar data — load via fetch instead of inline"
```

---

## Task 7: Theme.js refactor (inline critical, defer rest)

Extract the critical anti-flicker code into an inline script in head.liquid. Move everything else to a deferred script.

**Files:**
- Modify: `_includes/head.liquid:72-84`
- Modify: `assets/js/theme.js`

- [ ] **Step 1: Replace the theme.js script tag and initTheme call in head.liquid**

In `_includes/head.liquid`, replace lines 72-84:

```html
<!-- Dark Mode -->
<script src="{{ '/assets/js/theme.js' | relative_url | bust_file_cache }}"></script>
{% if site.enable_darkmode %}
  <link
    defer
    rel="stylesheet"
    href="{{ '/assets/css/jekyll-pygments-themes-native.css' | relative_url | bust_file_cache }}"
    media="none"
    id="highlight_theme_dark"
  >
  <script>
    initTheme();
  </script>
{% endif %}
```

with:

```html
<!-- Dark Mode: inline critical anti-flicker, defer the rest -->
{% if site.enable_darkmode %}
  <script>
    (function(){
      var ts = localStorage.getItem("theme");
      if (ts !== "dark" && ts !== "light" && ts !== "system") ts = "system";
      document.documentElement.setAttribute("data-theme-setting", ts);
      var theme;
      if (ts === "system") {
        theme = (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) ? "dark" : "light";
      } else {
        theme = ts;
      }
      document.documentElement.setAttribute("data-theme", theme);
    })();
  </script>
  <link
    defer
    rel="stylesheet"
    href="{{ '/assets/css/jekyll-pygments-themes-native.css' | relative_url | bust_file_cache }}"
    media="none"
    id="highlight_theme_dark"
  >
{% endif %}
<script defer src="{{ '/assets/js/theme.js' | relative_url | bust_file_cache }}"></script>
```

- [ ] **Step 2: Update theme.js to self-initialize when deferred**

Add at the very end of `assets/js/theme.js` (after line 252), so it runs when the deferred script loads:

```javascript

// Self-initialize when loaded as deferred script
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", function () { initTheme(); });
} else {
  initTheme();
}
```

And remove the `setThemeSetting(themeSetting)` call from `initTheme()` (line 237) since the inline script already set the attributes. Replace `initTheme` (lines 234-252):

```javascript
let initTheme = () => {
  // Attributes already set by inline script in <head>.
  // Apply component-level theming now that DOM is ready.
  applyTheme();

  const mode_toggle = document.getElementById("light-toggle");
  if (mode_toggle) {
    mode_toggle.addEventListener("click", function () {
      toggleThemeSetting();
    });
  }

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", ({ matches }) => {
    applyTheme();
  });
};
```

- [ ] **Step 3: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds.

- [ ] **Step 4: Verify the inline script is in head and theme.js is deferred**

```bash
grep -n "data-theme-setting" _site/index.html | head -3
grep -n "defer.*theme.js" _site/index.html | head -3
```
Expected: inline `data-theme-setting` script in head, `<script defer src="...theme.js">` later.

- [ ] **Step 5: Commit**

```bash
git add _includes/head.liquid assets/js/theme.js
git commit -m "perf: inline critical theme init, defer rest of theme.js"
```

---

## Task 8: Publication auto-discovery via ORCID + Semantic Scholar

New script that discovers publications from ORCID, fetches metadata from Semantic Scholar, and creates PRs with draft BibTeX entries.

**Files:**
- Create: `scripts/update_publications.py`
- Create: `.github/workflows/update-publications.yml`

- [ ] **Step 1: Create scripts/update_publications.py**

```python
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
```

- [ ] **Step 2: Test the script in dry-run mode**

```bash
pip install requests 2>/dev/null; python3 scripts/update_publications.py
```

Expected: fetches ORCID works, compares against papers.bib, prints any new DOIs found. Does NOT modify files or create PRs.

- [ ] **Step 3: Create .github/workflows/update-publications.yml**

```yaml
name: Discover New Publications

on:
  schedule:
    - cron: "17 9 * * 4" # Every Thursday 09:17 UTC
  workflow_dispatch:

jobs:
  discover-publications:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install requests

      - name: Discover and propose new publications
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/update_publications.py --pr
```

- [ ] **Step 4: Commit**

```bash
git add scripts/update_publications.py .github/workflows/update-publications.yml
git commit -m "feat: auto-discover publications via ORCID + Semantic Scholar, create draft PRs"
```

---

## Task 9: SEO improvements (meta descriptions + ScholarlyArticle structured data)

Add missing page descriptions and ScholarlyArticle JSON-LD to publication entries.

**Files:**
- Modify: `_pages/about.md` (frontmatter)
- Modify: `_pages/cv.md` (frontmatter)
- Modify: `_pages/news.md` (frontmatter)
- Modify: `_layouts/bib.liquid`

- [ ] **Step 1: Add description frontmatter to pages that lack it**

In `_pages/about.md`, add to the frontmatter:

```yaml
description: >
  Joshua Chiou — Senior Advisor, Genomics at Lilly. Translating proteomics
  and human genetics into clinical insights for cardiometabolic and obesity programs.
```

In `_pages/cv.md`, add to the frontmatter:

```yaml
description: >
  Curriculum vitae of Joshua Chiou — experience, education, publications,
  and skills in computational genetics and proteomics.
```

In `_pages/news.md`, add to the frontmatter:

```yaml
description: >
  Recent news and career updates from Joshua Chiou.
```

- [ ] **Step 2: Add ScholarlyArticle JSON-LD to bib.liquid**

At the very end of `_layouts/bib.liquid`, just before the closing `</div>` of the outermost row div, add:

```liquid
  {% if site.serve_schema_org and entry.doi %}
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "ScholarlyArticle",
      "headline": {{ entry.title | jsonify }},
      "datePublished": "{{ entry.year }}",
      {% if entry.journal %}"isPartOf": {"@type": "Periodical", "name": {{ entry.journal | jsonify }}},{% endif %}
      "identifier": {"@type": "PropertyValue", "propertyID": "DOI", "value": "{{ entry.doi }}"},
      "url": "https://doi.org/{{ entry.doi }}"
    }
    </script>
  {% endif %}
```

- [ ] **Step 3: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds.

- [ ] **Step 4: Verify JSON-LD appears in publication pages**

```bash
grep -c "ScholarlyArticle" _site/publications/index.html
```
Expected: a count matching the number of publications with DOIs.

- [ ] **Step 5: Commit**

```bash
git add _pages/about.md _pages/cv.md _pages/news.md _layouts/bib.liquid
git commit -m "seo: add page descriptions + ScholarlyArticle structured data for publications"
```

---

## Task 10: Lighthouse CI audit

Add Lighthouse CI to the deploy pipeline.

**Files:**
- Modify: `.github/workflows/deploy.yml`

- [ ] **Step 1: Add Lighthouse CI step to deploy.yml**

In `.github/workflows/deploy.yml`, add after the "Purge unused CSS" step (after line 58) and before "Upload Pages artifact":

```yaml
      - name: Lighthouse CI audit 🔦
        uses: treosh/lighthouse-ci-action@v12
        with:
          urls: |
            _site/index.html
            _site/publications/index.html
          uploadArtifacts: true
          configJson: |
            {
              "ci": {
                "assert": {
                  "assertions": {
                    "categories:performance": ["warn", {"minScore": 0.8}],
                    "categories:accessibility": ["warn", {"minScore": 0.95}],
                    "categories:best-practices": ["warn", {"minScore": 0.9}],
                    "categories:seo": ["warn", {"minScore": 0.9}]
                  }
                }
              }
            }
```

Note: uses `warn` (not `error`) so it reports but doesn't block deploy initially.

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add Lighthouse CI audit to deploy pipeline (assertion mode)"
```

---

## Task 11: Cycling page polish (error handling + loading states)

Add graceful handling when Strava data is missing.

**Files:**
- Modify: `_projects/fun_cycling.md:12-68`

- [ ] **Step 1: Add data-missing guard to the stats section**

In `_projects/fun_cycling.md`, wrap the stats section (lines 53-68) with a Liquid guard. Replace:

```markdown
### Stats

<div class="row mb-4 text-center">
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_rides | default: "—" }}</h3>
    <small class="text-muted">rides</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_miles | default: "—" }}</h3>
    <small class="text-muted">miles</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_ft | default: "—" }}</h3>
    <small class="text-muted">ft elevation</small>
  </div>
</div>
```

with:

```markdown
### Stats

{% if stats.total_rides %}
<div class="row mb-4 text-center">
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_rides }}</h3>
    <small class="text-muted">rides</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_miles }}</h3>
    <small class="text-muted">miles</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_ft }}</h3>
    <small class="text-muted">ft elevation</small>
  </div>
</div>
{% else %}
<p class="text-muted">Stats updating — check back soon.</p>
{% endif %}
```

- [ ] **Step 2: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add _projects/fun_cycling.md
git commit -m "ux: add graceful fallback when Strava data is missing on cycling page"
```

---

## Task 12: Cat gallery buildout (lazy loading + Swiper)

Upgrade the cat gallery from a basic Bootstrap grid to a Swiper gallery with lazy loading.

**Files:**
- Modify: `_projects/fun_cats.md`

- [ ] **Step 1: Rewrite fun_cats.md with Swiper gallery**

Replace the entire contents of `_projects/fun_cats.md` with:

```markdown
---
layout: page
title: Claire
description: The real senior scientist in the family.
img: assets/img/projects/fun/cats/claire-main.webp
importance: 4
category: fun
swiper: true
---

{% include figure.liquid loading="eager" path="assets/img/projects/fun/cats/claire-main.webp" class="img-fluid rounded z-depth-1 mb-3" alt="Claire" %}

<div class="swiper mySwiper mt-3">
  <div class="swiper-wrapper">
    {% for i in (1..5) %}
    <div class="swiper-slide">
      {% capture img_path %}assets/img/projects/fun/cats/claire-gallery-{{ i }}.webp{% endcapture %}
      {% include figure.liquid loading="lazy" path=img_path class="img-fluid rounded z-depth-1" alt="Claire" zoomable=true %}
    </div>
    {% endfor %}
  </div>
  <div class="swiper-pagination"></div>
  <div class="swiper-button-prev"></div>
  <div class="swiper-button-next"></div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function () {
  new Swiper('.mySwiper', {
    slidesPerView: 1,
    spaceBetween: 16,
    loop: true,
    pagination: { el: '.swiper-pagination', clickable: true },
    navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
    breakpoints: {
      576: { slidesPerView: 2 },
      992: { slidesPerView: 3 }
    }
  });
});
</script>
```

Note: This uses `webp` paths — the WebP files were generated in Task 4. If Task 4 hasn't run yet, keep `.jpg` paths. Also note that al-folio includes Swiper via CDN when `swiper: true` is set in frontmatter (check `_includes/scripts/` for Swiper include).

- [ ] **Step 2: Verify Swiper is available in the template**

```bash
grep -r "swiper" _includes/ --include="*.liquid" -l
```

Expected: at least one include file that loads Swiper CSS/JS when the page has `swiper: true`. If not found, add Swiper CSS/JS includes manually.

- [ ] **Step 3: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add _projects/fun_cats.md
git commit -m "ux: upgrade cat gallery to Swiper carousel with lazy loading"
```

---

## Task 13: Contributions page polish (group by year)

Group open-source contributions by year in the `/code` page.

**Files:**
- Modify: `_pages/code.md` (contributions section)

- [ ] **Step 1: Replace the contributions list with year-grouped version**

In `_pages/code.md`, replace the contributions `<ul>` block (everything from `<ul class="list-unstyled">` to the closing `</ul>`) with:

```liquid
{% assign sorted_contribs = site.data.contributions | sort: "date" | reverse %}
{% assign current_year = "" %}
<ul class="list-unstyled">
  {% for c in sorted_contribs %}
    {% assign c_year = c.date | date: "%Y" %}
    {% if c_year != current_year %}
      {% assign current_year = c_year %}
      <li class="mt-4 mb-2"><h4 class="text-muted">{{ current_year }}</h4></li>
    {% endif %}
    <li class="mb-4 contribution-item">
      <div class="mb-1">
        <strong>{{ c.pr_title }}</strong>
        &nbsp;&middot;&nbsp;
        <a href="{{ c.url }}" target="_blank" rel="noopener noreferrer">{{ c.repo }}</a>
        &nbsp;&middot;&nbsp;
        <span class="text-muted small">{{ c.date }}</span>
      </div>
      <div class="mb-1">
        {% if c.type %}
          {% if c.type == "bug fix" %}{% assign tc = "badge-bug" %}
          {% elsif c.type == "performance" %}{% assign tc = "badge-perf" %}
          {% elsif c.type == "feature" %}{% assign tc = "badge-feature" %}
          {% elsif c.type == "packaging" %}{% assign tc = "badge-pkg" %}
          {% elsif c.type == "compatibility" %}{% assign tc = "badge-compat" %}
          {% else %}{% assign tc = "badge-compat" %}{% endif %}
          <span class="badge-type {{ tc }}">{{ c.type }}</span>
        {% endif %}
        {% if c.language %}<span class="badge-type badge-lang">{{ c.language }}</span>{% endif %}
      </div>
      <div class="mb-1">
        <small class="text-muted">{{ c.blurb }}</small>
      </div>
      <a class="pr-link" href="{{ c.pr_url }}" target="_blank" rel="noopener noreferrer">
        <i class="fa-solid fa-code-pull-request"></i> View pull request
      </a>
    </li>
  {% endfor %}
</ul>
```

- [ ] **Step 2: Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```
Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add _pages/code.md
git commit -m "ux: group open-source contributions by year on /code page"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] 1a Dead asset cleanup → Task 1 Step 1
- [x] 1b Image optimization → Task 4
- [x] 1c Build-time GitHub stats → Task 3
- [x] 1d Preconnect hints → Task 1 Step 2
- [x] 1e Strava externalization → Task 6
- [x] 1f Theme.js refactor → Task 7
- [x] 2a Publication auto-discovery → Task 8
- [x] 2b Scholar stats reliability → Task 2
- [x] 2c Dynamic journal pills → Task 2
- [x] 2d Image optimization CI → Task 4
- [x] 2e Lighthouse CI → Task 10
- [x] 3a Enable search → Task 1 Step 3
- [x] 3b GoatCounter → Task 5
- [x] 3c SEO improvements → Task 9
- [x] 3d Cycling page polish → Task 11 (loading states in Task 6, error handling in Task 11)
- [x] 3e Cat gallery → Task 12
- [x] 3f Contributions polish → Task 13

**Placeholder scan:** No TBDs, TODOs, or "add appropriate" hand-waves. All code blocks are complete.

**Type consistency:** `scholar_stats.json` fields (`top_journals`, `top_journal_papers`, `citations`, `h_index`) used consistently across Task 2 script and Task 2 about.liquid update. `github_stats.json` fields (`avatar_url`, `name`, `public_repos`, `followers`, `total_stars`, `repos`) used consistently between Task 3 script and Task 3 code.md rewrite.
