---
layout: page
permalink: /code/
title: code
nav: true
nav_order: 4
description: >
  A slice of my public coding activity. Most production work lives in enterprise GitHub organizations
  (Pfizer, Lilly) and isn't reflected here.
---

{% assign gh = site.data.github_stats %}

<div class="github-profile-card mb-5" id="github-profile-card">
  <div class="github-profile-inner-d">
    <div class="github-profile-left">
      <a href="https://github.com/joshchiou" target="_blank" rel="noopener noreferrer"
         class="github-profile-identity">
        {% if gh.avatar_url %}
          <img src="{{ gh.avatar_url }}" alt="GitHub avatar" class="github-avatar">
        {% else %}
          <img src="" alt="GitHub avatar" class="github-avatar" style="display:none">
        {% endif %}
        <div>
          <div class="github-profile-name">{{ gh.name | default: "Josh Chiou" }}</div>
          <div class="github-profile-login">@joshchiou</div>
        </div>
      </a>
    </div>
    <div class="github-profile-right-d">
      <div class="github-profile-stats">
        <div class="gh-stat"><span class="gh-stat-val">{{ gh.public_repos | default: "—" }}</span><span class="gh-stat-label">repos</span></div>
        <div class="gh-stat"><span class="gh-stat-val">{{ gh.total_stars | default: "—" }}</span><span class="gh-stat-label">stars</span></div>
        <div class="gh-stat"><span class="gh-stat-val">{{ gh.followers | default: "—" }}</span><span class="gh-stat-label">followers</span></div>
      </div>
      <div class="gh-stat-divider"></div>
      <div class="github-profile-orgs-d">
        <div class="github-profile-orgs-icons">
          <a href="https://github.com/EliLillyCo" target="_blank" rel="noopener noreferrer" title="Eli Lilly & Company">
            <img src="https://avatars.githubusercontent.com/u/16001067?v=4&s=40" alt="Eli Lilly">
          </a>
          <a href="https://github.com/conda-forge" target="_blank" rel="noopener noreferrer" title="conda-forge">
            <img src="https://avatars.githubusercontent.com/u/11897326?v=4&s=40" alt="conda-forge">
          </a>
          <a href="https://github.com/noobies-tennis" target="_blank" rel="noopener noreferrer" title="Noobies Tennis">
            <img src="https://avatars.githubusercontent.com/u/97570579?v=4&s=40" alt="Noobies Tennis">
          </a>
        </div>
        <span class="github-profile-orgs-label">organizations</span>
      </div>
    </div>
  </div>
</div>

## Featured repositories

Repositories I've built or contributed to significantly.

{% assign LANG_COLORS = "Python:#3572A5,R:#198CE7,JavaScript:#f1e05a,TypeScript:#2b7489,Shell:#89e051,Ruby:#701516,HTML:#e34c26,CSS:#563d7c" | split: "," %}

<div class="repo-card-grid mb-4">
  {% for item in site.data.repositories.github_repos %}
    {% assign repo = item.repo %}
    {% assign repo_parts = repo | split: '/' %}
    {% assign owner = repo_parts[0] %}
    {% assign rname = repo_parts[1] %}
    {% assign repo_data = gh.repos[repo] %}
    <a class="repo-card" href="https://github.com/{{ repo }}" target="_blank" rel="noopener noreferrer">
      <div class="repo-card-header">
        <i class="fa-regular fa-book"></i>
        <span class="repo-card-name">
          {% if site.data.repositories.github_users contains owner %}{{ rname }}{% else %}{{ repo }}{% endif %}
        </span>
      </div>
      <div class="repo-card-desc">{{ item.desc }}</div>
      <div class="repo-card-meta">
        {% if repo_data.language %}
          {% assign lang_color = "#8a8a8a" %}
          {% for pair in LANG_COLORS %}
            {% assign kv = pair | split: ":" %}
            {% if kv[0] == repo_data.language %}
              {% assign lang_color = kv[1] %}
            {% endif %}
          {% endfor %}
          <span class="repo-card-lang">
            <span class="lang-dot" style="background:{{ lang_color }}"></span>
            {{ repo_data.language }}
          </span>
        {% endif %}
        {% if repo_data.stars > 0 %}
          <span class="repo-card-stat"><i class="fa-regular fa-star"></i> {{ repo_data.stars }}</span>
        {% endif %}
        {% if repo_data.forks > 0 %}
          <span class="repo-card-stat"><i class="fa-solid fa-code-fork"></i> {{ repo_data.forks }}</span>
        {% endif %}
      </div>
    </a>
  {% endfor %}
</div>

---

## Open-source contributions

Selected merged pull requests to community scientific software.

{% assign sorted_contribs = site.data.contributions | sort: "date" | reverse %}
{% assign current_year = "" %}
<ul class="list-unstyled">
  {% for c in sorted_contribs %}
    {% assign c_year = c.date | date: "%Y" %}
    {% if c_year != current_year %}
      {% assign current_year = c_year %}
      <li class="mt-4 mb-2"><h4 class="text-muted">{{ current_year }}</h4></li>
    {% endif %}
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
