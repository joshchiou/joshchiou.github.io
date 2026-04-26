#!/usr/bin/env python3
"""
Parse Google Maps Timeline location history into travel data files.

Usage:
    python scripts/parse_location_history.py /path/to/location-history.json

Download location-history.json from Google Maps:
    Maps → your profile → Timeline → Export → Export timeline data (JSON)

Requirements:
    pip install pyyaml requests

Output:
    _data/travel_countries.yml  — unique countries visited (for choropleth map)
    _data/travel_cities.yml     — candidate cities visited (review and prune before committing)

Geocoding uses Nominatim (OpenStreetMap) and caches results to
scripts/.geocode_cache.json so re-runs are instant. All unique places are
geocoded on the first run regardless of filters, so you can re-run with
tighter or looser thresholds without re-fetching.

The countries file is reliable. The cities file will contain noise (restaurants,
shops, etc.). Review it and delete entries that are not meaningful destinations
before committing.
"""

import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml requests")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install pyyaml requests")
    sys.exit(1)

# Minimum visit duration in hours to include an entry.
# 1h captures day trips; raise to 4h to filter airport transits more aggressively.
MIN_VISIT_HOURS = 1

# Minimum overall visit probability (0.0–1.0) to include an entry.
MIN_CONFIDENCE = 0.5

# Skip routine semantic types — not travel destinations.
SKIP_SEMANTIC_TYPES = {"Home", "Work"}

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_HEADERS = {"User-Agent": "joshchiou.github.io/1.0"}

COUNTRY_ALIASES = {
    # Normalize all US variants to the GeoJSON name ("United States of America")
    "United States": "United States of America",
    "USA": "United States of America",
    "US": "United States of America",
    "U.S.A.": "United States of America",
    "U.S.": "United States of America",
    "UK": "United Kingdom",
    "U.K.": "United Kingdom",
    "England": "United Kingdom",
    "Scotland": "United Kingdom",
    "Wales": "United Kingdom",
    "Northern Ireland": "United Kingdom",
    "Great Britain": "United Kingdom",
    "Korea": "South Korea",
    "Republic of Korea": "South Korea",
    "ROC": "Taiwan",
    "Taiwan, Province of China": "Taiwan",
    "Viet Nam": "Vietnam",
    "España": "Spain",
    # GeoJSON (datasets/geo-countries) uses "Czechia" — no alias needed but keep for safety
    "Czech Republic": "Czechia",
    "Slovak Republic": "Slovakia",
    "Türkiye": "Turkey",
    "Turkish Republic": "Turkey",
    "Russian Federation": "Russia",
    "UAE": "United Arab Emirates",
    "Holland": "Netherlands",
    "PRC": "China",
    # GeoJSON uses "Hong Kong S.A.R." and "Macao S.A.R"
    "HK": "Hong Kong S.A.R.",
    "Hong Kong": "Hong Kong S.A.R.",
    "Macau SAR": "Macao S.A.R",
    "Macau": "Macao S.A.R",
}


def parse_iso_timestamp(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def entry_duration_hours(entry: dict) -> float:
    start = parse_iso_timestamp(entry.get("startTime", ""))
    end = parse_iso_timestamp(entry.get("endTime", ""))
    if start and end:
        return (end - start).total_seconds() / 3600
    return 0.0


def parse_geo(geo_str: str) -> tuple[float, float] | tuple[None, None]:
    """Parse 'geo:lat,lon' string into (lat, lon) floats."""
    if not geo_str or not geo_str.startswith("geo:"):
        return None, None
    try:
        lat, lon = geo_str[4:].split(",")
        return float(lat), float(lon)
    except ValueError:
        return None, None


def normalise_country(raw: str) -> str:
    return COUNTRY_ALIASES.get(raw.strip(), raw.strip())


def load_cache(path: Path) -> dict:
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return {}


def save_cache(path: Path, cache: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode_place(place_id: str, lat: float, lon: float, cache: dict) -> dict | None:
    """
    Reverse geocode a place via Nominatim, cached by placeID.
    Returns {"country": str, "city": str | None} or None on failure.
    Sleeps 1.1s per uncached request to respect Nominatim's 1 req/sec limit.
    """
    if place_id in cache:
        return cache[place_id]

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"format": "json", "lat": lat, "lon": lon, "zoom": 10},
            headers=NOMINATIM_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"  Warning: geocoding failed for {lat:.4f},{lon:.4f}: {exc}")
        cache[place_id] = None
        return None

    time.sleep(1.1)

    addr = data.get("address", {})
    country_raw = addr.get("country", "")
    if not country_raw:
        cache[place_id] = None
        return None

    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("county")
        or ""
    )

    result = {
        "country": normalise_country(country_raw),
        "city": city.strip() if city else None,
    }
    cache[place_id] = result
    return result


def build_geocode_cache(timeline: list, cache: dict) -> int:
    """
    Geocode all unique placeIDs from level-0 visits regardless of filters.
    This ensures the cache is complete so re-runs with different thresholds
    don't need new API calls. Returns number of new requests made.
    """
    unique: dict[str, tuple[float, float]] = {}
    for entry in timeline:
        if "visit" not in entry:
            continue
        visit = entry["visit"]
        if visit.get("hierarchyLevel") != "0":
            continue
        candidate = visit.get("topCandidate", {})
        place_id = candidate.get("placeID")
        if not place_id or place_id in cache:
            continue
        lat, lon = parse_geo(candidate.get("placeLocation", ""))
        if lat is not None and place_id not in unique:
            unique[place_id] = (lat, lon)

    new_calls = len(unique)
    if not unique:
        print(f"  All {len(cache)} places already cached — skipping geocoding")
        return 0

    print(f"  Geocoding {new_calls} new places at ~1/sec "
          f"(~{new_calls}s, cache already has {len(cache)} entries)...")
    for i, (place_id, (lat, lon)) in enumerate(unique.items(), 1):
        geocode_place(place_id, lat, lon, cache)
        if i % 20 == 0 or i == new_calls:
            print(f"  {i}/{new_calls} geocoded")

    return new_calls


