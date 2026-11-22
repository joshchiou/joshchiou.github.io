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
  const isCounted = (li) => dataOf(li).counted !== "false";
  const countedTotal = items.filter(isCounted).length;

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

    // The count matches the page header: entries with counted = {false} in papers.bib (the
    // thesis) are listed but not counted (D-019).
    let visible = 0;
    let uncountedVisible = 0;
    items.forEach((li) => {
      if (textMisses.has(li) || !matchesFilters(li)) li.classList.add("unloaded");
      else if (isCounted(li)) visible += 1;
      else uncountedVisible += 1;
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
      const extra = uncountedVisible ? `, plus the PhD thesis` : "";
      countEl.textContent = `Showing ${visible} of ${countedTotal} publications${extra}`;
      countEl.hidden = !filtering;
    }
    if (resetBtn) resetBtn.hidden = !filtering;
    if (emptyEl) emptyEl.hidden = !(filtering && visible + uncountedVisible === 0);
    if (clearBtn) clearBtn.hidden = !searchTerm;
  };

  const setFilter = (key, value) => {
    state[key] = value;
    syncControls();
    syncUrl();
    apply();
  };

  Object.entries(selects).forEach(([key, el]) => el.addEventListener("change", () => setFilter(key, el.value)));

  // Filter on every keystroke, at most once per frame (40 entries is cheap). The old 300 ms
  // debounce made the first keystroke look ignored.
  let frame = 0;
  searchInput.addEventListener("input", function () {
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = 0;
      apply();
    });
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

  // A #term in the URL fills the box. Without one, keep whatever the visitor already typed
  // before this module loaded instead of clearing it.
  const readHash = () => {
    const term = decodeURIComponent(window.location.hash.substring(1));
    if (term || window.location.hash) searchInput.value = term;
    apply();
  };
  window.addEventListener("hashchange", readHash);

  syncControls();
  readHash();
});
