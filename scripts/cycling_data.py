#!/usr/bin/env python3
"""Maintain the cycling page data from Apple Health.

Strava's API became paid in June 2026, so rides now come from Apple Health (D-018). Rides up to
2026-06-21 stay in a frozen Strava archive; newer rides live in _data/cycling_rides.json. Every
command rebuilds the files the cycling page reads (_data/cycling_stats.json and
_data/cycling_calendar.json) from the archive plus the ride list.

Commands:
    import-health EXPORT.zip [--dry-run]
        Read cycling workouts from an Apple Health export ("Export All Health Data" in the
        Health app) and merge the ones after the archive into the ride list. Rides already
        listed are matched and updated, so the export fills in elevation for rides the
        Shortcut added. Accepts the .zip or the export.xml inside it.
    add-shortcut
        Add one ride posted by the iPhone Shortcut. Reads JSON from the PAYLOAD environment
        variable: {"start": ISO 8601, "end": ISO 8601, "distance": number, "unit": "mi"|"km"}.
        Used by .github/workflows/add-ride.yml.
    rebuild
        Regenerate the page data from the archive and the ride list.
"""

import argparse
import json
import os
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree

DATA = Path(__file__).resolve().parent.parent / "_data"
ARCHIVE = DATA / "cycling_strava_archive.json"
RIDES = DATA / "cycling_rides.json"
STATS = DATA / "cycling_stats.json"
CALENDAR = DATA / "cycling_calendar.json"

CYCLING = "HKWorkoutActivityTypeCycling"
DISTANCE = "HKQuantityTypeIdentifierDistanceCycling"
TO_KM = {"km": 1.0, "mi": 1.609344, "m": 0.001, "ft": 0.0003048, "yd": 0.0009144}
TO_M = {"m": 1.0, "cm": 0.01, "km": 1000.0, "ft": 0.3048, "mi": 1609.344}
TO_MIN = {"min": 1.0, "s": 1 / 60, "hr": 60.0, "h": 60.0}


def load(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=1) + "\n")
    print(f"  wrote {path.name}")


# ---------------------------------------------------------------- matching


def same_ride(a: dict, b: dict) -> bool:
    """Rides are stored without start times (the repo is public), so match on date, distance,
    and duration. Two rides on one day differ in distance or duration in practice."""
    return (
        a["date"] == b["date"]
        and abs(a["distance_km"] - b["distance_km"]) <= max(0.3, 0.03 * b["distance_km"])
        and abs(a["moving_time_min"] - b["moving_time_min"]) <= 3
    )


def merge(rides: list[dict], new: dict) -> str:
    for i, ride in enumerate(rides):
        if same_ride(ride, new):
            if new.get("elevation_m") is None and ride.get("elevation_m") is not None:
                return "unchanged"
            if ride == new:
                return "unchanged"
            rides[i] = new
            return "updated"
    rides.append(new)
    return "added"


# ---------------------------------------------------------------- Apple Health export


def open_export(path: Path):
    if path.suffix == ".zip":
        z = zipfile.ZipFile(path)
        name = next(n for n in z.namelist() if n.endswith("/export.xml") or n == "export.xml")
        return z.open(name)
    return open(path, "rb")


def quantity(value: str | None, unit: str | None, table: dict) -> float | None:
    if value is None:
        return None
    if unit is None:  # metadata values look like "4520 cm"
        value, _, unit = value.partition(" ")
    factor = table.get(unit.strip())
    return float(value) * factor if factor is not None else None


def health_rides(path: Path) -> list[dict]:
    rides = []
    with open_export(path) as f:
        for _, el in ElementTree.iterparse(f, events=("end",)):
            if el.tag != "Workout":
                if el.tag == "Record":
                    el.clear()  # records are most of the file; drop them as we go
                continue
            if el.get("workoutActivityType") == CYCLING:
                km = quantity(el.get("totalDistance"), el.get("totalDistanceUnit"), TO_KM)
                elevation = None
                for child in el:
                    if child.tag == "WorkoutStatistics" and child.get("type") == DISTANCE:
                        km = quantity(child.get("sum"), child.get("unit"), TO_KM)
                    elif child.tag == "MetadataEntry" and child.get("key") == "HKElevationAscended":
                        elevation = quantity(child.get("value"), None, TO_M)
                minutes = quantity(el.get("duration"), el.get("durationUnit", "min"), TO_MIN)
                if km and minutes:
                    rides.append(ride_record(el.get("startDate")[:10], km, minutes, elevation, "apple_health"))
            el.clear()
    return rides


