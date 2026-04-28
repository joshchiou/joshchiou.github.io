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

The setup leans toward local-first: automations run on-device, voice commands use a local
speech-to-text model rather than a cloud service, and dashboards are built in Lovelace with
custom cards for energy monitoring and multi-room audio. The system runs continuously without
cloud dependency, which is the most important design constraint.

### Stack

- **Hardware** --- Intel NUC running Home Assistant OS, Zigbee coordinator (SONOFF), Z-Wave stick
- **Solar** --- SunPower PV system monitored via ha-esunpower, energy dashboard tracking production vs. consumption
- **Voice** --- Local Whisper STT + Piper TTS, no cloud dependency for voice commands
- **Lighting** --- Zigbee bulbs and switches (Hue, IKEA TRADFRI), automations for circadian lighting
- **Climate** --- Smart thermostat + occupancy-based automations
- **Media** --- Multi-room audio via Sonos integration, media dashboard for whole-house control

### Design principles

The system is designed around a few rules: everything runs locally (no cloud calls for
critical automations), every automation should degrade gracefully if a sensor goes offline,
and the dashboard should be usable by anyone in the house without training. If the internet
goes down, the lights still work.
