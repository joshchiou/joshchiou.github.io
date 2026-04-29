# Copilot Instructions

Personal academic website — customized fork of [al-folio](https://github.com/alshedivat/al-folio). Built with Jekyll + Liquid templates, deployed to GitHub Pages.

## Build & Dev

```bash
bundle install                    # first time only
bundle exec jekyll serve          # local dev at http://localhost:4000
bundle exec jekyll build --strict_front_matter  # production build (use before pushing)
docker compose up                 # recommended — matches CI exactly
```

No test suite. Linting via Prettier (Liquid/HTML/JS):
```bash
npx prettier --check .            # check
npx prettier --write .            # fix
```

## Architecture

All personal content lives in a small set of files; everything else is upstream al-folio template:

| File/Dir | Purpose |
|---|---|
| `_pages/about.md` | Landing page body copy |
| `_config.yml` | Site metadata, feature flags, nav |
| `_data/cv.yml` | CV structured data (experience, education, skills, awards) |
| `_bibliography/papers.bib` | All publications (rendered via jekyll-scholar) |
| `_news/*.md` | News items on the about page (reverse-chronological) |
| `_projects/*.md` | Project cards (`work_` or `fun_` prefix) |
| `_data/contributions.yml` | Open-source PR list |
| `_data/strava_*.json` | Auto-updated by GitHub Actions weekly |
| `_data/travel_*.yml` | From `scripts/parse_location_history.py` |

**Template files to leave alone** (upstream al-folio, will conflict on upgrades):
- `_sass/` — except custom additions at the bottom of `_base.scss`
- `assets/libs/` — vendored JS
- `_config.yml` `third_party_libraries` block (integrity hashes)
- `bin/` — CI scripts

**Custom template overrides** (safe to edit):
- `_layouts/bib.liquid` — Altmetric badge + citation counts
- `_includes/publication_meta.liquid` — per-paper metadata display
- `_includes/head.liquid` — Google Search Console verification tag

## Key Conventions

**Tagline sync:** When role/focus changes, update both `_pages/about.md` `subtitle:` frontmatter AND `_config.yml` `description:` field together.

**Project cards:** Frontmatter fields: `layout: page`, `title`, `description`, `img`, `importance` (integer, lower = higher priority), `category: work` or `category: fun`, optionally `related_publications: true`. Cite papers in body with `{% cite bib_key %}`.

**News items:** Use `layout: post`, `date: YYYY-MM-DD HH:MM:SS-OFFSET`, `inline: true`. Short inline HTML snippets, not markdown prose.

**Publications:** Cite in project pages with `{% cite bib_key %}`. Key bib keys: `chiou2021interpreting` (T1D + exocrine, *Nature* 2021), `chiou2021single` (islet scATAC-seq), `sun2023plasma` (UKB-PPP, *Nature* 2023), `intact2025multi` (Multi-INTACT).

**Project images:** Use `python3 scripts/prep_images.py <src_dir> assets/img/projects/work/` to generate responsive WebP. Update `img:` frontmatter. Add `img_position: top|center|bottom` to control CSS `object-position` cropping.

## Data Pipelines

**Strava** (auto via `.github/workflows/update-strava.yml`, weekly Monday 06:00 UTC):
```bash
python3 scripts/update_strava.py  # requires STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN env vars
```

**Travel** (manual, run locally after Google Maps Timeline JSON export):
```bash
python3 scripts/parse_location_history.py /path/to/location-history.json
# outputs _data/travel_countries.yml and _data/travel_cities.yml
# geocodes via Nominatim; caches to scripts/.geocode_cache.json (~5 min first run, instant on re-runs)
# review travel_cities.yml before committing — contains noise from restaurants/shops
```

## CI/CD

- **Deploy:** Pushes to `main`/`master` trigger build → PurgeCSS → GitHub Pages deploy
- **Broken links:** Checked via `broken-links.yml` / `broken-links-site.yml`
- **Publications/GitHub stats:** Auto-updated via scheduled workflows
