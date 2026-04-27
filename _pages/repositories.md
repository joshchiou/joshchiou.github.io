---
layout: page
permalink: /repositories/
title: code
nav: true
nav_order: 4
description: >
  A slice of my public coding activity. Most production work lives in enterprise GitHub organizations
  (Pfizer, Lilly) and isn't reflected here.
---

<div class="mb-4">
  <a href="https://github.com/joshchiou" target="_blank" rel="noopener noreferrer">
    <img
      class="repo-img-light"
      src="https://github-readme-stats.vercel.app/api?username=joshchiou&show_icons=true&hide_border=true&count_private=true&theme={{ site.repo_theme_light }}"
      alt="GitHub stats"
    >
    <img
      class="repo-img-dark"
      src="https://github-readme-stats.vercel.app/api?username=joshchiou&show_icons=true&hide_border=true&count_private=true&theme={{ site.repo_theme_dark }}"
      alt="GitHub stats"
    >
  </a>
</div>

## Maintained

<div class="d-flex flex-wrap gap-3 mb-4" id="repo-cards">
  {% for repo in site.data.repositories.github_repos %}
    {% assign repo_parts = repo | split: '/' %}
    <a class="repo-card" href="https://github.com/{{ repo }}" target="_blank" rel="noopener noreferrer"
       data-repo="{{ repo }}">
      <div class="repo-card-header">
        <i class="fa-regular fa-book"></i>
        <span class="repo-card-name">
          {% assign owner = repo_parts[0] %}
          {% assign rname = repo_parts[1] %}
          {% if site.data.repositories.github_users contains owner %}{{ rname }}{% else %}{{ repo }}{% endif %}
        </span>
      </div>
      <div class="repo-card-desc" id="desc-{{ repo | replace: '/', '-' }}">
        <span class="text-muted" style="font-size:0.78rem">Loading&hellip;</span>
      </div>
      <div class="repo-card-meta" id="meta-{{ repo | replace: '/', '-' }}"></div>
    </a>
  {% endfor %}
</div>

<script>
(function () {
  var LANG_COLORS = {
    Python: '#3572A5', R: '#198CE7', JavaScript: '#f1e05a',
    TypeScript: '#2b7489', Shell: '#89e051', Ruby: '#701516',
    Java: '#b07219', CSS: '#563d7c', HTML: '#e34c26'
  };

  var repos = {{ site.data.repositories.github_repos | jsonify }};

  repos.forEach(function (repo) {
    var slug = repo.replace('/', '-');
    fetch('https://api.github.com/repos/' + repo)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var descEl = document.getElementById('desc-' + slug);
        var metaEl = document.getElementById('meta-' + slug);
        if (!descEl || !metaEl) return;

        descEl.textContent = d.description || '';

        var lang = d.language || '';
        var color = LANG_COLORS[lang] || '#8a8a8a';
        var stars = d.stargazers_count || 0;
        var forks = d.forks_count || 0;

        var html = '';
        if (lang) {
          html += '<span class="repo-card-lang">'
               + '<span class="lang-dot" style="background:' + color + '"></span>'
               + lang + '</span>';
        }
        if (stars > 0) {
          html += '<span class="repo-card-stat"><i class="fa-regular fa-star"></i> ' + stars + '</span>';
        }
        if (forks > 0) {
          html += '<span class="repo-card-stat"><i class="fa-solid fa-code-fork"></i> ' + forks + '</span>';
        }
        metaEl.innerHTML = html;
      })
      .catch(function () {
        var descEl = document.getElementById('desc-' + slug);
        if (descEl) descEl.textContent = '';
      });
  });
})();
</script>

---

## Open-source contributions

Selected merged pull requests to community scientific software.

<ul class="list-unstyled">
  {% for c in site.data.contributions %}
  <li class="mb-4 contribution-item">
    <div class="mb-1">
      <strong>{{ c.pr_title }}</strong>
      &nbsp;&middot;&nbsp;
      <a href="{{ c.url }}" target="_blank" rel="noopener noreferrer">{{ c.repo }}</a>
      &nbsp;&middot;&nbsp;
      <span class="text-muted small">{{ c.date }}</span>
    </div>
    <div class="mb-1">
      {% if c.type %}
        {% if c.type == "bug fix" %}{% assign tc = "badge-bug" %}
        {% elsif c.type == "performance" %}{% assign tc = "badge-perf" %}
        {% elsif c.type == "feature" %}{% assign tc = "badge-feature" %}
        {% elsif c.type == "packaging" %}{% assign tc = "badge-pkg" %}
        {% elsif c.type == "compatibility" %}{% assign tc = "badge-compat" %}
        {% else %}{% assign tc = "badge-compat" %}{% endif %}
        <span class="badge-type {{ tc }}">{{ c.type }}</span>
      {% endif %}
      {% if c.language %}<span class="badge-type badge-lang">{{ c.language }}</span>{% endif %}
    </div>
    <div class="mb-1">
      <small class="text-muted">{{ c.blurb }}</small>
    </div>
    <a class="pr-link" href="{{ c.pr_url }}" target="_blank" rel="noopener noreferrer">
      <i class="fa-solid fa-code-pull-request"></i> View pull request
    </a>
  </li>
  {% endfor %}
</ul>

<a href="https://github.com/search?q=author%3Ajoshchiou+is%3Apr+is%3Amerged&type=pullrequests" target="_blank" rel="noopener noreferrer">See all merged pull requests &rarr;</a>
