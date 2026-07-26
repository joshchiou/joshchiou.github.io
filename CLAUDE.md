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

Three places to update together when role/focus changes:
1. `_pages/about.md` subtitle (visible header)
2. `_config.yml` description (meta tag)
3. `_includes/head.liquid` homepage Person JSON-LD (`jobTitle`, `worksFor`, `description`)

The homepage Person + WebSite structured data is hand-curated in `head.liquid`.
`_includes/metadata.liquid` deliberately skips the homepage so the same subject
isn't described by two competing entities; both reference the same
`@id` (`https://joshchiou.github.io/#person`).

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

## Data pipelines

**Strava:** `scripts/update_strava.py` — run manually or via `.github/workflows/update-strava.yml`.
Requires env vars: `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`.
GitHub Actions secrets set in repo Settings → Secrets and variables → Actions.

**Travel:** `scripts/parse_location_history.py /path/to/location-history.json` — run locally after
downloading from Google Maps → Timeline → Export timeline data (JSON).
Outputs `_data/travel_countries.yml` and `_data/travel_cities.yml`. Geocodes via Nominatim and
caches to `scripts/.geocode_cache.json`. Review cities file before committing (noise from
restaurants/shops). First run ~5 min (289 places at 1 req/sec); re-runs instant.

**Contributions:** `scripts/update_contributions.py` — finds merged PRs to repos the user doesn't
own and opens a PR proposing `_data/contributions.yml` entries (weekly via
`.github/workflows/update-contributions.yml`). Proposed entries carry `needs_review: true`, a
placeholder `type`, and the PR title as a provisional `blurb` — always curate before merging.
Defaults to only PRs merged after the newest date already in the file; use `--since` to widen.
Run without `--pr` for a dry run.

**Shared HTTP:** all API-facing scripts use `scripts/_http.py` (`request_with_retry` /
`get_json`) for retry, backoff, `Retry-After` and rate-limit handling. Add new API calls through
it rather than calling `requests` directly. `update_scholar.py` is the exception — it shells out
to `scholarly` instead of making HTTP calls itself.

Each pipeline preserves last-known-good data rather than publishing a regression when an API
misbehaves (see the drop-tolerance guard in `update_strava.py` and the preserve-on-failure paths
in `update_github.py` / `update_scholar.py`).

## Bib keys for key papers

- `chiou2021interpreting` — T1D + exocrine pancreas, *Nature* 2021
- `chiou2021single` — islet scATAC-seq, 2021
- `sun2023plasma` — UKB-PPP, *Nature* 2023
- `intact2025multi` — Multi-INTACT methods paper

## Don't touch unless re-templating

- `_sass/` — al-folio CSS (upstream), except custom additions at the end of `_base.scss`
- `assets/libs/` — vendored JS libraries
- `_config.yml` third_party_libraries block — library versions/integrity hashes
- `bin/` — CI scripts (upstream)

## Project card images

Each project card has a thumbnail image set via `img:` in its frontmatter. Currently using
abstract SVGs in `assets/img/projects/work/` and `assets/img/projects/fun/`.

To replace an SVG with a real image:
1. Run `python3 scripts/prep_images.py /path/to/source assets/img/projects/work/` (or `fun/`)
2. Update the `img:` field in the project's `_projects/*.md` frontmatter
3. Optionally add `img_position: top` (or `center`, `bottom`) to control cropping via CSS `object-position`

Image pipeline generates responsive WebP versions at 480/800/1400px widths automatically.
