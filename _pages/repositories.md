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

<div class="github-profile-card mb-5" id="github-profile-card">
  <div class="github-profile-inner">
    <div class="github-profile-left">
      <a href="https://github.com/joshchiou" target="_blank" rel="noopener noreferrer"
         class="github-profile-identity">
        <img id="gh-avatar" src="" alt="GitHub avatar" class="github-avatar">
        <div>
          <div class="github-profile-name" id="gh-name">Josh Chiou</div>
          <div class="github-profile-login">@joshchiou</div>
        </div>
      </a>
    </div>
    <div class="github-profile-stats" id="gh-stats">
      <div class="gh-stat"><span class="gh-stat-val" id="gh-repos">—</span><span class="gh-stat-label">repos</span></div>
      <div class="gh-stat"><span class="gh-stat-val" id="gh-stars">—</span><span class="gh-stat-label">stars</span></div>
      <div class="gh-stat"><span class="gh-stat-val" id="gh-followers">—</span><span class="gh-stat-label">followers</span></div>
    </div>
  </div>
</div>

## Featured repositories

Repositories I've built or contributed to significantly.


<div class="repo-card-grid mb-4">
  {% for item in site.data.repositories.github_repos %}
    {% assign repo = item.repo %}
    {% assign repo_parts = repo | split: '/' %}
    {% assign owner = repo_parts[0] %}
    {% assign rname = repo_parts[1] %}
    <a class="repo-card" href="https://github.com/{{ repo }}" target="_blank" rel="noopener noreferrer"
       data-repo="{{ repo }}" data-custom-desc="{{ item.desc }}">
      <div class="repo-card-header">
        <i class="fa-regular fa-book"></i>
        <span class="repo-card-name">
          {% if site.data.repositories.github_users contains owner %}{{ rname }}{% else %}{{ repo }}{% endif %}
        </span>
      </div>
      <div class="repo-card-desc">{{ item.desc }}</div>
      <div class="repo-card-meta" id="meta-{{ repo | replace: '/', '-' }}">
        <span class="text-muted" style="font-size:0.75rem">Loading&hellip;</span>
      </div>
    </a>
  {% endfor %}
</div>

<script>
(function () {
  var LANG_COLORS = {
    Python: '#3572A5', R: '#198CE7', JavaScript: '#f1e05a',
    TypeScript: '#2b7489', Shell: '#89e051', Ruby: '#701516',
    HTML: '#e34c26', CSS: '#563d7c'
  };

  // Stats card
  fetch('https://api.github.com/users/joshchiou')
    .then(function (r) { return r.json(); })
    .then(function (u) {
      var av = document.getElementById('gh-avatar');
      var nm = document.getElementById('gh-name');
      if (av) { av.src = u.avatar_url; av.style.display = 'block'; }
      if (nm && u.name) nm.textContent = u.name;
      var reposEl = document.getElementById('gh-repos');
      var followEl = document.getElementById('gh-followers');
      if (reposEl) reposEl.textContent = u.public_repos;
      if (followEl) followEl.textContent = u.followers;
    });

  fetch('https://api.github.com/users/joshchiou/repos?per_page=100')
    .then(function (r) { return r.json(); })
    .then(function (repos) {
      var stars = repos.reduce(function (s, r) { return s + r.stargazers_count; }, 0);
      var el = document.getElementById('gh-stars');
      if (el) el.textContent = stars;
    });

  // Repo cards — fetch language/stars/forks
  var cards = document.querySelectorAll('.repo-card[data-repo]');
  cards.forEach(function (card) {
    var repo = card.getAttribute('data-repo');
    var slug = repo.replace('/', '-');
    var metaEl = document.getElementById('meta-' + slug);
    fetch('https://api.github.com/repos/' + repo)
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!metaEl) return;
        var lang  = d.language || '';
        var color = LANG_COLORS[lang] || '#8a8a8a';
        var stars = d.stargazers_count || 0;
        var forks = d.forks_count || 0;
        var html = '';
        if (lang) {
          html += '<span class="repo-card-lang">'
               + '<span class="lang-dot" style="background:' + color + '"></span>'
               + lang + '</span>';
        }
        if (stars > 0) html += '<span class="repo-card-stat"><i class="fa-regular fa-star"></i> ' + stars + '</span>';
        if (forks > 0) html += '<span class="repo-card-stat"><i class="fa-solid fa-code-fork"></i> ' + forks + '</span>';
        metaEl.innerHTML = html || '<span style="font-size:0.75rem;opacity:0">&nbsp;</span>';
      })
      .catch(function () { if (metaEl) metaEl.innerHTML = ''; });
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

<div class="mt-3">
  <a href="https://github.com/search?q=author%3Ajoshchiou+is%3Apr+is%3Amerged&type=pullrequests"
     target="_blank" rel="noopener noreferrer">See all merged pull requests &rarr;</a>
</div>
