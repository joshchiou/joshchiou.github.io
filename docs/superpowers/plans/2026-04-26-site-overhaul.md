# Personal Site Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all al-folio template content with personal content, canonicalize messaging, add dynamic Strava and travel visualizations, and clean up unused infrastructure.

**Architecture:** 11 sequential tasks. Tasks 1–6 are pure file operations on the Jekyll source tree; Tasks 7–9 add data pipeline infrastructure (Python + GitHub Actions + ECharts/Leaflet). Tasks 8 and 9 are independent of each other. Each task ends with a build verification and a commit.

**Tech Stack:** Jekyll (al-folio fork), Liquid templates, ECharts 5 (calendar heatmap), Leaflet 1.9 (travel map), Python 3.11 (Strava pipeline), GitHub Actions (weekly Strava refresh), Ruby/Bundler.

**Build command:** `bundle exec jekyll build --strict_front_matter` (run after every task)
**Dev server:** `bundle exec jekyll serve`
**Working directory:** repo root

---

## File Map

### Created
- `_projects/work_t1d_exocrine.md`
- `_projects/work_islet_epigenomics.md`
- `_projects/work_ukb_ppp.md`
- `_projects/work_pfizer_targets.md`
- `_projects/work_lilly_proteomics.md`
- `_projects/fun_home_assistant.md`
- `_projects/fun_cycling.md`
- `_projects/fun_cocktails.md`
- `_projects/fun_cats.md`
- `_projects/fun_travel.md`
- `_data/contributions.yml`
- `_data/strava_calendar.json` (placeholder → updated by GitHub Actions)
- `_data/strava_stats.json` (placeholder → updated by GitHub Actions)
- `_data/travel_countries.yml` (populated from Takeout script)
- `_data/travel_cities.yml` (populated from Takeout script)
- `scripts/update_strava.py`
- `.github/workflows/update-strava.yml`
- `CLAUDE.md`
- `UPSTREAM_README.md`

### Modified
- `_config.yml` — remove blog, comments, external sources; add SEO; update description/keywords
- `_pages/about.md` — subtitle + opening paragraph
- `_pages/projects.md` — update description
- `_pages/repositories.md` — restructure into Maintained + Contributions sections
- `_news/2025-10-20-lilly.md` — past tense rewrite
- `_data/cv.yml` — align Pfizer scope wording
- `_data/repositories.yml` — trim to 2 personal repos
- `_layouts/post.liquid` — remove dead blog/comments conditional blocks
- `scripts/parse_takeout.py` — rename output files to underscores
- `README.md` — rewrite as personal site README

### Deleted
- `_pages/about_einstein.md`, `profiles.md`, `teaching.md`, `blog.md`, `dropdown.md`
- `_posts/*.md` (28 files)
- `_projects/1_project.md` … `10_project.md`
- `_data/coauthors.yml`, `venues.yml`
- `_layouts/profiles.liquid`, `distill.liquid`, `archive-category.liquid`, `archive-tag.liquid`, `archive-year.liquid`
- `_includes/latest_posts.liquid`, `related_posts.liquid`, `disqus.liquid`, `giscus.liquid`, `pagination.liquid`
- `assets/img/1.jpg` … `12.jpg`, `template_error.png`
- `assets/pdf/example_pdf.pdf`

---

## Task 1: Template cleanup

**Files:** Delete everything in the "Deleted" list above. Edit `_layouts/post.liquid`.

- [ ] **Delete template pages**

```bash
git rm _pages/about_einstein.md _pages/profiles.md _pages/teaching.md _pages/blog.md _pages/dropdown.md
```

- [ ] **Delete all demo posts**

```bash
git rm _posts/*.md
```

- [ ] **Delete template projects**

```bash
git rm _projects/1_project.md _projects/2_project.md _projects/3_project.md \
       _projects/4_project.md _projects/5_project.md _projects/6_project.md \
       _projects/7_project.md _projects/8_project.md _projects/9_project.md \
       _projects/10_project.md
```

- [ ] **Delete unused data files**

```bash
git rm _data/coauthors.yml _data/venues.yml
```

- [ ] **Delete unused layouts**

```bash
git rm _layouts/profiles.liquid _layouts/distill.liquid \
       _layouts/archive-category.liquid _layouts/archive-tag.liquid \
       _layouts/archive-year.liquid
```

- [ ] **Delete unused includes**

```bash
git rm _includes/latest_posts.liquid _includes/related_posts.liquid \
       _includes/disqus.liquid _includes/giscus.liquid _includes/pagination.liquid
```

- [ ] **Delete template images and PDF**

```bash
git rm assets/img/1.jpg assets/img/2.jpg assets/img/3.jpg assets/img/4.jpg \
       assets/img/5.jpg assets/img/6.jpg assets/img/7.jpg assets/img/8.jpg \
       assets/img/9.jpg assets/img/10.jpg assets/img/11.jpg assets/img/12.jpg \
       assets/img/template_error.png \
       assets/pdf/example_pdf.pdf
```

- [ ] **Clean dead includes from `_layouts/post.liquid`**

Remove lines 87–98 — three conditional blocks that reference the deleted includes. The lines to remove are:

```liquid
  {% if site.related_blog_posts.enabled %}
    {% if page.related_posts == null or page.related_posts %}
      {% include related_posts.liquid %}
    {% endif %}
  {% endif %}

  {% if site.disqus_shortname and page.disqus_comments %}
    {% include disqus.liquid %}
  {% endif %}
  {% if site.giscus and page.giscus_comments %}
    {% include giscus.liquid %}
  {% endif %}
```

After removing those 12 lines, the end of `_layouts/post.liquid` should be:

```liquid
  {% if page.citation %}
    {% include citation.liquid %}
  {% endif %}

  {% if page.related_publications %}
    <h2>References</h2>
    <div class="publications">
      {% bibliography --cited_in_order %}
    </div>
  {% endif %}
</div>
```

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Expected: `Build complete!` or similar, no errors. If you see "Could not find X", a deleted file is still referenced — grep for it and remove the reference.

- [ ] **Commit**

```bash
git add -A
git commit -m "cleanup: remove all al-folio template content and unused includes"
```

---

## Task 2: Config consolidation

**Files:** `_config.yml`

- [ ] **Update site description, keywords, and SEO flags**

In `_config.yml`, replace:

```yaml
description: >
  Senior Advisor in Data Science and Computational Biology at Lilly,
  working on clinical trial proteomics for obesity and cardiometabolic drug programs.
```

with:

```yaml
description: >-
  Senior Advisor, Genomics at Lilly. Translating large-scale proteomics and human
  genetics into mechanistic and biomarker insights to inform clinical strategy for
  cardiometabolic and obesity drug programs.
```

