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
