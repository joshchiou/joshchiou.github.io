#!/usr/bin/env python3
"""
Fetch Strava activity data and write _data/strava_calendar.json and _data/strava_stats.json.

Run manually:
    STRAVA_CLIENT_ID=... STRAVA_CLIENT_SECRET=... STRAVA_REFRESH_TOKEN=... \
        python scripts/update_strava.py

Or triggered automatically by .github/workflows/update-strava.yml.

Resilience: requests retry with backoff on rate limits (429) and transient 5xx
errors, activity fields are read defensively so a schema change can't crash the
run, and existing data files are preserved if a fetch yields no rides (rather
than overwriting good data with an empty result).

Requirements: pip install requests
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import requests  # noqa: F401  (used indirectly via _http)
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

from _http import request_with_retry

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide", "GravelRide", "MountainBikeRide"}
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
REPO_ROOT = Path(__file__).parent.parent

MAX_PAGES = 100  # safety valve against a pagination loop (200/page = 20k activities)

# Preserve existing data if a fetch returns fewer than this fraction of the
# previously recorded rides (see the guard in main()).
RIDE_COUNT_DROP_TOLERANCE = 0.8


def get_access_token() -> str:
    resp = request_with_retry("POST", TOKEN_URL, data={
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }, timeout=30)
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError("Strava token response did not contain an access_token")
    return token


def fetch_all_activities(token: str) -> list[dict]:
    activities = []
    page = 1
    headers = {"Authorization": f"Bearer {token}"}
    while page <= MAX_PAGES:
        resp = request_with_retry(
            "GET",
            ACTIVITIES_URL,
            headers=headers,
            params={"per_page": 200, "page": page},
            timeout=60,
        )
        batch = resp.json()
        if not isinstance(batch, list) or not batch:
            break
        activities.extend(batch)
        print(f"  Fetched page {page}: {len(batch)} activities (total: {len(activities)})")
        if len(batch) < 200:
            break
        page += 1
    return activities


def _distance_km(a: dict) -> float:
    return (a.get("distance") or 0) / 1000


def _is_ride(a: dict) -> bool:
    # Strava added sport_type alongside the legacy type field; check both.
    return a.get("sport_type") in RIDE_TYPES or a.get("type") in RIDE_TYPES


def _local_date(a: dict) -> str:
    # Fall back to start_date (UTC) if the local variant is missing.
    return (a.get("start_date_local") or a.get("start_date") or "")[:10]


def compute_calendar_data(rides: list[dict]) -> list[list]:
    """Returns [[date_str, distance_km], ...] for ECharts calendar heatmap."""
    daily: defaultdict[str, float] = defaultdict(float)
    for a in rides:
        date = _local_date(a)
        if date:
            daily[date] += _distance_km(a)
    return [[date, round(val, 2)] for date, val in sorted(daily.items())]


def compute_stats(rides: list[dict]) -> dict:
    """Returns all-time aggregate stats and monthly distance breakdown."""
    total_distance_km = round(sum(_distance_km(a) for a in rides), 1)
    total_elevation_m = round(sum(a.get("total_elevation_gain") or 0 for a in rides))

    distances_km = [_distance_km(a) for a in rides]
    longest_ride_km = round(max(distances_km), 1) if distances_km else 0
    avg_ride_km = round(sum(distances_km) / len(distances_km), 1) if distances_km else 0

    monthly: defaultdict[str, float] = defaultdict(float)
    for a in rides:
        date = _local_date(a)
        if date:
            monthly[date[:7]] += _distance_km(a)

    monthly_list = [
        {"month": k, "distance_km": round(v, 1)}
        for k, v in sorted(monthly.items())
    ]

    return {
        "total_rides": len(rides),
        "total_distance_km": total_distance_km,
        "total_elevation_m": total_elevation_m,
        "longest_ride_km": longest_ride_km,
        "avg_ride_km": avg_ride_km,
        "monthly": monthly_list,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def compute_ride_log(rides: list[dict], limit: int = 15) -> list[dict]:
    """Returns the most recent rides with name, distance, elevation, speed."""
    sorted_rides = sorted(rides, key=_local_date, reverse=True)
    log = []
    for a in sorted_rides[:limit]:
        entry = {
            "date": _local_date(a),
            "name": a.get("name", "Ride"),
            "distance_km": round(_distance_km(a), 1),
            "elevation_m": round(a.get("total_elevation_gain") or 0),
            "moving_time_min": round((a.get("moving_time") or 0) / 60),
        }
        if (a.get("average_speed") or 0) > 0:
            entry["avg_speed_kmh"] = round(a["average_speed"] * 3.6, 1)
        if a.get("commute"):
            entry["type"] = "commute"
        log.append(entry)
    return log


def load_existing_stats() -> dict:
    path = REPO_ROOT / "_data" / "strava_stats.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def write_json(path: Path, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"  → {path}")


def main() -> None:
    for var in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN"):
        if not os.environ.get(var):
            print(f"Error: environment variable {var} is not set")
            sys.exit(1)

    print("Refreshing Strava access token...")
    token = get_access_token()

    print("Fetching all activities...")
    activities = fetch_all_activities(token)
    rides = [a for a in activities if _is_ride(a)]
    print(f"Found {len(rides)} cycling activities out of {len(activities)} total")

    # Last-known-good guard. Ride history is append-only in practice, so a
    # sharp drop in ride count means a truncated/failed fetch (auth hiccup,
    # pagination cut short, schema change) rather than real data. Preserve the
    # existing files in that case instead of publishing a regression.
    #
    # The threshold is deliberately loose rather than "any decrease" so that
    # deleting a stray ride doesn't wedge the pipeline permanently.
    previous_rides = load_existing_stats().get("total_rides", 0)
    if previous_rides > 0 and len(rides) < previous_rides * RIDE_COUNT_DROP_TOLERANCE:
        print(f"Only {len(rides)} rides returned vs {previous_rides} previously — "
              "treating as an incomplete fetch and preserving existing data files.")
        return
    if not rides:
        print("No rides returned and no existing data — writing empty datasets.")

    calendar_data = compute_calendar_data(rides)
    stats = compute_stats(rides)
    ride_log = compute_ride_log(rides)

    data_dir = REPO_ROOT / "_data"
    write_json(data_dir / "strava_calendar.json", calendar_data)
    write_json(data_dir / "strava_stats.json", stats)
    write_json(data_dir / "strava_rides.json", ride_log)

    print(f"\nDone. {stats['total_rides']} rides · "
          f"{stats['total_distance_km']} km · "
          f"{stats['total_elevation_m']} m elevation")


if __name__ == "__main__":
    main()
