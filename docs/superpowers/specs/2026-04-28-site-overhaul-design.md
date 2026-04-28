# Site Overhaul: Performance, Automation & Discoverability

**Date:** 2026-04-28
**Audience:** Mixed professional + community (pharma/biotech peers, academic collaborators, open-source community)
**Pain points addressed:** Performance & speed, data freshness / automation gaps, discoverability & analytics

## Architecture: Three Parallel Workstreams

Work is organized into three independent workstreams that can be implemented and reviewed in parallel. Within each workstream, items are ordered by priority.

---

## Workstream 1: Performance & Asset Optimization

### 1a. Dead asset cleanup

Remove `assets/img/prof_pic_color.png` (14MB). Not referenced anywhere in the codebase — confirmed by grep across all `.md`, `.liquid`, `.yml`, and `.html` files. Delete the file and add to `.gitignore` if a local copy is desired.

### 1b. Image optimization pipeline

The cat gallery has 15MB of unoptimized JPEGs (individual files up to 4.5MB). The existing `scripts/prep_images.py` generates responsive WebP at 480/800/1400px widths.

**Action:** Run `prep_images.py` on `assets/img/projects/fun/cats/` to generate WebP responsive variants. Commit the optimized variants so they're in the repo (avoids regenerating on every build). For future images, the CI step in 2d catches anything missed.

### 1c. Build-time GitHub stats

The `/code` page currently makes 3+ serial unauthenticated GitHub API calls on every page load. No caching, no error handling, easily rate-limited (60 req/hr for unauthenticated).

**New script:** `scripts/update_github.py`
- Fetches profile data (`/users/joshchiou`), aggregated star count (`/users/joshchiou/repos?per_page=100`), and per-featured-repo metadata (language, stars, forks).
- Uses `GITHUB_TOKEN` for authenticated requests (5,000 req/hr).
- Writes `_data/github_stats.json` with: avatar URL, name, public_repos, followers, total_stars, and a `repos` object keyed by `owner/name` with language, stars, forks.

**New workflow:** `.github/workflows/update-github.yml` — runs weekly (similar cadence to Strava/Scholar).

**Page update:** `/code` page reads `site.data.github_stats` at build time. Zero client-side API calls. Repo cards render language dots, star counts, and fork counts from build-time data. Falls back gracefully if data file is missing (shows static content without stats).

### 1d. Preconnect hints

Add to `_includes/head.liquid`:
```html
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```
Saves ~100-300ms on first paint by establishing connections early.

### 1e. Strava data externalization

Currently `{{ site.data.strava_calendar | jsonify }}` is inlined in the cycling page HTML. This grows linearly with ride history.

**Action:** Modify `scripts/update_strava.py` to also write `assets/data/strava_calendar.json`. The cycling page loads this via `fetch()` instead of inlining. Keeps page HTML lean. Add a loading skeleton while the fetch completes.

### 1f. Theme.js refactor

`assets/js/theme.js` is loaded synchronously in `<head>` (render-blocking) to prevent theme flicker.

**Action:** Extract the ~20 lines of critical anti-flicker code (read localStorage, set `data-theme` attribute, set `data-theme-setting`) into an inline `<script>` in `head.liquid`. Move the rest of `theme.js` (component theme handlers for ECharts, Mermaid, Giscus, tables, etc.) to a deferred script loaded at the end of `<body>`. Eliminates render-blocking without introducing flicker.

---

## Workstream 2: Automation & Data Pipelines

### 2a. Publication auto-discovery via ORCID + Semantic Scholar

New script: `scripts/update_publications.py`

