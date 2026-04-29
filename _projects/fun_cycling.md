---
layout: page
title: Cycling
description: Strava-powered cycling stats — activity calendar and all-time totals.
img: assets/img/projects/fun/cycling.svg
importance: 2
category: fun
chart:
  echarts: true
---

{% assign stats = site.data.strava_stats %}
{% assign total_miles = stats.total_distance_km | times: 0.621371 | round %}
{% assign total_ft = stats.total_elevation_m | times: 3.28084 | round %}
{% assign bikes = site.data.bikes %}

### Bike fleet

{% for bike in bikes %}
<div class="bike-card mb-4">
  <div class="bike-card-img-wrap">
    {% if bike.image %}
      <img src="{{ bike.image | relative_url }}" alt="{{ bike.name }}">
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
</div>
{% endfor %}

### Stats

{% if stats.total_rides %}
<div class="row mb-4 text-center">
  <div class="col-4">
    <h3 class="mb-0">{{ stats.total_rides }}</h3>
    <small class="text-muted">rides</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_miles }}</h3>
    <small class="text-muted">miles</small>
  </div>
  <div class="col-4">
    <h3 class="mb-0">{{ total_ft }}</h3>
    <small class="text-muted">ft elevation</small>
  </div>
</div>
{% else %}
<p class="text-muted">Stats updating — check back soon.</p>
{% endif %}

<div id="last-ride-card" class="mb-4" style="display:none">
  <small class="text-muted">Last ride: <span id="last-ride-date"></span> &middot; <span id="last-ride-dist"></span></small>
</div>

### Activity calendar (year to date)

<div id="cycling-calendar"></div>
<p class="text-muted mt-1 mb-4"><small>Each cell is one day; color shows miles ridden.</small></p>

### Monthly distance

<div class="chart-toggle mb-2">
  <button class="chart-toggle-btn active" data-view="alltime">All-time</button>
  <button class="chart-toggle-btn" data-view="byyear">By year</button>
</div>
<div id="cycling-monthly" style="height: 280px;"></div>

### Cumulative distance

<div id="cycling-cumulative" style="height: 250px;"></div>

