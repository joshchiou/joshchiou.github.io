import { highlightSearchTerm } from "./highlight-search-term.js";

// Publications page: text search (kept in the URL hash, as in upstream al-folio)
// plus two dropdowns, "show" (selected papers, or first or co-first authorship)
// and "theme", kept in the query string (e.g. ?show=first&theme=diabetes).
// Each entry carries its filter data on a hidden .pub-filter-data span from
// _layouts/bib.liquid.
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("bibsearch");
  if (!searchInput) return;
  const clearBtn = document.getElementById("bibsearch-clear");
  const countEl = document.getElementById("bibsearch-count");
  const resetBtn = document.getElementById("pub-filter-reset");
  const emptyEl = document.getElementById("pub-filter-empty");
  const selects = {
    show: document.getElementById("pub-filter-show"),
    theme: document.getElementById("pub-filter-theme"),
  };

  const items = Array.from(document.querySelectorAll(".publications ol.bibliography > li"));
  const dataOf = (li) => {
    const d = li.querySelector(".pub-filter-data");
    return d ? d.dataset : {};
  };

  // Start from the query string, ignoring values the dropdowns don't offer.
  const state = { show: "", theme: "" };
  const params = new URLSearchParams(window.location.search);
  Object.entries(selects).forEach(([key, el]) => {
    const value = params.get(key);
    if (value && Array.from(el.options, (o) => o.value).includes(value)) state[key] = value;
  });

  const matchesFilters = (li) => {
    const d = dataOf(li);
    if (state.show === "selected" && d.selected !== "true") return false;
    if (state.show === "first" && d.role !== "first") return false;
    if (state.theme) {
      const themes = (d.themes || "").split(/\s+/).filter(Boolean);
      if (state.theme === "other" ? themes.length > 0 : !themes.includes(state.theme)) return false;
    }
    return true;
  };

  const syncControls = () => {
    Object.entries(selects).forEach(([key, el]) => {
      el.value = state[key];
      el.classList.toggle("active", Boolean(state[key]));
    });
  };

  const syncUrl = () => {
    const q = new URLSearchParams();
    Object.entries(state).forEach(([k, v]) => v && q.set(k, v));
    const qs = q.toString();
    const url = window.location.pathname + (qs ? "?" + qs : "") + window.location.hash;
    window.history.replaceState(null, "", url);
  };

  const apply = () => {
    const searchTerm = searchInput.value.toLowerCase().trim();
    document.querySelectorAll(".publications .unloaded").forEach((el) => el.classList.remove("unloaded"));

    // Text matches (highlightSearchTerm also paints the matches).
    let textMisses = new Set();
    const nonMatching = highlightSearchTerm({ search: searchTerm, selector: ".publications ol.bibliography > li" });
    if (nonMatching) {
      textMisses = new Set(nonMatching);
    } else if (searchTerm && !CSS.highlights) {
      items.forEach((li) => li.innerText.toLowerCase().includes(searchTerm) || textMisses.add(li));
    }

    let visible = 0;
    items.forEach((li) => {
      if (textMisses.has(li) || !matchesFilters(li)) li.classList.add("unloaded");
      else visible += 1;
    });

    // Hide a year heading and its list when nothing in it is left.
    document.querySelectorAll(".publications ol.bibliography").forEach((ol) => {
      if (!ol.querySelector(":scope > li:not(.unloaded)")) {
        ol.classList.add("unloaded");
        const heading = ol.previousElementSibling;
        if (heading && /^H[2-4]$/.test(heading.tagName)) heading.classList.add("unloaded");
      }
    });

    const filtering = Boolean(searchTerm || state.show || state.theme);
    if (countEl) {
      countEl.textContent = `Showing ${visible} of ${items.length}`;
      countEl.hidden = !filtering;
    }
    if (resetBtn) resetBtn.hidden = !filtering;
    if (emptyEl) emptyEl.hidden = !(filtering && visible === 0);
    if (clearBtn) clearBtn.hidden = !searchTerm;
  };

  const setFilter = (key, value) => {
    state[key] = value;
    syncControls();
    syncUrl();
    apply();
  };

  Object.entries(selects).forEach(([key, el]) => el.addEventListener("change", () => setFilter(key, el.value)));

  // Search waits for 300 ms without typing.
  let timeoutId;
  searchInput.addEventListener("input", function () {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(apply, 300);
  });

  const clearSearch = () => {
    searchInput.value = "";
    if (window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  };

  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      clearSearch();
      apply();
      searchInput.focus();
    });
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      clearSearch();
      state.show = state.theme = "";
      syncControls();
      syncUrl();
      apply();
    });
  }

  searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      clearSearch();
      apply();
      searchInput.blur();
    }
  });

  const readHash = () => {
    searchInput.value = decodeURIComponent(window.location.hash.substring(1));
    apply();
  };
  window.addEventListener("hashchange", readHash);

  syncControls();
  readHash();
});