Replace:

```yaml
keywords: proteomics, computational biology, statistical genetics, pQTL
```

with:

```yaml
keywords: proteomics, computational biology, statistical genetics, pQTL, human genetics, GWAS, single-cell genomics, biomarker discovery, target discovery, cardiometabolic, obesity, Lilly
```

Replace:

```yaml
serve_og_meta: false # Include Open Graph meta tags in the HTML head
serve_schema_org: false # Include Schema.org in the HTML head
og_image: # The site-wide (default for all links) Open Graph preview image
```

with:

```yaml
serve_og_meta: true
serve_schema_org: true
og_image: assets/img/prof_pic.jpg
```

- [ ] **Remove blog infrastructure**

Delete these entire blocks from `_config.yml`:

```yaml
blog_name: al-folio # blog_name will be displayed in your blog page
blog_description: a simple whitespace theme for academics
permalink: /blog/:year/:title/
lsi: false # produce an index for related posts
```

```yaml
pagination:
  enabled: true

related_blog_posts:
  enabled: true
  max_related: 5
```

```yaml
# Giscus comments (RECOMMENDED)
# Follow instructions on https://giscus.app/ to setup for your repo to fill out the information below.
giscus:
  repo: # <your-github-user-name>/<your-github-repo-name>
  repo_id: # leave empty or specify your repo_id (see https://giscus.app/)
  category: Comments # name of the category under which discussions will be created
  category_id: # leave empty or specify your category_id (see https://giscus.app/)
  mapping: title # identify discussions by post title
  strict: 1 # use strict identification mode
  reactions_enabled: 1 # enable (1) or disable (0) emoji reactions
  input_position: bottom # whether to display input form below (bottom) or above (top) the comments
  theme: preferred_color_scheme # name of the color scheme (preferred works well with al-folio light/dark mode)
  emit_metadata: 0
  lang: en

# Disqus comments (DEPRECATED)
disqus_shortname: al-folio # put your disqus shortname
# https://help.disqus.com/en/articles/1717111-what-s-a-shortname
```

```yaml
# External sources.
# If you have blog posts published on medium.com or other external sources,
# you can display them in your blog by adding a link to the RSS feed.
external_sources:
  - name: medium.com
    rss_url: https://medium.com/@al-folio/feed
  - name: Google Blog
    posts:
      - url: https://blog.google/technology/ai/google-gemini-update-flash-ai-assistant-io-2024/
        published_date: 2024-05-14
```

```yaml
latest_posts:
  enabled: false
  scrollable: true # adds a vertical scroll bar if there are more than 3 new posts items
  limit: 3 # leave blank to include all the blog posts
```

```yaml
# Display different tags and categories
display_tags: ["formatting", "images", "links", "math", "code", "blockquotes"] # these tags will be displayed on the front page of your blog
display_categories: ["external-services"] # these categories will be displayed on the front page of your blog
```

```yaml
newsletter:
  enabled: false
  endpoint: # your loops endpoint (e.g., https://app.loops.so/api/newsletter-form/YOUR-ENDPOINT)
  # https://loops.so/docs/forms/custom-form
```

- [ ] **Remove jekyll-archives config block**

Delete entirely:

```yaml
# -----------------------------------------------------------------------------
# Jekyll Archives
# -----------------------------------------------------------------------------

jekyll-archives:
  enabled: [year, tags, categories] # enables year, tag and category archives (remove if you need to disable one of them).
  layouts:
    year: archive-year
    tag: archive-tag
    category: archive-category
  permalinks:
    year: "/blog/:year/"
    tag: "/blog/tag/:name/"
    category: "/blog/category/:name/"
```

- [ ] **Remove unused plugins from the plugins list**

In the `plugins:` list, remove these four lines:

```yaml
  - jekyll-archives
  - jekyll-jupyter-notebook
  - jekyll-paginate-v2
  - jekyll-twitter-plugin
```

- [ ] **Disable repo trophies**

In the `repo_trophies:` block, set `enabled: false`:

```yaml
repo_trophies:
  enabled: false
```

- [ ] **Add docs/ and scripts/ to exclude list**

In the `exclude:` list, add after the last entry:

```yaml
  - docs/
  - scripts/
```

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Expected: clean build. If you see "Liquid Exception" related to `latest_posts`, verify all references to removed config keys are gone from `_layouts/about.liquid` — they are guarded by `if site.latest_posts.enabled` so they resolve to nothing, not errors.

- [ ] **Commit**

```bash
git add _config.yml
git commit -m "config: remove blog/comments/external-sources, enable OG/Schema.org, update description and keywords"
```

---

## Task 3: Content rewrites

**Files:** `_pages/about.md`, `_news/2025-10-20-lilly.md`, `_data/cv.yml`, `_pages/projects.md`, `_data/repositories.yml`

- [ ] **Update about page subtitle and opening paragraph**

Replace the entire content of `_pages/about.md`:

```markdown
---
layout: about
title: about
permalink: /
subtitle: Senior Advisor, Genomics · Lilly · Translational Proteomics & Statistical Genetics

profile:
  align: right
  image: prof_pic.jpg
  image_circular: true
  more_info:

news: true
selected_papers: true
social: true
---

I am a Senior Advisor in Genomics at [Lilly](https://www.lilly.com), translating large-scale proteomics and human genetics into mechanistic and biomarker insights to inform clinical strategy for cardiometabolic and obesity drug programs.

Previously, I was a Senior Principal Computational Geneticist in the [Internal Medicine Research Unit](https://www.pfizer.com/science/focus-areas/internal-medicine) at [Pfizer](https://www.pfizer.com), where I partnered with biologists to identify novel targets for cardiovascular and renal disease, led cloud-native infrastructure projects for statistical genetics, and contributed to pre-competitive consortiums such as the [UK Biobank Pharma Proteomics Project](https://www.ukbiobank.ac.uk/projects/large-scale-proteomic-profiling-to-facilitate-genetics-guided-drug-discovery-and-precision-medicine-the-uk-biobank-pharma-proteomics-project-ukb-ppp/) (UKB-PPP).

I completed my PhD in [Biomedical Sciences](https://biomedsci.ucsd.edu/) at [UC San Diego](https://ucsd.edu/) in the [Gaulton Lab](https://gaultonlab.org/), where I used single-cell epigenomics to study the regulatory landscape of the pancreas and its relevance to the genetic risk of type 1 and type 2 diabetes.
```

- [ ] **Rewrite Lilly news item to past tense**

Replace the content of `_news/2025-10-20-lilly.md`:

```markdown
---
layout: post
date: 2025-10-20 09:00:00-0400
inline: true
related_posts: false
---

Joined <a href="https://www.lilly.com" target="_blank">Lilly</a> as Senior Advisor, Genomics, working on translational proteomics for obesity clinical trials.
```

