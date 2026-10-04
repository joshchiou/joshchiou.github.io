# CLAUDE.md

Josh Chiou's personal academic website: an al-folio Jekyll fork, deployed to GitHub Pages.
This file is the starting point for a new session; the guides below hold the detail.

## Read first

- [docs/site-guide.md](docs/site-guide.md): every page, the file that feeds it, the automation, and
  recipes for common changes (new paper, news item, talk, repo, project).
- [docs/design.md](docs/design.md): typeface, colors, components, image rules, illustration palette,
  accessibility checks.
- [docs/writing-style.md](docs/writing-style.md): voice, naming, punctuation, and patterns for each
  kind of text.
- [docs/STATUS.md](docs/STATUS.md): what is live, what is open, and who it waits on. Rewritten at
  the end of each session with the `handoff` skill (repo rules in `.claude/handoff-inputs.md`).
- [docs/DECISIONS.md](docs/DECISIONS.md): append-only log of decisions and why the alternatives
  were rejected. Check it before changing something that looks odd.

Two writing rules apply to all visible text, docs, and commit messages:

1. **American English** (analyze, color, modeling, gray, traveled).
2. **No em dashes.** Rewrite with a comma, colon, parentheses, or a new sentence. En dashes only in
   number ranges. `grep -rn "—" _pages _projects _news _data _includes _layouts _config.yml _bibliography assets/js`
   should come back empty.

## What this is

