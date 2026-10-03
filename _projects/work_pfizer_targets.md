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
  Built the genetics pipelines and cloud infrastructure Pfizer used to find and prioritize drug targets.
</div>

When I joined Pfizer's Internal Medicine Research Unit, genetics-based target discovery relied
on one-off analyses run by individual scientists on an aging HPC cluster. Nothing reusable
connected GWAS evidence to functional genomics to a target nomination. Over four years I built
that pipeline. It combined human genetic evidence (GWAS, exome-wide association studies,
colocalization, and Mendelian randomization) with functional genomics, including single-cell
chromatin accessibility, eQTL and pQTL data, and deep learning predictions of variant function,
to find and rank new targets with genetic support for efficacy and selectivity. Several targets
it found advanced into the Pfizer portfolio.

I also led the move of Pfizer's genomics analysis to AWS: GWAS and fine-mapping pipelines that
scale, a standard way to harmonize summary statistics, and support for new multi-omics datasets.
That work involved teams from Internal Medicine, Inflammation & Immunology, Statistics, and
Machine Learning & Computational Sciences.

---

**Related:** [UK Biobank Pharma Proteomics Project]({{ '/projects/work_ukb_ppp/' | relative_url }}), the pQTL data behind some of the target ranking described above.
