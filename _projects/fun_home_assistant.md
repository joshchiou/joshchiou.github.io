---
layout: page
title: Home Assistant
description: Home automation setup with solar monitoring, local AI, and custom integrations.
img: assets/img/projects/fun/home-assistant.svg
importance: 1
category: fun
---

I run [Home Assistant](https://www.home-assistant.io/) on a local server as the hub for home
automation, controlling lights, climate, media, and monitoring solar production from a
SunPower PV system. The SunPower integration was adapted from an open-source fork; I contributed
a fix for a memory-leak bug that caused crashes when the PVS serial is an IP address
([ha-esunpower #64](https://github.com/smcneece/ha-esunpower/pull/64)).

The setup leans toward local-first: automations run on-device, local
setups preferred over cloud services, and dashboards are built in Lovelace with
custom cards e.g. for energy monitoring. The system runs continuously without
cloud dependency, which is the most important design constraint.

### Stack

- **Hardware** --- Custom built server running Ubuntu 24.04 LTS, Zigbee coordinator (SLZB-06), Thread border routers
- **Software** --- Docker containers for Home Assistant, Zigbee2MQTT, RTLAMR2MQTT, OpenThread, NUT, and custom Python scripts for data processing
- **Solar** --- SunPower PV system monitored via ha-esunpower, energy dashboard tracking production vs. consumption
- **Lighting** --- Zigbee/Matter switches and lightbulbs (IKEA, SONOFF), automations for circadian lighting
- **Climate** --- Smart thermostat + occupancy-based automations

### Design principles

The system is designed around a few rules: everything runs locally (no cloud calls for
critical automations), every automation should degrade gracefully if a sensor goes offline,
and the dashboard should be usable by anyone in the house without training. If the internet
goes down, the lights still work.