- [ ] **Align Pfizer scope in cv.yml**

In `_data/cv.yml`, find the Senior Principal Computational Geneticist entry (year 2023–2025) and update `maindescription` to use "cardiovascular and renal disease" (currently says "renal and cardiovascular disease"):

```yaml
    - title: Senior Principal Computational Geneticist
      institution: Pfizer
      location: Cambridge, MA
      year: 2023 - 2025
      maindescription: >-
        I collaborated with cross-functional teams for cardiovascular and renal target discovery integrating human
        genetics, functional genomics, and large language models, while driving delivery of scalable
        cloud infrastructure for large-scale genomics analysis across the organization.
```

Also update the Senior Computational Geneticist entry (year 2021–2023):

```yaml
    - title: Senior Computational Geneticist
      institution: Pfizer
      location: Cambridge, MA
      year: 2021 - 2023
      maindescription: >-
        I partnered with biologists to identify novel targets for cardiovascular and renal disease
        through integrative multi-omics, with several advancing into the portfolio, and served as the
        genetics expert for indication expansion teams.
```

- [ ] **Update projects page description**

In `_pages/projects.md`, change the front matter description from:

```yaml
description: A growing collection of your cool projects.
```

to:

```yaml
description: Research programs and personal projects.
```

- [ ] **Trim repositories.yml to personal repos only**

Replace the entire content of `_data/repositories.yml`:

```yaml
github_repos:
  - joshchiou/T1D_snATAC
  - joshchiou/joshchiou.github.io

repo_description_lines_max: 2
```

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Then open `http://localhost:4000` in the dev server. Verify: about page subtitle reads correctly, Lilly news item reads "Joined Lilly…" (past tense), CV Pfizer entries say "cardiovascular and renal".

```bash
bundle exec jekyll serve
```

- [ ] **Commit**

```bash
git add _pages/about.md _news/2025-10-20-lilly.md _data/cv.yml _pages/projects.md _data/repositories.yml
git commit -m "content: canonicalize tagline, rewrite Lilly news past-tense, align Pfizer scope wording"
```

---

## Task 4: Work project cards

**Files:** Create 5 new `_projects/work_*.md`. Create `assets/img/projects/work/` directory with placeholder.

Note: `img` fields use `assets/img/prof_pic.jpg` as a temporary placeholder. Replace with real figures once available.

- [ ] **Create work image directory**

```bash
mkdir -p assets/img/projects/work
touch assets/img/projects/work/.gitkeep
```

- [ ] **Create `_projects/work_t1d_exocrine.md`**

```markdown
---
layout: page
title: Type 1 Diabetes and the Exocrine Pancreas
description: Discovering acinar cell contributions to T1D genetic risk using single-cell epigenomics.
img: assets/img/prof_pic.jpg
importance: 1
category: work
related_publications: false
---

Type 1 diabetes (T1D) has long been understood as a disease of the pancreatic islets, where
immune-mediated destruction of insulin-producing beta cells drives hyperglycemia. My PhD work
challenged this tissue-centric view by integrating T1D genome-wide association study (GWAS)
loci with single-cell chromatin accessibility maps of the human pancreas, revealing that a
substantial proportion of T1D risk variants are active in acinar cells — the exocrine compartment
responsible for digestive enzyme secretion. This finding, published in {% cite chiou2021interpreting %},
implicated acinar dysfunction as a previously underappreciated component of T1D pathophysiology.

Building on this, subsequent work from our lab showed that circulating pancreatic enzyme levels
are a causal biomarker of T1D risk {% cite gaulton2024circulating %}, and single-cell multiome
profiling of pancreas tissue across disease stages revealed dynamic cell-type-specific regulatory
programs during T1D progression {% cite chiou2025singlecell %}. Together, these studies shifted
the field's view of T1D from a purely islet-centric disease to one with measurable exocrine
contributions, opening new avenues for early detection and intervention.

Data and code: [joshchiou/T1D\_snATAC](https://github.com/joshchiou/T1D_snATAC)
```

- [ ] **Create `_projects/work_islet_epigenomics.md`**

```markdown
---
layout: page
title: Single-Cell Epigenomics of Pancreatic Islets
description: Mapping cell-type-specific chromatin accessibility and its role in diabetes genetic risk.
img: assets/img/prof_pic.jpg
importance: 2
category: work
related_publications: false
---

The pancreatic islet contains multiple interacting cell types — beta, alpha, delta, and others —
each with distinct transcriptional programs and disease associations. My PhD work applied
single-cell ATAC-seq to human islets to generate high-resolution maps of cell-type-specific
chromatin accessibility, revealing regulatory programs active in each cell type and linking
them to type 1 and type 2 diabetes GWAS loci {% cite chiou2021single %}. This provided a
framework for interpreting non-coding genetic variants in the context of islet cell-type identity.

Complementary work characterized how environmental and nutrient signals reshape the islet
epigenome to control adaptive insulin secretion {% cite islet2023nutrient %}, and examined
how genetic variation at type 2 diabetes loci affects cell-type-specific regulatory activity
across disease states {% cite wang2023integrating %}. The resulting resource — a catalog of
islet cell-type regulatory elements annotated with disease-relevant variants — is widely used
in the field for interpreting diabetes GWAS results.
```

- [ ] **Create `_projects/work_ukb_ppp.md`**

```markdown
---
layout: page
title: UK Biobank Pharma Proteomics Project
description: Pre-competitive consortium mapping the genetic architecture of the human plasma proteome.
img: assets/img/prof_pic.jpg
importance: 3
category: work
related_publications: false
---

The [UK Biobank Pharma Proteomics Project](https://www.ukbiobank.ac.uk/projects/large-scale-proteomic-profiling-to-facilitate-genetics-guided-drug-discovery-and-precision-medicine-the-uk-biobank-pharma-proteomics-project-ukb-ppp/)
(UKB-PPP) was a pre-competitive consortium of thirteen pharmaceutical companies and the UK Biobank,
profiling ~3,000 plasma proteins using the Olink Proximity Extension Assay across 54,306
participants. The flagship analysis, published in {% cite sun2023plasma %}, characterized
protein quantitative trait loci (pQTLs), their genetic architecture, and their associations
with disease outcomes — providing one of the most comprehensive maps to date of how human
genetics shapes the circulating proteome.

My contributions focused on the statistical genetics infrastructure and analytical pipelines
underpinning the consortium's analyses. The UKB-PPP dataset has since become a foundational
resource for Mendelian randomization, drug target validation, and multi-omics integration
across the pharmaceutical industry, enabling rapid translation of genetic insights into
actionable hypotheses for drug discovery programs.
```

