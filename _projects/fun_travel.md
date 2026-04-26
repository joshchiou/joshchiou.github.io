---
layout: page
title: Travel
description: Places visited, mapped.
img: assets/img/prof_pic.jpg
importance: 5
category: fun
map: true
---

{% assign countries = site.data.travel_countries %}
{% assign cities = site.data.travel_cities %}

<div id="travel-map" style="height: 480px; border-radius: 8px; overflow: hidden;"></div>

<p class="mt-2 text-muted">
  <small>
    {{ countries | size }} countries &nbsp;·&nbsp; {{ cities | size }} cities
  </small>
</p>

<script>
(function () {
  // Countries visited (injected at build time by Jekyll)
  var visitedCountries = {{ countries | map: "name" | jsonify }};

  // Cities (lat/lon markers)
  var cityData = {{ cities | jsonify }};

  // Wait for Leaflet to be available (loaded by map: true in front matter)
  function initMap() {
    var mapEl = document.getElementById('travel-map');
    if (!mapEl) return;

    var map = L.map(mapEl, { scrollWheelZoom: false }).setView([20, 0], 2);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 19
    }).addTo(map);

    // Load committed GeoJSON (no CDN dependency)
    // NOTE: world-countries.geojson uses feature.properties.name.
    // These names must stay in sync with COUNTRY_ALIASES in scripts/parse_location_history.py.
    // e.g. the GeoJSON has "United States of America" but Nominatim + COUNTRY_ALIASES
    // normalizes to "United States" — so COUNTRY_ALIASES must map the GeoJSON name too.
    fetch('{{ "/assets/json/world-countries.geojson" | relative_url }}')
      .then(function (r) { return r.json(); })
      .then(function (geojson) {
        var visited = new Set(visitedCountries);
        L.geoJSON(geojson, {
          style: function (feature) {
            var name = feature.properties.name || '';
            var isVisited = visited.has(name);
            return {
              fillColor: isVisited ? '#4575b4' : '#d3d3d3',
              fillOpacity: isVisited ? 0.65 : 0.3,
              color: '#fff',
              weight: 0.5
            };
          },
          onEachFeature: function (feature, layer) {
            var name = feature.properties.name || '';
            if (visited.has(name)) {
              layer.bindTooltip(name);
            }
          }
        }).addTo(map);
      });

    // City markers
    cityData.forEach(function (city) {
      if (city.lat && city.lon) {
        L.circleMarker([city.lat, city.lon], {
          radius: 4,
          fillColor: '#e84848',
          color: '#fff',
          weight: 1,
          fillOpacity: 0.8
        }).bindTooltip(city.name + ', ' + city.country).addTo(map);
      }
    });
  }

  if (document.readyState === 'complete') {
    initMap();
  } else {
    document.addEventListener('readystatechange', function () {
      if (document.readyState === 'complete') initMap();
    });
  }
})();
</script>
