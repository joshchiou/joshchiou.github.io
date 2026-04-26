# Personal Site Overhaul — Design

**Date:** 2026-04-26
**Repo:** joshchiou.github.io (al-folio Jekyll fork)
**Goal:** Convert remaining template content into intentional personal content, fix latent bugs, tighten messaging across pages, and add lightweight documentation so the customizations are legible to future-me.

---

## 1. Scope

### Pages kept (4 nav items)

| Page          | Permalink        | Status                              |
| ------------- | ---------------- | ----------------------------------- |
| about         | `/`              | Customized — minor rewrites         |
| publications  | `/publications/` | Customized — keep                   |
| projects      | `/projects/`     | **Repopulate** — replace template   |
| cv            | `/cv/`           | Customized — keep                   |
| repositories  | `/repositories/` | **Restructure** — contributions-led |

`repositories` is reachable from the about-page social row (GitHub icon → list page), not from the top nav. Top nav stays at four items: about · publications · projects · cv.

### Pages deleted

- `_pages/about_einstein.md`
- `_pages/profiles.md` (people page)
- `_pages/teaching.md`
- `_pages/blog.md`
- `_pages/dropdown.md` (no longer needed once the submenu collapses)
- All `_posts/*.md` (28 demo posts)
- All template `_projects/*.md` (10 demo projects, replaced)
- `_data/coauthors.yml` (Einstein/Bach placeholders, not used by Josh's bib)
- `_data/venues.yml` (placeholder venues, not used)

### Layouts/includes consequences

- `_layouts/profiles.liquid` — delete (only used by the deleted people page).
- `_includes/news.liquid`, `_includes/social.liquid`, `_includes/header.liquid` — keep, but verify the dropdown removal doesn't leave dead code in `header.liquid`. Inline-edit if it does.
- `_includes/latest_posts.liquid`, `_includes/related_posts.liquid`, `_includes/disqus.liquid`, `_includes/giscus.liquid`, `_includes/pagination.liquid` — delete (blog gone).
- `_includes/audio.liquid`, `_includes/video.liquid`, `_includes/figure.liquid` — keep (still used by about/projects).
- `_layouts/post.liquid` — **keep** (the `news` collection's `defaults: layout: post` depends on it; each news item has its own URL even when displayed inline).
- `_layouts/distill.liquid`, `_layouts/archive-*.liquid` — delete (only used by demo posts and the jekyll-archives plugin we're dropping).

### Plugins / config simplifications

Remove from `_config.yml`:

- `blog_name`, `blog_description`, `permalink: /blog/...`, `lsi`, `pagination`, `related_blog_posts`, `giscus` block, `disqus_shortname`, `external_sources`, `latest_posts`, `display_tags`, `display_categories`, `jekyll-archives` block.
- Plugins to drop: `jekyll-archives`, `jekyll-jupyter-notebook`, `jekyll-paginate-v2`, `jekyll-twitter-plugin`. (Verify nothing in retained pages depends on them; remove only if confirmed unused.)
- `newsletter.enabled: false` already; remove the `newsletter:` block entirely for cleanliness.
- `_config.yml: include: ["_pages"]` — keep.
- Add `docs/` to `exclude:` so the spec/design dir doesn't get published.

---

## 2. Content updates

### 2.1 Tagline canonicalization

Three strings drift today. We pick canonical phrasings and propagate.

**About-page subtitle (visible header):**

```
Senior Advisor, Genomics · Lilly · Translational Proteomics & Statistical Genetics
```

Replaces the current `Senior Advisor, Genomics · Lilly · Cardiometabolic Research, Data Science`.

**`_config.yml: description` (meta description, used for `<meta name="description">`):**

```
Senior Advisor, Genomics at Lilly. Translating large-scale proteomics and human genetics into mechanistic and biomarker insights to inform clinical strategy for cardiometabolic and obesity drug programs.
```

Replaces the current 2-line description.

**`_config.yml: keywords` (meta keywords):**

```
proteomics, computational biology, statistical genetics, pQTL, human genetics, GWAS, single-cell genomics, biomarker discovery, target discovery, cardiometabolic, obesity, Lilly
```

Was: `proteomics, computational biology, statistical genetics, pQTL`.

**About-page body paragraph 1** updated to match — opening sentence becomes:

> I am a Senior Advisor in Genomics at [Lilly](https://www.lilly.com), translating large-scale proteomics and human genetics into mechanistic and biomarker insights to inform clinical strategy for cardiometabolic and obesity drug programs.

(Replaces the current "working on proteomics for obesity clinical trials. My research focuses on…" sentence — same meaning, aligned phrasing, more keyword-rich.)

### 2.2 News collection cleanup

`_news/2025-10-20-lilly.md` — currently reads "Excited to be joining Lilly…". As of 2026-04-26 that's six months stale. Rewrite to past-tense, matching the older Pfizer-join entry's voice:

> Joined [Lilly](https://www.lilly.com) as Senior Advisor, Genomics, working on translational proteomics for obesity clinical trials.

(Drops the "Diabetes, Obesity, and Complications Therapeutic Area" name since the team was reorganized; matches CV current title.)

Other news entries: keep as-is. They are factually correct historical milestones.

### 2.3 CV alignment

Confirm `_data/cv.yml` Lilly entry matches:

- `title: Senior Advisor, Genomics` ✅ (already correct)
- `maindescription` — keep current phrasing; it reads well.

Pfizer scope phrasing: about page currently says "cardiovascular and renal diseases"; CV says "renal and cardiovascular disease". Standardize to **"cardiovascular and renal disease"** in both for SEO (cardiovascular gets more searches than renal) and for parallel structure.

### 2.4 Projects page repopulation

Replace `display_categories: [work, fun]` content. The `projects.md` page itself stays as-is (the Liquid loop is fine); we just swap the underlying `_projects/*.md` files.

**File naming convention:** `_projects/work_<slug>.md` and `_projects/fun_<slug>.md`. The `importance` field controls within-category order (lower = first).

#### Work cards (5)

Each card has: `title`, `description` (1 line), `category: work`, `img: assets/img/projects/<slug>.{jpg,png,webp}` (user-supplied), `importance: <int>`, `related_publications: true` (where applicable), and a body that is 2 paragraphs + paper/code links.

1. **`work_t1d-exocrine-pancreas.md`** — *Type 1 diabetes and the exocrine pancreas* (PhD)
   - Anchor: Chiou et al. *Nature* 2021
   - Code: `joshchiou/T1D_snATAC`
   - Importance: 1

2. **`work_islet-single-cell-epigenomics.md`** — *Single-cell epigenomics of human pancreatic islets* (PhD)
   - Anchors: scATAC-seq + multi-omic islet papers from your bib
   - Importance: 2

3. **`work_ukb-ppp.md`** — *UK Biobank Pharma Proteomics Project* (Pfizer/consortium)
   - Anchor: Sun et al. *Nature* 2023 + the follow-up consortium papers in your bib
   - Importance: 3

4. **`work_pfizer-target-discovery.md`** — *Human-genetics-driven target discovery for cardiovascular and renal disease* (Pfizer)
   - No specific targets named; describes approach (genetics + functional genomics + multi-omics → portfolio).
   - Importance: 4

5. **`work_lilly-obesity-proteomics.md`** — *Translational proteomics for obesity clinical trials* (Lilly, current)
   - Forward-looking placeholder; describes the program scope without trial specifics.
   - Importance: 5

#### Fun cards (5)

1. **`fun_home-assistant.md`** — *Home Assistant*
   - Body: brief tour of the setup, screenshot of a dashboard, link to `ha-esunpower` fork.
   - Importance: 1

2. **`fun_cycling.md`** — *On the bike* (Strava-powered, dynamic)
   - Hero visual: **GitHub-style activity calendar** — one square per day, color intensity = distance. Generated from Strava API. Privacy-safe: no routes shown (most rides are commutes).
   - Supporting: 3-stat strip (all-time totals: rides, distance, elevation).
   - Detail page: monthly distance bar chart (all-time).
   - Data pipeline: GitHub Actions workflow on weekly schedule. Fetches all activities via Strava API (`activity:read_all` scope), computes stats, writes `_data/strava-calendar.json` + `_data/strava-stats.json`, commits back to repo.
   - Secrets required in GitHub repo settings: `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`.
   - User creates a new Strava API app (separate from openclaw) at `strava.com/settings/api`.
   - Implementation: ECharts heatmap calendar (already in template) for activity calendar; small stat callouts beneath.
   - Importance: 2

3. **`fun_cocktails.md`** — *Cocktails*
   - Body: short note + photo gallery using medium-zoom (already in template).
   - Importance: 3

4. **`fun_cats.md`** — *Cats* — **Claire**
   - `assets/img/projects/fun/cats/claire-main.jpg` → card hero (558K, already in repo).
   - `claire-gallery-1.jpg` through `claire-gallery-5.jpg` → medium-zoom gallery on detail page (15MB total; imagemagick generates WebP at build time, no manual compression needed).
   - Body: one sentence + gallery.
   - Importance: 4

5. **`fun_travel.md`** — *Travel* (Takeout-powered, manually refreshed)
   - **Card hero**: visited-countries choropleth using ECharts world map (just needs country name list; built-in, no external GeoJSON required).
   - **Stat strip**: X countries · Y cities.
   - **Detail page**: Leaflet city dot map with markers at `_data/travel-cities.yml` locations.
   - Data pipeline: **Option D** — one-time Google Takeout export → `scripts/parse_takeout.py` (already written) → commits `_data/travel-countries.yml` + `_data/travel-cities.yml`. Refresh when you feel like it; no automation.
   - `_data/travel-countries.yml` and `_data/travel-cities.yml` are generated by `scripts/parse_takeout.py /path/to/Takeout`. Cities file requires manual pruning of restaurants/offices before commit.
   - Importance: 5

**User content dependencies:** images for work cards (hero figures from papers or schematics), Home Assistant screenshot, cocktail photos. Claire's photos already in repo. Strava and travel cards are data-driven and need no images beyond the generated visualizations.

### 2.5 Repositories page restructure

`_pages/repositories.md` becomes two manually-curated sections.

**Top of page — short framing paragraph:**

> A small slice of my coding life on public GitHub. Most production work lives in enterprise GitHub orgs (Pfizer, Lilly) and isn't reflected here. Below: repos I maintain, plus contributions to community scientific software.

**Section 1 — Maintained:**

Use the existing `repository/repo.liquid` include (the GitHub-stats card embed). Repos:

- `joshchiou/T1D_snATAC` (data/code companion to the *Nature* T1D paper)
- `joshchiou/joshchiou.github.io` (this site)

(Drops the "GitHub users" featured-user card and the "trophies" section — both feel out of register for an academic page. We disable `repo_trophies` in `_config.yml`.)

**Section 2 — Open-source contributions (curated):**

A new `_data/contributions.yml` lists ~6–8 most substantive merged PRs. Schema:

```yaml
- repo: scverse/SnapATAC2
  pr: 412 # PR number
  title: Parallel IDF
  date: 2025-06-30
  blurb: Parallelized inverse-document-frequency computation in dimensionality reduction.

- repo: stephenslab/susieR
  pr: 251
  title: Compatibility with rpy2
  date: 2025-02-25
  blurb: Restored Python interop so susieR can be called from rpy2 pipelines.

# … 4–6 more …
```

The exact 6–8 will be the most "memorable" PRs (paraphrasing user's own description) — selection happens during implementation, user reviews. Final list will pull from: SnapATAC2 (3 PRs), susieR, gwaslab, ArchR, fine-mapping-inf, conda-forge/staged-recipes, ha-esunpower.

**"See all merged PRs" link** at the section bottom: `https://github.com/search?q=author%3Ajoshchiou+is%3Apr+is%3Amerged&type=pullrequests`.

The page rendering will need a small Liquid block in `_pages/repositories.md` to iterate `site.data.contributions` and render each as a list item with repo · title · date · blurb. No new include necessary — inline.

### 2.6 SEO / metadata enablement

In `_config.yml`:

- `serve_og_meta: false` → `true`.
- `serve_schema_org: false` → `true`.
- `og_image:` → `assets/img/prof_pic.jpg` (or a dedicated 1200×630 OG image if user supplies one; `prof_pic.jpg` works as a fallback since the meta logic falls back to per-page front-matter overrides).
- `last_updated: true` already set ✅.
- Verify `_includes/metadata.liquid` produces JSON-LD that matches the canonicalized tagline.

---

## 3. Documentation

Two files added at repo root.

### 3.1 `CLAUDE.md` (new)

Short. Contains:

- One-paragraph repo orientation: "Personal academic site, al-folio Jekyll fork. Customizations live in `_pages/about.md`, `_data/cv.yml`, `_bibliography/papers.bib`, `_news/`, `_projects/`, and selectively in `_layouts/bib.liquid` and `_includes/publication_meta.liquid`."
- Build commands: `bundle exec jekyll serve` (local), `bin/cibuild` (CI parity).
- Where the canonical tagline / description live (so the next person editing knows to update both `_pages/about.md` subtitle and `_config.yml: description` together).
- "Don't touch unless deliberately re-templating" list: `_layouts/distill.liquid` (unused), the al-folio CSS in `_sass/`, `assets/libs/`.
- Link to upstream al-folio docs (CUSTOMIZE.md, FAQ.md) for template-level questions.

### 3.2 `README.md` (rewrite)

Replace the upstream al-folio README with a personal-site README:

- One-paragraph "what this is" + link to live site.
- `Local development` section with `bundle install`, `bundle exec jekyll serve`, port note.
- `Structure` section pointing at the same key files as CLAUDE.md.
- Credit footer: "Built on [al-folio](https://github.com/alshedivat/al-folio) by Maruan Al-Shedivat."

The upstream README content can be archived to `UPSTREAM_README.md` if any of it (e.g., the Lighthouse score table, the contributor list) is worth preserving. Default: archive it.

---

## 4. Bug audit (pass during implementation)

Known items already collected:

- Stale Lilly news (fixed in §2.2).
- Tagline drift (fixed in §2.1).
- Pfizer scope phrasing mismatch (fixed in §2.3).
- Template `_data/repositories.yml` (replaced).
- Empty `giscus.repo` (deleted with blog).
- `disqus_shortname: al-folio` lingering despite no comments (deleted).
- 12 numbered placeholder images in `assets/img/` (deleted with template projects).
- `assets/pdf/example_pdf.pdf` (template artifact — delete).

A second-pass audit during implementation will run:

- `bundle exec jekyll build --strict_front_matter` to surface broken front-matter.
- Lychee / `lychee.yml` workflow over the built site for broken external links.
- Visual scan of about / projects / publications / cv / repositories in dev server, light/dark mode, mobile breakpoint.
- Check `_includes/social.liquid` only emits icons for set `_config.yml` socials (it should already; verify).
- Confirm `_includes/scripts/*` aren't loading anything for deleted features (e.g., MathJax — keep it; pseudocode/tikzjax/typograms — drop them, they're for the demo posts only).

Any new bugs found during this pass get fixed inline; the spec doesn't try to enumerate them all up front.

---

## 5. Out of scope (explicit)

- A `/now/` page. Considered, deferred — comes back as a future enhancement if user wants to maintain it.
- A press / Altmetric "highlights" callout on the about page. Same — defer.
- Talks subsection in CV. Defer until there's a second talk.
- Replacing the al-folio CSS. Visual identity stays as-is.
- Replacing the al-folio CSS. Visual identity stays as-is.
- Migrating to a different theme/SSG. No.
- `/now/` page, press/Altmetric callouts, talks CV subsection — all deferred.

---

## 6. Implementation phasing (preview)

The implementation plan (next step) will phase this as:

1. **Cleanup** — delete templates, demo posts, demo projects, unused layouts/includes/plugins, `_data/*` placeholders. Single commit.
2. **Config consolidation** — `_config.yml` simplifications, plugin removals, SEO enablement, tagline propagation. Single commit.
3. **Content rewrites** — about-page sentence, Lilly news, Pfizer scope alignment. Single commit.
4. **New project cards** — 10 `_projects/*.md` files with placeholder images. Single commit.
5. **Repositories page rebuild** — `_data/contributions.yml` + page rewrite. Single commit.
6. **Strava pipeline** — GitHub Actions workflow, `_data/strava-calendar.json` + `_data/strava-stats.json` schema, cycling card ECharts implementation. Requires GitHub secrets set first.
7. **Travel map** — `_data/travel-countries.yml` + `_data/travel-cities.yml` (from Takeout), ECharts choropleth card, Leaflet city dots on detail page. Requires Takeout export from user.
8. **Documentation** — `CLAUDE.md`, `README.md` rewrite, `UPSTREAM_README.md` archive. Single commit.
9. **Bug-audit pass** — fixes from §4 audit. One or more commits depending on what's found.

User reviews each phase before next begins. Phase 4 (project content) is the heaviest; the body text in those cards will be drafted by me and reviewed by user before commit.

---

## 7. Open content dependencies on user

These block specific phases but don't block writing the plan:

- **Work card images** (5): hero figures from anchor papers or schematics. Phase 4 ships with placeholders; swap-in afterward.
- **Home Assistant screenshot** — user-supplied for the Home Assistant card.
- **Cocktail photos** — user-supplied.
- **Strava API secrets** — `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN` must be in GitHub repo secrets before Phase 6 workflow runs. OAuth instructions provided in conversation.
- **Google Takeout export** — required for Phase 7 (travel map). Request at myaccount.google.com → Data & privacy → Download your data → Location History. Run `python scripts/parse_takeout.py /path/to/Takeout` locally, commit output YAML.
- **Claire photos** — already in repo at `assets/img/projects/fun/cats/`. No action needed.
- **Optional 1200×630 OG image** — falls back to `prof_pic.jpg` if not supplied.

No content dependency on user for the cleanup, config, repositories, or documentation phases.
