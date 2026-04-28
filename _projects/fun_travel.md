---
layout: page
title: Travel
description: Places visited, mapped.
img: assets/img/projects/fun/travel.svg
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
  var visitedCountries = {{ countries | map: "name" | jsonify }};
  var cityData = {{ cities | jsonify }};

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  var map, tileLayer, geoLayer, cityMarkers = [];

  var TILES = {
    light: 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
    dark: 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
  };

  function countryStyle(feature) {
    var name = feature.properties.name || '';
    var visited = new Set(visitedCountries);
    var isVisited = visited.has(name);
    var dark = isDark();
    return {
      fillColor: isVisited ? (dark ? '#58a6ff' : '#4575b4') : (dark ? '#2d333b' : '#d3d3d3'),
      fillOpacity: isVisited ? 0.65 : (dark ? 0.4 : 0.3),
      color: dark ? '#444c56' : '#fff',
      weight: 0.5
    };
  }

  function cityStyle() {
    var dark = isDark();
    return {
      radius: 4,
      fillColor: dark ? '#f97583' : '#e84848',
      color: dark ? '#2d333b' : '#fff',
      weight: 1,
      fillOpacity: 0.8
    };
  }

  function initMap() {
    var mapEl = document.getElementById('travel-map');
    if (!mapEl) return;

    var dark = isDark();
    map = L.map(mapEl, { scrollWheelZoom: false }).setView([20, 0], 2);

    tileLayer = L.tileLayer(dark ? TILES.dark : TILES.light, {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 19
    }).addTo(map);

    fetch('{{ "/assets/json/world-countries.geojson" | relative_url }}')
      .then(function (r) { return r.json(); })
      .then(function (geojson) {
        var visited = new Set(visitedCountries);
        geoLayer = L.geoJSON(geojson, {
          style: countryStyle,
          onEachFeature: function (feature, layer) {
            var name = feature.properties.name || '';
            if (visited.has(name)) {
              layer.bindTooltip(name);
            }
          }
        }).addTo(map);
      });

    cityData.forEach(function (city) {
      if (city.lat && city.lon) {
        var marker = L.circleMarker([city.lat, city.lon], cityStyle())
          .bindTooltip(city.name + ', ' + city.country)
          .addTo(map);
        cityMarkers.push(marker);
      }
    });
  }

  function updateTheme() {
    if (!map) return;
    var dark = isDark();
    tileLayer.setUrl(dark ? TILES.dark : TILES.light);
    if (geoLayer) { geoLayer.setStyle(countryStyle); }
    var style = cityStyle();
    cityMarkers.forEach(function (m) { m.setStyle(style); });
  }

  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-theme') { updateTheme(); }
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  if (document.readyState === 'complete') {
    initMap();
  } else {
    document.addEventListener('readystatechange', function () {
      if (document.readyState === 'complete') initMap();
    });
  }
})();
</script>
