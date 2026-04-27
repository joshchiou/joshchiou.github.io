---
layout: page
title: Cycling
description: Strava-powered cycling stats — activity calendar and all-time totals.
img: assets/img/projects/placeholder-fun.svg
importance: 2
category: fun
chart:
  echarts: true
---

{% assign stats = site.data.strava_stats %}
{% assign total_miles = stats.total_distance_km | times: 0.621371 | round %}
{% assign total_ft = stats.total_elevation_m | times: 3.28084 | round %}

<div class="row mb-4 text-center">
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_rides | default: "—" }}</h3>
    <small class="text-muted">rides</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_miles | default: "—" }}</h3>
    <small class="text-muted">miles</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_ft | default: "—" }}</h3>
    <small class="text-muted">ft elevation</small>
  </div>
</div>

### Activity calendar ({{ 'now' | date: '%Y' }})

<div id="cycling-calendar" style="height: 185px;"></div>
<p class="text-muted mt-1 mb-4"><small>Each cell is one day; color shows miles ridden.</small></p>

### Monthly distance (all-time)

<div id="cycling-monthly" style="height: 280px;"></div>

<script>
(function () {
  var KM_TO_MI = 0.621371;

  var rawCalendar = {{ site.data.strava_calendar | jsonify }};
  var calendarMiles = rawCalendar.map(function (d) {
    return [d[0], Math.round(d[1] * KM_TO_MI * 10) / 10];
  });
  var maxMiles = Math.ceil(Math.max.apply(null, calendarMiles.map(function (d) { return d[1]; })) / 10) * 10;

  var months   = {{ site.data.strava_stats.monthly | map: "month" | jsonify }};
  var distMiles = {{ site.data.strava_stats.monthly | map: "distance_km" | jsonify }}.map(function (km) {
    return Math.round(km * KM_TO_MI * 10) / 10;
  });

  function initCharts() {
    var calEl = document.getElementById('cycling-calendar');
    if (calEl && window.echarts) {
      echarts.init(calEl).setOption({
        tooltip: {
          formatter: function (p) { return p.data[0] + '<br/>' + p.data[1] + ' mi'; }
        },
        visualMap: {
          min: 0,
          max: maxMiles,
          show: true,
          orient: 'horizontal',
          left: 'right',
          bottom: 0,
          itemWidth: 10,
          itemHeight: 70,
          text: ['more', 'less'],
          textStyle: { fontSize: 10 },
          inRange: { color: ['#e8f4f8', '#74add1', '#2980b9'] }
        },
        calendar: {
          range: '{{ 'now' | date: '%Y' }}',
          cellSize: ['auto', 16],
          top: 20, left: 40, right: 115,
          itemStyle: { borderWidth: 2, borderColor: '#fff' },
          yearLabel: { show: false },
          monthLabel: { fontSize: 11 },
          dayLabel: { nameMap: ['S', 'M', 'T', 'W', 'T', 'F', 'S'] }
        },
        series: [{ type: 'heatmap', coordinateSystem: 'calendar', data: calendarMiles }]
      });
    }

    var barEl = document.getElementById('cycling-monthly');
    if (barEl && window.echarts) {
      echarts.init(barEl).setOption({
        tooltip: {
          trigger: 'axis',
          formatter: function (params) { return params[0].name + '<br/>' + params[0].value + ' mi'; }
        },
        grid: { left: 55, right: 20, top: 15, bottom: 65 },
        xAxis: {
          type: 'category',
          data: months,
          axisLabel: { rotate: 45, interval: 0, fontSize: 11 }
        },
        yAxis: {
          type: 'value',
          name: 'miles',
          nameTextStyle: { fontSize: 11 },
          splitLine: { lineStyle: { type: 'dashed', opacity: 0.5 } }
        },
        series: [{
          type: 'bar',
          data: distMiles,
          itemStyle: { color: '#2980b9', borderRadius: [3, 3, 0, 0] },
          emphasis: { itemStyle: { color: '#1a5f8a' } }
        }]
      });
    }
  }

  if (document.readyState === 'complete') { initCharts(); }
  else { window.addEventListener('load', initCharts); }
})();
</script>

<small class="text-muted">Updated {{ stats.updated_at | date: "%b %-d, %Y" | default: "never" }} via Strava API.</small>
