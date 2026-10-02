---
layout: page
title: Translational Proteomics for Obesity Clinical Trials
description: Mechanistic and biomarker insights from large-scale proteomics in phase 2/3 obesity trials, including the SURMOUNT-5 head-to-head comparison.
img: assets/img/projects/work/lilly-proteomics.svg
importance: 5
category: work
related_publications: false
---

<div class="project-tldr">
  <strong>TL;DR</strong>
  Understanding the molecular mechanisms of weight loss therapeutics through large-scale proteomics.
</div>

When a patient on a GLP-1 receptor agonist loses significant body weight, hundreds of plasma
proteins change. The central analytical challenge is interpretation: which of those changes
reflect the drug's direct mechanism, and which are indirect consequences of weight loss itself?
Disentangling these signals is what determines whether a protein change is a real biomarker
candidate or an artifact that would mislead clinical decisions.

At Lilly, I work at this intersection of clinical omics and drug development, applying
large-scale proteomics (primarily Olink Explore HT and SomaScan 11k) to phase 2 and phase 3
clinical trials for obesity and cardiometabolic disease. The analytical toolkit combines
longitudinal mixed models to track protein trajectories over time, mediation analysis to test
whether protein changes drive clinical outcomes, dose-response comparisons across treatment
arms, and genetic causal inference (Mendelian randomization, pQTL colocalization) to anchor
signals in biology rather than confounding. I also build the analytical infrastructure
(pipelines, data models, dashboards) that supports the broader clinical omics team.

## SURMOUNT-5: tirzepatide versus semaglutide

SURMOUNT-5 compared tirzepatide (10 and 15 mg) head-to-head with semaglutide (1.7 and 2.4 mg) in
adults with obesity. A head-to-head design is unusually informative for proteomics: both arms lose
substantial weight, so differences between them point toward biology that weight loss alone does
not explain. In exploratory analyses, tirzepatide was associated with distinct changes in the
plasma proteome compared with semaglutide, offering early biological insight into the differences
in cardiometabolic benefit observed between the two therapies. I presented this work as an oral
presentation at [EASD 2026](https://easddistribute.m-anage.com/from.storage?image=DRQMKAdip9FzW2MCANbX41tkQmjbrlQspmPo0v0BxT9lAgy13X6VS7zqtYA0Botg0)
in Milan.

---

**Related:** [UK Biobank Pharma Proteomics Project]({{ '/projects/work_ukb_ppp/' | relative_url }}) — the foundational proteomics resource that guides some of the analytical work described above.
