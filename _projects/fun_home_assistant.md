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
home automation to control lights, climate, and media while monitoring solar production from
a SunPower PV system. The system is designed around one hard constraint: **if the internet goes
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
all on local hardware. Click any component for details.

<div class="hass-diagram">

  <div class="hass-layer" data-layer="devices">
    <div class="hass-layer-label">Devices</div>
    <div class="hass-layer-right">
      <div class="hass-chip-row">
        <button class="hass-chip" data-title="SunPower PV" data-desc="Residential solar array monitored in real time via the SunPower PVS gateway on the local network. Production data feeds the HA energy dashboard through the ha-esunpower integration.">
          <i class="fa-solid fa-solar-panel"></i> SunPower PV
        </button>
        <button class="hass-chip" data-title="Smart Meter" data-desc="Utility meter that broadcasts consumption data over 433 MHz AMR radio. An RTL-SDR USB dongle passively receives these one-way transmissions — no utility account access required.">
          <i class="fa-solid fa-gauge"></i> Smart Meter
        </button>
        <button class="hass-chip" data-title="IKEA Tradfri" data-desc="Zigbee bulbs, outlet plugs, and motion sensors from IKEA's Tradfri line. Paired directly to Zigbee2MQTT — no IKEA hub or cloud dependency.">
          <i class="fa-solid fa-lightbulb"></i> IKEA Tradfri
        </button>
        <button class="hass-chip" data-title="SONOFF" data-desc="Zigbee switches, relays, and sensors. Paired directly to Zigbee2MQTT for fully local operation.">
          <i class="fa-solid fa-toggle-on"></i> SONOFF
        </button>
        <button class="hass-chip" data-title="Smart Thermostat" data-desc="Wi-Fi thermostat integrated directly into Home Assistant. Occupancy-based automations adjust setpoints to avoid conditioning an empty house.">
          <i class="fa-solid fa-temperature-half"></i> Smart Thermostat
        </button>
        <button class="hass-chip" data-title="UPS" data-desc="Uninterruptible power supply protecting the server. NUT (Network UPS Tools) exposes battery charge, load percentage, and estimated runtime as HA sensor entities.">
          <i class="fa-solid fa-battery-three-quarters"></i> UPS
        </button>
      </div>
      <div class="hass-node-detail"></div>
    </div>
  </div>

  <div class="hass-connector" aria-hidden="true">
    <svg class="hass-flow-svg" viewBox="0 0 300 24" preserveAspectRatio="none">
      <line class="hass-flow-line--1" x1="25%" y1="0" x2="25%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--2" x1="50%" y1="0" x2="50%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--3" x1="75%" y1="0" x2="75%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
    </svg>
  </div>

  <div class="hass-layer" data-layer="protocol">
    <div class="hass-layer-label">Protocol</div>
    <div class="hass-layer-right">
      <div class="hass-chip-row">
        <button class="hass-chip" data-title="Zigbee 802.15.4" data-desc="Low-power mesh radio protocol coordinated by an SLZB-06 Zigbee coordinator. Handles all IKEA and SONOFF devices. Traffic is decoded by Zigbee2MQTT and published to the local MQTT broker.">
          <i class="fa-solid fa-wifi"></i> Zigbee 802.15.4
        </button>
        <button class="hass-chip" data-title="Thread / Matter" data-desc="IPv6-based mesh protocol for newer smart home devices. Thread border routers bridge the mesh to the local IP network. HA has native Matter support — no cloud commissioning required.">
          <i class="fa-solid fa-share-nodes"></i> Thread / Matter
        </button>
        <button class="hass-chip" data-title="AMR 433 MHz" data-desc="Automatic Meter Reading: one-way radio packets broadcast by the utility smart meter. Received passively by the RTL-SDR dongle and decoded by RTLAMR2MQTT. No pairing or utility account access needed.">
          <i class="fa-solid fa-tower-broadcast"></i> AMR 433 MHz
        </button>
      </div>
      <div class="hass-node-detail"></div>
    </div>
  </div>

  <div class="hass-connector" aria-hidden="true">
    <svg class="hass-flow-svg" viewBox="0 0 300 24" preserveAspectRatio="none">
      <line class="hass-flow-line--1" x1="25%" y1="0" x2="25%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--2" x1="50%" y1="0" x2="50%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--3" x1="75%" y1="0" x2="75%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
    </svg>
  </div>

  <div class="hass-layer" data-layer="bridges">
    <div class="hass-layer-label">Bridges</div>
    <div class="hass-layer-right">
      <div class="hass-chip-row">
        <button class="hass-chip" data-title="Zigbee2MQTT" data-desc="Translates Zigbee radio traffic from the SLZB-06 coordinator into MQTT messages. Supports 3000+ devices. The primary bridge for all Zigbee devices — no vendor clouds involved.">
          <i class="fa-solid fa-arrows-left-right"></i> Zigbee2MQTT
        </button>
        <button class="hass-chip" data-title="RTLAMR2MQTT" data-desc="Decodes AMR utility meter readings received by the RTL-SDR dongle and publishes them as MQTT messages. Runs as a Docker container alongside the SDR device.">
          <i class="fa-solid fa-satellite-dish"></i> RTLAMR2MQTT
        </button>
        <button class="hass-chip" data-title="OpenThread" data-desc="Thread border router daemon (otbr-agent) that connects the Thread 802.15.4 mesh to the local IP network, enabling Matter-over-Thread devices to reach Home Assistant.">
          <i class="fa-solid fa-sitemap"></i> OpenThread
        </button>
        <button class="hass-chip" data-title="NUT" data-desc="Network UPS Tools monitors the UPS over USB and exposes battery charge, load, and runtime estimates. The HA NUT integration pulls these as sensor entities.">
          <i class="fa-solid fa-battery-three-quarters"></i> NUT
        </button>
      </div>
      <div class="hass-node-detail"></div>
    </div>
  </div>

  <div class="hass-connector" aria-hidden="true">
    <svg class="hass-flow-svg" viewBox="0 0 300 24" preserveAspectRatio="none">
      <line class="hass-flow-line--1" x1="25%" y1="0" x2="25%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--2" x1="50%" y1="0" x2="50%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--3" x1="75%" y1="0" x2="75%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
    </svg>
  </div>

  <div class="hass-layer hass-layer--core" data-layer="core">
    <div class="hass-layer-label">Core</div>
    <div class="hass-layer-right">
      <div class="hass-chip-row">
        <button class="hass-chip hass-chip--core" data-title="Home Assistant" data-desc="The automation engine — runs as a Docker container on the home server (Ubuntu 24.04 LTS). Consumes MQTT events from the bridges, runs all automations on-device, and serves the Lovelace UI over the local network.">
          <i class="fa-solid fa-house"></i> Home Assistant
        </button>
        <button class="hass-chip hass-chip--core" data-title="ha-esunpower" data-desc="Custom integration for SunPower PV systems. Adapted from an open-source fork; I contributed a fix for a memory-leak crash when the PVS gateway serial is an IP address (PR #64).">
          <i class="fa-solid fa-solar-panel"></i> ha-esunpower
        </button>
        <button class="hass-chip hass-chip--core" data-title="Mosquitto MQTT" data-desc="Local MQTT broker running as a Docker container. All bridges (Zigbee2MQTT, RTLAMR2MQTT, NUT) publish to this broker; Home Assistant subscribes to receive device state updates.">
          <i class="fa-solid fa-arrows-left-right"></i> Mosquitto MQTT
        </button>
      </div>
      <div class="hass-node-detail"></div>
    </div>
  </div>

  <div class="hass-connector" aria-hidden="true">
    <svg class="hass-flow-svg" viewBox="0 0 300 24" preserveAspectRatio="none">
      <line class="hass-flow-line--1" x1="25%" y1="0" x2="25%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--2" x1="50%" y1="0" x2="50%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
      <line class="hass-flow-line--3" x1="75%" y1="0" x2="75%" y2="24" stroke="#18bcf2" stroke-width="1.5" stroke-dasharray="4 4" stroke-linecap="round"/>
    </svg>
  </div>

  <div class="hass-layer" data-layer="dashboards">
    <div class="hass-layer-label">Dashboards</div>
    <div class="hass-layer-right">
      <div class="hass-chip-row">
        <button class="hass-chip" data-title="Energy Dashboard" data-desc="Built-in HA energy dashboard showing solar production vs. grid consumption in real time and historically. Data comes from ha-esunpower (production) and the AMR smart meter (consumption).">
          <i class="fa-solid fa-chart-line"></i> Energy Dashboard
        </button>
        <button class="hass-chip" data-title="Lighting" data-desc="Lovelace dashboard for manual scene and circadian lighting control. Automations adjust color temperature throughout the day; override scenes are a single tap.">
          <i class="fa-solid fa-sliders"></i> Lighting
        </button>
        <button class="hass-chip" data-title="Climate" data-desc="Smart thermostat control with occupancy-based automations. When the house is empty the thermostat backs off; it pre-conditions before regular arrival times.">
          <i class="fa-solid fa-temperature-half"></i> Climate
        </button>
        <button class="hass-chip" data-title="Custom Cards" data-desc="Purpose-built Lovelace cards for energy monitoring and at-a-glance system status. Designed for zero training — anyone in the house can read and operate them.">
          <i class="fa-solid fa-table-cells"></i> Custom Cards
        </button>
      </div>
      <div class="hass-node-detail"></div>
    </div>
  </div>

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
