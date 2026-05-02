---
layout: page
permalink: /publications/
title: publications
description: Full publication list in reverse chronological order.
nav: true
nav_order: 1
---

{% include publication_meta.liquid %}

{% include bib_search.liquid %}

<div class="publications">

<h2 class="bibliography selected-heading"><i class="fa-solid fa-star"></i> Selected</h2>

{% bibliography --group_by none --query @*[selected=true]* --sort_by cv_order --order ascending %}

<h2 class="pub-section-heading all-heading">All Publications</h2>

{% bibliography %}

</div>
