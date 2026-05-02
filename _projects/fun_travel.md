---
layout: page
title: Travel
description: Places visited, mapped.
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
</div>
<div class="travel-map-legend mb-5">
  <span class="travel-legend-swatch travel-legend-visited"></span><span class="travel-legend-label">Visited</span>
  <span class="travel-legend-swatch travel-legend-city"></span><span class="travel-legend-label">Cities</span>
</div>

### Countries & Cities

<div class="accordion travel-accordion mb-5" id="travelAccordion">
  {% assign sorted_countries = countries | sort: "name" %}
  {% for country in sorted_countries %}
    {% assign country_cities = cities | where: "country", country.name %}
    {% assign continent_slug = country.continent | downcase | replace: " ", "-" %}
    <div class="accordion-item travel-accordion-item">
      <h2 class="accordion-header" id="heading-{{ forloop.index }}">
        <button class="accordion-button collapsed travel-accordion-btn" type="button"
                data-bs-toggle="collapse"
                data-bs-target="#collapse-{{ forloop.index }}"
                aria-expanded="false"
                aria-controls="collapse-{{ forloop.index }}">
          <span class="travel-country-flag">{{ country.flag }}</span>
          <span class="travel-country-name">{{ country.name }}</span>
          <span class="travel-country-meta">
            <span class="badge travel-continent-badge travel-continent-{{ continent_slug }}">{{ country.continent }}</span>
            <span class="travel-city-count">{{ country_cities | size }}&nbsp;{% if country_cities.size == 1 %}city{% else %}cities{% endif %}</span>
          </span>
        </button>
      </h2>
      <div id="collapse-{{ forloop.index }}" class="accordion-collapse collapse"
           aria-labelledby="heading-{{ forloop.index }}">
        <div class="accordion-body travel-accordion-body">
          <div class="travel-city-pills">
            {% for city in country_cities %}
              <span class="travel-city-pill">{{ city.name }}</span>
            {% endfor %}
            {% if country_cities.size == 0 %}
              <span class="travel-city-pill text-muted">No cities logged</span>
            {% endif %}
          </div>
        </div>
      </div>
    </div>
  {% endfor %}
