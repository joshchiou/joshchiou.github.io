# Decisions log

Append-only record of choices that constrain future work on this site. Each entry gives the
context, the decision, and why the alternatives were rejected.

These are things about the site that are **not** derivable from the code, written down so nobody
has to guess, and so nobody "fixes" them back. An entry is not a veto: if you are about to change
something an entry explains, say in your change why the original reason no longer applies. Never
edit an entry except to add `**Superseded by** [D-0NN](#<slug>)`, where `<slug>` is GitHub's
auto-anchor for the newer heading: lowercase, punctuation dropped, spaces to hyphens. So
`## D-001: Scholar stats come from SerpAPI` is `#d-001-scholar-stats-come-from-serpapi`.
Rewording a heading changes its anchor and breaks every link to it, so don't.

Entries D-001 to D-012 were written on 2026-10-03 from the work merged in PRs #52 to #59.

---

## D-001: Scholar stats come from SerpAPI

_Recorded 2026-10-03 (owner's choice of source) · `scripts/update_scholar.py`, PR #58_

**Context.** The citation count on /publications/ sat at 8,196 for weeks while the real number
was 8,655. Google Scholar serves a CAPTCHA to GitHub Actions runners, so the `scholarly` fetch in
the weekly workflow failed every time.

**Decision.** The workflow reads the profile through SerpAPI's Google Scholar Author API, with the
`SERPAPI_KEY` repo secret. The free plan covers one run a week. Without the key, the script falls
back to `scholarly`, which only works from a home connection, not from CI.

**Why not update the numbers by hand.** They go stale between edits; Josh had to supply the
8,655 figure himself to find out the count was behind.

## D-002: A failed Scholar fetch turns the run red and changes nothing

_Recorded 2026-10-03 · `scripts/update_scholar.py`, PR #53_

**Context.** The script used to keep the last-known values on a failed fetch, write them back
with a fresh `updated_at`, and exit 0. The workflow stayed green while the numbers were weeks old,
which is how the 8,196 count went unnoticed.

**Decision.** On a failed fetch the script exits non-zero and leaves `_data/scholar_stats.json`
untouched. A red Update Scholar Stats run means the site is showing stale numbers.

**Why not write "n/a" on failure.** One failed week would blank the metrics on the live site.
Keeping the old numbers and failing loudly is the better trade.

## D-003: Talk slides go to Zenodo, and only with employer clearance

_Recorded 2026-10 (owner's decision) · `scripts/zenodo_deposit.py`, `docs/talks/`_

**Context.** The repo is public, and talk decks contain employer data: the EASD 2026 deck is
© Lilly, and the Festival of Genomics 2025 deck contains Pfizer data.

**Decision.** Slides are archived on Zenodo for a permanent DOI, never committed to this repo.
`zenodo_deposit.py` creates a draft only, and Josh publishes it himself. The EASD 2026 deck is not
cleared and must not be uploaded anywhere. The Festival of Genomics 2025 deck is on hold until
Josh says otherwise ("we probably shouldn't post it publicly yet"); its metadata is ready in
`docs/talks/festival-of-genomics-2025.zenodo.json`.

**Why not commit the PDFs.** Anything pushed to a public repo stays in its history, so a deck
committed by mistake can't be fully withdrawn.

## D-004: Homepage theme images are 5:2 composites of whole figures

_Recorded 2026-10-03 (owner's request) · `assets/img/research_themes/`, PR #56_

**Context.** The homepage research cards reused the 16:10 project card images. On a phone the card
crops them, so the figures looked cut off.

**Decision.** Each theme card has its own 1200x480 (5:2) image with two panels, ideally from two
different papers, each fitted whole into its half, with a 4px `#c4c4c4` vertical divider between
them so they read as separate figures. `img_credit` in `_data/research_themes.yml` names both
sources. Never point a theme card at a 16:10 card image.

**Why not crop one figure tighter.** Any single crop that fits 5:2 loses most of a Manhattan plot
or UMAP, and still crops differently at each screen width.

## D-005: The population proteomics card pairs the pQTL map with genotype boxplots

_Recorded 2026-10-03 (owner's choice) · `assets/img/research_themes/population-proteomics.webp`, PR #56_

**Context.** The right panel first used the FSHB example, then the cis/trans effect-size
scatter (Sun 2023 Fig. 2c).

**Decision.** The right panel is the BAFF (TNFSF13B) and TNFRSF13C genotype boxplots from Sun et
al., _Nature_ 2023, Fig. 3c, next to the pQTL map (Fig. 2a).

**Why not FSHB.** It isn't central to the paper's story (owner's call).

**Why not the cis/trans scatter.** Josh wanted a panel that reads as a QTL. The boxplots show
protein level by genotype, and their blue and orange match the map's color coding.

## D-006: The T1D card uses the Manhattan plot

_Recorded 2026-10-03 (owner's choice) · `assets/img/projects/work/t1d-manhattan.webp`, PR #56_

**Context.** Josh named two candidates from Chiou et al., _Nature_ 2021: the Manhattan plot and
the CFTR figure.

**Decision.** The T1D project card and its publication thumbnail use the Manhattan plot (Fig. 1a),
with the leader lines and annotation text removed so it reads at card size. The diabetes genetics
theme card pairs it with the islet scATAC UMAP.

**Why not the CFTR figure.** It was the other candidate; the reason for preferring the Manhattan
plot wasn't recorded at the time.

## D-007: Work without public figures gets synthetic illustrations

_Recorded 2026-10-03 · `scripts/render_project_art.py`, PR #55_

**Context.** The Lilly, Pfizer, and Home Assistant cards had no public figures to use, and
unpublished trial results can't appear on the site.

**Decision.** Those cards are drawn by `render_project_art.py` from synthetic data, in real chart
forms from the work (trajectories, volcano plots), with no axis labels. The credit line says
"Illustration with synthetic data; it shows no study results." When the SURMOUNT-5 paper is
published, the Lilly card can switch to a real figure (see "Pending" in
[site-guide.md](site-guide.md)).

**Why not stock images or icons.** Josh asked for figures from the work where possible, and generic
art says nothing about the project.

## D-008: The Lilly illustration uses Lilly red and blue, with red for the larger change

_Recorded 2026-10-03 (owner's request) · `lilly()` in `scripts/render_project_art.py`, PR #59_

**Context.** The Lilly card used the generic dataviz blue and orange. Josh asked for Lilly colors,
sampled from the EASD 2026 deck.

**Decision.** Red `#e0241a` (the logo red) and blue `#2e5a94`. Red is the arm with the larger
decrease in the trajectory plot and the increased proteins in the volcano plot (owner's call).
Only the color values come from the deck. This applies only to the Lilly card and its homepage
version; other illustrations keep the dataviz palette.

**Why not the deck navy `#0c376d`.** It fails the dataviz validator's lightness-band check against
the red: it is dark enough to overpower the red as a data color. `#2e5a94` is the darkest step in
that family that passes every check.

## D-009: American English and no em dashes, everywhere

_Recorded 2026-10-03 (owner's rule) · [writing-style.md](writing-style.md), PR #56_

**Context.** The site mixed British and American spellings and used em dashes heavily.

**Decision.** All visible text, the docs, and commit messages use American English and no em
dashes. The grep in [CLAUDE.md](../CLAUDE.md) must come back empty. En dashes appear only in
number ranges.

## D-010: The CV PDF is rendered at deploy time, not committed

_Recorded 2026-10-02 · `scripts/build_cv_pdf.py`, `deploy.yml`, PR #52_

**Context.** A committed `assets/pdf/CV.pdf` has to be re-exported by hand after every edit to
`_data/cv.yml`, or it falls out of step with `/cv/`.

**Decision.** The deploy workflow renders `/cv/` to PDF with Playwright and Chromium, so the PDF
always matches the data. Print layout lives in the `@media print` block of `_sass/_custom.scss`.

## D-011: Data workflows redeploy the site through `workflow_run`

_Recorded 2026-10-03 · `.github/workflows/deploy.yml`, PR #53_

**Context.** The Scholar, GitHub stats, and Strava workflows push with `GITHUB_TOKEN`, and those
pushes don't trigger other workflows. New data was committed but never deployed.

**Decision.** `deploy.yml` also runs on `workflow_run` after each data workflow succeeds. Any new
data workflow that should update the live site must be added to that list.

**Why not push with a personal access token.** A PAT would work, but it is a long-lived secret with
wide scope, kept only to trigger a deploy.

## D-012: Newer medRxiv and bioRxiv DOIs use the 10.64898 prefix

_Recorded 2026-10-03 · `_layouts/bib.liquid`, PR #57_

**Context.** The VIDRA preprint (2026) couldn't be found under `10.1101/`; its DOI is
`10.64898/2026.07.04.26357214`. The Preprint badge only matched `10.1101/`.

**Decision.** The Preprint badge matches both `10.1101/` and `10.64898/`. Look up new medRxiv or
bioRxiv DOIs under both prefixes.

**Why not mark preprints by hand in the bib entry.** The DOI check already works for every older
preprint, and a per-entry flag is easy to forget.

## D-013: The Timeline parser only appends to the travel files

_Recorded 2026-10-03 (owner's request) · `scripts/parse_location_history.py`_

**Context.** The parser regenerated both travel files from scratch. That dropped the hand-added
Milan and Rome entries, the `continent` and `flag` fields on every country, and the `state` field
on US cities, none of which the parser produced. It also brought back every city that had been
pruned as noise. Since Google moved Timeline onto the phone, exports are manual, so partial
exports of recent months are the likely way to add trips.

**Decision.** A re-run appends only countries and cities missing from the files, at the end, and
never rewrites existing lines. New countries get a `flag` from the ISO code and need a `continent`
by hand; new US cities get a `state`. Every city the script has proposed is recorded in
`scripts/.travel_seen.json`, so one deleted from `travel_cities.yml` is not proposed again.

**Why not commit the seen list.** It names every town the script has proposed, including ones
deliberately left off the site, and the repo is public. The cost is that a machine without the file
proposes previously deleted cities once more.

## D-014: Publication counts come from papers.bib at build time

_Recorded 2026-10-04 (owner's request) · `_plugins/publication-stats.rb`, `scripts/check_site.py`_

**Context.** The homepage showed 40 publications and the publications page showed 38. The homepage
number came from `_data/scholar_stats.json`, where the weekly Scholar workflow wrote a count of
`papers.bib`; the publications page had "38 publications" typed into
`_includes/publication_meta.liquid`, which nobody updated when two papers were added in PR #57.
Nothing checked that the two agreed.

**Decision.** A Jekyll plugin counts `papers.bib` on every build and exposes the total, the
Selected count, and the top-journal counts as `site.data.publication_stats`. Every page reads from
it. `scholar_stats.json` holds only what comes from Scholar. `scripts/check_site.py` recounts
everything independently from the source files and compares it with the built pages; it runs on
every PR and gates the deploy.

**Why not keep the count in `scholar_stats.json`.** The file only changes when the Scholar fetch
succeeds (D-002), so a new paper wouldn't be counted until the next good Wednesday run, and never if
SerpAPI is down.

**Why not a Liquid tag such as jekyll-scholar's `bibliography_count`.** It can't take the journal
names from a list, so the top-journal counts would be hand-copied into the template.

## D-015: The homepage journal chips are the Nature and Cell flagship research journals

_Recorded 2026-10-04 (owner's question) · `top_journals` in `_config.yml`_

**Context.** The chips listed only _Nature_, _Nature Genetics_, and _Cell_, a list picked in the
April 2026 overhaul without a stated rule. Josh has papers in _Nature Medicine_ (2) and _Nature
Immunology_ (1) as well.

**Decision.** The chips name the flagship and specialty research journals of the Nature and Cell
families and _Science_: _Nature_, _Nature Genetics_, _Nature Medicine_, _Cell_, _Nature
Immunology_ (12 papers). Order is by paper count, ties in list order.

**Superseded by** [D-017](#d-017-journal-chips-are-ordered-by-impact-factor)

**Why not _Nature Communications_, _Science Advances_, _Cell Genomics_, or _Genome Biology_.** Good
journals, but broad-scope or open-access siblings; listing them would make the line read as every
journal rather than a highlight.

## D-016: Inline scripts read the theme from `data-theme`, because `theme.js` is deferred

_Recorded 2026-10-04 · `_includes/scripts/{search,echarts,vega,mermaid,diff2html}.liquid`_

**Context.** This fork loads `theme.js` with `defer` and sets the theme with a small inline script
in `head.liquid`, to avoid a flash of the wrong theme without blocking rendering. Upstream al-folio
loads `theme.js` normally, and its inline scripts call `determineComputedTheme()` from it. Here
those calls ran before `theme.js` and threw on every page, which stopped the site search setup
(the search button did nothing) and the ECharts code-block setup.

**Decision.** Inline scripts read `document.documentElement.getAttribute('data-theme')`, which the
head snippet has already set, and `test_interactive.py` fails on any JavaScript error.

**Why not stop deferring `theme.js`.** It would block rendering on every page to serve five lines
that only need a value already on the page.

## D-017: Journal chips are ordered by impact factor

_Recorded 2026-10-04 (owner's request) · `top_journals` in `_config.yml`_

**Context.** D-015 chose the five journals and ordered the chips by how many papers Josh has in
each. Josh asked for impact-factor order instead.

**Decision.** Same five journals, in `_config.yml` order, which is by 2025 Journal Impact Factor
(JCR released June 2026): _Nature_ 56.1, _Nature Medicine_ 52.5, _Cell_ 42.5, _Nature
Immunology_ 26.5, _Nature Genetics_ 25.5. The values come from secondary listings of the JCR, not
the publishers' pages. Re-check the order each June; in the 2024 JCR _Nature Medicine_ was above
_Nature_.

**Why not keep paper-count order.** It put _Nature Genetics_ second, which reads as a ranking of
the journals rather than of Josh's output.

**Superseded by** [D-020](#d-020-journal-chips-use-a-fixed-order)

## D-018: Cycling data comes from Apple Health, not the Strava API

_Recorded 2026-10-04 (owner's request) · `scripts/cycling_data.py`, `add-ride.yml`, [cycling-data.md](cycling-data.md)_

**Context.** Strava put its API behind a paid subscription in June 2026. The daily Update Strava
Data workflow has returned 403 Forbidden since early July, and the cycling page stopped at June 21.
Josh records rides with Apple Fitness on the Apple Watch.

**Decision.** Rides through 2026-06-21 are frozen in `_data/cycling_strava_archive.json`, which
reproduces the last Strava numbers exactly. Newer rides come from Apple Health in two ways: an
iPhone Shortcut that fires when a Watch cycling workout ends and posts start, end, and distance to
the Add Ride workflow (`repository_dispatch`), and a periodic Health export imported with
`cycling_data.py import-health`, which adds elevation and fills gaps. Rides are stored as date,
distance, moving time, and elevation only, with no start times or routes, because the repo is
public; duplicates are matched on those fields.

**Why not pay for Strava.** $11.99 a month to keep a hobby page's ride count current.

**Why not Health Auto Export.** It posts richer data automatically, but in its own JSON format,
which GitHub's API doesn't accept, so it would need a relay server. It also needs a subscription.

**Why keep the Strava archive instead of re-importing everything from Health.** Rides recorded in
the Strava app may not be in Health, and the archive is the record the site already showed.

## D-019: The publication count includes unpublished preprints but not the thesis

_Recorded 2026-10-04 (owner's decision) · `counted` field in `papers.bib`, `scripts/check_preprints.py`_

**Context.** The count of 40 included the PhD thesis and three preprints (VIDRA on medRxiv 2026,
INTERFACE on bioRxiv 2024, and the pancreatic enzyme T1D paper on medRxiv 2024). On 2026-10-04
none of the three had a published version on bioRxiv, medRxiv, or PubMed.

**Decision.** The thesis stays on /publications/ but carries `counted = {false}`, so the count is 39. Preprints count until they're published. `check_preprints.py` runs weekly and fails when one
has a journal version, so the entry gets replaced instead of the paper being counted twice.

**Why not drop the thesis from the list.** It is part of the record; only the count was in question.

**Why not use the `@phdthesis` entry type.** `bib.liquid` builds the venue line from the journal
field, so a type change would mean template work for one entry.

## D-020: Journal chips use a fixed order

_Recorded 2026-10-04 (owner's choice) · `top_journals` in `_config.yml`_

**Context.** D-017 ordered the chips by impact factor, which has to be re-checked every June and
flips between _Nature_ and _Nature Medicine_ from year to year.

**Decision.** A fixed order chosen by Josh: _Nature_, _Cell_, _Nature Medicine_, _Nature Genetics_,
_Nature Immunology_. The order in `_config.yml` is the order on the page; nothing re-sorts it.

**Why not impact factor.** It changes yearly and needs maintenance for no gain to the reader.

## D-021: Health fills the days the Strava archive missed

_Recorded 2026-10-04 (owner's question) · `scripts/cycling_data.py import-health`_

**Context.** Health has cycling workouts from 2026-01-13 on. For January through June 2026 it
holds every day Strava logged plus 19 days Strava never received, including all of May (165 km).
Strava alone has the 2024 and 2025 rides. Where both have a day, their distances agree to within
a kilometer or two.

**Decision.** The Strava archive stays the record for every day it has a ride. Health rides on
earlier days the archive has no ride for are added to `cycling_rides.json`, like newer rides.
Rides also store whether they started in the morning or afternoon ("am"/"pm"), because on seven
days the two commutes were within 1% of each other in distance and couldn't be told apart.

**Why not replace Strava with Health from January 2026.** Git keeps only one Strava snapshot, so
the archive's ride count and elevation can't be split at a date; the day-level rule needs no split.

**Why not store start times.** The repo is public; morning or afternoon is enough to match a
Shortcut ride to the same workout in a later export.
