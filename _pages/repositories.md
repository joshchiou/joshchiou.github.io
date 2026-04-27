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

<div class="repositories d-flex flex-wrap flex-md-row flex-column justify-content-between align-items-center">
  {% for repo in site.data.repositories.github_repos %}
    {% include repository/repo.liquid repository=repo %}
  {% endfor %}
</div>

---

## Open-source contributions

Selected merged pull requests to community scientific software.

<ul class="list-unstyled">
  {% for c in site.data.contributions %}
  <li class="mb-4 contribution-item">
    <div class="mb-1">
      <a href="{{ c.pr_url }}" target="_blank" rel="noopener noreferrer"><strong>{{ c.pr_title }}</strong></a>
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
    <small class="text-muted">{{ c.blurb }}</small>
  </li>
  {% endfor %}
</ul>

<a href="https://github.com/search?q=author%3Ajoshchiou+is%3Apr+is%3Amerged&type=pullrequests" target="_blank" rel="noopener noreferrer">See all merged pull requests &rarr;</a>