- [ ] **Create `_projects/work_pfizer_targets.md`**

```markdown
---
layout: page
title: Genetics-Driven Target Discovery for Cardiovascular and Renal Disease
description: Integrative multi-omics pipeline for identifying and validating drug targets at Pfizer.
img: assets/img/prof_pic.jpg
importance: 4
category: work
related_publications: false
---

At Pfizer's Internal Medicine Research Unit, I built and led the computational genetics
component of target discovery programs for cardiovascular and renal disease. The core
approach integrated human genetic evidence — GWAS, exome-wide association studies,
colocalization, and Mendelian randomization — with functional genomics layers including
single-cell chromatin accessibility, eQTL and pQTL datasets, and protein structure
predictions to nominate and prioritize novel targets with genetic support for efficacy
and selectivity. Several targets identified through this pipeline advanced into the
Pfizer portfolio.

Beyond individual target programs, I led the development of cloud-native genomics infrastructure
enabling large-scale analyses across the organization: scalable GWAS and fine-mapping pipelines
on AWS, standardized multi-ancestry summary statistics harmonization, and integration of
emerging multi-omics datasets. I also contributed to the UKB-PPP consortium and published
methods for multi-trait integration and causal inference {% cite intact2025multi %} that
are applicable across therapeutic areas.
```

- [ ] **Create `_projects/work_lilly_proteomics.md`**

```markdown
---
layout: page
title: Translational Proteomics for Obesity Clinical Trials
description: Generating mechanistic and biomarker insights from large-scale proteomics in phase 2/3 obesity programs.
img: assets/img/prof_pic.jpg
importance: 5
category: work
related_publications: false
---

At Lilly, I work at the intersection of clinical omics and drug development: applying
large-scale proteomics — primarily Olink and SomaScan platforms — to phase 2 and phase 3
clinical trials for obesity and cardiometabolic disease. The goal is to translate protein
abundance changes measured in trial participants into mechanistic hypotheses about drug
biology and actionable biomarker strategies that inform clinical decisions.

This work requires bridging statistical genetics, proteomics methodology, and clinical
endpoint analysis: interpreting proteomic trajectories in the context of pQTL and genetic
association data, applying survival analysis and mixed models to longitudinal omics data,
and integrating electronic health record data to characterize patient subgroups. I also
build the analytical infrastructure — pipelines, data models, dashboards — that supports
the broader clinical omics team.
```

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Navigate to `http://localhost:4000/projects/` and verify five work cards appear. Check each detail page loads without errors.

- [ ] **Commit**

```bash
git add _projects/work_t1d_exocrine.md _projects/work_islet_epigenomics.md \
        _projects/work_ukb_ppp.md _projects/work_pfizer_targets.md \
        _projects/work_lilly_proteomics.md assets/img/projects/work/
git commit -m "projects: add 5 work project cards (research programs)"
```

---

## Task 5: Fun project cards — static (Home Assistant, Cocktails, Claire)

**Files:** Create 3 `_projects/fun_*.md`, create `assets/img/projects/fun/` subdirectories.

- [ ] **Create directory structure**

```bash
mkdir -p assets/img/projects/fun/home-assistant
mkdir -p assets/img/projects/fun/cocktails
touch assets/img/projects/fun/home-assistant/.gitkeep
touch assets/img/projects/fun/cocktails/.gitkeep
```

- [ ] **Create `_projects/fun_home_assistant.md`**

Replace `YOUR_DASHBOARD_SCREENSHOT.jpg` with the actual filename once you add one to `assets/img/projects/fun/home-assistant/`. For now, `prof_pic.jpg` is the placeholder.

```markdown
---
layout: page
title: Home Assistant
description: Home automation setup with solar monitoring, local AI, and custom integrations.
img: assets/img/prof_pic.jpg
importance: 1
category: fun
---

I run [Home Assistant](https://www.home-assistant.io/) on a local server as the hub for home
automation — controlling lights, climate, media, and monitoring solar production from a
SunPower PV system. The SunPower integration was adapted from an open-source fork; I contributed
a fix for a memory-leak bug that caused crashes when the PVS serial is an IP address
([ha-esunpower #64](https://github.com/smcneece/ha-esunpower/pull/64)).

The setup leans toward local-first: automations run on-device, voice commands use a local
speech-to-text model rather than a cloud service, and dashboards are built in Lovelace with
custom cards for energy monitoring and multi-room audio. The system runs continuously without
cloud dependency, which has been the most satisfying design constraint.
```

- [ ] **Create `_projects/fun_cocktails.md`**

```markdown
---
layout: page
title: Cocktails
description: Notes from the house bar.
img: assets/img/prof_pic.jpg
importance: 3
category: fun
---

Mostly classic cocktails with occasional detours into original recipes. Current obsessions
lean towards stirred drinks: Negroni variations, spec-forward Manhattans, and anything that
involves a good amaro. The house bar has a soft spot for aged rum and Japanese whisky.
```

- [ ] **Create `_projects/fun_cats.md`**

```markdown
---
layout: page
title: Claire
description: The real senior scientist in the family.
img: assets/img/projects/fun/cats/claire-main.jpg
importance: 4
category: fun
---

{% include figure.liquid path="assets/img/projects/fun/cats/claire-main.jpg" class="img-fluid rounded z-depth-1 mb-3" alt="Claire" %}

<div class="row">
  <div class="col-sm mt-3 mt-md-0">
    {% include figure.liquid path="assets/img/projects/fun/cats/claire-gallery-1.jpg" class="img-fluid rounded z-depth-1" alt="Claire" %}
  </div>
  <div class="col-sm mt-3 mt-md-0">
    {% include figure.liquid path="assets/img/projects/fun/cats/claire-gallery-2.jpg" class="img-fluid rounded z-depth-1" alt="Claire" %}
  </div>
  <div class="col-sm mt-3 mt-md-0">
    {% include figure.liquid path="assets/img/projects/fun/cats/claire-gallery-3.jpg" class="img-fluid rounded z-depth-1" alt="Claire" %}
  </div>
</div>
<div class="row mt-3">
  <div class="col-sm mt-3 mt-md-0">
    {% include figure.liquid path="assets/img/projects/fun/cats/claire-gallery-4.jpg" class="img-fluid rounded z-depth-1" alt="Claire" %}
  </div>
  <div class="col-sm mt-3 mt-md-0">
    {% include figure.liquid path="assets/img/projects/fun/cats/claire-gallery-5.jpg" class="img-fluid rounded z-depth-1" alt="Claire" %}
  </div>
  <div class="col-sm mt-3 mt-md-0"></div>
</div>
```

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Visit `http://localhost:4000/projects/` — verify both `work` and `fun` categories appear. Navigate to the Claire detail page; confirm all 5 gallery images load (imagemagick generates WebP variants during build).

