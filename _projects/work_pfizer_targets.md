---
layout: page
title: Genetics-Driven Target Discovery
description: Genetics and multi-omics pipelines for finding and validating drug targets at Pfizer.
img: assets/img/projects/work/pfizer-targets.webp
img_credit: "Illustration with synthetic data; it shows no study results."
og_image: /assets/img/projects/og/pfizer-targets.jpg
importance: 4
category: work
related_publications: false
---

<div class="project-tldr">
  <strong>TL;DR</strong>
  Led the team that built the genetics pipelines and cloud infrastructure Pfizer used to find and prioritize drug targets.
</div>

When I joined Pfizer's Internal Medicine Research Unit, genetics-based target discovery relied
on one-off analyses run by individual scientists on a high-performance computing (HPC) cluster.
Nothing reusable connected genome-wide association study (GWAS) evidence to functional genomics
to a target nomination. Over four years I led the team that built that pipeline. The idea was to
layer genetic association (GWAS, exome studies, Mendelian randomization) with functional data
(single-cell chromatin, expression and protein quantitative trait loci) so you could go from a
locus to a ranked target with genetic support for both efficacy and selectivity.

Alongside the pipeline work, I led the migration of Pfizer's genomics analysis to Amazon Web
Services (AWS), mainly to get GWAS and fine-mapping running at a scale the on-premise cluster
couldn't handle. That was a cross-functional effort with teams in statistics, machine learning,
and several therapeutic areas.

---

**Related:** [UK Biobank Pharma Proteomics Project]({{ '/projects/work_ukb_ppp/' | relative_url }}), the pQTL data behind some of the target ranking described above.
