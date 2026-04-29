---
layout: page
title: Claire
description: The real senior scientist in the family.
img: assets/img/projects/fun/cats/claire-main.webp
importance: 4
category: fun
---

{% assign claire = site.data.claire %}
{% assign genetics = site.data.claire_genetics %}

<!-- ── Hero ──────────────────────────────────────────────────────────────── -->
<div class="claire-hero">

  <!-- Left: photo + stat table -->
  <div class="claire-hero-left">
    <div class="claire-hero-img-wrap">
      {% include figure.liquid loading="eager" path="assets/img/projects/fun/cats/claire-main.webp" class="img-fluid" alt="Claire" zoomable=true %}
    </div>
    <div class="claire-stat-table">
      <div class="claire-stat-cell">
        <div class="claire-stat-label">Breed</div>
        <div class="claire-stat-val">Domestic Shorthair</div>
      </div>
      <div class="claire-stat-cell">
        <div class="claire-stat-label">Gender</div>
        <div class="claire-stat-val">&#9792; Female</div>
      </div>
      <div class="claire-stat-cell">
        <div class="claire-stat-label">Born</div>
        <div class="claire-stat-val">~2018</div>
      </div>
      <div class="claire-stat-cell">
        <div class="claire-stat-label">Coat</div>
        <div class="claire-stat-val">Gray</div>
      </div>
    </div>
  </div>

  <!-- Right: lede + Basepaws genetics -->
  <div class="claire-hero-right">
    <p class="claire-lede">
      &ldquo;Joined the family in February 2021 and has since contributed significantly
      to the household&rsquo;s research culture through sustained application of lap
      occupancy.&rdquo;
    </p>

    <div class="claire-genetics">
      <div class="claire-section-eyebrow">&#x1F9EC;&nbsp; Basepaws Breed Analysis</div>

      {% for breed in genetics.breeds %}
      <div class="claire-breed-row">
        <span class="claire-breed-name">{{ breed.name }}</span>
        <div class="claire-breed-track">
          <div class="claire-breed-fill {{ breed.cls }}" style="width: {{ breed.pct }}%"></div>
        </div>
        <span class="claire-breed-pct">{{ breed.pct }}%</span>
      </div>
      {% endfor %}

      <div class="claire-chr-section">
        <div class="claire-section-eyebrow">Chromosome Map</div>
        <div class="claire-chr-grid">
          {% for chr in genetics.chromosomes %}
          <div class="claire-chr-row">
            <span class="claire-chr-label">{{ chr.id }}</span>
            <div class="claire-chr-track">
              {% for seg in chr.segments %}
              <div class="claire-chr-seg {{ seg.cls }}" style="width: {{ seg.width }}%"></div>
              {% endfor %}
            </div>
          </div>
          {% endfor %}
        </div>
        <div class="claire-chr-legend">
          {% for breed in genetics.breeds %}
          <div class="claire-legend-item">
            <div class="claire-legend-dot {{ breed.cls }}"></div>
            <span>{{ breed.name }}</span>
          </div>
          {% endfor %}
        </div>
      </div>
    </div>
  </div>

</div><!-- /claire-hero -->

<!-- ── Section divider ───────────────────────────────────────────────────── -->
<div class="claire-divider">
  <div class="claire-divider-line"></div>
  <span class="claire-divider-text">Life in Photos</span>
  <div class="claire-divider-line"></div>
</div>

<!-- ── Timeline ──────────────────────────────────────────────────────────── -->
{% for entry in claire %}
<div class="claire-era">
  <div class="claire-era-header">
    <div class="claire-era-eyebrow">{{ entry.year }}</div>
    <div class="claire-era-title">{{ entry.milestone }}</div>
    <div class="claire-era-location">{{ entry.location }}</div>
  </div>
  <div class="claire-era-photo">
    {% include figure.liquid loading="lazy" path=entry.img class="img-fluid" alt=entry.milestone zoomable=true %}
  </div>
  {% if entry.caption %}
  <p class="claire-era-caption">{{ entry.caption }}</p>
  {% endif %}
</div>
{% endfor %}
