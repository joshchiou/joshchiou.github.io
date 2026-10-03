#!/usr/bin/env python3
"""
Parse Google Maps Timeline location history into travel data files.

Usage:
    python scripts/parse_location_history.py /path/to/location-history.json
    python scripts/parse_location_history.py --dry-run /path/to/location-history.json

Export the JSON on your phone (Timeline is stored on the device, so there is no API):
    Google Maps → your profile → Timeline → ⋮ → Export Timeline data
Both the iOS export (a list of entries) and the Android one ("semanticSegments") work.

Requirements:
    pip install pyyaml requests

Output (merged, never overwritten):
    _data/travel_countries.yml: countries visited (for choropleth map)
    _data/travel_cities.yml: cities visited (review the new ones before committing)

Re-runs only append places that are not in the files yet, so hand-added entries and fields
(continent, flag, state) are never lost. Cities you delete stay deleted: every city the
script has proposed is remembered in scripts/.travel_seen.json (gitignored, since it lists
places you chose not to publish) and is not proposed again. Without that file, every city
missing from travel_cities.yml is proposed once more.

Geocoding uses Nominatim (OpenStreetMap) and caches results to
scripts/.geocode_cache.json so re-runs are instant. All unique places are
geocoded on the first run regardless of filters, so you can re-run with
tighter or looser thresholds without re-fetching.

New countries are reliable, but need a continent added by hand. New cities contain
noise (towns you passed through, suburbs). Review the ones the script prints and delete
any that are not meaningful destinations before committing.
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

# Skip routine semantic types, which are not travel destinations. Compared case-insensitively:
# the iOS export says "Home", the Android one "HOME".
SKIP_SEMANTIC_TYPES = {"home", "work"}

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
    # GeoJSON (datasets/geo-countries) uses "Czechia"; no alias needed but keep for safety
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


def normalise_timeline(data) -> list:
    """Return the export as a list of iOS-style entries.

    The iOS export is already a list of {"startTime", "endTime", "visit": {...}}. The Android
    export is {"semanticSegments": [...]} with "placeId" instead of "placeID", a numeric
    hierarchyLevel, and "placeLocation": {"latLng": "42.36°, -71.09°"}.
    """
    if isinstance(data, list):
        return data
    entries = []
    for seg in data.get("semanticSegments", []):
        visit = seg.get("visit")
        if not visit:
            continue
        cand = visit.get("topCandidate", {})
        loc = cand.get("placeLocation", {})
        lat_lng = loc.get("latLng", "") if isinstance(loc, dict) else ""
        geo = "geo:" + lat_lng.replace("°", "").replace(" ", "") if lat_lng else ""
        entries.append({
            "startTime": seg.get("startTime", ""),
            "endTime": seg.get("endTime", ""),
            "visit": {
                "hierarchyLevel": str(visit.get("hierarchyLevel", "")),
                "probability": visit.get("probability", 0),
                "topCandidate": {
                    "placeID": cand.get("placeId") or cand.get("placeID"),
                    "semanticType": cand.get("semanticType"),
                    "placeLocation": geo,
                },
            },
        })
    return entries


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
        # Not cached, so the next run retries it; a cached None would skip the place forever.
        print(f"  Warning: geocoding failed for {lat:.4f},{lon:.4f}: {exc}")
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
        "state": addr.get("state"),
        "country_code": addr.get("country_code"),
    }
    cache[place_id] = result
    return result


def build_geocode_cache(timeline: list, cache: dict) -> int:
    """Ensures the cache is complete so re-runs with different thresholds don't need new API calls.
    Returns number of new requests made."""
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
        if lat is not None:
            unique[place_id] = (lat, lon)

    new_calls = len(unique)
    if not unique:
        print(f"  All {len(cache)} places already cached, skipping geocoding")
        return 0

    print(f"  Geocoding {new_calls} new places at ~1/sec "
          f"(~{new_calls}s, cache already has {len(cache)} entries)...")
    for i, (place_id, (lat, lon)) in enumerate(unique.items(), 1):
        geocode_place(place_id, lat, lon, cache)
        if i % 20 == 0 or i == new_calls:
            print(f"  {i}/{new_calls} looked up")

    failed = sum(1 for place_id in unique if place_id not in cache)
    if failed:
        print(f"  {failed} lookups failed and will be retried next run; "
              "places they cover are skipped this time.")

    return new_calls


def parse_timeline(timeline: list, cache: dict):
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
        if (candidate.get("semanticType") or "").lower() in SKIP_SEMANTIC_TYPES:
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
            rec["code"] = geo.get("country_code")
        rec["count"] += 1

        if city:
            key = f"{city}|{country}"
            crec = cities[key]
            if crec["lat"] is None:
                crec["lat"] = round(lat, 4)
                crec["lon"] = round(lon, 4)
                crec["country"] = country
                crec["state"] = geo.get("state")
            crec["count"] += 1

    print(f"  Processed {processed} qualifying visits")
    print(f"  Skipped: {skipped_level} sub-visits, {skipped_routine} Home/Work, "
          f"{skipped_confidence} low-confidence, {skipped_duration} short-duration, "
          f"{skipped_nogeo} no-geo")
    return countries, cities


def load_yaml_list(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def flag_emoji(code: str | None) -> str | None:
    """Two-letter ISO code to a flag emoji ("us" -> 🇺🇸)."""
    if not code or len(code) != 2 or not code.isalpha():
        return None
    return "".join(chr(0x1F1E6 + ord(c) - ord("a")) for c in code.lower())


def new_countries(existing: list, countries: dict) -> list:
    have = {c["name"] for c in existing}
    out = []
    for name, info in sorted(countries.items(), key=lambda x: (-x[1]["count"], x[0])):
        if name in have:
            continue
        entry = {"name": name}
        flag = flag_emoji(info.get("code"))
        if flag:
            entry["flag"] = flag
        if info["lat"] is not None:
            entry["lat"] = info["lat"]
            entry["lon"] = info["lon"]
        out.append(entry)
    return out


def new_cities(existing: list, cities: dict, seen: set) -> list:
    """Cities not in the file and never proposed before (so deleted ones stay deleted)."""
    have = {f"{c['name']}|{c['country']}" for c in existing}
    out = []
    for key, info in sorted(cities.items(), key=lambda x: (-x[1]["count"], x[0])):
        if key in have or key in seen:
            continue
        entry = {"name": key.split("|")[0], "country": info["country"]}
        if info["country"] == "United States of America" and info.get("state"):
            entry["state"] = info["state"]
        if info["lat"] is not None:
            entry["lat"] = info["lat"]
            entry["lon"] = info["lon"]
        out.append(entry)
    return out


def append_yaml(path: Path, entries: list) -> None:
    """Append entries to the end of a YAML list file without touching existing lines."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if text and not text.endswith("\n"):
        text += "\n"
    for entry in entries:
        lines = []
        for i, (k, v) in enumerate(entry.items()):
            value = json.dumps(v, ensure_ascii=False) if isinstance(v, str) else v
            lines.append(f"{'- ' if i == 0 else '  '}{k}: {value}")
        text += "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv[1:]
    if len(args) != 1:
        print(f"Usage: python {sys.argv[0]} [--dry-run] /path/to/location-history.json")
        print()
        print("Export on your phone: Google Maps → your profile → Timeline → ⋮ → Export Timeline data")
        sys.exit(1)

    json_path = Path(args[0]).expanduser().resolve()
    if not json_path.is_file():
        print(f"Error: '{json_path}' is not a file")
        sys.exit(1)

    repo_root = Path(__file__).parent.parent
    cache_path = Path(__file__).parent / ".geocode_cache.json"
    seen_path = Path(__file__).parent / ".travel_seen.json"
    countries_out = repo_root / "_data" / "travel_countries.yml"
    cities_out = repo_root / "_data" / "travel_cities.yml"

    print(f"Loading: {json_path}")
    with open(json_path, encoding="utf-8") as f:
        timeline = normalise_timeline(json.load(f))
    print(f"  {len(timeline)} timeline entries\n")

    cache = load_cache(cache_path)
    new_calls = build_geocode_cache(timeline, cache)
    save_cache(cache_path, cache)
    if new_calls:
        print(f"  Cache saved to {cache_path} ({len(cache)} total entries)")

    print("\nBuilding output...")
    countries, cities = parse_timeline(timeline, cache)
    print(f"Results: {len(countries)} countries, {len(cities)} unique city-level places\n")

    existing_countries = load_yaml_list(countries_out)
    existing_cities = load_yaml_list(cities_out)
    seen = set(load_cache(seen_path) or [])
    if not seen:
        print("  No scripts/.travel_seen.json yet: cities you deleted earlier may be proposed again.\n")

    add_countries = new_countries(existing_countries, countries)
    add_cities = new_cities(existing_cities, cities, seen)

    print(f"New countries ({len(add_countries)}):")
    for c in add_countries:
        print(f"  + {c['name']}   (add a continent by hand)")
    print(f"New cities ({len(add_cities)}):")
    for c in add_cities:
        print(f"  + {c['name']}, {c.get('state') or c['country']}")

    if dry_run:
        print("\nDry run: nothing written.")
        return

    append_yaml(countries_out, add_countries)
    append_yaml(cities_out, add_cities)
    seen |= {f"{c['name']}|{c['country']}" for c in existing_cities}
    seen |= set(cities)
    with open(seen_path, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)

    print(
        "\nDone. Existing entries were left as they were."
        "\n  Add a continent to each new country in travel_countries.yml."
        "\n  Delete new cities that are not real destinations; they won't be proposed again."
        "\n  Then run python3 scripts/render_travel_card.py to redraw the card."
    )


if __name__ == "__main__":
    main()
