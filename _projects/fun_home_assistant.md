---
layout: page
title: Home Assistant
description: Home automation setup with solar monitoring, local AI, and custom integrations.
img: assets/img/projects/fun/home-assistant.svg
importance: 1
category: fun
---

{% assign s = site.data.hass_stats %}

I run [Home Assistant](https://www.home-assistant.io/) on a self-hosted server as the hub for
home automation. It started with solar: after installing a SunPower PV system I wanted to
monitor production locally without depending on SunPower's cloud app, so I set up Home
Assistant to pull data directly from the PVS gateway on my LAN. From there it grew to
controlling lights, climate, and media while monitoring utility consumption — the tinkerer in
me couldn't resist. The system is designed around one hard constraint: **if the internet goes
down, everything still works.**

{% if s.automations or s.entities or s.integrations or s.since %}
<div class="hass-stats">
  <div class="hass-stat">
    <span class="hass-stat-val">{{ s.automations | default: "—" }}</span>
    <span class="hass-stat-label">automations</span>
  </div>
  <div class="hass-stat">
    <span class="hass-stat-val">{{ s.entities | default: "—" }}</span>
    <span class="hass-stat-label">entities</span>
  </div>
  <div class="hass-stat">
    <span class="hass-stat-val">{{ s.integrations | default: "—" }}</span>
    <span class="hass-stat-label">integrations</span>
  </div>
  <div class="hass-stat">
    <span class="hass-stat-val">{{ s.since | default: "—" }}</span>
    <span class="hass-stat-label">since</span>
  </div>
</div>
{% endif %}

### Architecture

The stack is layered: physical devices talk over radio protocols, protocol bridges translate
those signals to MQTT, and Home Assistant consumes the events to run automations and dashboards —
all on local hardware. <span class="text-muted" style="font-size: 0.82rem;">Tap any component for details.</span>

<div class="hass-diagram">

{% for layer in site.data.hass_layers %}
  {% if layer.core %}
  <div class="hass-layer hass-layer--core" data-layer="{{ layer.layer }}">
  {% else %}
  <div class="hass-layer" data-layer="{{ layer.layer }}">
  {% endif %}
    <div class="hass-layer-label">{{ layer.label }}</div>
    <div class="hass-layer-right">
      <div class="hass-chip-row">
        {% for chip in layer.chips %}
        <button class="hass-chip{% if layer.core %} hass-chip--core{% endif %}" data-title="{{ chip.title }}" data-desc="{{ chip.desc }}">
          <i class="{{ chip.icon }}"></i> {{ chip.title }}
        </button>
        {% endfor %}
      </div>
      <div class="hass-node-detail"></div>
    </div>
  </div>

  {% unless forloop.last %}
  <div class="hass-connector" aria-hidden="true">
    <svg class="hass-flow-svg" viewBox="0 0 300 24" preserveAspectRatio="none">
      <line class="hass-flow-line--1" x1="25%" y1="0" x2="25%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--2" x1="50%" y1="0" x2="50%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--3" x1="75%" y1="0" x2="75%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
    </svg>
  </div>
  {% endunless %}
{% endfor %}

</div>

### Design principles

<div class="hass-principles">
  <div class="hass-principle-card">
    <div class="hass-principle-icon"><i class="fa-solid fa-house-signal"></i></div>
    <h5>Local-first</h5>
    <p>No automation depends on an external cloud. Lights, climate, and energy monitoring keep working if the internet goes down.</p>
  </div>
  <div class="hass-principle-card">
    <div class="hass-principle-icon"><i class="fa-solid fa-shield-halved"></i></div>
    <h5>Graceful degradation</h5>
    <p>Every automation has a safe fallback when a sensor goes offline. The system fails open for comfort and closed for safety.</p>
  </div>
  <div class="hass-principle-card">
    <div class="hass-principle-icon"><i class="fa-solid fa-users"></i></div>
    <h5>Zero-training UI</h5>
    <p>Dashboards are designed to be usable by anyone in the house with no Home Assistant knowledge required.</p>
  </div>
</div>

### Open source

The SunPower PV integration is adapted from [ha-esunpower](https://github.com/smcneece/ha-esunpower). I contributed a fix for a memory-leak crash that occurred when the PVS gateway's serial number is an IP address:

- [ha-esunpower #64](https://github.com/smcneece/ha-esunpower/pull/64) — fix memory leak when `pvs_serial` is an IP address

<script>
(function () {
  function closeAll() {
    document.querySelectorAll('.hass-chip.active').forEach(function (c) {
      c.classList.remove('active');
    });
    document.querySelectorAll('.hass-node-detail.open').forEach(function (d) {
      d.classList.remove('open');
      d.innerHTML = '';
    });
  }

  document.querySelectorAll('.hass-chip').forEach(function (chip) {
    chip.addEventListener('click', function (e) {
      e.stopPropagation();
      var layer = chip.closest('.hass-layer');
      var detail = layer.querySelector('.hass-node-detail');
      var wasActive = chip.classList.contains('active');
      closeAll();
      if (!wasActive) {
        chip.classList.add('active');
        detail.innerHTML = '<strong>' + chip.dataset.title + '</strong> — ' + chip.dataset.desc;
        detail.classList.add('open');
      }
    });
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('.hass-diagram')) {
      closeAll();
    }
  });
})();
</script>