def ride_record(date: str, km: float, minutes: float, elevation_m: float | None, source: str) -> dict:
    return {
        "date": date,
        "distance_km": round(km, 2),
        "moving_time_min": round(minutes),
        "elevation_m": None if elevation_m is None else round(elevation_m),
        "source": source,
    }


# ---------------------------------------------------------------- Shortcut payload


def shortcut_ride(payload: dict) -> dict:
    try:
        start = datetime.fromisoformat(str(payload["start"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(payload["end"]).replace("Z", "+00:00"))
        distance = float(payload["distance"])
        unit = str(payload.get("unit", "mi")).strip().lower()
    except (KeyError, ValueError, TypeError) as exc:
        sys.exit(f"Bad payload {payload!r}: {exc}")
    if unit not in ("mi", "km"):
        sys.exit(f"Bad unit {unit!r}; expected mi or km")
    km = distance * TO_KM[unit]
    minutes = (end - start).total_seconds() / 60
    if not 0 < km < 500:
        sys.exit(f"Distance {km:.1f} km is out of range")
    if not 0 < minutes < 24 * 60:
        sys.exit(f"Duration {minutes:.0f} min is out of range")
    if start.date() > datetime.now(timezone.utc).date() + timedelta(days=1):
        sys.exit("Ride starts in the future")
    # The date part of the Shortcut's ISO string is the local date of the ride.
    return ride_record(str(payload["start"])[:10], km, minutes, None, "shortcut")


# ---------------------------------------------------------------- page data


def rebuild() -> None:
    archive = load(ARCHIVE, None)
    if archive is None:
        sys.exit(f"{ARCHIVE.name} is missing")
    rides = sorted(load(RIDES, []), key=lambda r: r["date"])

    daily: defaultdict[str, float] = defaultdict(float)
    monthly: defaultdict[str, float] = defaultdict(float)
    for date, km in archive["calendar"]:
        daily[date] += km
    for m in archive["monthly"]:
        monthly[m["month"]] += m["distance_km"]
    for r in rides:
        daily[r["date"]] += r["distance_km"]
        monthly[r["date"][:7]] += r["distance_km"]

    distances = [r["distance_km"] for r in rides]
    total_rides = archive["total_rides"] + len(rides)
    total_km = archive["total_distance_km"] + sum(distances)
    stats = {
        "total_rides": total_rides,
        "total_distance_km": round(total_km, 1),
        "total_elevation_m": round(archive["total_elevation_m"] + sum(r["elevation_m"] or 0 for r in rides)),
        "longest_ride_km": round(max([archive["longest_ride_km"], *distances]), 1),
        "avg_ride_km": round(total_km / total_rides, 1) if total_rides else 0,
        "monthly": [{"month": k, "distance_km": round(v, 1)} for k, v in sorted(monthly.items())],
        "rides_missing_elevation": sum(1 for r in rides if r["elevation_m"] is None),
        "last_ride": rides[-1]["date"] if rides else archive["through"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    write(STATS, stats)
    write(CALENDAR, [[d, round(v, 2)] for d, v in sorted(daily.items())])


# ---------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    imp = sub.add_parser("import-health", help="merge rides from an Apple Health export")
    imp.add_argument("export", type=Path)
    imp.add_argument("--dry-run", action="store_true")
    sub.add_parser("add-shortcut", help="add the ride in $PAYLOAD")
    sub.add_parser("rebuild", help="regenerate the page data")
    args = parser.parse_args()

    if args.command == "rebuild":
        return rebuild()

    archive = load(ARCHIVE, None)
    if archive is None:
        sys.exit(f"{ARCHIVE.name} is missing")
    rides = load(RIDES, [])

    if args.command == "add-shortcut":
        ride = shortcut_ride(json.loads(os.environ.get("PAYLOAD") or "{}"))
        if ride["date"] <= archive["through"]:
            sys.exit(f"Ride on {ride['date']} is inside the Strava archive (through {archive['through']})")
        print(f"{merge(rides, ride)}: {ride}")
    else:
        found = health_rides(args.export)
        new = [r for r in found if r["date"] > archive["through"]]
        print(f"Export has {len(found)} cycling workouts; {len(new)} after {archive['through']}")
        counts: defaultdict[str, int] = defaultdict(int)
        for ride in new:
            counts[merge(rides, ride)] += 1
        print("  " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())) if counts else "  nothing new")
        if args.dry_run:
            return

    rides.sort(key=lambda r: (r["date"], r["distance_km"]))
    write(RIDES, rides)
    rebuild()


if __name__ == "__main__":
    main()
