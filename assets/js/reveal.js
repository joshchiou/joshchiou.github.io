/* Scroll entrance animations for .animate-in blocks.
 *
 * Deliberately standalone and jQuery-free. This logic used to live in
 * common.js, which is wrapped in $(document).ready() — so when jQuery failed to
 * load from the CDN, nothing in that file ran, .visible was never applied, and
 * every .animate-in section stayed at opacity 0. On the about page that is the
 * stats bar, selected work, news and selected publications: the entire body of
 * the page rendered blank rather than merely unanimated.
 *
 * Content must never depend on a third-party library to become visible.
 */
(function () {
  function revealAll(els) {
    els.forEach(function (el) {
      el.classList.add("visible");
    });
  }

  function init() {
    var els = Array.prototype.slice.call(document.querySelectorAll(".animate-in"));
    if (els.length === 0) return;

    /* No observer support, or the visitor prefers reduced motion: show
       everything at once rather than waiting for a scroll event that will
       never be answered. (CSS also forces opacity 1 under reduced motion;
       applying the class keeps the DOM state consistent either way.) */
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!("IntersectionObserver" in window) || reduceMotion) {
      revealAll(els);
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 }
    );
    els.forEach(function (el) {
      observer.observe(el);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
