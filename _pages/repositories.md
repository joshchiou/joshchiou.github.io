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
  <li class="mb-3">
    <a href="{{ c.pr_url }}" target="_blank" rel="noopener noreferrer"><strong>{{ c.pr_title }}</strong></a>
    &nbsp;·&nbsp;
    <a href="{{ c.url }}" target="_blank" rel="noopener noreferrer">{{ c.repo }}</a>
    &nbsp;·&nbsp;
    <span class="text-muted">{{ c.date }}</span>
    <br>
    <small>{{ c.blurb }}</small>
  </li>
  {% endfor %}
</ul>

<a href="https://github.com/search?q=author%3Ajoshchiou+is%3Apr+is%3Amerged&type=pullrequests" target="_blank" rel="noopener noreferrer">See all merged pull requests →</a>
