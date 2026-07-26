(function () {
  var data = window._travelData;
  if (!data) return;

  var VISITED_COUNTRIES = data.countries;
  var CITY_DATA = data.cities;
  var RAW_COUNTRIES = data.rawCountries;
  var GEOJSON_URL = data.geojsonUrl;
  var PHOTO_BASE = data.photoBase;

  /* ── Lookups ─────────────────────────────────────────────────────────── */
  var COUNTRY_CONTINENT = {};
  RAW_COUNTRIES.forEach(function (c) {
    COUNTRY_CONTINENT[c.name] = c.continent;
  });
  var visitedSet = new Set(VISITED_COUNTRIES);

  /* ── Color palettes ──────────────────────────────────────────────────── */
  var PAL = {
    light: { "North America": "#4575b4", Europe: "#e67e22", Asia: "#27ae60", _unvisited: "#e0e0e0", _border: "#ffffff" },
    dark: { "North America": "#58a6ff", Europe: "#f5a623", Asia: "#4ade80", _unvisited: "#333333", _border: "#2a2a2a" },
  };
  var BAR_COLOR = { "North America": "#3d6aab", Europe: "#c96910", Asia: "#1f823e" };
  var CITY_DOT = {
    light: { fill: "#c0392b", stroke: "#ffffff" },
    dark: { fill: "#f97583", stroke: "#1c1c1d" },
  };
  var BASE_RADIUS = 5;

  function isDark() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }
  function pal() {
    return isDark() ? PAL.dark : PAL.light;
  }
  function cityDot() {
    return isDark() ? CITY_DOT.dark : CITY_DOT.light;
  }

  /* ── Metro clustering ────────────────────────────────────────────────── */
  var CLUSTER_KM = 80;

  function haversine(a, b) {
    var R = 6371;
    var dLat = ((b.lat - a.lat) * Math.PI) / 180;
    var dLon = ((b.lon - a.lon) * Math.PI) / 180;
    var la1 = (a.lat * Math.PI) / 180,
      la2 = (b.lat * Math.PI) / 180;
    var x = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(la1) * Math.cos(la2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1 - x));
  }

  function clusterCities(cities) {
    var clusters = [];
    cities.forEach(function (city) {
      var nearest = null,
        nearestDist = Infinity;
      clusters.forEach(function (cl) {
        var d = haversine(cl.centroid, city);
        if (d < nearestDist) {
          nearestDist = d;
          nearest = cl;
        }
      });
      if (nearest && nearestDist < CLUSTER_KM) {
        nearest.cities.push(city);
        nearest.centroid.lat =
          nearest.cities.reduce(function (s, c) {
            return s + c.lat;
          }, 0) / nearest.cities.length;
        nearest.centroid.lon =
          nearest.cities.reduce(function (s, c) {
            return s + c.lon;
          }, 0) / nearest.cities.length;
      } else {
        clusters.push({ cities: [city], centroid: { lat: city.lat, lon: city.lon } });
      }
    });
    return clusters;
  }

  /* ── D3 map state ────────────────────────────────────────────────────── */
  var svgSel, projection, geoPath, countriesG, citiesG, zoomG, zoomBehavior;
  var allClusters = {};

  /* ── Map init ────────────────────────────────────────────────────────── */
  function initMap() {
    var el = document.getElementById("travel-map-svg");
    if (!el || typeof d3 === "undefined") return;

    var W = 960,
      H = 500;
    svgSel = d3.select(el);

    zoomBehavior = d3
      .zoom()
      .scaleExtent([1, 8])
      .filter(function (event) {
        return event.ctrlKey || event.type !== "wheel";
      })
      .on("zoom", function (event) {
        zoomG.attr("transform", event.transform);
        citiesG.selectAll("circle.city-dot").attr("r", Math.max(1.5, BASE_RADIUS / event.transform.k));
      });
    svgSel.call(zoomBehavior).on("dblclick.zoom", function () {
      svgSel.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity);
    });

    var resetBtn = document.getElementById("travel-map-reset");
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        svgSel.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity);
      });
    }

    projection = d3
      .geoNaturalEarth1()
      .scale(160)
      .translate([W / 2, H / 2]);
    geoPath = d3.geoPath().projection(projection);

    zoomG = svgSel.append("g").attr("class", "zoom-group");
    countriesG = zoomG.append("g").attr("class", "countries-layer");
    citiesG = zoomG.append("g").attr("class", "cities-layer");

    visitedSet.forEach(function (name) {
      var c = CITY_DATA.filter(function (x) {
        return x.country === name;
      });
      allClusters[name] = clusterCities(c);
    });

    fetch(GEOJSON_URL)
      .then(function (r) {
        return r.json();
      })
      .then(function (geojson) {
        renderCountries(geojson);
        renderCities();
      })
      .catch(function (e) {
        console.warn("Travel GeoJSON failed:", e);
      });
  }

  /* ── Country rendering ───────────────────────────────────────────────── */
  function countryFill(name) {
    var p = pal();
    return visitedSet.has(name) ? p[COUNTRY_CONTINENT[name]] || p["North America"] : p._unvisited;
  }

  function renderCountries(geojson) {
    var tooltip = document.getElementById("travel-map-tooltip");

    countriesG
      .selectAll("path")
      .data(geojson.features)
      .enter()
      .append("path")
      .attr("d", geoPath)
      .attr("class", function (d) {
        return visitedSet.has(d.properties.name) ? "country-visited" : "country-unvisited";
      })
      .attr("fill", function (d) {
        return countryFill(d.properties.name);
      })
      .attr("stroke", pal()._border)
      .attr("stroke-width", 0.5)
      .on("mouseenter", function (event, d) {
        var name = d.properties.name;
        if (!visitedSet.has(name)) return;
        var here = CITY_DATA.filter(function (c) {
          return c.country === name;
        });
        var html = "<strong>" + name + "</strong>";
        if (here.length) {
          var summary;
          if (
            name === "United States of America" &&
            here.some(function (c) {
              return c.state;
            })
          ) {
            var byState = {};
            here.forEach(function (c) {
              var s = c.state || "—";
              byState[s] = (byState[s] || 0) + 1;
            });
            summary = Object.keys(byState)
              .sort(function (a, b) {
                return byState[b] - byState[a];
              })
              .map(function (s) {
                return byState[s] > 1 ? s + " (" + byState[s] + ")" : s;
              })
              .join(" · ");
          } else {
            var clusters = allClusters[name] || [];
            summary = clusters
              .map(function (cl) {
                return cl.cities.length === 1 ? cl.cities[0].name : cl.cities[0].name + " +" + (cl.cities.length - 1);
              })
              .join(" · ");
          }
          html += '<br><span class="tt-cities">' + summary + "</span>";
        }
        tooltip.innerHTML = html;
        tooltip.classList.add("visible");
        tooltip.removeAttribute("aria-hidden");
        enterHoverState(name);
      })
      .on("mousemove", function (event) {
        var box = document.getElementById("travel-map-svg").getBoundingClientRect();
        tooltip.style.left = event.clientX - box.left + 14 + "px";
        tooltip.style.top = event.clientY - box.top + 14 + "px";
      })
      .on("mouseleave", function () {
        tooltip.classList.remove("visible");
        tooltip.setAttribute("aria-hidden", "true");
        exitHoverState();
      })
      .on("click", function (event, d) {
        var name = d.properties.name;
        if (!visitedSet.has(name)) return;
        var row = document.querySelector('.travel-bar-row[data-country="' + CSS.escape(name) + '"]');
        if (row) {
          var body = row.querySelector(".travel-bar-body");
          if (body && body.hidden) {
            row.querySelector(".travel-bar-header").click();
          }
          row.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      });

    updateMapColors();
  }

  function updateMapColors() {
    if (!countriesG) return;
    var p = pal();
    countriesG
      .selectAll("path")
      .attr("fill", function (d) {
        return countryFill(d.properties.name);
      })
      .attr("stroke", p._border);
  }

  /* ── City dots ───────────────────────────────────────────────────────── */
  function renderCities() {
    var dot = cityDot();
    citiesG
      .selectAll("circle.city-dot")
      .data(
        CITY_DATA.filter(function (c) {
          return c.lat && c.lon;
        })
      )
      .enter()
      .append("circle")
      .attr("class", "city-dot")
      .attr("cx", function (d) {
        var p = projection([d.lon, d.lat]);
        return p ? p[0] : -9999;
      })
      .attr("cy", function (d) {
        var p = projection([d.lon, d.lat]);
        return p ? p[1] : -9999;
      })
      .attr("r", BASE_RADIUS)
      .attr("fill", dot.fill)
      .attr("stroke", dot.stroke)
      .attr("stroke-width", 1.5)
      .append("title")
      .text(function (d) {
        return d.name + ", " + d.country;
      });
  }

  function updateCityColors() {
    if (!citiesG) return;
    var dot = cityDot();
    citiesG.selectAll("circle.city-dot").attr("fill", dot.fill).attr("stroke", dot.stroke);
  }

  /* ── Hover cluster state ─────────────────────────────────────────────── */
  function enterHoverState(name) {
    citiesG.selectAll("circle.city-dot").attr("opacity", function (d) {
      return d.country === name ? 0 : 0.1;
    });

    var clusters = allClusters[name] || [];
    var dot = cityDot();

    var cgs = citiesG
      .selectAll("g.metro-cluster")
      .data(clusters)
      .enter()
      .append("g")
      .attr("class", "metro-cluster")
      .attr("transform", function (cl) {
        var p = projection([cl.centroid.lon, cl.centroid.lat]);
        return p ? "translate(" + p[0] + "," + p[1] + ")" : "translate(-9999,-9999)";
      });

    cgs
      .append("circle")
      .attr("r", function (cl) {
        return Math.max(7, 5 + cl.cities.length * 2.5);
      })
      .attr("fill", dot.fill)
      .attr("stroke", isDark() ? "#1c1c1d" : "#ffffff")
      .attr("stroke-width", 2)
      .attr("opacity", 0)
      .transition()
      .duration(180)
      .attr("opacity", 0.92);

    cgs
      .filter(function (cl) {
        return cl.cities.length > 1;
      })
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("font-size", "11px")
      .attr("font-weight", "700")
      .attr("fill", "#ffffff")
      .attr("pointer-events", "none")
      .text(function (cl) {
        return cl.cities.length;
      });

    cgs.append("title").text(function (cl) {
      return cl.cities
        .map(function (c) {
          return c.name;
        })
        .join(" · ");
    });
  }

  function exitHoverState() {
    citiesG.selectAll("circle.city-dot").attr("opacity", 1);
    citiesG.selectAll("g.metro-cluster").remove();
  }

  /* ── Bar chart ───────────────────────────────────────────────────────── */
  function buildBarChart() {
    var wrap = document.getElementById("travel-bars-wrap");
    if (!wrap) return;

    var barData = RAW_COUNTRIES.map(function (c) {
      return {
        name: c.name,
        flag: c.flag || "",
        continent: c.continent,
        cities: CITY_DATA.filter(function (x) {
          return x.country === c.name;
        }),
      };
    }).sort(function (a, b) {
      return b.cities.length - a.cities.length;
    });

    var maxCount = barData.length ? barData[0].cities.length : 1;

    barData.forEach(function (country) {
      var pct = Math.max(4, Math.round((country.cities.length / maxCount) * 100));
      var barColor = BAR_COLOR[country.continent] || "#555";

      var row = document.createElement("div");
      row.className = "travel-bar-row";
      row.setAttribute("data-country", country.name);

      var header = document.createElement("div");
      header.className = "travel-bar-header";
      header.innerHTML =
        '<span class="travel-bar-flag">' +
        country.flag +
        "</span>" +
        '<span class="travel-bar-name">' +
        country.name +
        "</span>" +
        '<div class="travel-bar-track">' +
        '<div class="travel-bar-fill" style="width:' +
        pct +
        "%;background:" +
        barColor +
        '">' +
        '<span class="travel-bar-count">' +
        country.cities.length +
        "</span>" +
        "</div>" +
        "</div>" +
        '<span class="travel-bar-chevron" aria-hidden="true">▾</span>';

      var body = document.createElement("div");
      body.className = "travel-bar-body";
      body.hidden = true;

      var pills = document.createElement("div");
      pills.className = "travel-city-pills";

      if (country.cities.length) {
        country.cities.forEach(function (city) {
          var pill = document.createElement("span");
          pill.className = "travel-city-pill";
          pill.textContent = city.name;
          pills.appendChild(pill);
        });
      } else {
        var pill = document.createElement("span");
        pill.className = "travel-city-pill travel-city-pill--empty";
        pill.textContent = "No cities logged";
        pills.appendChild(pill);
      }

      body.appendChild(pills);

      header.addEventListener("click", function () {
        var open = !body.hidden;
        body.hidden = open;
        header.querySelector(".travel-bar-chevron").textContent = open ? "▾" : "▴";
        row.classList.toggle("open", !open);
      });

      row.appendChild(header);
      row.appendChild(body);
      wrap.appendChild(row);
    });
  }

  /* ── Photo gallery ───────────────────────────────────────────────────── */
  function initGallery() {
    var wrapper = document.getElementById("travelSwiperWrapper");
    var swiperEl = document.getElementById("travelSwiper");
    var placeholder = document.getElementById("travelGalleryPlaceholder");
    if (!wrapper) return;

    var TOTAL = 6;
    var loaded = [],
      probed = 0;

    for (var i = 1; i <= TOTAL; i++) {
      (function (idx) {
        var img = new Image();
        img.onload = function () {
          loaded.push({ idx: idx, src: img.src });
          finish();
        };
        img.onerror = finish;
        img.src = PHOTO_BASE + idx + ".webp";
      })(i);
    }

    function finish() {
      probed++;
      if (probed < TOTAL) return;
      if (loaded.length === 0) return;
      loaded.sort(function (a, b) {
        return a.idx - b.idx;
      });
      loaded.forEach(function (item) {
        var slide = document.createElement("div");
        slide.className = "swiper-slide";
        var img = document.createElement("img");
        img.src = item.src;
        img.className = "img-fluid rounded z-depth-1";
        img.alt = "Travel photo";
        img.loading = "lazy";
        slide.appendChild(img);
        wrapper.appendChild(slide);
      });
      placeholder.style.display = "none";
      swiperEl.style.display = "";
      if (typeof Swiper !== "undefined") {
        new Swiper("#travelSwiper", {
          slidesPerView: 1,
          spaceBetween: 16,
          loop: loaded.length > 3,
          pagination: { el: ".swiper-pagination", clickable: true },
          navigation: { nextEl: ".swiper-button-next", prevEl: ".swiper-button-prev" },
          breakpoints: { 576: { slidesPerView: 2 }, 992: { slidesPerView: 3 } },
        });
      }
    }
  }

  /* ── Theme observer ──────────────────────────────────────────────────── */
  new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === "data-theme") {
        updateMapColors();
        updateCityColors();
      }
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  /* ── Boot ────────────────────────────────────────────────────────────── */
  function boot() {
    buildBarChart();
    initGallery();

    // Lazy-load the D3 map when it scrolls into view
    var mapWrap = document.getElementById("travel-map-wrap");
    if (mapWrap && "IntersectionObserver" in window) {
      var observer = new IntersectionObserver(
        function (entries) {
          if (entries[0].isIntersecting) {
            observer.disconnect();
            initMap();
          }
        },
        { rootMargin: "200px" }
      );
      observer.observe(mapWrap);
    } else {
      initMap();
    }
  }

  if (document.readyState === "complete") {
    boot();
  } else {
    window.addEventListener("load", boot);
  }
})();
