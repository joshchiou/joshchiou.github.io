---
layout: page
title: Single-Cell Epigenomics of Pancreatic Islets
description: Mapping cell-type-specific chromatin accessibility and its role in diabetes genetic risk.
img: assets/img/projects/work/islet-scatac-umap.webp
img_credit: "Figure adapted from Chiou et al., <em>Nature Genetics</em> 2021 (Fig. 1a)."
og_image: /assets/img/projects/og/islet-scatac-umap.jpg
importance: 2
category: work
related_publications: true
---

<div class="project-tldr">
  <strong>TL;DR</strong>
  Single-cell chromatin maps of human pancreatic islets revealed how type 2 diabetes risk variants alter gene regulation at the cell type level.
</div>

Hundreds of genetic variants influence type 2 diabetes risk, but most sit in non-coding regions
of the genome, where it's hard to tell what they do without knowing which regulatory elements are
active in which cells. For my PhD, I used single-cell ATAC-seq on human islets to map chromatin
accessibility in each cell type (beta, alpha, delta, and others), then linked the regulatory
programs active in each cell type to type 2 diabetes GWAS loci {% cite chiou2021single %}. That
made it possible to read non-coding risk variants in terms of the islet cells they act in.

Related work looked at how nutrient signals change the islet epigenome to control insulin
secretion {% cite islet2023nutrient %}, and at how genetic variants at type 2 diabetes loci change
regulatory activity in each cell type as the disease develops {% cite wang2023integrating %}. The
catalog of islet regulatory elements from this work is widely used to interpret diabetes GWAS
results.

---

**Related:** [Type 1 Diabetes and the Exocrine Pancreas]({{ '/projects/work_t1d_exocrine/' | relative_url }}), the companion project that used the same single-cell approach to trace T1D risk to acinar and ductal cells.