- [ ] **Commit**

```bash
git add _projects/fun_home_assistant.md _projects/fun_cocktails.md \
        _projects/fun_cats.md \
        assets/img/projects/fun/home-assistant/ assets/img/projects/fun/cocktails/
git commit -m "projects: add fun project cards (Home Assistant, Cocktails, Claire)"
```

---

## Task 6: Repositories page rebuild

**Files:** `_pages/repositories.md`, `_data/contributions.yml`

- [ ] **Create `_data/contributions.yml`**

```yaml
# Curated list of merged open-source contributions.
# Add new entries at the top. date: YYYY-MM-DD

- repo: scverse/SnapATAC2
  url: https://github.com/scverse/SnapATAC2
  pr_title: "Parallel IDF"
  pr_url: https://github.com/scverse/SnapATAC2/pull/404
  date: 2025-06-30
  blurb: Parallelized inverse-document-frequency computation in dimensionality reduction, cutting runtime on large datasets.

- repo: conda-forge/staged-recipes
  url: https://github.com/conda-forge/staged-recipes
  pr_title: "Add r-mmrm: Mixed Models for Repeated Measures"
  pr_url: https://github.com/conda-forge/staged-recipes/pull/31675
  date: 2025-12-10
  blurb: Packaged r-mmrm for conda-forge, making it available as a conda dependency for clinical trial analysis pipelines.

- repo: stephenslab/susieR
  url: https://github.com/stephenslab/susieR
  pr_title: "Compatibility with rpy2"
  pr_url: https://github.com/stephenslab/susieR/pull/247
  date: 2025-02-25
  blurb: Restored Python interoperability so susieR can be called from rpy2 pipelines.

- repo: smcneece/ha-esunpower
  url: https://github.com/smcneece/ha-esunpower
  pr_title: "fix: prevent memory leak crash when PVS serial is an IP address"
  pr_url: https://github.com/smcneece/ha-esunpower/pull/64
  date: 2025-03-26
  blurb: Fixed a memory leak that caused the Home Assistant integration to crash when the SunPower PVS serial number is configured as an IP address.

- repo: Cloufield/gwaslab
  url: https://github.com/Cloufield/gwaslab
  pr_title: "add fix ID before assign rsID"
  pr_url: https://github.com/Cloufield/gwaslab/pull/118
  date: 2024-11-27
  blurb: Added a variant ID normalization step before rsID assignment, preventing downstream mapping errors in GWAS summary statistics workflows.

- repo: scverse/SnapATAC2
  url: https://github.com/scverse/SnapATAC2
  pr_title: "Fix for multiple harmony covariates"
  pr_url: https://github.com/scverse/SnapATAC2/pull/342
  date: 2024-10-01
  blurb: Fixed batch correction when more than one covariate is passed to Harmony integration.

- repo: GreenleafLab/ArchR
  url: https://github.com/GreenleafLab/ArchR
  pr_title: "Update GroupExport.R"
  pr_url: https://github.com/GreenleafLab/ArchR/pull/2006
  date: 2023-08-21
  blurb: Fixed group export function compatibility with updated dependencies.

- repo: FinucaneLab/fine-mapping-inf
  url: https://github.com/FinucaneLab/fine-mapping-inf
  pr_title: "Add filter for duplicate credible sets"
  pr_url: https://github.com/FinucaneLab/fine-mapping-inf/pull/2
  date: 2022-11-08
  blurb: Added deduplication step for credible sets output, preventing redundant entries in fine-mapping results.
```

- [ ] **Rewrite `_pages/repositories.md`**

```markdown
---
layout: page
permalink: /repositories/
title: code
nav: false
description: >
  A slice of my public coding activity. Most production work lives in enterprise GitHub organizations
  (Pfizer, Lilly) and isn't reflected here.
---

## Maintained

<div class="repositories d-flex flex-wrap flex-md-row flex-column justify-content-between align-items-center">
  {% for repo in site.data.repositories.github_repos %}
    {% include repository/repo.liquid repository=repo %}
  {% endfor %}
</div>

---

## Open-source contributions

Selected merged pull requests to community scientific software.

<ul class="list-unstyled">
  {% for c in site.data.contributions %}
  <li class="mb-3">
    <a href="{{ c.pr_url }}" target="_blank" rel="noopener noreferrer"><strong>{{ c.pr_title }}</strong></a>
    &nbsp;·&nbsp;
    <a href="{{ c.url }}" target="_blank" rel="noopener noreferrer">{{ c.repo }}</a>
    &nbsp;·&nbsp;
    <span class="text-muted">{{ c.date }}</span>
    <br>
    <small>{{ c.blurb }}</small>
  </li>
  {% endfor %}
</ul>

<a href="https://github.com/search?q=author%3Ajoshchiou+is%3Apr+is%3Amerged&type=pullrequests" target="_blank" rel="noopener noreferrer">See all merged pull requests →</a>
```

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Visit `http://localhost:4000/repositories/`. Verify two repo cards render (T1D_snATAC and joshchiou.github.io), the contributions list renders with 8 items, and the "See all" link is present.

- [ ] **Commit**

```bash
git add _pages/repositories.md _data/contributions.yml
git commit -m "repositories: restructure as maintained repos + curated contributions list"
```

---

## Task 7: Strava data pipeline

**Files:** `scripts/update_strava.py`, `.github/workflows/update-strava.yml`, `_data/strava_calendar.json` (placeholder), `_data/strava_stats.json` (placeholder)

**Prerequisite:** GitHub repo secrets `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN` must be set before the workflow can run. See OAuth instructions in session context.

- [ ] **Fix parse_takeout.py output filenames (underscore convention)**

In `scripts/parse_takeout.py`, update the output paths from hyphen to underscore naming:

```python
    countries_out = repo_root / "_data" / "travel_countries.yml"
    cities_out = repo_root / "_data" / "travel_cities.yml"
```

Also update the header comments in `write_yaml` calls to match:

```python
    write_yaml(
        countries_out,
        build_countries_output(countries),
        [
            "Auto-generated by scripts/parse_takeout.py",
            "Countries visited (from Google Takeout Location History)",
            "Regenerate: python scripts/parse_takeout.py /path/to/Takeout",
        ],
    )

    write_yaml(
        cities_out,
        build_cities_output(cities),
        [
            "Auto-generated by scripts/parse_takeout.py",
            "Candidate cities/places visited — REVIEW AND PRUNE before committing.",
            "This file contains noise: restaurants, offices, transit stops, etc.",
            "Delete any entry that isn't a meaningful destination.",
            "Regenerate: python scripts/parse_takeout.py /path/to/Takeout",
        ],
    )
```

