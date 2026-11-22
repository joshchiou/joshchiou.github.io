# Project status

_Last updated: 2026-11-22 · branch `claude/keen-curie-wsfpjj` (not merged)_

The one-page handoff: what is true right now, what is waiting on whom, and where the detail
lives. Rewritten in place at the end of each working session; history is in git and in
[`DECISIONS.md`](DECISIONS.md), not here.

## 1. What this project is

Josh Chiou's personal academic website, an al-folio Jekyll fork deployed to GitHub Pages at
joshchiou.github.io. Start at [`../CLAUDE.md`](../CLAUDE.md), then
[`site-guide.md`](site-guide.md) for what feeds each page.

## 2. Current state

- **What is live** is whatever `deploy.yml` last built from `master`. The 2026-11-22 site review is
  on `claude/keen-curie-wsfpjj` and is not live until it is merged; no PR has been opened.
- **On the branch (2026-11-22 review):**
  - Homepage stats: the real numbers were already in the static HTML; the count-up now only plays
    in a visible tab, writes nothing before its first frame, and a timer restores the real number,
    so a crawler snapshot can't catch a 0.
  - Publications filter: "Showing X of 39 publications", matching the header (the thesis was
    counted as the 40th; D-019).
  - Theme toggle icons at 1.2rem (the filled sun was a speck at 16px); `color-scheme` follows the
    site theme, so the Ctrl+K modal and other scrollbars are dark in dark mode.
  - Cycling projection by day as of the last ride
    ([D-024](DECISIONS.md#d-024-the-cycling-projection-is-by-day-as-of-the-last-ride)).
  - Dark mode: figures and thumbnails dimmed and framed; Altmetric's white disc appears only after
    the badge loads.
  - Research cards keep the paper figures; diagrams were tried and Josh preferred the figures
    ([D-023](DECISIONS.md#d-023-the-homepage-research-cards-keep-the-paper-figures)).
  - One CTA row (Publications, CV, PDF); code page without KPI tiles; homepage news without code
    items ([D-026](DECISIONS.md#d-026-the-code-page-and-homepage-lead-with-work-not-activity-counts)).
  - Social card redrawn without numbers, plus `og:image` size and alt tags
    ([D-025](DECISIONS.md#d-025-figures-photos-and-the-social-card-stay-as-designed)).
  - Tests: filter count, cycling pace line, homepage news; `check_site.py` checks the code page's
    repo list instead of the removed tiles. All 73 tests and `check_site.py` pass locally (CDN via
    the npm fallback); `check_sri.py` not run (jsDelivr blocked in the sandbox).
- **Scholar stats:** 9,024 citations, h-index 28 (`_data/scholar_stats.json`, 2026-11-18).
- **Cycling data** stops at 2026-09-10 (`check_site.py` warns: 73 days without a ride).

## 3. Settled decisions

The full append-only log, D-001 to D-026, is [`DECISIONS.md`](DECISIONS.md). D-001 to D-013 were
settled on 2026-10-03, D-014 to D-021 on 2026-10-04, D-022 on 2026-11-03, and D-023 to D-026 on
2026-11-22.

| #     | Decision                                                                                          | Ref                                                                                                       |
| ----- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| D-001 | Scholar stats come from SerpAPI; Google Scholar blocks Actions runners                            | [D-001](DECISIONS.md#d-001-scholar-stats-come-from-serpapi)                                               |
| D-002 | A failed Scholar fetch exits non-zero and leaves the stats file alone                             | [D-002](DECISIONS.md#d-002-a-failed-scholar-fetch-turns-the-run-red-and-changes-nothing)                  |
| D-003 | Slides go to Zenodo with employer clearance; EASD 2026 not cleared, Festival of Genomics on hold  | [D-003](DECISIONS.md#d-003-talk-slides-go-to-zenodo-and-only-with-employer-clearance)                     |
| D-004 | Homepage theme images are 5:2 two-panel composites of whole figures, with a divider               | [D-004](DECISIONS.md#d-004-homepage-theme-images-are-52-composites-of-whole-figures)                      |
| D-005 | Population proteomics card: pQTL map plus BAFF/TNFRSF13C genotype boxplots, not FSHB              | [D-005](DECISIONS.md#d-005-the-population-proteomics-card-pairs-the-pqtl-map-with-genotype-boxplots)      |
| D-006 | The T1D card uses the Manhattan plot (Fig. 1a)                                                    | [D-006](DECISIONS.md#d-006-the-t1d-card-uses-the-manhattan-plot)                                          |
| D-007 | Work without public figures gets synthetic illustrations that say so                              | [D-007](DECISIONS.md#d-007-work-without-public-figures-gets-synthetic-illustrations)                      |
| D-008 | Lilly card: red `#e0241a` and blue `#2e5a94`; red is the larger decrease and the increase         | [D-008](DECISIONS.md#d-008-the-lilly-illustration-uses-lilly-red-and-blue-with-red-for-the-larger-change) |
| D-009 | American English and no em dashes in site text, docs, and commits                                 | [D-009](DECISIONS.md#d-009-american-english-and-no-em-dashes-everywhere)                                  |
| D-010 | The CV PDF is rendered at deploy time, not committed                                              | [D-010](DECISIONS.md#d-010-the-cv-pdf-is-rendered-at-deploy-time-not-committed)                           |
| D-011 | Data workflows redeploy the site through `workflow_run`                                           | [D-011](DECISIONS.md#d-011-data-workflows-redeploy-the-site-through-workflow_run)                         |
| D-012 | The Preprint badge matches both `10.1101/` and `10.64898/`                                        | [D-012](DECISIONS.md#d-012-newer-medrxiv-and-biorxiv-dois-use-the-1064898-prefix)                         |
| D-013 | The Timeline parser only appends; deleted cities stay deleted                                     | [D-013](DECISIONS.md#d-013-the-timeline-parser-only-appends-to-the-travel-files)                          |
| D-014 | Publication counts come from `papers.bib` at build time; `check_site.py` gates the deploy         | [D-014](DECISIONS.md#d-014-publication-counts-come-from-papersbib-at-build-time)                          |
| D-015 | Journal chips: Nature, Nature Genetics, Nature Medicine, Cell, Nature Immunology                  | [D-015](DECISIONS.md#d-015-the-homepage-journal-chips-are-the-nature-and-cell-flagship-research-journals) |
| D-016 | Inline scripts read `data-theme`; `theme.js` is deferred                                          | [D-016](DECISIONS.md#d-016-inline-scripts-read-the-theme-from-data-theme-because-themejs-is-deferred)     |
| D-017 | Journal chips ordered by 2025 impact factor; re-check each June                                   | [D-017](DECISIONS.md#d-017-journal-chips-are-ordered-by-impact-factor)                                    |
| D-018 | Cycling data from Apple Health (Shortcut plus Health export); Strava frozen at 2026-06-21         | [D-018](DECISIONS.md#d-018-cycling-data-comes-from-apple-health-not-the-strava-api)                       |
| D-019 | Count includes unpublished preprints, not the thesis (39)                                         | [D-019](DECISIONS.md#d-019-the-publication-count-includes-unpublished-preprints-but-not-the-thesis)       |
| D-020 | Journal chips in a fixed order: Nature, Cell, Nature Medicine, Nature Genetics, Nature Immunology | [D-020](DECISIONS.md#d-020-journal-chips-use-a-fixed-order)                                               |
| D-021 | Health fills days the Strava archive missed; rides store am/pm for matching                       | [D-021](DECISIONS.md#d-021-health-fills-the-days-the-strava-archive-missed)                               |
| D-022 | Selected papers are a filter on /publications/, not a second list                                 | [D-022](DECISIONS.md#d-022-selected-papers-are-a-filter-on-the-publications-page-not-a-second-list)       |
| D-023 | Homepage research cards keep the paper figures (diagrams tried and rejected)                      | [D-023](DECISIONS.md#d-023-the-homepage-research-cards-keep-the-paper-figures)                            |
| D-024 | Cycling projection is by day, as of the last ride                                                 | [D-024](DECISIONS.md#d-024-the-cycling-projection-is-by-day-as-of-the-last-ride)                          |
| D-025 | Figures, photos, and the social card stay as designed (dimming and new card reverted)             | [D-025](DECISIONS.md#d-025-figures-photos-and-the-social-card-stay-as-designed)                           |
| D-026 | Code page and homepage news lead with work, not activity counts                                   | [D-026](DECISIONS.md#d-026-the-code-page-and-homepage-lead-with-work-not-activity-counts)                 |
| n/a   | Handoff docs follow the `handoff` skill: this file rewritten in place, `DECISIONS.md` append-only | [`.claude/handoff-inputs.md`](../.claude/handoff-inputs.md)                                               |

## 4. Open items (ranked by impact)

1. **Review and merge `claude/keen-curie-wsfpjj`** (owner). Look at the new social card (Josh
   was unsure about its dot grid) and the dark-mode changes; after merging, re-scrape the homepage in LinkedIn's
   Post Inspector so it drops the cached card with old numbers.
2. **Set up the ride Shortcut and its GitHub token** (owner only), following
   [`cycling-data.md`](cycling-data.md). No ride since 2026-09-10 has been imported, so the cycling
   page's "this year" numbers are as of that date. The `STRAVA_*` repo secrets can be deleted.
3. **Revoke the Zenodo token that was pasted into an earlier chat** (owner only). Create a new
   one with `deposit:write` scope and store it as `ZENODO_TOKEN` in the environment settings,
   never in chat.
4. **Talks section structure** (proposed 2026-11-22, not built): keep `_data/cv.yml` as the one
   source, add optional `date`, `type` (oral, invited, poster), `session`, and `project` (link to
   the project page) fields, and a homepage "upcoming / recent talk" line driven by the newest
   entry. Waits on Josh's go-ahead.
5. **PR #49 is waiting on Josh.** It conflicts with `scripts/update_scholar.py`, which no longer
   counts papers (D-014), and touches the same data scripts as #53 and #58. Leave it alone unless
   Josh asks.
6. **When the SURMOUNT-5 proteomics paper is published**, follow the checklist under "Pending" in
   [`site-guide.md`](site-guide.md).
7. **Talk decks stay offline until cleared**
   ([D-003](DECISIONS.md#d-003-talk-slides-go-to-zenodo-and-only-with-employer-clearance)). The
   EASD 2026 deck is not cleared; the Festival of Genomics 2025 deck is on hold.
8. **Stale branches on GitHub** (owner to delete, or say the word). Merged: `claude/director-easd-update`,
   `claude/docs-style`, `claude/figure-fetch`, `claude/fix-data-refresh`, `claude/lilly-colors`,
   `claude/project-graphics`, `claude/scholar-serpapi`, `claude/vidra-preprint`. Closed PR #54:
   `auto/new-publications-1790979034`. Not checked: `copilot/fix-doi-errors-in-publications`.
   Keep `claude/personal-website-review-g4soy3`; it is PR #49's branch.
9. **Owner checks from the content review:** reuse terms for the T1D and islet card figures
   (non-CC-BY papers), and the Lilly card colors (D-008), which a reader could map to the drugs.
10. **Polish not done:** the leftover card in five-item grids (code page repos too), extra badge
    colors, and the UCSD logo in dark mode.

## 5. Known-stale documentation

- `docs/superpowers/` records the April and May 2026 redesigns and is not kept current, by design
  (see "History" in [`site-guide.md`](site-guide.md)). Where it disagrees with the guides or
  `CLAUDE.md`, they win.
