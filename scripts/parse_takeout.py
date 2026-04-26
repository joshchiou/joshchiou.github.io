#!/usr/bin/env python3
"""
Parse Google Takeout Semantic Location History into travel data files.

Usage:
    python scripts/parse_takeout.py /path/to/Takeout

Requirements:
    pip install pyyaml

Output:
    _data/travel-countries.yml  — unique countries visited (for choropleth map)
    _data/travel-cities.yml     — candidate cities visited (review and prune before committing)

The countries file is reliable. The cities file will contain noise (restaurants,
offices, transit stops). Review it and delete entries that aren't meaningful
destinations before committing.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

# Minimum visit duration in hours to include an entry.
# 4h filters most airport transits; raise to 8h to be more conservative.
MIN_VISIT_HOURS = 4

# Minimum visit confidence (0-100) to include an entry.
MIN_CONFIDENCE = 50

# Normalise common country abbreviations and variants to full English names
# (matching what ECharts world map expects).
COUNTRY_ALIASES = {
    "USA": "United States",
    "US": "United States",
    "U.S.A.": "United States",
    "U.S.": "United States",
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
    "Czechia": "Czech Republic",
    "Slovak Republic": "Slovakia",
    "Türkiye": "Turkey",
    "Russian Federation": "Russia",
    "UAE": "United Arab Emirates",
    "Holland": "Netherlands",
    "PRC": "China",
    "HK": "Hong Kong",
    "Macau SAR": "Macau",
}


def parse_iso_timestamp(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def visit_duration_hours(duration: dict) -> float:
    start = parse_iso_timestamp(duration.get("startTimestamp", ""))
    end = parse_iso_timestamp(duration.get("endTimestamp", ""))
    if start and end:
        return (end - start).total_seconds() / 3600
    return 0.0


def normalise_country(raw: str) -> str:
    raw = raw.strip()
    return COUNTRY_ALIASES.get(raw, raw)


def extract_country(address: str) -> str | None:
    """
    Extract country from a Google address string.
    Addresses look like: "Place Name, City, State ZIP, Country"
    The country is almost always the last comma-separated token.
    """
    if not address:
        return None
    parts = [p.strip() for p in address.split(",")]
    for candidate in reversed(parts):
        candidate = candidate.strip()
        # Skip purely numeric tokens (ZIP codes) and empty strings
        if candidate and not candidate.replace(" ", "").isdigit():
            return normalise_country(candidate)
    return None


def extract_city(location: dict, address: str) -> str | None:
    """
    Best-effort city extraction. Uses the address rather than the place name
    because place names are often businesses.
    Returns the first meaningful address component (city-level).
    """
    if not address:
        return location.get("name")
    parts = [p.strip() for p in address.split(",")]
    # Skip the first part if it looks like a street address (contains digits)
    for part in parts:
        if part and not any(char.isdigit() for char in part):
            return part
    return parts[0] if parts else None


def find_semantic_history_files(takeout_dir: Path) -> list[Path]:
    """
    Locate monthly JSON files under any of the known Takeout folder variants.
    """
    search_roots = [
        "Location History (Timeline)/Semantic Location History",
        "Location History/Semantic Location History",
        "Semantic Location History",
    ]
    for root in search_roots:
        files = sorted((takeout_dir / root).rglob("*.json")) if (takeout_dir / root).exists() else []
        if files:
            print(f"Found {len(files)} monthly files under: {root}")
            return files

    # Fallback: search the whole Takeout tree
    files = sorted(takeout_dir.rglob("Semantic Location History/**/*.json"))
    if files:
        print(f"Found {len(files)} files via recursive search")
        return files

    return []


def parse_takeout(takeout_dir: Path):
    files = find_semantic_history_files(takeout_dir)
    if not files:
        print(
            "\nNo Semantic Location History files found."
            "\nExpected path like:"
            "\n  Takeout/Location History (Timeline)/Semantic Location History/2023/2023_JANUARY.json"
            "\n\nMake sure you extracted the full Takeout zip and are passing the"
            "\npath to the top-level 'Takeout' directory."
        )
        sys.exit(1)

    # country_name -> {lat, lon, visit_count}
    countries: dict[str, dict] = defaultdict(lambda: {"lat": None, "lon": None, "count": 0})
    # "city|country" -> {lat, lon, country, visit_count}
    cities: dict[str, dict] = defaultdict(lambda: {"lat": None, "lon": None, "country": None, "count": 0})

    skipped = 0
    processed = 0

    for filepath in files:
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(f"  Warning: skipping {filepath.name} ({exc})")
            continue

        for obj in data.get("timelineObjects", []):
            if "placeVisit" not in obj:
                continue

            visit = obj["placeVisit"]
            location = visit.get("location", {})
            duration = visit.get("duration", {})
            confidence = visit.get("visitConfidence", 0)

            if confidence < MIN_CONFIDENCE:
                skipped += 1
                continue

            hours = visit_duration_hours(duration)
            if hours < MIN_VISIT_HOURS:
                skipped += 1
                continue

            address = location.get("address", "")
            lat_e7 = location.get("latitudeE7")
            lon_e7 = location.get("longitudeE7")
            lat = round(lat_e7 / 1e7, 4) if lat_e7 is not None else None
            lon = round(lon_e7 / 1e7, 4) if lon_e7 is not None else None

            country = extract_country(address)
            if not country:
                skipped += 1
                continue

            processed += 1

            # Country record
            rec = countries[country]
            if rec["lat"] is None and lat is not None:
                rec["lat"] = lat
                rec["lon"] = lon
            rec["count"] += 1

            # City record (key = "city|country" to disambiguate same-name cities)
            city = extract_city(location, address)
            if city:
                key = f"{city}|{country}"
                crec = cities[key]
                if crec["lat"] is None and lat is not None:
                    crec["lat"] = lat
                    crec["lon"] = lon
                    crec["country"] = country
                crec["count"] += 1

    print(f"  Processed {processed} qualifying visits, skipped {skipped} (low confidence / short duration)")
    return countries, cities


def write_yaml(path: Path, data: list, header_lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for line in header_lines:
            f.write(f"# {line}\n")
        f.write("\n")
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"  → {path}  ({len(data)} entries)")


def build_countries_output(countries: dict) -> list:
    sorted_entries = sorted(countries.items(), key=lambda x: (-x[1]["count"], x[0]))
    out = []
    for name, info in sorted_entries:
        entry = {"name": name}
        if info["lat"] is not None:
            entry["lat"] = info["lat"]
            entry["lon"] = info["lon"]
        out.append(entry)
    return out


def build_cities_output(cities: dict, min_visits: int = 1) -> list:
    """
    Returns cities sorted by visit count. Includes all entries with >= min_visits.
    The resulting file is meant to be reviewed and pruned — it will contain noise.
    """
    sorted_entries = sorted(cities.items(), key=lambda x: (-x[1]["count"], x[0]))
    out = []
    for key, info in sorted_entries:
        if info["count"] < min_visits:
            continue
        name = key.split("|")[0]
        entry = {"name": name, "country": info["country"]}
        if info["lat"] is not None:
            entry["lat"] = info["lat"]
            entry["lon"] = info["lon"]
        out.append(entry)
    return out


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} /path/to/Takeout")
        sys.exit(1)

    takeout_dir = Path(sys.argv[1]).expanduser().resolve()
    if not takeout_dir.is_dir():
        print(f"Error: '{takeout_dir}' is not a directory")
        sys.exit(1)

    repo_root = Path(__file__).parent.parent
    countries_out = repo_root / "_data" / "travel-countries.yml"
    cities_out = repo_root / "_data" / "travel-cities.yml"

    print(f"Parsing Takeout from: {takeout_dir}\n")
    countries, cities = parse_takeout(takeout_dir)

    print(f"\nResults: {len(countries)} countries, {len(cities)} unique places\n")

    write_yaml(
        countries_out,
        build_countries_output(countries),
        [
            "Auto-generated by scripts/parse_takeout.py",
            "Countries visited (from Google Takeout Location History)",
            "Regenerate: python scripts/parse_takeout.py /path/to/Takeout",
        ],
    )

    write_yaml(
        cities_out,
        build_cities_output(cities),
        [
            "Auto-generated by scripts/parse_takeout.py",
            "Candidate cities/places visited — REVIEW AND PRUNE before committing.",
            "This file contains noise: restaurants, offices, transit stops, etc.",
            "Delete any entry that isn't a meaningful destination.",
            "Regenerate: python scripts/parse_takeout.py /path/to/Takeout",
        ],
    )

    print(
        "\nDone."
        "\n  travel-countries.yml is reliable — commit as-is."
        "\n  travel-cities.yml needs review — remove entries that aren't real destinations."
    )


if __name__ == "__main__":
    main()
