# Project status

_Last updated: 2026-10-04 · branch `master` (merge of `claude/islet-greenwald-style`)_

The one-page handoff: what is true right now, what is waiting on whom, and where the detail
lives. Rewritten in place at the end of each working session; history is in git and in
[`DECISIONS.md`](DECISIONS.md), not here.

## 1. What this project is

Josh Chiou's personal academic website, an al-folio Jekyll fork deployed to GitHub Pages at
joshchiou.github.io. Start at [`../CLAUDE.md`](../CLAUDE.md), then
[`site-guide.md`](site-guide.md) for what feeds each page.

## 2. Current state

- **What is live** is whatever `deploy.yml` last built from `master`. The 2026-10-04 session merged
  `claude/islet-greenwald-style` (PR #62 plus the commits after it); its deploy is the first to run
  the new number checks before going live. If that Deploy site run is red, the site still shows
  the 2026-10-03 build.
- **Merged on 2026-10-04:**
  - Islet page cites Greenwald 2019 instead of Wortham 2023; style guide filled out.
  - Publication counts come from `papers.bib` at build time; the thesis is listed but not counted,
    preprints count until published (39 today)
    ([D-014](DECISIONS.md#d-014-publication-counts-come-from-papersbib-at-build-time),
    [D-019](DECISIONS.md#d-019-the-publication-count-includes-unpublished-preprints-but-not-the-thesis)).
  - Checks and tests: `check_site.py` (numbers across pages), `check_sri.py` (CDN hashes),
    `check_preprints.py`, and browser tests in `tests/`, run by the new Site checks workflow on
    every PR, push, and Monday; `check_site.py` also gates the deploy.
  - Fixed: the Swiper hash that froze the cocktails and travel carousels, and site search, broken
    on every page by the deferred `theme.js`
    ([D-016](DECISIONS.md#d-016-inline-scripts-read-the-theme-from-data-theme-because-themejs-is-deferred)).
  - Cycling data from Apple Health; Strava frozen at 2026-06-21; 91 Health rides imported (55
    after the archive, 36 on 2026 days Strava missed), 148 rides in all through 2026-09-10 ([D-018](DECISIONS.md#d-018-cycling-data-comes-from-apple-health-not-the-strava-api)).
  - Journal chips: five journals in a fixed order ([D-020](DECISIONS.md#d-020-journal-chips-use-a-fixed-order)).
  - Content, style, and design review fixes, including Josh's wording for the Lilly and Pfizer
    pages.
- **Scholar stats:** 8,655 citations, h-index 28 (`_data/scholar_stats.json`, 2026-10-03).
- **Not yet run on GitHub:** the Site checks workflow and `check_preprints.py` (the bioRxiv API and
  jsDelivr are blocked in the cloud sandbox, so they were tested locally with stand-ins).

## 3. Settled decisions

The full append-only log, 21 entries from D-001 to D-021, is [`DECISIONS.md`](DECISIONS.md).
D-001 to D-013 were settled on 2026-10-03, D-014 to D-021 on 2026-10-04.

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
| n/a   | Handoff docs follow the `handoff` skill: this file rewritten in place, `DECISIONS.md` append-only | [`.claude/handoff-inputs.md`](../.claude/handoff-inputs.md)                                               |

## 4. Open items (ranked by impact)

1. **Set up the ride Shortcut and its GitHub token** (owner only), following
   [`cycling-data.md`](cycling-data.md). Rides through 2026-09-10 are imported; later rides need the
   Shortcut or another Health export. The `STRAVA_*` repo secrets can be deleted.
2. **Revoke the Zenodo token that was pasted into an earlier chat** (owner only). Create a new
   one with `deposit:write` scope and store it as `ZENODO_TOKEN` in the environment settings,
   never in chat.
3. **PR #49 is waiting on Josh.** It now also conflicts with `scripts/update_scholar.py`, which no
   longer counts papers (D-014). "Harden data-pipeline scripts against API changes; fix h-index
   count-up", opened 2026-07-28 from another session. It touches the same data scripts that #53
   and #58 changed, so expect overlap; it hasn't been checked against the current `master`.
   Leave it alone unless Josh asks.
4. **When the SURMOUNT-5 proteomics paper is published**, follow the four-step checklist under
   "Pending" in [`site-guide.md`](site-guide.md): bib entry, Lilly project page, `.lycheeignore`,
   news item, and optionally a real figure in place of the synthetic card
   ([D-007](DECISIONS.md#d-007-work-without-public-figures-gets-synthetic-illustrations)).
5. **Talk decks stay offline until cleared**
   ([D-003](DECISIONS.md#d-003-talk-slides-go-to-zenodo-and-only-with-employer-clearance)). The
   Festival of Genomics 2025 metadata is ready; upload only when Josh says so.
6. **Stale branches on GitHub** (owner to delete, or say the word). Merged: `claude/director-easd-update`,
   `claude/docs-style`, `claude/figure-fetch`, `claude/fix-data-refresh`, `claude/lilly-colors`,
   `claude/project-graphics`, `claude/scholar-serpapi`, `claude/vidra-preprint`. Closed PR #54:
   `auto/new-publications-1790979034`. Not checked: `copilot/fix-doi-errors-in-publications`.
   Keep `claude/personal-website-review-g4soy3`; it is PR #49's branch.

7. **Owner checks from the content review:** reuse terms for the T1D and islet card figures
   (non-CC-BY papers), and the Lilly card colors (D-008), which a reader could map to the drugs.
8. **Polish not done:** a higher-resolution Greenwald thumbnail (the open-access figure is on
   hosts this environment's network policy blocks; allow them or upload the figure), the
   leftover card in five-item grids, extra badge colors, the UCSD logo and white figure
   backgrounds in dark mode.

## 5. Known-stale documentation

- `docs/superpowers/` records the April and May 2026 redesigns and is not kept current, by design
  (see "History" in [`site-guide.md`](site-guide.md)). Where it disagrees with the guides or
  `CLAUDE.md`, they win.