- [ ] **Create placeholder data files**

```bash
echo '[]' > _data/strava_calendar.json
```

Create `_data/strava_stats.json`:

```json
{
  "total_rides": 0,
  "total_distance_km": 0,
  "total_elevation_m": 0,
  "monthly": [],
  "updated_at": "1970-01-01T00:00:00+00:00"
}
```

- [ ] **Create `scripts/update_strava.py`**

```python
#!/usr/bin/env python3
"""
Fetch Strava activity data and write _data/strava_calendar.json and _data/strava_stats.json.

Run manually:
    STRAVA_CLIENT_ID=... STRAVA_CLIENT_SECRET=... STRAVA_REFRESH_TOKEN=... \
        python scripts/update_strava.py

Or triggered automatically by .github/workflows/update-strava.yml.

Requirements: pip install requests
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide"}
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
REPO_ROOT = Path(__file__).parent.parent


def get_access_token() -> str:
    resp = requests.post(TOKEN_URL, data={
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_all_activities(token: str) -> list[dict]:
    activities = []
    page = 1
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        resp = requests.get(
            ACTIVITIES_URL,
            headers=headers,
            params={"per_page": 200, "page": page},
            timeout=60,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        activities.extend(batch)
        page += 1
        print(f"  Fetched page {page - 1}: {len(batch)} activities (total: {len(activities)})")
    return activities


def compute_calendar_data(activities: list[dict]) -> list[list]:
    """
    Returns [[date_str, distance_km], ...] for ECharts calendar heatmap.
    Aggregates multiple rides on the same day.
    """
    daily: dict[str, float] = {}
    for a in activities:
        if a.get("type") not in RIDE_TYPES:
            continue
        date = a["start_date_local"][:10]  # YYYY-MM-DD
        daily[date] = daily.get(date, 0.0) + a["distance"] / 1000
    return [[date, round(val, 2)] for date, val in sorted(daily.items())]


def compute_stats(activities: list[dict]) -> dict:
    """Returns all-time aggregate stats and monthly distance breakdown."""
    rides = [a for a in activities if a.get("type") in RIDE_TYPES]

    total_distance_km = round(sum(a["distance"] for a in rides) / 1000, 1)
    total_elevation_m = round(sum(a["total_elevation_gain"] for a in rides))

    monthly: dict[str, float] = {}
    for a in rides:
        month = a["start_date_local"][:7]  # YYYY-MM
        monthly[month] = monthly.get(month, 0.0) + a["distance"] / 1000

    monthly_list = [
        {"month": k, "distance_km": round(v, 1)}
        for k, v in sorted(monthly.items())
    ]

    return {
        "total_rides": len(rides),
        "total_distance_km": total_distance_km,
        "total_elevation_m": total_elevation_m,
        "monthly": monthly_list,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"  → {path}")


def main() -> None:
    for var in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN"):
        if not os.environ.get(var):
            print(f"Error: environment variable {var} is not set")
            sys.exit(1)

    print("Refreshing Strava access token...")
    token = get_access_token()

    print("Fetching all activities...")
    activities = fetch_all_activities(token)
    rides = [a for a in activities if a.get("type") in RIDE_TYPES]
    print(f"Found {len(rides)} cycling activities out of {len(activities)} total")

    calendar_data = compute_calendar_data(activities)
    stats = compute_stats(activities)

    data_dir = REPO_ROOT / "_data"
    write_json(data_dir / "strava_calendar.json", calendar_data)
    write_json(data_dir / "strava_stats.json", stats)

    print(f"\nDone. {stats['total_rides']} rides · "
          f"{stats['total_distance_km']} km · "
          f"{stats['total_elevation_m']} m elevation")


if __name__ == "__main__":
    main()
```

- [ ] **Create `.github/workflows/update-strava.yml`**

```yaml
name: Update Strava Data

on:
  schedule:
    - cron: "0 6 * * 1" # Every Monday 06:00 UTC
  workflow_dispatch: # Allow manual trigger from GitHub Actions UI

jobs:
  update-strava:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests

      - name: Fetch and update Strava data
        env:
          STRAVA_CLIENT_ID: ${{ secrets.STRAVA_CLIENT_ID }}
          STRAVA_CLIENT_SECRET: ${{ secrets.STRAVA_CLIENT_SECRET }}
          STRAVA_REFRESH_TOKEN: ${{ secrets.STRAVA_REFRESH_TOKEN }}
        run: python scripts/update_strava.py

      - name: Commit updated data files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add _data/strava_calendar.json _data/strava_stats.json
          git diff --staged --quiet || git commit -m "chore: update Strava activity data [skip ci]"
          git push
```

Note: `[skip ci]` in the commit message prevents the Strava update from triggering another build loop if your CI is set up to rebuild on all commits. Remove it if your CI explicitly skips `chore:` commits another way.

- [ ] **Test the script locally** (requires your three Strava env vars)

```bash
STRAVA_CLIENT_ID=your_id STRAVA_CLIENT_SECRET=your_secret \
  STRAVA_REFRESH_TOKEN=your_token \
  python scripts/update_strava.py
```

Expected output:
```
Refreshing Strava access token...
Fetching all activities...
  Fetched page 1: 200 activities (total: 200)
  Fetched page 2: 200 activities (total: 400)
  ...
Found NNN cycling activities out of MMM total
  → .../joshchiou.github.io/_data/strava_calendar.json
  → .../joshchiou.github.io/_data/strava_stats.json

Done. NNN rides · NNN.N km · NNN m elevation
```

If you get a 401, the refresh token is expired — re-run the OAuth flow from the session instructions to get a new one.

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

The build should pass regardless of whether strava_calendar.json is empty or populated (placeholder `[]` is valid JSON).

- [ ] **Commit**

```bash
git add scripts/update_strava.py .github/workflows/update-strava.yml \
        _data/strava_calendar.json _data/strava_stats.json \
        scripts/parse_takeout.py
git commit -m "feat: add Strava data pipeline (weekly GitHub Actions update)"
```

---

## Task 8: Cycling project card with ECharts calendar

**Files:** `_projects/fun_cycling.md`

This task depends on Task 7 (the `_data/strava_calendar.json` and `_data/strava_stats.json` files must exist). Run it after Task 7 even if the Strava script hasn't been run yet — the placeholders work fine for the build.

The ECharts calendar heatmap embeds `site.data.strava_calendar` via Liquid (rendered at Jekyll build time). ECharts is loaded by setting `chart.echarts: true` in the front matter, then the template automatically processes `language-echarts` code blocks using `JSON.parse()`.

- [ ] **Create `_projects/fun_cycling.md`**

