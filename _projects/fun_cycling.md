---
layout: page
title: Cycling
description: Six bikes, a slow cooker full of chain wax, and a couple years of Strava data.
img: assets/img/projects/fun/cycling.svg
importance: 2
category: fun
map: true
chart:
  echarts: true
---

{% assign stats = site.data.strava_stats %}
{% assign total_miles = stats.total_distance_km | times: 0.621371 | round %}
{% assign total_ft = stats.total_elevation_m | times: 3.28084 | round %}
{% assign bikes = site.data.bikes %}

<p class="text-muted mb-4">I ride a 2002 LeMond Zurich 18 miles to commute to work and back, year-round. Ice is basically the only thing that stops me. On weekends my wife and I pick whichever bikes fit the terrain: road loops around the Fells and out to Nahant, or gravel days in Acadia and Beaver Brook. We also try to find bike trips wherever we travel.</p>

<h2 class="page-chapter">By the numbers</h2>

{% if stats.total_rides %}
<div class="row mb-2 text-center">
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_rides }}</h3>
    <small class="text-muted">rides</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_miles }}</h3>
    <small class="text-muted">miles</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_ft | divided_by: 1000 }}k</h3>
    <small class="text-muted">ft climbed</small>
  </div>
</div>
<div class="text-center mb-4" style="font-size: 0.82rem; color: var(--global-text-color-light);">
  <span id="stat-streak"></span><span id="stat-streak-sep" style="display:none"> &nbsp;·&nbsp; </span><span id="stat-best-streak"></span><span id="stat-pace-sep" style="display:none"> &nbsp;·&nbsp; </span><span id="stat-pace"></span>
</div>
{% else %}
<p class="text-muted">Stats updating. Check back soon.</p>
{% endif %}

<div id="last-ride-card" class="mb-4" style="display:none">
  <small class="text-muted">Last ride: <span id="last-ride-date"></span> · <span id="last-ride-dist"></span></small>
</div>

<div class="chart-toggle chart-view-tabs mb-2">
  <button class="chart-toggle-btn chart-view-btn active" data-view="calendar">Calendar</button>
  <button class="chart-toggle-btn chart-view-btn" data-view="monthly">Monthly</button>
  <button class="chart-toggle-btn chart-view-btn" data-view="cumulative">Cumulative</button>
</div>

<div id="cycling-calendar" class="cycling-chart-pane"></div>
<div id="cycling-monthly" class="cycling-chart-pane" style="display:none; height: 280px;"></div>
<div id="cycling-cumulative" class="cycling-chart-pane" style="display:none; height: 250px;"></div>

<p class="text-muted mt-1 mb-2"><small id="chart-caption">Each cell is one day; color shows miles ridden.</small></p>

<a href="https://strava.app.link/gjWmumzIT2b" class="strava-link" target="_blank" rel="noopener">
  <i class="fa-brands fa-strava"></i> View on Strava
</a>


<h2 class="page-chapter">Highlights</h2>

<p class="text-muted mb-3">A few rides that stand out.</p>

<div class="featured-rides">
  {% for ride in site.data.featured_rides %}
  <div class="featured-ride-card">
    <img class="featured-ride-img" src="{{ ride.image }}" alt="{{ ride.title }}" loading="lazy">
    <div class="featured-ride-body">
      <h4 class="featured-ride-title">{{ ride.title }}</h4>
      <p class="featured-ride-meta">{{ ride.location }} · {{ ride.distance_km | times: 0.621371 | round }} mi</p>
      <p class="featured-ride-story">{{ ride.story }}</p>
    </div>
  </div>
  {% endfor %}
</div>


<h2 class="page-chapter">The bikes</h2>

<p class="text-muted mb-4">Six vintage frames found on Craigslist and rebuilt in my basement. Four LeMond road bikes and two late-90s Specialized Stumpjumpers converted to gravel bikes, inspired by builds on r/xbiking. I do all the wrenching myself, from cable swaps and bearing overhauls to full drivetrain upgrades. All the drivetrains run on hot-waxed chain: strip the factory grease, melted wax in a slow cooker, re-dip every few hundred miles or whenever I remember.</p>

<div class="bike-carousel">
  <div class="bike-carousel-viewport">
    <div class="bike-carousel-track" id="bikeTrack">
      {% for bike in bikes %}
      <div class="bike-card bike-carousel-slide">
        <div class="bike-card-img-wrap">
          {% if bike.image %}
            <img src="{{ bike.image | relative_url }}" alt="{{ bike.name }}" loading="lazy">
          {% else %}
            <div class="bike-card-placeholder">
              <i class="fa-solid fa-bicycle"></i>
            </div>
          {% endif %}
        </div>
        <div class="bike-card-body">
          <div class="bike-card-header">
            <div>
              <h4 class="bike-card-title">{{ bike.year }} {{ bike.name }}</h4>
            </div>
            {% if bike.status %}
              <span class="bike-card-status">{{ bike.status }}</span>
            {% endif %}
          </div>
        </div>
        <div class="bike-card-details">
          {% for group in bike.groups %}
            <div class="bike-chip-group">
              <span class="bike-chip-group-label">{{ group.label }}</span>
              <div class="bike-chip-list">
                {% for item in group.items %}
                  <span class="bike-chip">{{ item }}</span>
                {% endfor %}
              </div>
            </div>
          {% endfor %}
        </div>
        <button class="bike-card-toggle" aria-expanded="false" aria-label="Show specs">
          <span>Specs</span> <i class="fa-solid fa-chevron-down"></i>
        </button>
      </div>
      {% endfor %}
    </div>
  </div>
  <div class="bike-carousel-controls" id="bikeControls">
    <button class="bike-carousel-btn" id="bikePrev" aria-label="Previous bike">
      <i class="fa-solid fa-chevron-left"></i>
    </button>
    <div class="bike-carousel-dots" id="bikeDots"></div>
    <button class="bike-carousel-btn" id="bikeNext" aria-label="Next bike">
      <i class="fa-solid fa-chevron-right"></i>
    </button>
  </div>
</div>

<script>
window._cyclingData = {
  monthly: {{ site.data.strava_stats.monthly | jsonify }},
  calendar: {{ site.data.strava_calendar | jsonify }}
};
</script>
<script src="{{ '/assets/js/cycling.js' | relative_url }}"></script>

<p class="text-muted text-right mt-4 mb-0" style="font-size: 0.75rem; opacity: 0.6;">Data via Strava API · {{ stats.updated_at | date: "%b %-d, %Y" | default: "–" }}</p>
