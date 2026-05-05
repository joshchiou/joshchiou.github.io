---
layout: page
title: Genetics-Driven Novel Target Discovery
description: Integrative multi-omics pipeline for identifying and validating drug targets at Pfizer.
img: assets/img/projects/work/pfizer-targets.svg
importance: 4
category: work
related_publications: false
---

<div class="project-tldr">
  <strong>TL;DR</strong>
  Built cloud-native genomics infrastructure pipelines for integrative target discovery at Pfizer.
</div>

When I joined Pfizer's Internal Medicine Research Unit, genetics-informed target discovery
relied on ad-hoc analyses run by individual scientists on legacy HPC infrastructure. There was
no scalable, reusable pipeline connecting GWAS evidence to functional genomics to target
nomination. Over 4+ years I built that connective layer: an integrative approach combining
human genetic evidence (GWAS, exome-wide association studies, colocalization, and Mendelian
randomization) with functional genomics layers including single-cell chromatin accessibility,
eQTL and pQTL datasets, and deep learning-based functional predictions to nominate and
prioritize novel targets with genetic support for efficacy and selectivity. Several targets
identified through this pipeline advanced into the Pfizer portfolio.

Beyond individual target programs, I led the development of cloud-native genomics infrastructure
on AWS, enabling large-scale analyses across the organization: scalable GWAS and fine-mapping
pipelines, standardized summary statistics harmonization, and integration of emerging
multi-omics datasets. This was a cross-organizational collaboration spanning Internal Medicine,
Inflammation & Immunology, Statistics, and Machine Learning & Computational Sciences.

---

**Related:** [UK Biobank Pharma Proteomics Project]({{ '/projects/work_ukb_ppp/' | relative_url }}) — the pQTL resource that informed target prioritization analyses described above.
