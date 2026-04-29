---
layout: page
title: Travel
description: Places visited, mapped.
img: assets/img/projects/fun/travel.svg
importance: 5
category: fun
map: true
chart:
  echarts: true
images:
  slider: true
---

{% assign countries = site.data.travel_countries %}
{% assign cities = site.data.travel_cities %}
{% assign continents = countries | map: "continent" | uniq %}

<div class="travel-stats mb-3">
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

<div id="travel-map" style="height: 480px; border-radius: 8px; overflow: hidden;"></div>
<p class="text-muted mt-1 mb-4"><small>Click a highlighted country to see cities visited.</small></p>

### Where I've been

<div id="travel-donut" style="height: 280px;"></div>

### Photos

<div class="swiper mySwiper mt-3">
  <div class="swiper-wrapper">
    {% for i in (1..6) %}
    <div class="swiper-slide">
      {% capture img_path %}assets/img/projects/fun/travel/travel-{{ i }}.webp{% endcapture %}
      {% include figure.liquid loading="lazy" path=img_path class="img-fluid rounded z-depth-1" alt="Travel photo" zoomable=true %}
    </div>
    {% endfor %}
  </div>
  <div class="swiper-pagination"></div>
  <div class="swiper-button-prev"></div>
  <div class="swiper-button-next"></div>
</div>

<!-- Add travel photos as: assets/img/projects/fun/travel/travel-1.webp through travel-6.webp -->

<script>
document.addEventListener('DOMContentLoaded', function () {
  new Swiper('.mySwiper', {
    slidesPerView: 1,
    spaceBetween: 16,
    loop: true,
    pagination: { el: '.swiper-pagination', clickable: true },
    navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
    breakpoints: {
      576: { slidesPerView: 2 },
      992: { slidesPerView: 3 }
    }
  });
});
</script>

<script>
(function () {
  var visitedCountries = {{ countries | map: "name" | jsonify }};
  var cityData = {{ cities | jsonify }};
  var continentData = [
    {% assign grouped = countries | group_by: "continent" %}
    {% for g in grouped %}
      { name: '{{ g.name }}', value: {{ g.items | size }} }{% unless forloop.last %},{% endunless %}
    {% endfor %}
  ];

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  var map, tileLayer, geoLayer, cityMarkers = [];
  var donutChart;

  var TILES = {
    light: 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
    dark: 'https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png'
  };

  var CONTINENT_COLORS = {
    'North America': '#4575b4',
    'Europe': '#e67e22',
    'Asia': '#27ae60'
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
    if (!mapEl || typeof L === 'undefined') return;

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
              var countryCities = cityData.filter(function (c) { return c.country === name; });
              if (countryCities.length > 0) {
                var cityNames = countryCities.map(function (c) { return c.name; }).join(', ');
                var cityCount = countryCities.length;
                var label = cityCount + (cityCount === 1 ? ' city' : ' cities');
                layer.bindPopup('<strong>' + name + '</strong><br/><em>' + label + '</em>: ' + cityNames);
              } else {
                layer.bindPopup('<strong>' + name + '</strong>');
              }
            } else {
              layer.bindTooltip(name, { className: 'leaflet-tooltip-unvisited', opacity: 0.6 });
            }
          }
        }).addTo(map);
      })
      .catch(function (err) { console.warn('Failed to load country data:', err); });

    cityData.forEach(function (city) {
      if (city.lat && city.lon) {
        var marker = L.circleMarker([city.lat, city.lon], cityStyle())
          .bindTooltip(city.name + ', ' + city.country)
          .addTo(map);
        cityMarkers.push(marker);
      }
    });
  }

  function buildDonutOption() {
    var dark = isDark();
    var textColor = dark ? '#c8c8c8' : '#333333';
    return {
      tooltip: {
        trigger: 'item',
        formatter: function (p) { return p.name + ': ' + p.value + ' countr' + (p.value === 1 ? 'y' : 'ies'); }
      },
      legend: {
        bottom: 0,
        textStyle: { color: textColor, fontSize: 12 }
      },
      series: [{
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: dark ? '#22223a' : '#fff', borderWidth: 2 },
        label: {
          show: true,
          formatter: '{b}\n{c}',
          color: textColor,
          fontSize: 12
        },
        data: continentData.map(function (d) {
          return { name: d.name, value: d.value, itemStyle: { color: CONTINENT_COLORS[d.name] || '#888' } };
        })
      }]
    };
  }

  function initDonut() {
    var el = document.getElementById('travel-donut');
    if (!el || typeof echarts === 'undefined') return;
    if (donutChart) { echarts.dispose(el); }
    donutChart = echarts.init(el);
    donutChart.setOption(buildDonutOption());
  }

  function updateTheme() {
    if (map) {
      var dark = isDark();
      tileLayer.setUrl(dark ? TILES.dark : TILES.light);
      if (geoLayer) { geoLayer.setStyle(countryStyle); }
      var style = cityStyle();
      cityMarkers.forEach(function (m) { m.setStyle(style); });
    }
    initDonut();
  }

  window.addEventListener('resize', function () {
    if (donutChart) { donutChart.resize(); }
  });

  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-theme') { updateTheme(); }
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  function initAll() {
    initMap();
    initDonut();
  }

  if (document.readyState === 'complete') {
    setTimeout(initAll, 0);
  } else {
    window.addEventListener('load', initAll);
  }
})();
</script>
