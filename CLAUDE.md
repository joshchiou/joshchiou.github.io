# CLAUDE.md

Personal website — al-folio Jekyll fork. Claude Code context.

## What this is

Customized fork of [al-folio](https://github.com/alshedivat/al-folio). Customizations live in:
- `_pages/about.md` — landing page content
- `_data/cv.yml` — CV data (experience, education, skills, awards)
- `_bibliography/papers.bib` — all publications (jekyll-scholar)
- `_news/*.md` — news items shown on the about page
- `_projects/*.md` — project cards (work_ and fun_ prefixes)
- `_data/contributions.yml` — curated open-source PR list
- `_data/strava_calendar.json`, `_data/strava_stats.json` — auto-updated by GitHub Actions
- `_data/travel_countries.yml`, `_data/travel_cities.yml` — from Takeout script

Template-level files (`_sass/`, `assets/libs/`, `_layouts/`, `_includes/`) are mostly upstream
al-folio. Exceptions: `_layouts/bib.liquid` (Altmetric/badges), `_includes/publication_meta.liquid`,
`_includes/head.liquid` (Google verification).

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
```

Or with Docker (recommended — matches CI environment):

```bash
docker compose up
```

**CV PDF:** `assets/pdf/CV.pdf` is not committed. The deploy workflow renders `/cv/` to PDF with
`scripts/build_cv_pdf.py` (Playwright + Chromium), so it always matches `_data/cv.yml`. Print layout
lives in the `@media print` block of `_sass/_custom.scss`. To preview locally after a build:
`python3 scripts/build_cv_pdf.py --out ~/CV.pdf` (set `CHROMIUM_PATH` if needed).

## Data pipelines

**Strava:** `scripts/update_strava.py` — run manually or via `.github/workflows/update-strava.yml`.
Requires env vars: `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`.
GitHub Actions secrets set in repo Settings → Secrets and variables → Actions.

**Travel:** `scripts/parse_location_history.py /path/to/location-history.json` — run locally after
downloading from Google Maps → Timeline → Export timeline data (JSON).
Outputs `_data/travel_countries.yml` and `_data/travel_cities.yml`. Geocodes via Nominatim and
caches to `scripts/.geocode_cache.json`. Review cities file before committing (noise from
restaurants/shops). First run ~5 min (289 places at 1 req/sec); re-runs instant.

**Scholar stats:** `scripts/update_scholar.py` via `.github/workflows/update-scholar.yml` (weekly).
`scholarly` needs `bibtexparser<2` (pinned in the workflow). On a failed fetch the script exits
non-zero and leaves `_data/scholar_stats.json` unchanged, so a red run means stale numbers.

**Refresh chain:** the Scholar, GitHub stats, and Strava workflows push with `GITHUB_TOKEN`, which
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

- `_data/research_themes.yml` — the three research theme cards on the homepage
- `_data/press.yml` — media coverage listed on /publications/ (newest first)
- `_data/cv.yml` "Talks & Presentations" — also rendered on /publications/; add slides/video
  links as `linkitems` (`linkname: slides`, `link: https://doi.org/...`)
- `contact_note` in `_config.yml` — text under the homepage social icons

## Talk slides (Zenodo)

Slides are archived on Zenodo (DOI, permanent), not committed to this public repo.
`scripts/zenodo_deposit.py META.json slides.pdf` creates a **draft** only; Josh publishes it.
Metadata lives in `docs/talks/*.zenodo.json`. Needs `ZENODO_TOKEN` (deposit:write scope) and
`zenodo.org` allowed in the environment's network settings. Get employer clearance before
posting any deck: the EASD 2026 deck (© Lilly) is not cleared and must not be uploaded.
The Festival of Genomics 2025 deck is **on hold** (Josh, Oct 2026): do not upload until he says so.

## Bib keys for key papers

- `chiou2021interpreting` — T1D + exocrine pancreas, *Nature* 2021
- `chiou2021single` — islet scATAC-seq, 2021
- `sun2023plasma` — UKB-PPP, *Nature* 2023
- `intact2025multi` — Multi-INTACT methods paper

## Don't touch unless re-templating

- `_sass/` — al-folio CSS (upstream, with earlier customizations in `_base.scss`, `_cv.scss`,
  `_projects.scss`). Put new site-specific styles in `_sass/_custom.scss`, which is imported last.
- `assets/libs/` — vendored JS libraries
- `_config.yml` third_party_libraries block — library versions/integrity hashes
- `bin/` — CI scripts (upstream)

## Project card images

Each project card has a 16:10 image set via `img:` in its frontmatter, in `assets/img/projects/work/`
and `assets/img/projects/fun/`:
- Paper cards (T1D, islet, UKB-PPP) use cropped panels from Josh's papers. The same crops serve as
  `preview` thumbnails in `papers.bib`; other selected papers' thumbnails are in
  `assets/img/publication_preview/`.
- Lilly, Pfizer, and Home Assistant are drawn by `scripts/render_project_art.py` from synthetic data
  (no real results; the Lilly and Pfizer cards say so in their credit line).
- Travel is drawn by `scripts/render_travel_card.py` from the travel data files. Re-run it after
  editing them. Those files are auto-generated, so hand additions (Milan and Rome, 2026) are lost
  on a Takeout re-run unless the export includes them.
- `img_credit:` in a project's frontmatter adds a "Card image: …" attribution line at the bottom of
  its page. Every figure taken from a paper needs one.
- `og_image:` points at a JPG copy in `assets/img/projects/og/` (social sites don't read WebP/SVG
  reliably). Regenerate it when the card image changes.

To replace a card image with a photo:
1. Run `python3 scripts/prep_images.py /path/to/source assets/img/projects/work/` (or `fun/`)
2. Update the `img:` field in the project's `_projects/*.md` frontmatter
3. Optionally add `img_position: top` (or `center`, `bottom`) to control cropping via CSS `object-position`

Image pipeline generates responsive WebP versions at 480/800/1400px widths automatically.
