---
layout: page
title: Translational Proteomics for Obesity Clinical Trials
description: Large-scale proteomics in phase 2/3 obesity trials, including SURMOUNT-5.
img: assets/img/projects/work/lilly-proteomics.webp
img_credit: "Illustration with synthetic data; it shows no study results."
og_image: /assets/img/projects/og/lilly-proteomics.jpg
importance: 5
category: work
related_publications: false
---

<div class="project-tldr">
  <strong>TL;DR</strong>
  Using blood proteomics from clinical trials to figure out which protein changes come from obesity drugs themselves and which just follow the weight loss.
</div>

When a patient on a glucagon-like peptide-1 (GLP-1) receptor agonist loses a lot of weight, hundreds of plasma proteins
change. The challenge is working out which changes come from the drug itself and which simply
follow the weight loss. Only the first kind can tell you something about how the drug works.

At Lilly, I apply large-scale proteomics (mainly Olink Explore HT and SomaScan 11k) to phase 2
and phase 3 trials in obesity and cardiometabolic disease. The core analysis problem is causal
inference: a patient loses weight and hundreds of proteins move, so you need mixed models,
mediation analysis, and genetic anchoring (Mendelian randomization, protein quantitative trait
locus (pQTL) colocalization) to figure out which changes come from the drug rather than from
weight loss alone. I also build the pipelines and dashboards the clinical omics team uses day to
day.

## SURMOUNT-5: tirzepatide versus semaglutide

SURMOUNT-5 compared tirzepatide (10 and 15 mg) head-to-head with semaglutide (1.7 and 2.4 mg) in
adults with obesity. Tirzepatide led to more weight loss, so comparing the arms means separating
protein changes that track weight loss from those that don't. In exploratory analyses,
tirzepatide was associated with different changes in the plasma proteome than semaglutide. I
presented this work in an oral session at the European Association for the Study of Diabetes
(EASD) annual meeting, [EASD 2026](https://easddistribute.m-anage.com/from.storage?image=DRQMKAdip9FzW2MCANbX41tkQmjbrlQspmPo0v0BxT9lAgy13X6VS7zqtYA0Botg0)
in Milan.

The analysis code is public on GitHub at
[EliLillyCo/surmount5-proteomics](https://github.com/EliLillyCo/surmount5-proteomics), and an
interactive results dashboard is available at
[surmount5-proteomics.lilly.com](https://surmount5-proteomics.lilly.com).

---

**Related:** [UK Biobank Pharma Proteomics Project]({{ '/projects/work_ukb_ppp/' | relative_url }}), the population proteomics resource behind some of the methods described above.
