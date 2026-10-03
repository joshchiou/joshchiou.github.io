---
layout: page
title: Type 1 Diabetes and the Exocrine Pancreas
description: Discovering acinar and ductal cell contributions to T1D genetic risk using single-cell epigenomics.
img: assets/img/projects/work/t1d-manhattan.webp
img_credit: "Figure adapted from Chiou et al., <em>Nature</em> 2021 (Fig. 1a)."
og_image: /assets/img/projects/og/t1d-manhattan.jpg
importance: 1
category: work
related_publications: true
---

<div class="project-tldr">
  <strong>TL;DR</strong>
  Much of the genetic risk for type 1 diabetes acts in exocrine pancreas cells, not only in the islets.
</div>

Type 1 diabetes (T1D) is usually described as a disease of the pancreatic islets: the immune
system destroys the beta cells that make insulin. For my PhD, I combined T1D genome-wide
association study (GWAS) results with single-cell chromatin accessibility maps of the human
pancreas and found that many T1D risk variants are active in acinar and ductal cells. These are
the exocrine cells that make digestive enzymes and carry them to the gut. The finding, published
in {% cite chiou2021interpreting %}, pointed to the exocrine pancreas as part of the disease.

Later work from our lab showed that blood levels of pancreatic enzymes are a causal biomarker of
T1D risk {% cite gaulton2024circulating %}, and single-cell multiome profiling of pancreas tissue
across disease stages showed how regulatory programs in each cell type change as T1D progresses
{% cite chiou2025singlecell %}. Together, these studies make the case that T1D involves the
exocrine pancreas as well as the islets.

Data and code: [joshchiou/T1D\_snATAC](https://github.com/joshchiou/T1D_snATAC)

---

**Related:** [Single-Cell Epigenomics of Pancreatic Islets]({{ '/projects/work_islet_epigenomics/' | relative_url }}), companion project mapping islet cell-type chromatin accessibility and type 2 diabetes risk variants.
