# CLAUDE.md

Personal website — al-folio Jekyll fork. Claude Code context.

## What this is

Customized fork of [al-folio](https://github.com/alshedivat/al-folio). Customizations live in:

- `_pages/about.md` — landing page content
- `_data/cv.yml` — CV data (experience, education, skills, awards)
- `_bibliography/papers.bib` — all publications (jekyll-scholar)
- `_news/*.md` — news items shown on the about page
- `_projects/*.md` — project cards (work* and fun* prefixes)
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
**Strava API access is paid as of 30 June 2026.** Standard tier (which is what a personal
single-user app gets) requires a Strava Developer Program subscription, ~$11.99/month. Without
it the activities endpoint returns 403 while the token refresh still succeeds — which is exactly
how this pipeline broke on 2026-07-03. A missing `activity:read_all` scope produces the same
status code, so always read the 403 response body (now logged by `scripts/_http.py`) before
concluding which it is. If the subscription isn't renewed, the cycling page can run entirely on
the Apple Health backfill below; disable the workflow and keep `_data/health_rides.json` current.
On failure the workflow opens a single tracking issue rather than failing silently.

**Apple Health backfill (now the primary cycling source):** `scripts/parse_apple_health.py
~/Downloads/export.zip` — run locally after iPhone → Health → profile → Export All Health Data.
Writes `_data/health_rides.json` (cycling only, in Strava's activity shape). Handles both pre- and
post-iOS 16 export layouts; `--dry-run` prints per-month coverage first.

Committing that one file is the whole update: `.github/workflows/update-cycling.yml` fires on any
push touching it and runs `update_strava.py --offline`, which rebuilds
`strava_calendar/stats/rides.json` from the backfill without calling Strava. Never hand-edit the
derived files.

`update_strava.py` merges the backfill with API results (when the API is available) on every run,
dropping duplicates by start time (±25 min) and distance (±25%) — matching on start time, not
date, so a two-way commute isn't collapsed into one ride. Two guards protect the switchover, both
bypassed by `--force`: it declines to write if any month present in the current data has no rides
in the new dataset, and preserves the existing files if the total drops more than 20%. Declining
exits non-zero under `--offline` (an explicit rebuild that does nothing must not report success)
but exits 0 for a scheduled API poll, where the next run self-heals.

The derived files carry `ride_sources` so the page credits Apple Health and/or Strava accurately
rather than inferring it from arithmetic that deduping would skew.

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

**Scholar caveat:** Google has no official Scholar API, so `update_scholar.py` shells out to
`scholarly`, which scrapes. Measured against citation changes in git history (May–Jul 2026) only
about 40% of weekly runs actually reach Google; the rest silently preserve the previous numbers.
That is why the script records `last_success_at` (advanced only by a real fetch) and marks
preserved runs `source: "preserved"` — a run that exits 0 is not evidence the fetch worked. The
workflow's `--check-freshness 35` gate catches a permanently stuck scraper. Free alternatives with
real APIs exist if the counts ever need to be reliable: OpenAlex (no key), Semantic Scholar, and
Crossref — all report lower counts than Google Scholar because they index less.

**Shared HTTP:** all API-facing scripts use `scripts/_http.py` (`request_with_retry` /
`get_json`) for retry, backoff, `Retry-After` and rate-limit handling. Add new API calls through
it rather than calling `requests` directly. `update_scholar.py` is the exception — it shells out
to `scholarly` instead of making HTTP calls itself.

Each pipeline preserves last-known-good data rather than publishing a regression when an API
misbehaves (see the drop-tolerance guard in `update_strava.py` and the preserve-on-failure paths
in `update_github.py` / `update_scholar.py`).

## Bib keys for key papers

- `chiou2021interpreting` — T1D + exocrine pancreas, _Nature_ 2021
- `chiou2021single` — islet scATAC-seq, 2021
- `sun2023plasma` — UKB-PPP, _Nature_ 2023
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