Customized fork of [al-folio](https://github.com/alshedivat/al-folio). Content lives in:

- `_pages/about.md`: landing page content
- `_data/cv.yml`: CV data (experience, education, talks, skills, awards)
- `_bibliography/papers.bib`: all publications (jekyll-scholar)
- `_news/*.md`: news items shown on the about page
- `_projects/*.md`: project cards and pages (`work_` and `fun_` prefixes)
- `_data/repositories.yml`, `_data/contributions.yml`: code page repos and open-source PRs
- `_data/research_themes.yml`, `_data/press.yml`: homepage theme cards, press list
- `_data/github_stats.json`, `_data/scholar_stats.json`: auto-updated by GitHub Actions
- `_data/cycling_*.json`: from Apple Health via `scripts/cycling_data.py` (docs/cycling-data.md)
- `_data/travel_countries.yml`, `_data/travel_cities.yml`: from the Timeline script, then hand-edited

Template-level files (`_sass/`, `assets/libs/`, `_layouts/`, `_includes/`) are mostly upstream
al-folio. Customized ones: `_layouts/bib.liquid` (thumbnails, TL;DRs, badges), `_layouts/page.liquid`
(image credit line), `_layouts/about.liquid`, `_includes/head.liquid` (JSON-LD, Google verification),
`_includes/metadata.liquid` (page titles, `og_image`), `_includes/publication_meta.liquid`, and the
new includes `research_themes.liquid`, `talks.liquid`, `press.liquid`.

## Tagline

Places to update together when role/focus changes:

1. `_pages/about.md` subtitle, front-matter description, and first paragraph
2. `_config.yml` description (meta tag)
3. `_includes/head.liquid` JSON-LD `jobTitle` and WebSite `description`
4. `_data/cv.yml` current role (add a `roles` entry, keep the previous one)
5. `assets/img/og-image.svg` (social preview), then `python3 scripts/render_og_image.py`
   to regenerate `og-image.png` (set `CHROMIUM_PATH` if Playwright's browser isn't installed)

## Build

```bash
bundle install          # first time only
bundle exec jekyll serve # local dev at http://localhost:4000
bundle exec jekyll build --strict_front_matter  # production build check
python3 scripts/check_site.py && python3 scripts/check_sri.py  # numbers and CDN hashes
python3 -m pytest tests  # unit and browser tests (after `npx purgecss -c purgecss.config.js`)
```

All three run in the "Site checks" workflow on every PR and weekly; `check_site.py` also runs in
`deploy.yml` before deploying. See "Automation" in docs/site-guide.md. Publication counts come from `papers.bib` at build time (`_plugins/publication-stats.rb`,
top journals listed in `top_journals` in `_config.yml`); never hardcode a count in a template.

Or with Docker (recommended, since it matches CI):

```bash
docker compose up
```

**CV PDF:** `assets/pdf/CV.pdf` is not committed. The deploy workflow renders `/cv/` to PDF with
`scripts/build_cv_pdf.py` (Playwright + Chromium), so it always matches `_data/cv.yml`. Print layout
lives in the `@media print` block of `_sass/_custom.scss`. To preview locally after a build:
`python3 scripts/build_cv_pdf.py --out ~/CV.pdf` (set `CHROMIUM_PATH` if needed).

## Data pipelines

**Cycling:** Apple Health, not Strava (its API became paid in June 2026; D-018). An iPhone
Shortcut posts each Apple Watch ride to the "Add Ride" workflow; a periodic Health export run
through `scripts/cycling_data.py import-health` adds elevation and fills gaps. Rides through
2026-06-21 are a frozen Strava archive. Setup and instructions: docs/cycling-data.md. Never
commit a Health export.

**Travel:** export the JSON on the phone (Google Maps → your profile → Timeline → ⋮ → Export
Timeline data; Timeline lives on the device, so this can't be automated), then run
`scripts/parse_location_history.py [--dry-run] /path/to/export.json`. iOS and Android exports
both work. It only appends places missing from `_data/travel_countries.yml` and
`_data/travel_cities.yml`, so hand edits survive (see docs/DECISIONS.md D-013). New countries need
a `continent` added by hand; review new cities and delete noise, which stays deleted because
proposed cities are remembered in `scripts/.travel_seen.json` (gitignored). Geocodes via Nominatim,
cached in `scripts/.geocode_cache.json` (gitignored; first run ~5 min at 1 req/sec). Never commit
the export itself.

**Scholar stats** (citations, h-index, i10-index): `scripts/update_scholar.py` via `.github/workflows/update-scholar.yml` (weekly).
Google Scholar blocks GitHub Actions runners, so the workflow reads the profile through SerpAPI
(Google Scholar Author API) using the `SERPAPI_KEY` repo secret; the free plan covers a weekly
run. Without the key the script falls back to `scholarly` (needs `bibtexparser<2`), which only
works off CI. On a failed fetch the script exits non-zero and leaves `_data/scholar_stats.json`
unchanged, so a red run means stale numbers.

**Refresh chain:** the Scholar, GitHub stats, and Add Ride workflows push with `GITHUB_TOKEN`, which
doesn't trigger push-based workflows, so `deploy.yml` also runs on `workflow_run` after each of
them succeeds. New data workflows that should update the live site must be added to that list.

**New publications:** `scripts/update_publications.py` (weekly) opens a PR with ORCID works whose
DOI and title aren't already in `papers.bib`; preprint versions with different titles still appear
and should be rejected in review. Needs repo setting "Allow GitHub Actions to create and approve
pull requests" (Settings → Actions → General).

**Publication metadata:** run the "Enrich Publication Metadata" workflow (manual trigger) to
add missing `abstract`, `pmid`, and open-access `pdf` fields from Europe PMC via
`scripts/enrich_bib.py`; it opens a PR. Selected papers also carry a hand-written `tldr`
(plain-language summary) and a `preview` image path.

## Homepage and publications data

- `_data/research_themes.yml`: the three research theme cards on the homepage
- `_data/press.yml`: media coverage listed on /publications/ (newest first)
- `_data/cv.yml` "Talks & Presentations": also rendered on /publications/; add slides/video
  links as `linkitems` (`linkname: slides`, `link: https://doi.org/...`)
- `contact_note` in `_config.yml`: text under the homepage social icons

## Talk slides (Zenodo)

Slides are archived on Zenodo (DOI, permanent), not committed to this public repo.
`scripts/zenodo_deposit.py META.json slides.pdf` creates a **draft** only; Josh publishes it.
Metadata lives in `docs/talks/*.zenodo.json`. Needs `ZENODO_TOKEN` (deposit:write scope) and
`zenodo.org` allowed in the environment's network settings. Get employer clearance before
posting any deck: the EASD 2026 deck (© Lilly) is not cleared and must not be uploaded.
The Festival of Genomics 2025 deck is **on hold** (Josh, Oct 2026): do not upload until he says so.

## Bib keys for key papers

- `chiou2021interpreting`: T1D and exocrine pancreas, _Nature_ 2021
- `chiou2021single`: islet scATAC-seq, 2021
- `sun2023plasma`: UKB-PPP, _Nature_ 2023
- `intact2025multi`: Multi-INTACT methods paper
- SURMOUNT-5 proteomics: not yet published; see "Pending" in docs/site-guide.md for what to do when it is

## Don't touch unless re-templating

- `_sass/`: al-folio CSS (upstream, with earlier customizations in `_base.scss`, `_cv.scss`,
  `_projects.scss`). Put new site-specific styles in `_sass/_custom.scss`, which is imported last.
- `assets/libs/`: vendored JS libraries
- `_config.yml` third_party_libraries block: library versions and integrity hashes. If you must
  change one, run `scripts/check_sri.py`; a wrong hash silently disables the library.
- `theme.js` is deferred, so inline scripts must read `data-theme` from `<html>` (set by the inline
  snippet in `head.liquid`) instead of calling `determineComputedTheme()` (D-016).
- `bin/`: CI scripts (upstream)

## Project card images

Each project card has a 16:10 image set via `img:` in its frontmatter, in `assets/img/projects/work/`
and `assets/img/projects/fun/`:

- Paper cards use cropped panels from Josh's papers: T1D uses the Manhattan plot (Chiou 2021
  _Nature_ Fig. 1a), islet the scATAC UMAP, UKB-PPP the pQTL map. The same crops serve as
  `preview` thumbnails in `papers.bib`; other selected papers' thumbnails are in
  `assets/img/publication_preview/`.
- Lilly, Pfizer, and Home Assistant are drawn by `scripts/render_project_art.py` from synthetic data
  (no real results; the Lilly and Pfizer cards say so in their credit line).
- Travel is drawn by `scripts/render_travel_card.py` from the travel data files. Re-run it after
  editing them.
- Homepage research theme images are separate 5:2 two-panel composites in
  `assets/img/research_themes/` (see docs/design.md); the clinical trial one comes from
  `render_project_art.py`.
- `img_credit:` in a project's frontmatter adds a "Card image: …" attribution line at the bottom of
  its page. Every figure taken from a paper needs one.
- `og_image:` points at a JPG copy in `assets/img/projects/og/` (social sites don't read WebP/SVG
  reliably). Regenerate it when the card image changes.

To replace a card image with a photo:

1. Run `python3 scripts/prep_images.py /path/to/source assets/img/projects/work/` (or `fun/`)
2. Update the `img:` field in the project's `_projects/*.md` frontmatter
3. Optionally add `img_position: top` (or `center`, `bottom`) to control cropping via CSS `object-position`

Image pipeline generates responsive WebP versions at 480/800/1400px widths automatically.
