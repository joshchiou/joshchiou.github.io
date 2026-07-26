#!/usr/bin/env python3
"""Extract cycling workouts from an Apple Health export for site backfill.

Apple Health holds rides that never reached Strava. This reads the Health
export and writes _data/health_rides.json, which update_strava.py merges with
the Strava API results (deduplicating overlaps) so the site reflects the full
history rather than only what synced.

Getting the export: iPhone → Health app → profile picture → Export All Health
Data. That produces export.zip; hand it to this script directly.

    python3 scripts/parse_apple_health.py ~/Downloads/export.zip
    python3 scripts/parse_apple_health.py export.xml --dry-run
    python3 scripts/parse_apple_health.py export.zip --min-km 1.5

Records are emitted in Strava's activity shape so the existing stat, calendar
and ride-log functions consume them unchanged.

Notes on the format, which varies by iOS version:
  * Pre-iOS 16 puts distance on the Workout element (``totalDistance``).
  * iOS 16+ moved it into a ``<WorkoutStatistics>`` child.
  * Elevation lives in a ``HKElevationAscended`` MetadataEntry, in centimetres.
  * Distance/energy units may be mi or km depending on locale.
Both layouts and either unit are handled.

export.xml is routinely hundreds of MB, so it is streamed with iterparse and
elements are released as we go rather than building a full tree in memory.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "_data" / "health_rides.json"

# Health activity types that belong on the cycling page.
CYCLING_TYPES = {
    "HKWorkoutActivityTypeCycling",
    "HKWorkoutActivityTypeHandCycling",
}
DISTANCE_STAT = "HKQuantityTypeIdentifierDistanceCycling"

MI_TO_KM = 1.609344
# Ignore sub-kilometre blips: stray auto-detected "workouts" that would
# otherwise pollute ride counts and streaks.
DEFAULT_MIN_KM = 1.0


def _to_km(value: float, unit: str | None) -> float:
    u = (unit or "").strip().lower()
    if u in ("mi", "mile", "miles"):
        return value * MI_TO_KM
    if u in ("m", "meter", "meters"):
        return value / 1000
    # km, and anything unexpected: Health exports distance in km or mi only.
    return value


def _to_minutes(value: float, unit: str | None) -> float:
    u = (unit or "").strip().lower()
    if u in ("s", "sec", "secs", "second", "seconds"):
        return value / 60
    if u in ("h", "hr", "hour", "hours"):
        return value * 60
    return value  # min


def _float(text) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_health_datetime(raw: str | None) -> datetime | None:
    """Parse Apple's "2025-01-15 08:12:33 -0500" into a naive local datetime.

    The offset is the local offset at that moment, so dropping it leaves local
    wall-clock time — which is what Strava's start_date_local also represents,
    letting the two be compared directly when deduplicating.
    """
    if not raw:
        return None
    stamp = raw.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(stamp, fmt)
            return dt.replace(tzinfo=None)
        except ValueError:
            continue
    # Last resort: ISO-ish strings.
    try:
        return datetime.fromisoformat(stamp).replace(tzinfo=None)
    except ValueError:
        return None


def _elevation_m(workout: ET.Element) -> float:
    """HKElevationAscended, e.g. value="12345 cm" (occasionally bare metres)."""
    for meta in workout.findall("MetadataEntry"):
        if meta.get("key") != "HKElevationAscended":
            continue
        raw = (meta.get("value") or "").strip()
        parts = raw.split()
        val = _float(parts[0]) if parts else None
        if val is None:
            return 0.0
        unit = parts[1].lower() if len(parts) > 1 else "cm"
        if unit == "cm":
            return val / 100
        if unit in ("mm",):
            return val / 1000
        if unit in ("ft", "feet"):
            return val * 0.3048
        return val  # m
    return 0.0


def _is_indoor(workout: ET.Element) -> bool:
    for meta in workout.findall("MetadataEntry"):
        if meta.get("key") == "HKIndoorWorkout":
            return (meta.get("value") or "").strip() in ("1", "true", "YES")
    return False


def _distance_km(workout: ET.Element) -> float | None:
    """Distance from either export layout."""
    # Pre-iOS 16: attribute on the Workout element.
    val = _float(workout.get("totalDistance"))
    if val is not None and val > 0:
        return _to_km(val, workout.get("totalDistanceUnit"))

    # iOS 16+: a WorkoutStatistics child.
    for stat in workout.findall("WorkoutStatistics"):
        if stat.get("type") != DISTANCE_STAT:
            continue
        val = _float(stat.get("sum"))
        if val is not None and val > 0:
            return _to_km(val, stat.get("unit"))
    return None


def build_record(workout: ET.Element) -> dict | None:
    """Convert a Workout element into a Strava-shaped activity dict."""
    start = parse_health_datetime(workout.get("startDate"))
    if start is None:
        return None

    km = _distance_km(workout)
    if km is None:
        return None

    minutes = _to_minutes(_float(workout.get("duration")) or 0.0, workout.get("durationUnit"))
    indoor = _is_indoor(workout)

    return {
        # Strava field names, so downstream code needs no special cases.
        "type": "VirtualRide" if indoor else "Ride",
        "sport_type": "VirtualRide" if indoor else "Ride",
        "name": "Indoor Ride" if indoor else "Ride",
        "distance": round(km * 1000, 1),  # metres
        "total_elevation_gain": round(_elevation_m(workout), 1),
        "moving_time": int(round(minutes * 60)),
        "start_date_local": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": "apple_health",
    }


def iter_workouts(path: Path):
    """Yield Workout elements from export.zip or export.xml, streaming."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if n.endswith("export.xml")]
            if not names:
                sys.exit(f"No export.xml inside {path}. Contents: {zf.namelist()[:10]}")
            # Prefer the shortest path: apple_health_export/export.xml, not
            # .../export_cda.xml or a nested duplicate.
            name = sorted(names, key=len)[0]
            print(f"Reading {name} from {path.name}")
            with zf.open(name) as fh:
                yield from _iter_xml(fh)
    else:
        print(f"Reading {path}")
        with open(path, "rb") as fh:
            yield from _iter_xml(fh)


