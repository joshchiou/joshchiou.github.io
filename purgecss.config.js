module.exports = {
  content: ["_site/**/*.html", "_site/**/*.js"],
  css: ["_site/assets/css/*.css"],
  output: "_site/assets/css/",
  skippedContentGlobs: ["_site/assets/**/*.html"],
  safelist: {
    standard: [
      /^badge-type/, /^badge-bug/, /^badge-perf/, /^badge-feature/,
      /^badge-pkg/, /^badge-compat/, /^badge-lang/,
      /^contribution-grid/, /^contrib-card/, /^contribution-item/,
      /^project-img-wrap/,
      /^repo-card/, /^repo-card-grid/, /^lang-dot/, /^pr-link/,
      /^github-profile/, /^github-avatar/, /^gh-stat/, /^gh-avatar/,
    ],
  },
};