**Data flow:**
1. Fetch publication list from **ORCID public API** (`GET /v3.0/0000-0002-4618-0647/works`). Returns DOIs, titles, journal names, years.
2. For each DOI not already present in `_bibliography/papers.bib`, fetch full metadata from **Semantic Scholar API** (`GET /graph/v1/paper/DOI:{doi}?fields=title,authors,venue,year,externalIds,abstract`).
3. Generate draft BibTeX entries matching the existing format:
   - Key format: `{firstauthor_lastname}{year}{first_title_word}` (matching existing convention like `chiou2021interpreting`)
   - Set `selected = false` by default
   - Omit `cv_order`, `altmetric`, `preview` fields (user adds manually during review)
4. **Create a pull request** (via `gh pr create`) with the new entries appended to `papers.bib`. PR body lists the new papers found for easy review.

**New workflow:** `.github/workflows/update-publications.yml` — runs weekly. Requires `GITHUB_TOKEN` (default) for PR creation.

**Key constraint:** `papers.bib` remains the single source of truth. The script only proposes additions; user reviews and merges.

### 2b. Scholar stats reliability

Revise `scripts/update_scholar.py`:

**Citation metrics strategy:**
- **Primary:** Google Scholar via `scholarly` library with 15-second timeout (spawned in subprocess, as current implementation does).
- **On failure:** Preserve the last known good values from `_data/scholar_stats.json`. Do NOT fall back to Semantic Scholar for display metrics — the 27% citation gap (7,529 GS vs 5,464 S2 as of 2026-04-28) makes S2 numbers misleading.
- **Plausibility check:** Only update if new citation count >= previous count (citations don't decrease). If scholarly returns a value below the last known, log a warning and keep the existing value.
- **Manual override:** Running `python scripts/update_scholar.py` locally always works as an escape valve — commit the result directly.

**Rationale:** Google Scholar is the metric the academic community recognizes. The 27% gap is attributable to GS's preprint-merging behavior and broader corpus indexing.

### 2c. Dynamic journal pills

Currently, the about page hardcodes `<span class="about-journal-pill">Nature</span>` etc. in `_layouts/about.liquid`.

**Action:** Extend `update_scholar.py` to scan `papers.bib` for journals in the `TOP_JOURNALS` set and write a `top_journals` array to `scholar_stats.json`:
```json
{
  "top_journals": [
    {"name": "Nature", "count": 4},
    {"name": "Cell", "count": 2},
    {"name": "Nature Genetics", "count": 3}
  ]
}
```

Update `about.liquid` to iterate over `stats.top_journals`. If a new top journal appears in `papers.bib`, it renders automatically.

### 2d. Image optimization CI step

Add a step in `deploy.yml` (after checkout, before Jekyll build) that:
1. Finds image files in `assets/img/` that are `.jpg`, `.jpeg`, or `.png` and larger than 500KB without corresponding WebP variants already committed.
2. Runs `prep_images.py` on them to generate WebP responsive variants as build artifacts (not committed — they supplement what's already in the repo).
3. This acts as a safety net for images that were committed without being pre-optimized.

### 2e. Lighthouse CI audit

Add `treosh/lighthouse-ci-action@v12` (or latest) to `deploy.yml` after the Jekyll build step.

**Configuration:**
- Test the built `_site/index.html` and `_site/publications/index.html` (two representative pages).
- Budgets: performance >= 80, accessibility >= 95, best-practices >= 90, SEO >= 90.
- Failures posted as GitHub check annotations. Does not block deploy initially (assertion mode) — can be switched to enforcement once baselines are met.

---

## Workstream 3: Discoverability & UX

### 3a. Enable site search

Set `search_enabled: true` in `_config.yml`. al-folio's built-in Ninja Keys command palette is already wired up — it indexes pages, publications, and projects. With 38 publications and 10 projects, search adds real navigation value.

No additional code needed — the template handles index generation and UI.

### 3b. GoatCounter analytics

**Integration:**
- Sign up at goatcounter.com (free for personal/non-commercial use).
- Add a `<script>` tag to `_includes/head.liquid` (or a new `_includes/scripts/goatcounter.liquid` partial for clean separation):
  ```html
  <script data-goatcounter="https://SITECODE.goatcounter.com/count"
          async src="//gc.zgo.at/count.js"></script>
  ```
- Gate behind a config flag: `enable_goatcounter: true` + `goatcounter_code: SITECODE` in `_config.yml`.
- No cookies, no consent banner, GDPR-compliant, ~3.5KB script.

**What it provides:** Page views, referrers, browser/OS stats, screen sizes, geographic data. No individual tracking.

### 3c. SEO improvements

**Per-page meta descriptions:** Add `description:` frontmatter to pages that lack it:
- `cv.md` — "Curriculum vitae of Joshua Chiou — experience, education, publications, and skills in computational genetics and proteomics."
- Any other pages missing descriptions.

**Structured data for publications:** Add `ScholarlyArticle` JSON-LD to `_layouts/bib.liquid` for each publication entry. Fields: `headline`, `author`, `datePublished`, `isPartOf` (journal), `identifier` (DOI). Improves Google Scholar indexing.

**OpenGraph images per page:** Add optional `og_image` frontmatter support in `_includes/metadata.liquid`. Project pages with distinctive images (cycling charts, travel map) can set custom OG previews for social sharing.

### 3d. Cycling page polish

- **Loading states:** Add skeleton placeholders (CSS-only, no JS) for the three ECharts containers. Replaced by charts once ECharts initializes.
- **Error handling:** If `site.data.strava_stats` is empty/missing, show a graceful "Stats updating — check back soon" message instead of empty charts.
- **Theme toggle efficiency:** Instead of destroying and re-creating ECharts instances on theme change, call `chart.setOption({ darkMode: isDark })` and update only the color palette. Reduces theme toggle lag.

### 3e. Cat gallery buildout

The page exists with 6 photos in a basic Bootstrap grid. Photos are 558KB to 4.5MB each.

**Actions:**
1. Run `prep_images.py` on all cat photos to generate WebP responsive variants.
2. Replace the basic grid with a Swiper gallery (already in al-folio's third-party libs). Thumbnails load first; clicking opens full-size in a lightbox.
3. Add `loading="lazy"` to all gallery images.

### 3f. Contributions page polish

Lower priority. The existing layout on `/code` is functional.

**Enhancements:**
- Group contributions by year with year headers.
- Add subtle language color dots (matching repo card style) next to each contribution.
- No structural changes needed.

---

## Implementation Order

Within each workstream, items are independent. Across workstreams, the recommended order for maximum early impact:

1. **1a** Dead asset cleanup (immediate, 14MB savings)
2. **3a** Enable search (one-line config change)
3. **1d** Preconnect hints (3 lines in head.liquid)
4. **2b** Scholar stats reliability fix (modify existing script)
5. **2c** Dynamic journal pills (extend scholar script + update about.liquid)
6. **1c** Build-time GitHub stats (new script + workflow + page rewrite)
7. **1b + 2d** Image optimization (prep_images run + CI step)
8. **3b** GoatCounter analytics (sign up + add script)
9. **1e** Strava data externalization (script change + page fetch refactor)
10. **1f** Theme.js refactor (split inline/deferred)
11. **2a** Publication auto-discovery (new script + workflow — most complex)
12. **3c** SEO improvements (meta descriptions, structured data, OG images)
13. **2e** Lighthouse CI (add Action step + budgets)
14. **3d** Cycling page polish (loading states, error handling, theme efficiency)
15. **3e** Cat gallery buildout (image optimization + Swiper)
16. **3f** Contributions page polish (grouping, icons)

---

## Out of Scope

- Dropping MDB or deduplicating Bootstrap/MDB CSS — high risk of regressions across the template; PurgeCSS already handles unused CSS removal in the deploy pipeline.
- Blog functionality — no blog posts exist and none are planned.
- Newsletter functionality — form exists in CSS but no backend; not a priority.
- Rewriting git history to remove large files — delete-and-move-on is simpler.