```markdown
---
layout: page
title: On the Bike
description: Strava-powered cycling stats — activity calendar and all-time totals.
img: assets/img/prof_pic.jpg
importance: 2
category: fun
chart:
  echarts: true
---

{% assign stats = site.data.strava_stats %}

<div class="row mb-4 text-center">
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_rides | default: "—" }}</h3>
    <small class="text-muted">rides</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_distance_km | default: "—" | round }}</h3>
    <small class="text-muted">km</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_elevation_m | default: "—" | round }}</h3>
    <small class="text-muted">m elevation</small>
  </div>
</div>

### Activity calendar ({{ 'now' | date: '%Y' }})

```echarts
{
  "tooltip": { "position": "top" },
  "visualMap": {
    "min": 0,
    "max": 80,
    "calculable": true,
    "orient": "horizontal",
    "left": "center",
    "inRange": { "color": ["#e0f3f8", "#74add1", "#313695"] }
  },
  "calendar": {
    "range": "{{ 'now' | date: '%Y' }}",
    "cellSize": ["auto", 14],
    "itemStyle": { "borderWidth": 0.5 },
    "yearLabel": { "show": false }
  },
  "series": [{
    "type": "heatmap",
    "coordinateSystem": "calendar",
    "data": {{ site.data.strava_calendar | jsonify }}
  }]
}
```

### Monthly distance (all-time)

```echarts
{
  "tooltip": { "trigger": "axis" },
  "xAxis": {
    "type": "category",
    "data": {{ site.data.strava_stats.monthly | map: "month" | jsonify }},
    "axisLabel": { "rotate": 45, "interval": 5 }
  },
  "yAxis": { "type": "value", "name": "km" },
  "series": [{
    "type": "bar",
    "data": {{ site.data.strava_stats.monthly | map: "distance_km" | jsonify }},
    "itemStyle": { "color": "#74add1" }
  }]
}
```

<small class="text-muted">Updated {{ stats.updated_at | date: "%b %-d, %Y" | default: "never" }} via Strava API.</small>
```

Note: the backtick fences above are literal in the markdown — they become `<pre><code class="language-echarts">` blocks that the template's ECharts script processes.

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Navigate to `http://localhost:4000/projects/fun-cycling/` in the dev server. With placeholder data (`[]`), the charts will render as empty. After running `update_strava.py`, rebuild and verify the calendar shows colored squares and the bar chart shows monthly data. Toggle dark mode and confirm the chart respects the theme (ECharts dark mode is automatic via `echartsTheme`).

- [ ] **Commit**

```bash
git add _projects/fun_cycling.md
git commit -m "projects: add cycling card with ECharts activity calendar and stats"
```

---

## Task 9: Travel project card with Leaflet map

**Files:** `_projects/fun_travel.md`, `_data/travel_countries.yml` (placeholder), `_data/travel_cities.yml` (placeholder)

**Prerequisite for real data:** Run `python scripts/parse_takeout.py /path/to/Takeout` after receiving your Google Takeout export and commit the output files. This task ships with empty placeholders so the page builds immediately.

- [ ] **Create placeholder travel data files**

```bash
printf "# Auto-generated by scripts/parse_takeout.py\n# Countries visited\n\n[]\n" > _data/travel_countries.yml
printf "# Auto-generated by scripts/parse_takeout.py\n# Cities visited\n\n[]\n" > _data/travel_cities.yml
```

- [ ] **Download country GeoJSON for offline use**

Download the Natural Earth country boundaries GeoJSON (~60KB) so the travel map has no runtime CDN dependency:

```bash
mkdir -p assets/json
curl -sL "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson" \
  -o assets/json/world-countries.geojson
```

Verify the file was downloaded:

```bash
wc -c assets/json/world-countries.geojson
```

Expected: ~800KB–2MB. The file is committed to the repo; the map loads it via relative URL with no external request.

- [ ] **Create `_projects/fun_travel.md`**

The page uses `map: true` (front matter) to load Leaflet, then uses a custom `<script>` block to build the choropleth and city markers from Jekyll data. Country boundaries load from `assets/json/world-countries.geojson` (committed to repo, no CDN dependency at runtime).

```markdown
---
layout: page
title: Travel
description: Places visited, mapped.
img: assets/img/prof_pic.jpg
importance: 5
category: fun
map: true
---

{% assign countries = site.data.travel_countries %}
{% assign cities = site.data.travel_cities %}

<div id="travel-map" style="height: 480px; border-radius: 8px; overflow: hidden;"></div>

<p class="mt-2 text-muted">
  <small>
    {{ countries | size }} countries &nbsp;·&nbsp; {{ cities | size }} cities
  </small>
</p>

<script>
(function () {
  // Countries visited (injected at build time by Jekyll)
  var visitedCountries = {{ countries | map: "name" | jsonify }};

  // Cities (lat/lon markers)
  var cityData = {{ cities | jsonify }};

  // Wait for Leaflet to be available (loaded by map: true in front matter)
  document.addEventListener('readystatechange', function () {
    if (document.readyState !== 'complete') return;

    var mapEl = document.getElementById('travel-map');
    if (!mapEl) return;

    var map = L.map(mapEl, { scrollWheelZoom: false }).setView([20, 0], 2);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 19
    }).addTo(map);

    // Load committed GeoJSON (no CDN dependency)
    fetch('{{ "/assets/json/world-countries.geojson" | relative_url }}')
      .then(function (r) { return r.json(); })
      .then(function (geojson) {
        var visited = new Set(visitedCountries);
        L.geoJSON(geojson, {
          style: function (feature) {
            var name = feature.properties.ADMIN || feature.properties.name || '';
            var isVisited = visited.has(name);
            return {
              fillColor: isVisited ? '#4575b4' : '#d3d3d3',
              fillOpacity: isVisited ? 0.65 : 0.3,
              color: '#fff',
              weight: 0.5
            };
          },
          onEachFeature: function (feature, layer) {
            var name = feature.properties.ADMIN || feature.properties.name || '';
            if (visited.has(name)) {
              layer.bindTooltip(name);
            }
          }
        }).addTo(map);
      });

    // City markers
    cityData.forEach(function (city) {
      if (city.lat && city.lon) {
        L.circleMarker([city.lat, city.lon], {
          radius: 4,
          fillColor: '#e84848',
          color: '#fff',
          weight: 1,
          fillOpacity: 0.8
        }).bindTooltip(city.name + ', ' + city.country).addTo(map);
      }
    });
  });
})();
</script>
```

**Known limitation:** The country name in `travel_countries.yml` (from Takeout parsing) must match the `ADMIN` property in the countries GeoJSON. Common mismatches to watch for after populating real data:
- "United States" vs "United States of America" — fix in `COUNTRY_ALIASES` in `parse_takeout.py`
- "United Kingdom" — usually matches
- Check the browser console after populating real data; unmatched countries won't be highlighted

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Navigate to `http://localhost:4000/projects/fun-travel/` in the dev server. With empty placeholder data, the map should render as a light grey world map with no highlighted countries. Open the browser console and verify no JavaScript errors.