<script>
(function () {
  var KM_TO_MI = 0.621371;

  // Monthly and cumulative data are small — keep inlined
  var monthlyRaw = {{ site.data.strava_stats.monthly | jsonify }};
  var months = monthlyRaw.map(function (m) { return m.month; });
  var distMiles = monthlyRaw.map(function (m) {
    return Math.round(m.distance_km * KM_TO_MI * 10) / 10;
  });

  var byYear = {};
  monthlyRaw.forEach(function (m) {
    var parts = m.month.split('-');
    var year = parts[0];
    var monthIdx = parseInt(parts[1], 10) - 1;
    if (!byYear[year]) byYear[year] = new Array(12).fill(0);
    byYear[year][monthIdx] = Math.round(m.distance_km * KM_TO_MI * 10) / 10;
  });
  var years = Object.keys(byYear).sort();
  var monthLabels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var yearColors = ['#2980b9', '#e67e22', '#27ae60', '#8e44ad', '#e74c3c'];

  var cumMonths = [];
  var cumValues = [];
  var running = 0;
  distMiles.forEach(function (val, i) {
    running += val;
    cumMonths.push(months[i]);
    cumValues.push(Math.round(running * 10) / 10);
  });

  var calChart, barChart, cumChart;
  var calendarMiles = null;
  var maxMiles = 0;
  var currentView = 'alltime';

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  // Fetch calendar data externally (keeps page HTML lean)
  var calEl = document.getElementById('cycling-calendar');
  if (calEl) {
    calEl.innerHTML = '<div style="height:155px;display:flex;align-items:center;justify-content:center"><small class="text-muted">Loading activity data&hellip;</small></div>';
  }
  fetch('{{ "/assets/data/strava_calendar.json" | relative_url }}')
    .then(function (r) { return r.json(); })
    .then(function (rawCalendar) {
      calendarMiles = rawCalendar.map(function (d) {
        return [d[0], Math.round(d[1] * KM_TO_MI * 10) / 10];
      });
      maxMiles = Math.ceil(Math.max.apply(null, calendarMiles.map(function (d) { return d[1]; })) / 10) * 10;

      // Show last ride card
      if (calendarMiles.length > 0) {
        var last = calendarMiles[calendarMiles.length - 1];
        var dateObj = new Date(last[0] + 'T00:00:00');
        var dateStr = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        var card = document.getElementById('last-ride-card');
        if (card) {
          document.getElementById('last-ride-date').textContent = dateStr;
          document.getElementById('last-ride-dist').textContent = last[1] + ' mi';
          card.style.display = '';
        }
      }

      initCalChart();
    })
    .catch(function () {
      if (calEl) calEl.innerHTML = '<small class="text-muted">Activity data unavailable.</small>';
    });

  function buildCalOption() {
    if (!calendarMiles) return {};
    var mobile = window.innerWidth < 576;
    var dark = isDark();
    var textColor   = dark ? '#c8c8c8' : '#333333';
    var emptyColor  = dark ? '#1e3a4a' : '#e8f4f8';
    var borderColor = dark ? '#2d2d2d' : '#ffffff';
    return {
      tooltip: {
        formatter: function (p) { return p.data[0] + '<br/>' + p.data[1] + ' mi'; }
      },
      visualMap: {
        min: 0, max: maxMiles, show: true,
        orient: 'horizontal',
        left: mobile ? 'center' : 'right',
        bottom: 0,
        itemWidth: 10, itemHeight: 70,
        text: ['more', 'less'],
        textStyle: { fontSize: 10, color: textColor },
        inRange: { color: [emptyColor, '#74add1', '#2980b9'] }
      },
      calendar: {
        range: ['{{ "now" | date: "%Y" }}-01-01', '{{ "now" | date: "%Y-%m-%d" }}'],
        cellSize: ['auto', mobile ? 13 : 16],
        top: 20,
        left: mobile ? 30 : 40,
        right: mobile ? 10 : 115,
        bottom: mobile ? 50 : 30,
        itemStyle: { borderWidth: 2, borderColor: borderColor },
        yearLabel: { show: false },
        monthLabel: { fontSize: 11, color: textColor },
        dayLabel: { nameMap: ['S', 'M', 'T', 'W', 'T', 'F', 'S'], color: textColor }
      },
      series: [{ type: 'heatmap', coordinateSystem: 'calendar', data: calendarMiles }]
    };
  }

  function buildBarOption() {
    var dark = isDark();
    var textColor  = dark ? '#c8c8c8' : '#333333';
    var splitColor = dark ? 'rgba(200,200,200,0.15)' : 'rgba(0,0,0,0.1)';

    if (currentView === 'byyear') {
      return {
        tooltip: {
          trigger: 'axis',
          formatter: function (params) {
            var lines = params.map(function (p) {
              return '<span style="color:' + p.color + '">●</span> ' + p.seriesName + ': ' + p.value + ' mi';
            });
            return params[0].name + '<br/>' + lines.join('<br/>');
          }
        },
        legend: {
          data: years,
          textStyle: { color: textColor, fontSize: 11 },
          top: 0
        },
        grid: { left: 55, right: 20, top: 35, bottom: 30 },
        xAxis: {
          type: 'category', data: monthLabels,
          axisLabel: { fontSize: 11, color: textColor },
          axisLine:  { lineStyle: { color: textColor } },
          axisTick:  { lineStyle: { color: textColor } }
        },
        yAxis: {
          type: 'value', name: 'miles',
          nameTextStyle: { fontSize: 11, color: textColor },
          axisLabel: { color: textColor },
          splitLine: { lineStyle: { type: 'dashed', color: splitColor } }
        },
        series: years.map(function (year, i) {
          return {
            name: year, type: 'line', data: byYear[year],
            smooth: true, symbol: 'circle', symbolSize: 6,
            lineStyle: { width: 2.5 },
            itemStyle: { color: yearColors[i % yearColors.length] }
          };
        })
      };
    }

    return {
      tooltip: {
        trigger: 'axis',
        formatter: function (params) { return params[0].name + '<br/>' + params[0].value + ' mi'; }
      },
      grid: { left: 55, right: 20, top: 15, bottom: 65 },
      xAxis: {
        type: 'category', data: months,
        axisLabel: { rotate: 45, interval: 0, fontSize: 11, color: textColor },
        axisLine:  { lineStyle: { color: textColor } },
        axisTick:  { lineStyle: { color: textColor } }
      },
      yAxis: {
        type: 'value', name: 'miles',
        nameTextStyle: { fontSize: 11, color: textColor },
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { type: 'dashed', color: splitColor } }
      },
      series: [{
        type: 'bar', data: distMiles,
        itemStyle: { color: '#2980b9', borderRadius: [3, 3, 0, 0] },
        emphasis: { itemStyle: { color: '#1a5f8a' } }
      }]
    };
  }

  function buildCumOption() {
    var dark = isDark();
    var textColor  = dark ? '#c8c8c8' : '#333333';
    var splitColor = dark ? 'rgba(200,200,200,0.15)' : 'rgba(0,0,0,0.1)';
    return {
      tooltip: {
        trigger: 'axis',
        formatter: function (params) { return params[0].name + '<br/>' + params[0].value + ' mi total'; }
      },
      grid: { left: 55, right: 20, top: 15, bottom: 65 },
      xAxis: {
        type: 'category', data: cumMonths,
        axisLabel: { rotate: 45, interval: 0, fontSize: 11, color: textColor },
        axisLine:  { lineStyle: { color: textColor } },
        axisTick:  { lineStyle: { color: textColor } }
      },
      yAxis: {
        type: 'value', name: 'miles',
        nameTextStyle: { fontSize: 11, color: textColor },
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { type: 'dashed', color: splitColor } }
      },
      series: [{
        type: 'line', data: cumValues,
        smooth: true,
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [
          { offset: 0, color: 'rgba(41,128,185,0.35)' },
          { offset: 1, color: 'rgba(41,128,185,0.05)' }
        ]}},
        lineStyle: { color: '#2980b9', width: 2.5 },
        itemStyle: { color: '#2980b9' },
        symbol: 'circle', symbolSize: 5
      }]
    };
  }

  function initCalChart() {
    var calEl = document.getElementById('cycling-calendar');
    if (calEl && window.echarts && calendarMiles) {
      if (calChart) { echarts.dispose(calEl); }
      var mobile = window.innerWidth < 576;
      calEl.style.height = (mobile ? 180 : 155) + 'px';
      calEl.innerHTML = '';
      calChart = echarts.init(calEl);
      calChart.setOption(buildCalOption());
    }
  }

  function initOtherCharts() {
    var barEl = document.getElementById('cycling-monthly');
    if (barEl && window.echarts) {
      if (barChart) { echarts.dispose(barEl); }
      barChart = echarts.init(barEl);
      barChart.setOption(buildBarOption());
    }
    var cumEl = document.getElementById('cycling-cumulative');
    if (cumEl && window.echarts) {
      if (cumChart) { echarts.dispose(cumEl); }
      cumChart = echarts.init(cumEl);
      cumChart.setOption(buildCumOption());
    }
  }

  function initAllCharts() {
    initCalChart();
    initOtherCharts();
  }

  document.querySelectorAll('.chart-toggle-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.chart-toggle-btn').forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      currentView = btn.getAttribute('data-view');
      var barEl = document.getElementById('cycling-monthly');
      if (barEl && window.echarts) {
        if (barChart) { echarts.dispose(barEl); }
        barChart = echarts.init(barEl);
        barChart.setOption(buildBarOption());
      }
    });
  });

  window.addEventListener('resize', function () {
    if (calChart) {
      var calEl = document.getElementById('cycling-calendar');
      var mobile = window.innerWidth < 576;
      calEl.style.height = (mobile ? 180 : 155) + 'px';
      calChart.resize();
      calChart.setOption(buildCalOption());
    }
    if (barChart) { barChart.resize(); }
    if (cumChart) { cumChart.resize(); }
  });

  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-theme') { initAllCharts(); }
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  if (document.readyState === 'complete') { initOtherCharts(); }
  else { window.addEventListener('load', initOtherCharts); }
})();
</script>

<p class="text-muted text-right mt-4 mb-0" style="font-size: 0.75rem; opacity: 0.6;">Data via Strava API · {{ stats.updated_at | date: "%b %-d, %Y" | default: "–" }}</p>
