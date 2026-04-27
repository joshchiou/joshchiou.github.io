---
layout: page
title: On the Bike
description: Strava-powered cycling stats — activity calendar and all-time totals.
img: assets/img/projects/placeholder-fun.svg
importance: 2
category: fun
chart:
  echarts: true
---

{% assign stats = site.data.strava_stats %}

<div class="row mb-4 text-center">
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_rides | default: "—" }}</h3>
    <small class="text-muted">rides</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_distance_km | default: "—" | round }}</h3>
    <small class="text-muted">km</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_elevation_m | default: "—" | round }}</h3>
    <small class="text-muted">m elevation</small>
  </div>
</div>

### Activity calendar ({{ 'now' | date: '%Y' }})

```echarts
{
  "tooltip": { "position": "top" },
  "visualMap": {
    "min": 0,
    "max": 80,
    "calculable": true,
    "orient": "horizontal",
    "left": "center",
    "inRange": { "color": ["#e0f3f8", "#74add1", "#313695"] }
  },
  "calendar": {
    "range": "{{ 'now' | date: '%Y' }}",
    "cellSize": ["auto", 14],
    "itemStyle": { "borderWidth": 0.5 },
    "yearLabel": { "show": false }
  },
  "series": [{
    "type": "heatmap",
    "coordinateSystem": "calendar",
    "data": {{ site.data.strava_calendar | jsonify }}
  }]
}
```

### Monthly distance (all-time)

```echarts
{
  "tooltip": { "trigger": "axis" },
  "xAxis": {
    "type": "category",
    "data": {{ site.data.strava_stats.monthly | map: "month" | jsonify }},
    "axisLabel": { "rotate": 45, "interval": 5 }
  },
  "yAxis": { "type": "value", "name": "km" },
  "series": [{
    "type": "bar",
    "data": {{ site.data.strava_stats.monthly | map: "distance_km" | jsonify }},
    "itemStyle": { "color": "#74add1" }
  }]
}
```

<small class="text-muted">Updated {{ stats.updated_at | date: "%b %-d, %Y" | default: "never" }} via Strava API.</small>
