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

<p class="text-muted mb-4">Two 2002 LeMond steel frames — the Zurich is my daily commuter and the Tourmalet is the backup. On weekends my wife and I explore the Boston area together, ranging from short loops around the Fells to longer rides out to Nahant, Castle Island, and beyond. I do all my own wrenching and always learn something new in the process.</p>

### Bike fleet

<div class="bike-carousel">
  <div class="bike-carousel-viewport">
    <div class="bike-carousel-track" id="bikeTrack">
      {% for bike in bikes %}
      <div class="bike-card bike-carousel-slide">
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

### Wrenching

<p class="text-muted mb-4">I service both bikes myself — cable swaps, brake and derailleur adjustments, bearing overhauls, and occasional full rebuilds. Both drivetrains run on hot-waxed chain: I strip the factory grease, melt wax in a slow cooker, and re-dip every few hundred miles. The drivetrain stays noticeably cleaner and quieter compared to wet lube, and touching up the wax mid-season is quick. Every bike I work on teaches me something new, which is a big part of why I enjoy it.</p>

### Stats

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
    <h3 class="mb-0">{{ total_ft }}</h3>
    <small class="text-muted">ft elevation</small>
  </div>
</div>
<div class="text-center mb-4" style="font-size: 0.82rem; color: var(--global-text-color-light);">
  <span id="stat-streak"></span><span id="stat-streak-sep" style="display:none"> &nbsp;·&nbsp; </span><span id="stat-best-streak"></span><span id="stat-pace-sep" style="display:none"> &nbsp;·&nbsp; </span><span id="stat-pace"></span>
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

  // ── Inline monthly data ──────────────────────────────────────────────────
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

  // ── YoY pace ─────────────────────────────────────────────────────────────
  var curYear = years[years.length - 1];
  var prevYear = String(parseInt(curYear, 10) - 1);
  var curYearData = byYear[curYear] || [];
  var curMonthIdx = -1;
  for (var _i = 11; _i >= 0; _i--) {
    if ((curYearData[_i] || 0) > 0) { curMonthIdx = _i; break; }
  }
  var yoyDelta = null, yoyPct = null, projFull = null;
  if (curMonthIdx >= 0 && byYear[prevYear]) {
    var curYTD = 0, prevYTD = 0;
    for (var _j = 0; _j <= curMonthIdx; _j++) {
      curYTD += curYearData[_j] || 0;
      prevYTD += byYear[prevYear][_j] || 0;
    }
    curYTD = Math.round(curYTD);
    prevYTD = Math.round(prevYTD);
    yoyDelta = curYTD - prevYTD;
    yoyPct   = prevYTD > 0 ? Math.round(yoyDelta / prevYTD * 100) : null;
    projFull = Math.round(curYTD / (curMonthIdx + 1) * 12);
  }

  function showPaceStat() {
    if (yoyDelta === null) return;
    var el  = document.getElementById('stat-pace');
    var sep = document.getElementById('stat-pace-sep');
    if (!el) return;
    var sign = yoyDelta >= 0 ? '+' : '';
    var pct  = yoyPct !== null ? ' (' + sign + yoyPct + '%)' : '';
    el.textContent = sign + yoyDelta + ' mi vs ' + prevYear + pct + ' · on pace for ~' + projFull + ' mi';
    el.style.color = yoyDelta >= 0 ? '#27ae60' : '#e74c3c';
    if (sep) sep.style.display = '';
  }

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

  // ── Streak helpers ───────────────────────────────────────────────────────
  function calcStreaks(data) {
    if (!data || data.length < 1) return { current: 0, best: 0 };
    var parsed = data.map(function (d) {
      var p = d[0].split('-');
      return new Date(+p[0], +p[1] - 1, +p[2]);
    }).sort(function (a, b) { return a - b; });

    var best = 1, run = 1;
    for (var i = 1; i < parsed.length; i++) {
      if ((parsed[i] - parsed[i - 1]) === 86400000) { run++; if (run > best) best = run; }
      else run = 1;
    }

    var today = new Date(); today.setHours(0, 0, 0, 0);
    var last = parsed[parsed.length - 1];
    var gap = Math.round((today - last) / 86400000);
    var current = 0;
    if (gap <= 1) {
      current = 1;
      for (var j = parsed.length - 2; j >= 0; j--) {
        if (Math.round((parsed[j + 1] - parsed[j]) / 86400000) === 1) current++;
        else break;
      }
    }
    return { current: current, best: best };
  }

  // ── Calendar fetch ───────────────────────────────────────────────────────
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

      // Last ride card
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

      // Streak stats
      var streaks = calcStreaks(calendarMiles);
      var streakEl = document.getElementById('stat-streak');
      var bestEl = document.getElementById('stat-best-streak');
      var sepEl = document.getElementById('stat-streak-sep');
      if (streakEl) {
        if (streaks.current > 1) {
          streakEl.textContent = streaks.current + '-day streak';
        }
      }
      if (bestEl && streaks.best > 1) {
        bestEl.textContent = 'best: ' + streaks.best + ' days';
        if (sepEl && streaks.current > 1) sepEl.style.display = '';
      }

      initCalChart();
    })
    .catch(function () {
      if (calEl) calEl.innerHTML = '<small class="text-muted">Activity data unavailable.</small>';
    });

  // ── Chart option builders ────────────────────────────────────────────────
  function buildCalOption() {
    if (!calendarMiles) return {};
    var mobile = window.innerWidth < 576;
    var dark = isDark();
    var textColor  = dark ? '#c8c8c8' : '#333333';
    var emptyColor = dark ? 'rgba(255,255,255,0.05)' : 'rgba(41,128,185,0.09)';
    var borderColor = dark ? 'rgba(255,255,255,0.05)' : 'rgba(41,128,185,0.15)';
    var activeHigh = dark ? '#74add1' : '#2980b9';
    var activeMid  = dark ? '#4a9fd4' : '#5aaee0';
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
        inRange: { color: [emptyColor, activeMid, activeHigh] }
      },
      calendar: {
        range: ['{{ "now" | date: "%Y" }}-01-01', '{{ "now" | date: "%Y-%m-%d" }}'],
        cellSize: ['auto', mobile ? 13 : 16],
        top: 20,
        left: mobile ? 30 : 40,
        right: mobile ? 10 : 115,
        bottom: mobile ? 50 : 30,
        itemStyle: { borderWidth: 1, borderColor: borderColor },
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
      var markerColor = dark ? 'rgba(200,200,200,0.3)' : 'rgba(100,100,100,0.28)';
      var markerLabelColor = dark ? 'rgba(200,200,200,0.5)' : 'rgba(100,100,100,0.55)';
      return {
        tooltip: {
          trigger: 'axis',
          formatter: function (params) {
            var lines = [];
            var curVal = null, prevVal = null;
            params.forEach(function (p) {
              lines.push('<span style="color:' + p.color + '">●</span> ' + p.seriesName + ': ' + (p.value || 0) + ' mi');
              if (p.seriesName === curYear) curVal = p.value;
              if (p.seriesName === prevYear) prevVal = p.value;
            });
            var result = params[0].name + '<br/>' + lines.join('<br/>');
            if (curVal && prevVal) {
              var d = Math.round(curVal - prevVal);
              var sign = d >= 0 ? '+' : '';
              var col  = d >= 0 ? '#27ae60' : '#e74c3c';
              result += '<br/><span style="font-size:0.88em;color:' + col + '">' + sign + d + ' mi vs ' + prevYear + '</span>';
            }
            return result;
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
          var s = {
            name: year, type: 'line', data: byYear[year],
            smooth: true, symbol: 'circle', symbolSize: 6,
            lineStyle: { width: 2.5 },
            itemStyle: { color: yearColors[i % yearColors.length] }
          };
          if (year === curYear && curMonthIdx >= 0) {
            s.markLine = {
              silent: true,
              symbol: ['none', 'none'],
              data: [{ xAxis: monthLabels[curMonthIdx] }],
              lineStyle: { type: 'dashed', color: markerColor, width: 1.5 },
              label: {
                show: true, position: 'insideEndTop',
                formatter: 'today', fontSize: 10, color: markerLabelColor
              }
            };
          }
          return s;
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

  // ── Chart init ───────────────────────────────────────────────────────────
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

  // ── Bike carousel ────────────────────────────────────────────────────────
  function initBikeCarousel() {
    var track = document.getElementById('bikeTrack');
    var controls = document.getElementById('bikeControls');
    if (!track) return;
    var slides = Array.prototype.slice.call(track.querySelectorAll('.bike-carousel-slide'));
    var n = slides.length;
    if (n <= 1) {
      if (controls) controls.style.display = 'none';
      return;
    }

    var cur = 0;
    var dots = [];
    var dotsEl = document.getElementById('bikeDots');
    var prevBtn = document.getElementById('bikePrev');
    var nextBtn = document.getElementById('bikeNext');

    for (var i = 0; i < n; i++) {
      var dot = document.createElement('button');
      dot.className = 'bike-carousel-dot';
      dot.setAttribute('aria-label', 'Bike ' + (i + 1));
      (function (idx) { dot.addEventListener('click', function () { go(idx); }); })(i);
      dotsEl.appendChild(dot);
      dots.push(dot);
    }

    function slideWidth() {
      return slides[0].offsetWidth + 16; // card width + 1rem gap
    }

    function go(idx) {
      cur = Math.max(0, Math.min(idx, n - 1));
      track.style.transform = 'translateX(-' + (cur * slideWidth()) + 'px)';
      dots.forEach(function (d, i) { d.classList.toggle('active', i === cur); });
      prevBtn.disabled = cur === 0;
      nextBtn.disabled = cur === n - 1;
    }

    prevBtn.addEventListener('click', function () { go(cur - 1); });
    nextBtn.addEventListener('click', function () { go(cur + 1); });
    go(0);

    window._bikeCarouselGo = go;
    window._bikeCarouselCur = function () { return cur; };
  }

  // ── Toggle buttons ───────────────────────────────────────────────────────
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

  // ── Resize & theme ───────────────────────────────────────────────────────
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
    // Re-snap carousel after resize
    if (window._bikeCarouselGo) { window._bikeCarouselGo(window._bikeCarouselCur()); }
  });

  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-theme') { initAllCharts(); }
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  // ── Boot ─────────────────────────────────────────────────────────────────
  if (document.readyState === 'complete') {
    initOtherCharts();
    initBikeCarousel();
    showPaceStat();
  } else {
    window.addEventListener('load', function () {
      initOtherCharts();
      initBikeCarousel();
      showPaceStat();
    });
  }
})();
</script>

<p class="text-muted text-right mt-4 mb-0" style="font-size: 0.75rem; opacity: 0.6;">Data via Strava API · {{ stats.updated_at | date: "%b %-d, %Y" | default: "–" }}</p>
