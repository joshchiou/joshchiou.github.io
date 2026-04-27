---
layout: page
title: Home Assistant
description: Home automation setup with solar monitoring, local AI, and custom integrations.
img: assets/img/projects/placeholder-fun.svg
importance: 1
category: fun
---

I run [Home Assistant](https://www.home-assistant.io/) on a local server as the hub for home
automation — controlling lights, climate, media, and monitoring solar production from a
SunPower PV system. The SunPower integration was adapted from an open-source fork; I contributed
a fix for a memory-leak bug that caused crashes when the PVS serial is an IP address
([ha-esunpower #64](https://github.com/smcneece/ha-esunpower/pull/64)).

The setup leans toward local-first: automations run on-device, voice commands use a local
speech-to-text model rather than a cloud service, and dashboards are built in Lovelace with
custom cards for energy monitoring and multi-room audio. The system runs continuously without
cloud dependency, which has been the most satisfying design constraint.