</div>

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
(function () {
  /* ── Data injected at build time ─────────────────────────────────────── */
  var VISITED_COUNTRIES = {{ countries | map: "name" | jsonify }};
  var CITY_DATA         = {{ cities | jsonify }};
  var RAW_COUNTRIES     = {{ countries | jsonify }};

  /* ── Continent lookup ────────────────────────────────────────────────── */
  var COUNTRY_CONTINENT = {};
  RAW_COUNTRIES.forEach(function (c) { COUNTRY_CONTINENT[c.name] = c.continent; });
  var visitedSet = new Set(VISITED_COUNTRIES);

  /* ── Color palettes ──────────────────────────────────────────────────── */
  var PAL = {
    light: {
      'North America': '#4575b4',
      'Europe':        '#e67e22',
      'Asia':          '#27ae60',
      _unvisited:      '#e0e0e0',
      _border:         '#ffffff'
    },
    dark: {
      'North America': '#58a6ff',
      'Europe':        '#f5a623',
      'Asia':          '#4ade80',
      _unvisited:      '#333333',
      _border:         '#2a2a2a'
    }
  };
  var CITY_DOT = {
    light: { fill: '#c0392b', stroke: '#ffffff' },
    dark:  { fill: '#f97583', stroke: '#1c1c1d' }
  };

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }
  function pal()     { return isDark() ? PAL.dark  : PAL.light; }
  function cityDot() { return isDark() ? CITY_DOT.dark : CITY_DOT.light; }

  /* ── Shared D3 state ─────────────────────────────────────────────────── */
  var svg, projection, geoPath, countriesG, citiesG;

  /* ── Map init ────────────────────────────────────────────────────────── */
  function initMap() {
    var el = document.getElementById('travel-map-svg');
    if (!el || typeof d3 === 'undefined') return;

    var W = 960, H = 500;
    svg = d3.select(el);

    projection = d3.geoNaturalEarth1()
      .scale(160)
      .translate([W / 2, H / 2]);

    geoPath   = d3.geoPath().projection(projection);
    countriesG = svg.append('g').attr('class', 'countries-layer');
    citiesG    = svg.append('g').attr('class', 'cities-layer');

    fetch('{{ "/assets/json/world-countries.geojson" | relative_url }}')
      .then(function (r) { return r.json(); })
      .then(function (geojson) {
        renderCountries(geojson);
        renderCities();
      })
      .catch(function (e) { console.warn('Travel map GeoJSON load failed:', e); });
  }

  function countryFill(name) {
    var p = pal();
    if (visitedSet.has(name)) {
      return p[COUNTRY_CONTINENT[name]] || p['North America'];
    }
    return p._unvisited;
  }

  function renderCountries(geojson) {
    var tooltip = document.getElementById('travel-map-tooltip');
    var wrap    = document.getElementById('travel-map-wrap');

    countriesG.selectAll('path')
      .data(geojson.features)
      .enter()
      .append('path')
      .attr('d', geoPath)
      .attr('class', function (d) {
        return visitedSet.has(d.properties.name) ? 'country-visited' : 'country-unvisited';
      })
      .attr('fill',   function (d) { return countryFill(d.properties.name); })
      .attr('stroke', pal()._border)
      .attr('stroke-width', 0.5)
      .on('mouseenter', function (event, d) {
        var name = d.properties.name;
        if (!visitedSet.has(name)) return;
        var citiesHere = CITY_DATA.filter(function (c) { return c.country === name; });
        var html = '<strong>' + name + '</strong>';
        if (citiesHere.length > 0) {
          html += '<br><span class="tt-cities">' + citiesHere.map(function (c) { return c.name; }).join(' · ') + '</span>';
        }
        tooltip.innerHTML = html;
        tooltip.classList.add('visible');
        tooltip.removeAttribute('aria-hidden');
      })
      .on('mousemove', function (event) {
        var svgBox = document.getElementById('travel-map-svg').getBoundingClientRect();
        tooltip.style.left = (event.clientX - svgBox.left + 14) + 'px';
        tooltip.style.top  = (event.clientY - svgBox.top  + 14) + 'px';
      })
      .on('mouseleave', function () {
        tooltip.classList.remove('visible');
        tooltip.setAttribute('aria-hidden', 'true');
      })
      .on('click', function (event, d) {
        var name = d.properties.name;
        if (!visitedSet.has(name)) return;
        var btns = document.querySelectorAll('.travel-accordion-btn');
        btns.forEach(function (btn) {
          if (btn.querySelector('.travel-country-name').textContent.trim() === name) {
            if (btn.classList.contains('collapsed')) { btn.click(); }
            btn.closest('.travel-accordion-item').scrollIntoView({ behavior: 'smooth', block: 'center' });
          }
        });
      });

    updateMapColors();
  }

  function updateMapColors() {
    if (!countriesG) return;
    var p = pal();
    countriesG.selectAll('path')
      .attr('fill',   function (d) { return countryFill(d.properties.name); })
      .attr('stroke', p._border);
  }

  function renderCities() {
    var dot = cityDot();
    citiesG.selectAll('circle')
      .data(CITY_DATA.filter(function (c) { return c.lat && c.lon; }))
      .enter()
      .append('circle')
      .attr('class', 'city-dot')
      .attr('cx', function (d) { var p = projection([d.lon, d.lat]); return p ? p[0] : -9999; })
      .attr('cy', function (d) { var p = projection([d.lon, d.lat]); return p ? p[1] : -9999; })
      .attr('r', 5)
      .attr('fill',         dot.fill)
      .attr('stroke',       dot.stroke)
      .attr('stroke-width', 1.5)
      .append('title')
      .text(function (d) { return d.name + ', ' + d.country; });
  }

  function updateCityColors() {
    if (!citiesG) return;
    var dot = cityDot();
    citiesG.selectAll('circle.city-dot')
      .attr('fill',   dot.fill)
      .attr('stroke', dot.stroke);
  }

  /* ── Photo gallery (graceful empty-state) ────────────────────────────── */
  function initGallery() {
    var wrapper     = document.getElementById('travelSwiperWrapper');
    var swiperEl    = document.getElementById('travelSwiper');
    var placeholder = document.getElementById('travelGalleryPlaceholder');
    if (!wrapper) return;

    var TOTAL = 6;
    var BASE  = '{{ "/assets/img/projects/fun/travel/travel-" | relative_url }}';
    var loaded = [], probed = 0;

    for (var i = 1; i <= TOTAL; i++) {
      (function (idx) {
        var img = new Image();
        img.onload = function () { loaded.push({ idx: idx, src: img.src }); finish(); };
        img.onerror = finish;
        img.src = BASE + idx + '.webp';
      })(i);
    }

    function finish() {
      probed++;
      if (probed < TOTAL) return;
      if (loaded.length === 0) return; /* keep placeholder */
      loaded.sort(function (a, b) { return a.idx - b.idx; });
      loaded.forEach(function (item) {
        var slide = document.createElement('div');
        slide.className = 'swiper-slide';
        var img = document.createElement('img');
        img.src = item.src;
        img.className = 'img-fluid rounded z-depth-1';
        img.alt = 'Travel photo';
        img.loading = 'lazy';
        slide.appendChild(img);
        wrapper.appendChild(slide);
      });
      placeholder.style.display = 'none';
      swiperEl.style.display = '';
      if (typeof Swiper !== 'undefined') {
        new Swiper('#travelSwiper', {
          slidesPerView: 1,
          spaceBetween: 16,
          loop: loaded.length > 3,
          pagination: { el: '.swiper-pagination', clickable: true },
          navigation: { nextEl: '.swiper-button-next', prevEl: '.swiper-button-prev' },
          breakpoints: { 576: { slidesPerView: 2 }, 992: { slidesPerView: 3 } }
        });
      }
    }
  }

  /* ── Theme observer ──────────────────────────────────────────────────── */
  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-theme') {
        updateMapColors();
        updateCityColors();
      }
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  /* ── Boot ────────────────────────────────────────────────────────────── */
  function boot() {
    initMap();
    initGallery();
  }

  if (document.readyState === 'complete') {
    boot();
  } else {
    window.addEventListener('load', boot);
  }
})();
</script>
