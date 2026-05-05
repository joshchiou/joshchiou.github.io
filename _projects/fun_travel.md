---
layout: page
title: Travel
description: Places my wife and I have explored together, mapped from Google Timeline data.
img: assets/img/projects/fun/travel.svg
importance: 5
category: fun
d3: true
images:
  slider: true
---

{% assign countries = site.data.travel_countries %}
{% assign cities = site.data.travel_cities %}
{% assign continents = countries | map: "continent" | uniq %}

My wife and I try to get abroad once or twice a year, plus domestic trips when we can. We don't chase bucket lists — we'd rather return somewhere we love than tick a new box. France keeps pulling us back: our honeymoon along the Côte d'Azur, a second trip from Paris down to Lake Annecy, and most recently Barcelona to Toulouse. Three trips, three different Frances.

<div class="travel-stats mb-4">
  <div class="travel-stat">
    <span class="travel-stat-val">{{ countries | size }}</span>
    <span class="travel-stat-label">countries</span>
  </div>
  <div class="travel-stat">
    <span class="travel-stat-val">{{ continents | size }}</span>
    <span class="travel-stat-label">continents</span>
  </div>
  <div class="travel-stat">
    <span class="travel-stat-val">{{ cities | size }}</span>
    <span class="travel-stat-label">cities</span>
  </div>
</div>

<div id="travel-map-wrap" class="travel-map-wrap mb-2">
  <svg id="travel-map-svg" class="travel-map-svg" viewBox="0 0 960 500" preserveAspectRatio="xMidYMid meet"></svg>
  <div id="travel-map-tooltip" class="travel-map-tooltip" aria-hidden="true"></div>
  <button id="travel-map-reset" class="travel-map-reset-btn" title="Reset zoom">
    <i class="fa-solid fa-compress"></i>
  </button>
</div>
<p class="travel-map-hint">Ctrl + scroll to zoom &nbsp;·&nbsp; drag to pan &nbsp;·&nbsp; double-click to reset &nbsp;·&nbsp; hover country for city clusters &nbsp;·&nbsp; click to expand below</p>
<div class="travel-map-legend mb-4">
  <span class="travel-legend-swatch travel-legend-visited"></span><span class="travel-legend-label">Visited</span>
  <span class="travel-legend-swatch travel-legend-city"></span><span class="travel-legend-label">Cities</span>
</div>

### Countries & Cities

<div id="travel-bars-wrap" class="travel-bars-wrap mb-5"></div>

### Photos

<div id="travel-gallery-section">
  <div class="swiper mySwiper mt-3" id="travelSwiper" style="display:none">
    <div class="swiper-wrapper" id="travelSwiperWrapper"></div>
    <div class="swiper-pagination"></div>
    <div class="swiper-button-prev"></div>
    <div class="swiper-button-next"></div>
  </div>
  <div class="travel-gallery-placeholder" id="travelGalleryPlaceholder">
    <i class="fa-regular fa-images fa-2x"></i>
    <p>No travel photos yet — check back later.</p>
  </div>
</div>

<script>
window._travelData = {
  countries: {{ countries | map: "name" | jsonify }},
  cities: {{ cities | jsonify }},
  rawCountries: {{ countries | jsonify }},
  geojsonUrl: '{{ "/assets/json/world-countries.geojson" | relative_url }}',
  photoBase: '{{ "/assets/img/projects/fun/travel/travel-" | relative_url }}'
};
</script>
<script src="{{ '/assets/js/travel.js' | relative_url }}"></script>
