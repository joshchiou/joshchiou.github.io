# Site guide

How joshchiou.github.io is put together: what each page shows, which file feeds it, and where to
make common changes. For visual design see [design.md](design.md). For writing rules see
[writing-style.md](writing-style.md).

## Pages

The site is an [al-folio](https://github.com/alshedivat/al-folio) Jekyll fork. The navigation bar
lists four pages in this order; the name in the top-left corner links to the homepage.

| Page             | URL              | Source                                            | Fed by                                                                                                                                           |
| ---------------- | ---------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| About (homepage) | `/`              | `_pages/about.md`, `_layouts/about.liquid`        | bio text in `about.md`, `_data/research_themes.yml`, selected papers in `papers.bib`, `_news/`, social links and `contact_note` in `_config.yml` |
| Publications     | `/publications/` | `_pages/publications.md`                          | `_bibliography/papers.bib`, `_data/scholar_stats.json`, talks from `_data/cv.yml`, `_data/press.yml`                                             |
| Projects         | `/projects/`     | `_pages/projects.md`, `_includes/projects.liquid` | `_projects/*.md`                                                                                                                                 |
| Code             | `/code/`         | `_pages/code.md`                                  | `_data/github_stats.json`, `_data/repositories.yml`, `_data/contributions.yml`                                                                   |
| CV               | `/cv/`           | `_pages/cv.md`, `_layouts/cv.liquid`              | `_data/cv.yml`; the PDF is rendered from this page at deploy time                                                                                |

Two pages are reachable but not in the navigation bar: `/news/` (full news archive) and the 404 page.

### Homepage, top to bottom

1. Name, tagline (`subtitle` in `about.md` front matter), and profile photo.
2. Bio: two short paragraphs and a link to the CV.
3. **research**: three theme cards from `_data/research_themes.yml`, each linking to a project,
   with a 5:2 image from `assets/img/research_themes/`.
4. **selected publications**: entries in `papers.bib` with `selected = {true}`.
5. **news**: the most recent items from `_news/`.
6. Contact: social icons and `contact_note` from `_config.yml`.

### Publications page, top to bottom

1. Citation metrics from `_data/scholar_stats.json` (`_includes/publication_meta.liquid`).
2. Search box.
3. **Selected**: papers with `selected = {true}`, ordered by `cv_order`, each with a 4:3 `preview`
   thumbnail and a one-sentence `tldr`.
4. **All publications**: every entry in `papers.bib`, newest first.
5. **Talks & Presentations**: read from the section of that name in `_data/cv.yml`.
6. **Press**: `_data/press.yml`, newest first.

### Projects

Each file in `_projects/` is one card and one page. The filename prefix sets the section:
`work_*.md` (category `work`) and `fun_*.md` (category `fun`). Cards within a section are ordered by
`importance` (lower comes first).

Every project page follows the same pattern:

1. A **TL;DR** box (`<div class="project-tldr">`) with one sentence.
2. Prose sections under `##` headings.
3. For work projects, a closing **Related:** line linking to a related project.
4. A "Card image: …" credit line, generated from `img_credit` in the front matter.

| Front matter           | Purpose                                                                              |
| ---------------------- | ------------------------------------------------------------------------------------ |
| `title`, `description` | Card title and one-line summary; the description is also the page's meta description |
| `img`                  | 16:10 card image, also used on the page                                              |
| `img_credit`           | Attribution line; required for any figure taken from a paper                         |
| `img_position`         | Optional `top`, `center`, or `bottom` crop anchor                                    |
| `og_image`             | Relative path to a JPG used for link previews                                        |
| `importance`           | Sort order within the section                                                        |
| `category`             | `work` or `fun`                                                                      |
| `related_publications` | `true` to list cited papers at the bottom                                            |

The fun pages pull from their own data files: cycling from `_data/strava_*.json`, `bikes.yml`,
`bike_gallery.yml`, `featured_rides.yml`, `cycling_locations.yml`; cocktails from
`cocktail_recipes.yml`, `cocktail_gallery.yml`; Home Assistant from `hass_layers.yml`,
`hass_stats.yml`; travel from `travel_countries.yml`, `travel_cities.yml`; Claire from
`claire.yml`, `claire_genetics.yml`.

## Automation

| Workflow                            | When                                                          | What it does                                                                                           |
| ----------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Deploy site (`deploy.yml`)          | Push to master, manual, and after each data workflow succeeds | Builds, renders the CV PDF, runs PurgeCSS, deploys to GitHub Pages                                     |
| Update Strava Data                  | Daily 06:00 UTC                                               | Refreshes `_data/strava_*.json`                                                                        |
| Update GitHub Stats                 | Tuesdays                                                      | Refreshes `_data/github_stats.json`, including stats for every repo in `repositories.yml`              |
| Update Scholar Stats                | Wednesdays                                                    | Refreshes `_data/scholar_stats.json` via SerpAPI (`SERPAPI_KEY` secret); a red run means stale numbers |
| Discover New Publications           | Thursdays                                                     | Opens a PR with ORCID works missing from `papers.bib`                                                  |
| Enrich Publication Metadata         | Manual                                                        | Opens a PR adding abstracts, PMIDs, and open-access PDF links                                          |
| Lint, Check for broken links        | Pull requests                                                 | Prettier (`npx prettier --check .`) and lychee on the source files; both should pass                   |
| Lighthouse CI, broken links on site | After deploy                                                  | Performance and built-site link checks                                                                 |

Generated data files, vendored files, and the historical notes in `docs/superpowers/` are listed in
`.prettierignore`. Sites that block bots, gated URLs, and Liquid expressions (which lychee would
read as literal paths) are listed in `.lycheeignore`. Run `npx prettier --write .` before
committing template or style changes.

Data workflows push with `GITHUB_TOKEN`, which does not trigger other workflows, so `deploy.yml`
lists each of them under `workflow_run`. Add any new data workflow to that list.

## Scripts

| Script                                                                                                 | Use                                                                          |
| ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `update_strava.py`, `update_github.py`, `update_scholar.py`, `update_publications.py`, `enrich_bib.py` | Run by the workflows above                                                   |
| `parse_location_history.py`                                                                            | Rebuilds the travel data from a Google Maps Timeline export (run locally)    |
| `render_travel_card.py`                                                                                | Redraws the travel card map from the travel data                             |
| `render_project_art.py`                                                                                | Redraws the Lilly, Pfizer, and Home Assistant card illustrations             |
| `render_og_image.py`                                                                                   | Renders `assets/img/og-image.png` (the site-wide link preview) from its SVG  |
| `prep_images.py`, `publish_images.sh`                                                                  | Convert photos to responsive WebP; publish gallery photos to GitHub releases |
| `build_cv_pdf.py`                                                                                      | Renders `/cv/` to PDF (the deploy workflow runs it)                          |
| `zenodo_deposit.py`                                                                                    | Creates a Zenodo draft for talk slides; Josh publishes it                    |

## Common changes

**New paper.** Add the entry to `papers.bib` (or merge the weekly discovery PR). For a selected
paper, add `selected = {true}`, a `cv_order`, a `tldr` (see the writing guide), and a 4:3 `preview`
image in `assets/img/publication_preview/`.

**News item.** Add `_news/YYYY-MM-DD-slug.md` with `layout: post`, `date`, and `inline: true`, and
one or two sentences of inline HTML. Links use `target="_blank"`.

**Talk.** Add an item to the "Talks & Presentations" section of `_data/cv.yml`. Slides and video go
in `linkitems`.

**Press mention.** Add to the top of `_data/press.yml`.

**Repository on the code page.** Add `repo: owner/name` and a one-sentence `desc` to
`_data/repositories.yml`, ending with the role where it adds something ("Author." or "Maintainer."). Cards show two lines,
so keep it under about 60 characters. Repos owned by
`joshchiou` show the short name; others show `owner/name`.

**New role or title.** Follow the tagline checklist in [CLAUDE.md](../CLAUDE.md), and add a news item.

**New project.** Copy an existing `_projects/` file of the same category, keep the page pattern
above, and make a 16:10 card image (see "Project card images" in CLAUDE.md).

## Pending: SURMOUNT-5 proteomics paper

The analysis code ([EliLillyCo/surmount5-proteomics](https://github.com/EliLillyCo/surmount5-proteomics))
and the results dashboard (surmount5-proteomics.lilly.com) are linked from the Lilly project page.
The dashboard needs a reviewer token until publication. When the paper is published:

1. Add it to `papers.bib` with `code` (the GitHub URL) and `website` (the dashboard URL) fields,
   `selected = {true}`, a `tldr`, and a `preview`.
2. On `_projects/work_lilly_proteomics.md`, change "opens to the public when the paper is
   published" to describe the dashboard as public, and cite the paper.
3. Remove the dashboard line from `.lycheeignore` so the link checker covers it.
4. Add a news item, and consider replacing the synthetic Lilly card illustration with a figure
   from the paper (with `img_credit`).

## History

`docs/superpowers/specs/` and `docs/superpowers/plans/` record earlier redesigns (April and May
2026). They explain past decisions but are not kept up to date; this guide and CLAUDE.md are.