def _iter_xml(fh):
    for event, elem in ET.iterparse(fh, events=("end",)):
        if elem.tag == "Workout":
            yield elem
            # Free the element (and its children) now that it is consumed.
            elem.clear()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("export", help="path to export.zip or export.xml")
    ap.add_argument("--min-km", type=float, default=DEFAULT_MIN_KM,
                    help=f"skip rides shorter than this (default {DEFAULT_MIN_KM})")
    ap.add_argument("--dry-run", action="store_true", help="summarise without writing")
    args = ap.parse_args()

    path = Path(args.export).expanduser()
    if not path.exists():
        sys.exit(f"No such file: {path}")

    total_workouts = 0
    cycling = 0
    records: list[dict] = []
    skipped_short = 0
    skipped_nodata = 0

    for workout in iter_workouts(path):
        total_workouts += 1
        if workout.get("workoutActivityType") not in CYCLING_TYPES:
            continue
        cycling += 1
        rec = build_record(workout)
        if rec is None:
            skipped_nodata += 1
            continue
        if rec["distance"] / 1000 < args.min_km:
            skipped_short += 1
            continue
        records.append(rec)

    records.sort(key=lambda r: r["start_date_local"])

    print(f"\n{total_workouts} workouts in export; {cycling} cycling")
    print(f"  {len(records)} usable rides")
    if skipped_short:
        print(f"  {skipped_short} skipped (< {args.min_km} km)")
    if skipped_nodata:
        print(f"  {skipped_nodata} skipped (no distance recorded)")

    if not records:
        print("\nNothing to write.")
        return

    km = sum(r["distance"] for r in records) / 1000
    print(f"  {records[0]['start_date_local'][:10]} → {records[-1]['start_date_local'][:10]}, "
          f"{km:,.0f} km total")

    monthly: defaultdict[str, list] = defaultdict(list)
    for r in records:
        monthly[r["start_date_local"][:7]].append(r)
    print("\nPer-month coverage (sanity-check this against your memory):")
    for month in sorted(monthly):
        rides = monthly[month]
        month_km = sum(x["distance"] for x in rides) / 1000
        print(f"  {month}: {len(rides):3d} rides, {month_km:7.1f} km")

    if args.dry_run:
        print("\nDry run — nothing written.")
        return

    OUT_PATH.write_text(json.dumps(records, separators=(",", ":")) + "\n")
    print(f"\nWrote {len(records)} rides to {OUT_PATH}")
    print("Commit that file; update_strava.py merges it with the Strava API "
          "results and drops duplicates.")


if __name__ == "__main__":
    main()
