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
  Using blood proteomics from clinical trials to understand how obesity drugs work, beyond the weight loss itself.
</div>

When a patient on a GLP-1 receptor agonist loses a lot of weight, hundreds of plasma proteins
change. The hard part is working out which changes come from the drug itself and which simply
follow the weight loss. Only the first kind can tell you something about how the drug works.

At Lilly, I apply large-scale proteomics (mainly Olink Explore HT and SomaScan 11k) to phase 2
and phase 3 trials in obesity and cardiometabolic disease. I use longitudinal mixed models to
track proteins over time, mediation analysis to test whether protein changes explain clinical
outcomes, dose-response comparisons across treatment arms, and genetic methods (Mendelian
randomization, pQTL colocalization) to separate causal signals from confounding. I also build
the pipelines, data models, and dashboards the clinical omics team works with.

## SURMOUNT-5: tirzepatide versus semaglutide

SURMOUNT-5 compared tirzepatide (10 and 15 mg) head-to-head with semaglutide (1.7 and 2.4 mg) in
adults with obesity. Because both arms lose a lot of weight, differences between them point to
biology that weight loss alone doesn't explain. In exploratory analyses, tirzepatide was
associated with different changes in the plasma proteome than semaglutide, which may help explain
the different cardiometabolic benefits seen with the two drugs. I presented this work in an oral
session at [EASD 2026](https://easddistribute.m-anage.com/from.storage?image=DRQMKAdip9FzW2MCANbX41tkQmjbrlQspmPo0v0BxT9lAgy13X6VS7zqtYA0Botg0)
in Milan.

The analysis code is public on GitHub at
[EliLillyCo/surmount5-proteomics](https://github.com/EliLillyCo/surmount5-proteomics). An interactive
results dashboard, [surmount5-proteomics.lilly.com](https://surmount5-proteomics.lilly.com),
accompanies the paper and opens to the public when the paper is published.

---

**Related:** [UK Biobank Pharma Proteomics Project]({{ '/projects/work_ukb_ppp/' | relative_url }}), the population proteomics resource behind some of the methods described above.
