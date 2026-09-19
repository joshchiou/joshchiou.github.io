(function () {
  var KM_TO_MI = 0.621371;
  var GOAL_MILES = 1000;

  var monthlyRaw = window._cyclingData.monthly;
  var calendarRaw = window._cyclingData.calendar;
  var ridesRaw = window._cyclingData.rides;
  var locationsRaw = window._cyclingData.locations;

  var months = monthlyRaw.map(function (m) {
    return m.month;
  });
  var distMiles = monthlyRaw.map(function (m) {
    return Math.round(m.distance_km * KM_TO_MI * 10) / 10;
  });

  var byYear = {};
  monthlyRaw.forEach(function (m) {
    var parts = m.month.split("-");
    var year = parts[0];
    var monthIdx = parseInt(parts[1], 10) - 1;
    if (!byYear[year]) byYear[year] = new Array(12).fill(0);
    byYear[year][monthIdx] = Math.round(m.distance_km * KM_TO_MI * 10) / 10;
  });
  var years = Object.keys(byYear).sort();
  var monthLabels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var yearColors = ["#2980b9", "#e67e22", "#27ae60", "#8e44ad", "#e74c3c"];

  // YoY pace
  var curYear = years[years.length - 1];
  var prevYear = String(parseInt(curYear, 10) - 1);
  var curYearData = byYear[curYear] || [];
  var curMonthIdx = -1;
  for (var _i = 11; _i >= 0; _i--) {
    if ((curYearData[_i] || 0) > 0) {
      curMonthIdx = _i;
      break;
    }
  }
  var yoyDelta = null,
    yoyPct = null,
    projFull = null;
  if (curMonthIdx >= 0 && byYear[prevYear]) {
    var curYTD = 0,
      prevYTD = 0;
    for (var _j = 0; _j <= curMonthIdx; _j++) {
      curYTD += curYearData[_j] || 0;
      prevYTD += byYear[prevYear][_j] || 0;
    }
    curYTD = Math.round(curYTD);
    prevYTD = Math.round(prevYTD);
    yoyDelta = curYTD - prevYTD;
    yoyPct = prevYTD > 0 ? Math.round((yoyDelta / prevYTD) * 100) : null;
    projFull = Math.round((curYTD / (curMonthIdx + 1)) * 12);
  }

  function showPaceStat() {
    if (yoyDelta === null) return;
    var el = document.getElementById("stat-pace");
    var sep = document.getElementById("stat-pace-sep");
    if (!el) return;
    var sign = yoyDelta >= 0 ? "+" : "";
    var pct = yoyPct !== null ? " (" + sign + yoyPct + "%)" : "";
    el.textContent = sign + yoyDelta + " mi vs " + prevYear + pct + " · on pace for ~" + projFull + " mi";
    el.style.color = yoyDelta >= 0 ? "#27ae60" : "#e74c3c";
    if (sep) sep.style.display = "";
  }

  // Cumulative data
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

  function isDark() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  // Streak helpers
  function calcStreaks(data) {
    if (!data || data.length < 1) return { current: 0, best: 0 };
    var parsed = data
      .map(function (d) {
        var p = d[0].split("-");
        return new Date(+p[0], +p[1] - 1, +p[2]);
      })
      .sort(function (a, b) {
        return a - b;
      });

    var best = 1,
      run = 1;
    for (var i = 1; i < parsed.length; i++) {
      if (parsed[i] - parsed[i - 1] === 86400000) {
        run++;
        if (run > best) best = run;
      } else run = 1;
    }

    var today = new Date();
    today.setHours(0, 0, 0, 0);
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

  // Calendar data
  calendarMiles = calendarRaw.map(function (d) {
    return [d[0], Math.round(d[1] * KM_TO_MI * 10) / 10];
  });
  maxMiles =
    Math.ceil(
      Math.max.apply(
        null,
        calendarMiles.map(function (d) {
          return d[1];
        })
      ) / 10
    ) * 10;

  // Last ride card
  if (calendarMiles.length > 0) {
    var lastRide = calendarMiles[calendarMiles.length - 1];
    var dateObj = new Date(lastRide[0] + "T00:00:00");
    var dateStr = dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    var card = document.getElementById("last-ride-card");
    if (card) {
      document.getElementById("last-ride-date").textContent = dateStr;
      document.getElementById("last-ride-dist").textContent = lastRide[1] + " mi";
      card.style.display = "";
    }
  }

  // Streak stats
  var streaks = calcStreaks(calendarMiles);
  var streakEl = document.getElementById("stat-streak");
  var bestEl = document.getElementById("stat-best-streak");
  var sepEl = document.getElementById("stat-streak-sep");
  if (streakEl && streaks.current > 1) {
    streakEl.textContent = streaks.current + "-day streak";
  }
  if (bestEl && streaks.best > 1) {
    bestEl.textContent = "best: " + streaks.best + " days";
    if (sepEl && streaks.current > 1) sepEl.style.display = "";
  }

  // Chart option builders
  function buildCalOption() {
    if (!calendarMiles) return {};
    var mobile = window.innerWidth < 576;
    var dark = isDark();
    var textColor = dark ? "#c8c8c8" : "#333333";
    var emptyColor = dark ? "rgba(255,255,255,0.05)" : "rgba(41,128,185,0.09)";
    var borderColor = dark ? "rgba(255,255,255,0.05)" : "rgba(41,128,185,0.15)";
    var activeHigh = dark ? "#74add1" : "#2980b9";
    var activeMid = dark ? "#4a9fd4" : "#5aaee0";
    var now = new Date();
    var yearStr = String(now.getFullYear());
    var todayStr = yearStr + "-" + String(now.getMonth() + 1).padStart(2, "0") + "-" + String(now.getDate()).padStart(2, "0");
    return {
      tooltip: {
        formatter: function (p) {
          return p.data[0] + "<br/>" + p.data[1] + " mi";
        },
      },
      visualMap: {
        min: 0,
        max: maxMiles,
        show: true,
        orient: "horizontal",
        left: mobile ? "center" : "right",
        bottom: 0,
        itemWidth: 10,
        itemHeight: 70,
        text: ["more", "less"],
        textStyle: { fontSize: 10, color: textColor },
        inRange: { color: [emptyColor, activeMid, activeHigh] },
      },
      calendar: {
        range: [yearStr + "-01-01", todayStr],
        cellSize: ["auto", mobile ? 13 : 16],
        top: 20,
        left: mobile ? 30 : 40,
        right: mobile ? 10 : 115,
        bottom: mobile ? 50 : 30,
        itemStyle: { borderWidth: 1, borderColor: borderColor },
        yearLabel: { show: false },
        monthLabel: { fontSize: 11, color: textColor },
        dayLabel: { nameMap: ["S", "M", "T", "W", "T", "F", "S"], color: textColor },
      },
      series: [{ type: "heatmap", coordinateSystem: "calendar", data: calendarMiles }],
    };
  }

  function buildBarOption() {
    var dark = isDark();
    var textColor = dark ? "#c8c8c8" : "#333333";
    var markerColor = dark ? "rgba(200,200,200,0.3)" : "rgba(100,100,100,0.28)";
    var markerLabelColor = dark ? "rgba(200,200,200,0.5)" : "rgba(100,100,100,0.55)";
    var splitColor = dark ? "rgba(200,200,200,0.15)" : "rgba(0,0,0,0.1)";

    return {
      tooltip: {
        trigger: "axis",
        formatter: function (params) {
          var lines = [];
          var curVal = null,
            prevVal = null;
          params.forEach(function (p) {
            lines.push('<span style="color:' + p.color + '">●</span> ' + p.seriesName + ": " + (p.value || 0) + " mi");
            if (p.seriesName === curYear) curVal = p.value;
            if (p.seriesName === prevYear) prevVal = p.value;
          });
          var result = params[0].name + "<br/>" + lines.join("<br/>");
          if (curVal && prevVal) {
            var d = Math.round(curVal - prevVal);
            var sign = d >= 0 ? "+" : "";
            var col = d >= 0 ? "#27ae60" : "#e74c3c";
            result += '<br/><span style="font-size:0.88em;color:' + col + '">' + sign + d + " mi vs " + prevYear + "</span>";
          }
          return result;
        },
      },
      legend: {
        data: years,
        textStyle: { color: textColor, fontSize: 11 },
        top: 0,
      },
      grid: { left: 55, right: 20, top: 35, bottom: 30 },
      xAxis: {
        type: "category",
        data: monthLabels,
        axisLabel: { fontSize: 11, color: textColor },
        axisLine: { lineStyle: { color: textColor } },
        axisTick: { lineStyle: { color: textColor } },
      },
      yAxis: {
        type: "value",
        name: "miles",
        nameTextStyle: { fontSize: 11, color: textColor },
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { type: "dashed", color: splitColor } },
      },
      series: years.map(function (year, i) {
        var s = {
          name: year,
          type: "line",
          data: byYear[year],
          smooth: true,
          symbol: "circle",
          symbolSize: 6,
          lineStyle: { width: 2.5 },
          itemStyle: { color: yearColors[i % yearColors.length] },
        };
        if (year === curYear && curMonthIdx >= 0) {
          s.markLine = {
            silent: true,
            symbol: ["none", "none"],
            data: [{ xAxis: monthLabels[curMonthIdx] }],
            lineStyle: { type: "dashed", color: markerColor, width: 1.5 },
            label: {
              show: true,
              position: "insideEndTop",
              formatter: "today",
              fontSize: 10,
              color: markerLabelColor,
            },
          };
        }
        return s;
      }),
    };
  }

  function buildCumOption() {
    var dark = isDark();
    var textColor = dark ? "#c8c8c8" : "#333333";
    var splitColor = dark ? "rgba(200,200,200,0.15)" : "rgba(0,0,0,0.1)";
    var goalColor = dark ? "rgba(231,76,60,0.5)" : "rgba(231,76,60,0.45)";

    // Goal line: project where 1000 mi lands on the x axis
    var goalMarkLine = {
      silent: true,
      symbol: ["none", "none"],
      data: [{ yAxis: GOAL_MILES }],
      lineStyle: { type: "dashed", color: goalColor, width: 1.5 },
      label: {
        show: true,
        position: "insideEndTop",
        formatter: GOAL_MILES + " mi goal",
        fontSize: 10,
        color: goalColor,
      },
    };

    return {
      tooltip: {
        trigger: "axis",
        formatter: function (params) {
          return params[0].name + "<br/>" + params[0].value + " mi total";
        },
      },
      grid: { left: 55, right: 20, top: 15, bottom: 65 },
      xAxis: {
        type: "category",
        data: cumMonths,
        axisLabel: { rotate: 45, interval: 0, fontSize: 11, color: textColor },
        axisLine: { lineStyle: { color: textColor } },
        axisTick: { lineStyle: { color: textColor } },
      },
      yAxis: {
        type: "value",
        name: "miles",
        nameTextStyle: { fontSize: 11, color: textColor },
        axisLabel: { color: textColor },
        splitLine: { lineStyle: { type: "dashed", color: splitColor } },
      },
      series: [
        {
          type: "line",
          data: cumValues,
          smooth: true,
          markLine: goalMarkLine,
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(41,128,185,0.35)" },
                { offset: 1, color: "rgba(41,128,185,0.05)" },
              ],
            },
          },
          lineStyle: { color: "#2980b9", width: 2.5 },
          itemStyle: { color: "#2980b9" },
          symbol: "circle",
          symbolSize: 5,
        },
      ],
    };
  }

  // Chart init
  function initCalChart() {
    var calEl = document.getElementById("cycling-calendar");
    if (calEl && window.echarts && calendarMiles) {
      if (calChart) {
        echarts.dispose(calEl);
      }
      var mobile = window.innerWidth < 576;
      calEl.style.height = (mobile ? 180 : 155) + "px";
      calEl.innerHTML = "";
      calChart = echarts.init(calEl);
      calChart.setOption(buildCalOption());
    }
  }

  function initBarChart() {
    var barEl = document.getElementById("cycling-monthly");
    if (barEl && window.echarts) {
      if (barChart) {
        echarts.dispose(barEl);
      }
      barChart = echarts.init(barEl);
      barChart.setOption(buildBarOption());
    }
  }

  function initCumChart() {
    var cumEl = document.getElementById("cycling-cumulative");
    if (cumEl && window.echarts) {
      if (cumChart) {
        echarts.dispose(cumEl);
      }
      cumChart = echarts.init(cumEl);
      cumChart.setOption(buildCumOption());
    }
  }

  // View switcher
  var chartCaptions = {
    calendar: "Each cell is one day; color shows miles ridden.",
    monthly: "Year-over-year monthly mileage comparison.",
    cumulative: "Running total miles over time.",
  };

  function showView(view) {
    var panes = {
      calendar: document.getElementById("cycling-calendar"),
      monthly: document.getElementById("cycling-monthly"),
      cumulative: document.getElementById("cycling-cumulative"),
    };
    Object.keys(panes).forEach(function (k) {
      if (panes[k]) panes[k].style.display = k === view ? "" : "none";
    });
    var cap = document.getElementById("chart-caption");
    if (cap) cap.textContent = chartCaptions[view] || "";

    if (view === "calendar" && !calChart) initCalChart();
    if (view === "monthly" && !barChart) initBarChart();
    if (view === "cumulative" && !cumChart) initCumChart();
    if (view === "calendar" && calChart) calChart.resize();
    if (view === "monthly" && barChart) barChart.resize();
    if (view === "cumulative" && cumChart) cumChart.resize();
  }

  // Bike carousel
  function initBikeCarousel() {
    var track = document.getElementById("bikeTrack");
    var controls = document.getElementById("bikeControls");
    if (!track) return;
    var slides = Array.prototype.slice.call(track.querySelectorAll(".bike-carousel-slide"));
    var n = slides.length;
    if (n <= 1) {
      if (controls) controls.style.display = "none";
      return;
    }

    var cur = 0;
    var dots = [];
    var dotsEl = document.getElementById("bikeDots");
    var prevBtn = document.getElementById("bikePrev");
    var nextBtn = document.getElementById("bikeNext");

    for (var i = 0; i < n; i++) {
      var dot = document.createElement("button");
      dot.className = "bike-carousel-dot";
      dot.setAttribute("aria-label", "Bike " + (i + 1));
      (function (idx) {
        dot.addEventListener("click", function () {
          go(idx);
        });
      })(i);
      dotsEl.appendChild(dot);
      dots.push(dot);
    }

    function slideWidth() {
      return slides[0].offsetWidth + 16;
    }

    function go(idx) {
      cur = Math.max(0, Math.min(idx, n - 1));
      track.style.transform = "translateX(-" + cur * slideWidth() + "px)";
      dots.forEach(function (d, i) {
        d.classList.toggle("active", i === cur);
      });
      prevBtn.disabled = cur === 0;
      nextBtn.disabled = cur === n - 1;
    }

    prevBtn.addEventListener("click", function () {
      go(cur - 1);
    });
    nextBtn.addEventListener("click", function () {
      go(cur + 1);
    });
    go(0);

    window._bikeCarouselGo = go;
    window._bikeCarouselCur = function () {
      return cur;
    };
  }

  // Bike card expand/collapse
  function initBikeExpand() {
    var cards = document.querySelectorAll(".bike-card");
    cards.forEach(function (card) {
      var toggle = card.querySelector(".bike-card-toggle");
      var details = card.querySelector(".bike-card-details");
      if (!toggle || !details) return;
      toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        var expanded = details.classList.toggle("expanded");
        toggle.setAttribute("aria-expanded", expanded);
        toggle.querySelector("i").className = expanded ? "fa-solid fa-chevron-up" : "fa-solid fa-chevron-down";
      });
    });
  }

  // Route map
  function initRouteMap() {
    var mapEl = document.getElementById("cycling-map");
    if (!mapEl || !window.L || !locationsRaw) return;

    var map = L.map(mapEl, { scrollWheelZoom: false, zoomControl: true });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    var typeColors = { commute: "#2980b9", road: "#27ae60", gravel: "#e67e22", travel: "#8e44ad" };
    var bounds = [];

    locationsRaw.forEach(function (loc) {
      var color = typeColors[loc.type] || "#2980b9";
      var marker = L.circleMarker([loc.coords[0], loc.coords[1]], {
        radius: loc.type === "commute" ? 8 : 6,
        fillColor: color,
        color: "#fff",
        weight: 2,
        fillOpacity: 0.85,
      }).addTo(map);
      marker.bindTooltip(loc.name, { direction: "top", offset: [0, -8] });
      bounds.push([loc.coords[0], loc.coords[1]]);
    });

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 5 });
    }
  }

  // Ride log table
  function initRideLog() {
    var tbody = document.getElementById("ride-log-body");
    if (!tbody || !ridesRaw || ridesRaw.length === 0) return;

    ridesRaw.forEach(function (ride) {
      var tr = document.createElement("tr");
      var dateObj = new Date(ride.date + "T00:00:00");
      var dateStr = dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric" });
      var dist = Math.round(ride.distance_km * KM_TO_MI * 10) / 10;
      var time = ride.moving_time_min ? ride.moving_time_min + " min" : "";

      tr.innerHTML = "<td>" + dateStr + "</td>" + "<td>" + ride.name + "</td>" + "<td>" + dist + " mi</td>" + "<td>" + time + "</td>";
      tbody.appendChild(tr);
    });
  }

  // View tabs
  document.querySelectorAll(".chart-view-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".chart-view-btn").forEach(function (b) {
        b.classList.remove("active");
      });
      btn.classList.add("active");
      showView(btn.getAttribute("data-view"));
    });
  });

  // Resize and theme
  function isVisible(el) {
    return el && el.offsetParent !== null;
  }

  window.addEventListener("resize", function () {
    var calEl = document.getElementById("cycling-calendar");
    if (calChart && isVisible(calEl)) {
      var mobile = window.innerWidth < 576;
      calEl.style.height = (mobile ? 180 : 155) + "px";
      calChart.resize();
      calChart.setOption(buildCalOption());
    }
    if (barChart && isVisible(document.getElementById("cycling-monthly"))) {
      barChart.resize();
    }
    if (cumChart && isVisible(document.getElementById("cycling-cumulative"))) {
      cumChart.resize();
    }
    if (window._bikeCarouselGo) {
      window._bikeCarouselGo(window._bikeCarouselCur());
    }
  });

  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === "data-theme") {
        if (calChart) initCalChart();
        if (barChart) initBarChart();
        if (cumChart) initCumChart();
      }
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  // Boot
  function boot() {
    initCalChart();
    initBikeCarousel();
    initBikeExpand();
    initRideLog();
    showPaceStat();

    // Lazy-load the Leaflet map when it scrolls into view
    var mapEl = document.getElementById("cycling-map");
    if (mapEl && "IntersectionObserver" in window) {
      var observer = new IntersectionObserver(
        function (entries) {
          if (entries[0].isIntersecting) {
            observer.disconnect();
            initRouteMap();
          }
        },
        { rootMargin: "200px" }
      );
      observer.observe(mapEl);
    } else {
      initRouteMap();
    }
  }
  if (document.readyState === "complete") {
    boot();
  } else {
    window.addEventListener("load", boot);
  }
})();