def parse_timeline(timeline: list, cache: dict):
    """Apply visit filters and build country/city aggregates from cached geocodes."""
    countries: dict[str, dict] = defaultdict(lambda: {"lat": None, "lon": None, "count": 0})
    cities: dict[str, dict] = defaultdict(lambda: {"lat": None, "lon": None, "country": None, "count": 0})

    processed = 0
    skipped_level = skipped_routine = skipped_confidence = skipped_duration = skipped_nogeo = 0

    for entry in timeline:
        if "visit" not in entry:
            continue

        visit = entry["visit"]

        if visit.get("hierarchyLevel") != "0":
            skipped_level += 1
            continue

        candidate = visit.get("topCandidate", {})
        if candidate.get("semanticType") in SKIP_SEMANTIC_TYPES:
            skipped_routine += 1
            continue

        if float(visit.get("probability", 0)) < MIN_CONFIDENCE:
            skipped_confidence += 1
            continue

        if entry_duration_hours(entry) < MIN_VISIT_HOURS:
            skipped_duration += 1
            continue

        place_id = candidate.get("placeID", "")
        lat, lon = parse_geo(candidate.get("placeLocation", ""))
        if lat is None:
            skipped_nogeo += 1
            continue

        geo = cache.get(place_id)
        if not geo:
            skipped_nogeo += 1
            continue

        country = geo["country"]
        city = geo["city"]
        processed += 1

        rec = countries[country]
        if rec["lat"] is None:
            rec["lat"] = round(lat, 4)
            rec["lon"] = round(lon, 4)
        rec["count"] += 1

        if city:
            key = f"{city}|{country}"
            crec = cities[key]
            if crec["lat"] is None:
                crec["lat"] = round(lat, 4)
                crec["lon"] = round(lon, 4)
                crec["country"] = country
            crec["count"] += 1

    print(f"  Processed {processed} qualifying visits")
    print(f"  Skipped: {skipped_level} sub-visits, {skipped_routine} Home/Work, "
          f"{skipped_confidence} low-confidence, {skipped_duration} short-duration, "
          f"{skipped_nogeo} no-geo")
    return countries, cities


def write_yaml(path: Path, data: list, header_lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for line in header_lines:
            f.write(f"# {line}\n")
        f.write("\n")
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"  → {path}  ({len(data)} entries)")


def build_countries_output(countries: dict) -> list:
    out = []
    for name, info in sorted(countries.items(), key=lambda x: (-x[1]["count"], x[0])):
        entry = {"name": name}
        if info["lat"] is not None:
            entry["lat"] = info["lat"]
            entry["lon"] = info["lon"]
        out.append(entry)
    return out


def build_cities_output(cities: dict) -> list:
    out = []
    for key, info in sorted(cities.items(), key=lambda x: (-x[1]["count"], x[0])):
        name = key.split("|")[0]
        entry = {"name": name, "country": info["country"]}
        if info["lat"] is not None:
            entry["lat"] = info["lat"]
            entry["lon"] = info["lon"]
        out.append(entry)
    return out


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} /path/to/location-history.json")
        print()
        print("Download from Google Maps → your profile → Timeline → Export timeline data (JSON)")
        sys.exit(1)

    json_path = Path(sys.argv[1]).expanduser().resolve()
    if not json_path.is_file():
        print(f"Error: '{json_path}' is not a file")
        sys.exit(1)

    repo_root = Path(__file__).parent.parent
    cache_path = Path(__file__).parent / ".geocode_cache.json"
    countries_out = repo_root / "_data" / "travel_countries.yml"
    cities_out = repo_root / "_data" / "travel_cities.yml"

    print(f"Loading: {json_path}")
    with open(json_path, encoding="utf-8") as f:
        timeline = json.load(f)
    print(f"  {len(timeline)} timeline entries\n")

    cache = load_cache(cache_path)
    new_calls = build_geocode_cache(timeline, cache)
    if new_calls:
        save_cache(cache_path, cache)
        print(f"  Cache saved to {cache_path} ({len(cache)} total entries)")

    print("\nBuilding output...")
    countries, cities = parse_timeline(timeline, cache)
    print(f"Results: {len(countries)} countries, {len(cities)} unique city-level places\n")

    write_yaml(
        countries_out,
        build_countries_output(countries),
        [
            "Auto-generated by scripts/parse_location_history.py",
            "Countries visited (from Google Maps Timeline)",
            "Regenerate: python scripts/parse_location_history.py /path/to/location-history.json",
        ],
    )
    write_yaml(
        cities_out,
        build_cities_output(cities),
        [
            "Auto-generated by scripts/parse_location_history.py",
            "Candidate cities visited — REVIEW AND PRUNE before committing.",
            "This file contains noise: restaurants, shops, transit stops, etc.",
            "Delete any entry that is not a meaningful destination.",
            "Regenerate: python scripts/parse_location_history.py /path/to/location-history.json",
        ],
    )

    print(
        "\nDone."
        "\n  travel_countries.yml is reliable — commit as-is."
        "\n  travel_cities.yml needs review — remove entries that are not real destinations."
    )


if __name__ == "__main__":
    main()
