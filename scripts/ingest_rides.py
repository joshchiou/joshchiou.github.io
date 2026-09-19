#!/usr/bin/env python3
"""Merge rides posted from a phone into _data/health_rides.json.

Apple Health has no cloud API, so nothing can pull from it — the phone has to
push. This is the receiving end: it takes a JSON payload of recent cycling
workouts, normalises it, and merges it into the backfill file using the same
duplicate detection the Strava pipeline uses. Re-posting the same rides is
therefore harmless, which matters because a phone automation will happily fire
twice.

Deliberately agnostic about what sent the payload, so switching between a plain
Shortcut, Health Exporter & Shortcuts, or Health Auto Export needs no change
here.

Canonical shape — the one to build in a Shortcut:

    {"rides": [
      {"start": "2026-07-26T08:10:00", "distance_km": 14.5,
       "elevation_m": 120, "duration_min": 45, "indoor": false}
    ]}

Also accepted: a bare top-level array, and Health Auto Export's
{"data": {"workouts": [...]}} with its {"qty": .., "units": ".."} measurements.

Usage:
    python3 scripts/ingest_rides.py --payload-env RIDES_PAYLOAD
    python3 scripts/ingest_rides.py --payload-file rides.json
    echo '{"rides": [...]}' | python3 scripts/ingest_rides.py
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parse_apple_health import parse_health_datetime  # noqa: E402
from update_strava import _is_duplicate, _is_ride  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
HEALTH_RIDES_PATH = REPO_ROOT / "_data" / "health_rides.json"

MI_TO_KM = 1.609344
# Matches parse_apple_health: ignore sub-kilometre auto-detected blips.
MIN_KM = 1.0

# Only cycling belongs on the cycling page. Compared case-insensitively against
# whatever the sender calls the activity.
CYCLING_NAMES = {
    "cycling", "ride", "bike", "biking", "outdoor cycle", "indoor cycle",
    "cycling (outdoor)", "cycling (indoor)", "hkworkoutactivitytypecycling",
    "handcycling", "hkworkoutactivitytypehandcycling", "virtualride",
    "gravelride", "mountainbikeride", "ebikeride",
}


def _qty(value, default_units: str, to_units: str) -> float | None:
    """Read a number that may be bare or a {"qty": .., "units": ".."} object."""
    units = default_units
    if isinstance(value, dict):
        units = (value.get("units") or value.get("unit") or default_units)
        value = value.get("qty", value.get("sum", value.get("value")))
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None

    u = str(units).strip().lower()
    if to_units == "km":
        if u in ("mi", "mile", "miles"):
            return num * MI_TO_KM
        if u in ("m", "meter", "meters", "metre", "metres"):
            return num / 1000
        return num  # km
    if to_units == "m":
        if u in ("cm",):
            return num / 100
        if u in ("ft", "feet", "foot"):
            return num * 0.3048
        if u in ("km",):
            return num * 1000
        return num  # m
    if to_units == "min":
        if u in ("s", "sec", "secs", "second", "seconds"):
            return num / 60
        if u in ("h", "hr", "hrs", "hour", "hours"):
            return num * 60
        return num  # min
    return num


def _first(d: dict, *keys):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return None


def _is_cycling(raw: dict) -> bool:
    """Whether this workout belongs on the cycling page.

    A record with no activity type at all is taken to be a ride: the canonical
    payload omits the field, and the sender is a ride-specific automation. Only
    an explicitly non-cycling type (a run smuggled in by a whole-Health export)
    is rejected.
    """
    name = _first(raw, "type", "sport_type", "workoutActivityType", "name", "activity")
    if name is None:
        return True
    return str(name).strip().lower() in CYCLING_NAMES


def normalise(raw: dict) -> dict | None:
    """Convert one posted workout into a Strava-shaped record, or None."""
    if not isinstance(raw, dict) or not _is_cycling(raw):
        return None

    start_raw = _first(raw, "start", "startDate", "start_date_local", "start_date", "date")
    start = parse_health_datetime(str(start_raw)) if start_raw else None
    if start is None:
        return None

    km = _qty(_first(raw, "distance_km", "distanceKm", "distance", "totalDistance"), "km", "km")
    if km is None or km < MIN_KM:
        return None

    elevation = _qty(
        _first(raw, "elevation_m", "elevationUp", "elevation", "total_elevation_gain"), "m", "m"
    ) or 0.0
    minutes = _qty(_first(raw, "duration_min", "duration", "moving_time_min"), "min", "min") or 0.0

    indoor = bool(raw.get("indoor") or raw.get("isIndoor"))
    if "indoor" in str(_first(raw, "type", "name", "activity") or "").lower():
        indoor = True

    return {
        "type": "VirtualRide" if indoor else "Ride",
        "sport_type": "VirtualRide" if indoor else "Ride",
        "name": "Indoor Ride" if indoor else "Ride",
        "distance": round(km * 1000, 1),
        "total_elevation_gain": round(elevation, 1),
        "moving_time": int(round(minutes * 60)),
        "start_date_local": start.strftime("%Y-%m-%dT%H:%M:%S"),
        # Same provenance as the bulk export: the data really is Apple Health,
        # only the delivery differs. Keeps the page's source credit correct.
        "source": "apple_health",
    }


def extract_rides(payload) -> list[dict]:
    """Pull the workout list out of whichever envelope the sender used."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if not isinstance(payload, dict):
        return []
    for path in (("rides",), ("workouts",), ("data", "workouts"), ("data", "rides")):
        node = payload
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                break
        if isinstance(node, list):
            return [r for r in node if isinstance(r, dict)]
    return []


