#!/usr/bin/env python3
"""Render the travel project card: a world map of visited countries and cities.

Reads assets/json/world-countries.geojson, _data/travel_countries.yml, and
_data/travel_cities.yml; writes assets/img/projects/fun/travel.svg (16:10).
Re-run after editing the travel data files.

Usage:
    python3 scripts/render_travel_card.py

Requires: pip install numpy matplotlib pyyaml
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/img/projects/fun/travel.svg"

SURFACE = "#fcfcfb"
LAND = "#e6e5e1"
BORDER = "#fcfcfb"
VISITED = "#2a78d6"  # categorical 1 (dataviz reference palette)
CITY = "#eb6834"  # categorical 2

LON_MIN, LON_MAX = -132, 154  # frame: US west coast through Japan
LAT_CENTER = 22


def miller(lon, lat):
    lat = np.radians(np.clip(lat, -85, 85))
    return np.asarray(lon, float), np.degrees(1.25 * np.log(np.tan(np.pi / 4 + 0.4 * lat)))


def rings(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    if geom["type"] == "MultiPolygon":
        return [poly[0] for poly in geom["coordinates"]]
    return []


def main():
    world = json.loads((ROOT / "assets/json/world-countries.geojson").read_text())
    countries = yaml.safe_load((ROOT / "_data/travel_countries.yml").read_text()) or []
    cities = yaml.safe_load((ROOT / "_data/travel_cities.yml").read_text()) or []
    visited = {c["name"] for c in countries}
    ref_lat = {c["name"]: c["lat"] for c in countries}

    fig = plt.figure(figsize=(8, 5), facecolor=SURFACE)
    ax = fig.add_axes([0, 0, 1, 1], facecolor=SURFACE)
    ax.set_axis_off()

    names = set()
    for f in world["features"]:
        name = f["properties"].get("name")
        names.add(name)
        if name == "Antarctica":
            continue
        ref = ref_lat.get(name)
        for ring in rings(f["geometry"]):
            xy = np.array(ring, float)
            if np.ptp(xy[:, 0]) > 180:  # ring crosses the antimeridian: unwrap it
                xy[:, 0] = np.where(xy[:, 0] < 0, xy[:, 0] + 360, xy[:, 0])
            # Shade only the part of a visited country near where it was visited, so
            # overseas territories (e.g. French Guiana) stay unshaded.
            shaded = ref is not None and abs(xy[:, 1].mean() - ref) < 30
            x, y = miller(xy[:, 0], xy[:, 1])
            ax.add_patch(Polygon(np.c_[x, y], closed=True, fc=VISITED if shaded else LAND, ec=BORDER, lw=0.5))

    missing = visited - names
    if missing:
        print(f"Warning: not in GeoJSON, so not shaded: {sorted(missing)}")

    lon = np.array([c["lon"] for c in cities])
    lat = np.array([c["lat"] for c in cities])
    x, y = miller(lon, lat)
    ax.scatter(x, y, s=22, color=CITY, edgecolor=SURFACE, linewidth=1.1, zorder=3)

    w = LON_MAX - LON_MIN
    _, yc = miller(0, LAT_CENTER)
    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(yc - w / 3.2, yc + w / 3.2)  # 16:10
    ax.set_aspect("auto")
    fig.savefig(OUT, format="svg", facecolor=SURFACE, metadata={"Date": None})
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(visited)} countries, {len(cities)} cities")


if __name__ == "__main__":
    main()
