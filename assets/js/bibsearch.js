import { highlightSearchTerm } from "./highlight-search-term.js";

document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("bibsearch");
  const clearBtn = document.getElementById("bibsearch-clear");
  const countEl = document.getElementById("bibsearch-count");

  const updateCount = (searchTerm) => {
    if (!countEl) return;
    if (!searchTerm) {
      countEl.hidden = true;
      return;
    }
    const visible = document.querySelectorAll(
      ".bibliography > li:not(.unloaded)",
    ).length;
    const total = document.querySelectorAll(".bibliography > li").length;
    countEl.textContent = `Showing ${visible} of ${total}`;
    countEl.hidden = false;
  };

  const updateClearBtn = (searchTerm) => {
    if (!clearBtn) return;
    clearBtn.hidden = !searchTerm;
  };

  // actual bibsearch logic
  const filterItems = (searchTerm) => {
    document
      .querySelectorAll(".bibliography, .unloaded")
      .forEach((element) => element.classList.remove("unloaded"));

    // highlight-search-term
    if (CSS.highlights) {
      const nonMatchingElements = highlightSearchTerm({
        search: searchTerm,
        selector: ".bibliography > li",
      });
      if (nonMatchingElements == null) {
        updateCount("");
        updateClearBtn(searchTerm);
        return;
      }
      nonMatchingElements.forEach((element) => {
        element.classList.add("unloaded");
      });
    } else {
      // Simply add unloaded class to all non-matching items if Browser does not support CSS highlights
      document.querySelectorAll(".bibliography > li").forEach((element) => {
        const text = element.innerText.toLowerCase();
        if (text.indexOf(searchTerm) == -1) {
          element.classList.add("unloaded");
        }
      });
    }

    document.querySelectorAll("h2.bibliography").forEach(function (element) {
      let iterator = element.nextElementSibling; // get next sibling element after h2, which can be h3 or ol
      let hideFirstGroupingElement = true;
      // iterate until next group element (h2), which is already selected by the querySelectorAll(-).forEach(-)
      while (iterator && iterator.tagName !== "H2") {
        if (iterator.tagName === "OL") {
          const ol = iterator;
          const unloadedSiblings = ol.querySelectorAll(":scope > li.unloaded");
          const totalSiblings = ol.querySelectorAll(":scope > li");

          if (unloadedSiblings.length === totalSiblings.length) {
            ol.previousElementSibling.classList.add("unloaded"); // Add the '.unloaded' class to the previous grouping element (e.g. year)
            ol.classList.add("unloaded"); // Add the '.unloaded' class to the OL itself
          } else {
            hideFirstGroupingElement = false; // there is at least some visible entry, don't hide the first grouping element
          }
        }
        iterator = iterator.nextElementSibling;
      }
      // Add unloaded class to first grouping element (e.g. year) if no item left in this group
      if (hideFirstGroupingElement) {
        element.classList.add("unloaded");
      }
    });

    // Hide selected heading when filtering
    const selectedHeading = document.querySelector(
      "h2.bibliography.selected-heading",
    );
    if (selectedHeading && searchTerm) {
      selectedHeading.classList.add("unloaded");
    }

    // Hide "All Publications" section heading when filtering
    const allHeading = document.querySelector("h2.pub-section-heading");
    if (allHeading && searchTerm) {
      allHeading.classList.add("unloaded");
    }

    updateCount(searchTerm);
    updateClearBtn(searchTerm);
  };

  const updateInputField = () => {
    const hashValue = decodeURIComponent(window.location.hash.substring(1)); // Remove the '#' character
    searchInput.value = hashValue;
    filterItems(hashValue);
  };

  // Sensitive search. Only start searching if there's been no input for 300 ms
  let timeoutId;
  searchInput.addEventListener("input", function () {
    clearTimeout(timeoutId); // Clear the previous timeout
    const searchTerm = this.value.toLowerCase();
    timeoutId = setTimeout(() => filterItems(searchTerm), 300);
  });

  // Clear button
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      searchInput.value = "";
      filterItems("");
      searchInput.focus();
    });
  }

  // Keyboard shortcut: Escape to clear
  searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      searchInput.value = "";
      filterItems("");
      searchInput.blur();
    }
  });

  window.addEventListener("hashchange", updateInputField); // Update the filter when the hash changes

  updateInputField(); // Update filter when page loads
});