def load_existing() -> list[dict]:
    if not HEALTH_RIDES_PATH.exists():
        return []
    try:
        data = json.loads(HEALTH_RIDES_PATH.read_text())
    except (json.JSONDecodeError, OSError) as e:
        sys.exit(f"Refusing to run: {HEALTH_RIDES_PATH.name} is unreadable ({e}). "
                 "Fix or delete it before ingesting, so a bad file isn't silently replaced.")
    return data if isinstance(data, list) else []


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--payload-env", metavar="VAR",
                     help="read the JSON payload from this environment variable")
    src.add_argument("--payload-file", metavar="PATH", help="read the JSON payload from a file")
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    args = ap.parse_args()

    if args.payload_env:
        # Read via the environment rather than interpolating into a shell
        # command: the payload is attacker-controlled if the phone's token ever
        # leaks, and must never reach a shell.
        text = os.environ.get(args.payload_env, "")
        if not text.strip():
            sys.exit(f"Environment variable {args.payload_env} is empty")
    elif args.payload_file:
        text = Path(args.payload_file).read_text()
    else:
        text = sys.stdin.read()

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        sys.exit(f"Payload is not valid JSON: {e}")

    posted = extract_rides(payload)
    if not posted:
        print("Payload contained no workouts. Nothing to do.")
        return
    print(f"Payload contained {len(posted)} workout(s)")

    candidates = []
    skipped = 0
    for raw in posted:
        rec = normalise(raw)
        if rec is None:
            skipped += 1
            continue
        candidates.append(rec)
    if skipped:
        print(f"  {skipped} skipped (not cycling, too short, or no usable start/distance)")

    existing = load_existing()
    merged = list(existing)
    added = 0
    for rec in candidates:
        # Compare against everything accepted so far, so a payload containing
        # the same ride twice can't add it twice either.
        if _is_duplicate(rec, merged) or not _is_ride(rec):
            continue
        merged.append(rec)
        added += 1

    print(f"  {added} new, {len(candidates) - added} already recorded")
    if added == 0:
        print("Nothing new — leaving the file untouched.")
        return

    merged.sort(key=lambda r: r.get("start_date_local", ""))
    if args.dry_run:
        print(f"Dry run — would grow {HEALTH_RIDES_PATH.name} "
              f"from {len(existing)} to {len(merged)} rides.")
        return

    HEALTH_RIDES_PATH.write_text(json.dumps(merged, separators=(",", ":")) + "\n")
    print(f"Wrote {HEALTH_RIDES_PATH} ({len(existing)} -> {len(merged)} rides)")


if __name__ == "__main__":
    main()