After populating with real Takeout data (when your export arrives), rebuild and verify countries are highlighted and city markers appear.

- [ ] **Commit**

```bash
git add _projects/fun_travel.md _data/travel_countries.yml _data/travel_cities.yml \
        assets/json/world-countries.geojson
git commit -m "projects: add travel card with Leaflet choropleth and city markers"
```

---

## Task 10: Documentation

**Files:** `CLAUDE.md` (new), `UPSTREAM_README.md` (new), `README.md` (rewrite)

- [ ] **Create `CLAUDE.md`**

```markdown
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

Two places to update together when role/focus changes:
1. `_pages/about.md` subtitle (visible header)
2. `_config.yml` description (meta tag)

## Build

```bash
bundle install          # first time only
bundle exec jekyll serve # local dev at http://localhost:4000
bundle exec jekyll build --strict_front_matter  # production build check
```

## Data pipelines

**Strava:** `scripts/update_strava.py` — run manually or via `.github/workflows/update-strava.yml`.
Requires env vars: `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REFRESH_TOKEN`.
GitHub Actions secrets set in repo Settings → Secrets and variables → Actions.

**Travel:** `scripts/parse_takeout.py /path/to/Takeout` — run locally after Google Takeout export.
Outputs `_data/travel_countries.yml` and `_data/travel_cities.yml`. Review cities file before
committing (contains noise from restaurants/offices).

## Bib keys for key papers

- `chiou2021interpreting` — T1D + exocrine pancreas, *Nature* 2021
- `chiou2021single` — islet scATAC-seq, 2021
- `sun2023plasma` — UKB-PPP, *Nature* 2023
- `intact2025multi` — Multi-INTACT methods paper

## Don't touch unless re-templating

- `_sass/` — al-folio CSS (upstream)
- `assets/libs/` — vendored JS libraries
- `_config.yml` third_party_libraries block — library versions/integrity hashes
- `bin/` — CI scripts (upstream)
```

- [ ] **Archive upstream README**

```bash
cp README.md UPSTREAM_README.md
git add UPSTREAM_README.md
```

- [ ] **Rewrite `README.md`**

```markdown
# joshchiou.github.io

Personal website of Joshua Chiou — [joshchiou.github.io](https://joshchiou.github.io).

Built on [al-folio](https://github.com/alshedivat/al-folio) by Maruan Al-Shedivat et al.

## Local development

```bash
bundle install
bundle exec jekyll serve
```

Site runs at `http://localhost:4000`.

## Structure

| Path | Purpose |
|---|---|
| `_pages/about.md` | Landing page |
| `_data/cv.yml` | CV data |
| `_bibliography/papers.bib` | Publications (jekyll-scholar) |
| `_news/*.md` | News items |
| `_projects/*.md` | Project cards |
| `_data/contributions.yml` | Open-source PR list |
| `scripts/update_strava.py` | Strava data pipeline |
| `scripts/parse_takeout.py` | Google Takeout parser for travel map |

## Data pipelines

See `CLAUDE.md` for details on the Strava and travel data pipelines.
```

- [ ] **Build and verify**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

- [ ] **Commit**

```bash
git add CLAUDE.md README.md UPSTREAM_README.md
git commit -m "docs: add CLAUDE.md, rewrite README, archive upstream README"
```

---

## Task 11: Bug audit pass

Run the full build, check links, visually scan every page. Fix anything found.

- [ ] **Strict build with full output**

```bash
bundle exec jekyll build --strict_front_matter --verbose 2>&1 | grep -E "Warning|Error|warn|error" | head -30
```

Address any warnings before moving on.

- [ ] **Run link checker**

```bash
bundle exec jekyll build --strict_front_matter
npx lychee _site/ --config .lycheeignore 2>&1 | tail -20
```

Fix broken internal links. Add unreachable external links to `.lycheeignore` only if the target URL is correct but temporarily down.

- [ ] **Visual checklist in dev server**

Start: `bundle exec jekyll serve`

Check each page in both light and dark mode, and at mobile width (375px):

| Page | Check |
|---|---|
| `/` (about) | Subtitle correct, news shows "Joined Lilly…" (past tense), selected publications render |
| `/publications/` | All papers render, Altmetric/Dimensions badges load, co-first asterisks correct |
| `/projects/` | Both work and fun categories show, all 10 cards have titles and descriptions |
| `/projects/work-type-1-diabetes…/` | Citations render, no broken links |
| `/projects/fun-cats/` | Gallery images load, imagemagick WebP variants used |
| `/projects/fun-cycling/` | ECharts calendar and bar chart render (populated if Strava script has been run) |
| `/projects/fun-travel/` | Leaflet map loads, no console errors |
| `/cv/` | All sections render, PDF link works, skill chips display |
| `/repositories/` | Two repo cards + 8 contribution list items |
| `/news/` | Full news list renders |
| `404.html` | Loads, redirect text present |

- [ ] **Verify OG/Schema.org meta**

```bash
bundle exec jekyll build --strict_front_matter
grep -A 3 'og:description\|og:image\|schema.org' _site/index.html | head -20
```

Confirm the `og:description` matches the updated `_config.yml` description and `og:image` points to `prof_pic.jpg`.

- [ ] **Fix any issues found** and commit in one or more targeted commits with descriptive messages.

- [ ] **Final build confirmation**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -3
```

Expected: `Build complete!` (or equivalent) with no errors or warnings.

---

## Post-plan: user content swaps

These are not tasks in the plan — they happen asynchronously as content becomes available:

- **Work card hero images:** Replace `assets/img/prof_pic.jpg` placeholder in each `_projects/work_*.md` with a figure from the anchor paper. Place in `assets/img/projects/work/`.
- **Home Assistant screenshot:** Add to `assets/img/projects/fun/home-assistant/` and update `img:` in `fun_home_assistant.md`.
- **Cocktail photos:** Add to `assets/img/projects/fun/cocktails/` and add `{% include figure.liquid path="assets/img/projects/fun/cocktails/PHOTO.jpg" class="img-fluid rounded z-depth-1" %}` includes in `fun_cocktails.md`.
- **Travel data:** Run `python scripts/parse_takeout.py /path/to/Takeout` when Takeout export arrives; review and commit `_data/travel_countries.yml` and `_data/travel_cities.yml`.
- **Country name mismatches:** After populating travel data, check the browser console on the travel page for unmatched country names and add them to `COUNTRY_ALIASES` in `parse_takeout.py`.
