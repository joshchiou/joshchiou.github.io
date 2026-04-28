#!/usr/bin/env python3
"""
Fetch Strava activity data and write _data/strava_calendar.json and _data/strava_stats.json.

Run manually:
    STRAVA_CLIENT_ID=... STRAVA_CLIENT_SECRET=... STRAVA_REFRESH_TOKEN=... \
        python scripts/update_strava.py

Or triggered automatically by .github/workflows/update-strava.yml.

Requirements: pip install requests
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide"}
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
REPO_ROOT = Path(__file__).parent.parent
ASSETS_DATA_DIR = REPO_ROOT / "assets" / "data"


def get_access_token() -> str:
    resp = requests.post(TOKEN_URL, data={
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }, timeout=30)
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_all_activities(token: str) -> list[dict]:
    activities = []
    page = 1
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        resp = requests.get(
            ACTIVITIES_URL,
            headers=headers,
            params={"per_page": 200, "page": page},
            timeout=60,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        activities.extend(batch)
        page += 1
        print(f"  Fetched page {page - 1}: {len(batch)} activities (total: {len(activities)})")
    return activities


def compute_calendar_data(rides: list[dict]) -> list[list]:
    """Returns [[date_str, distance_km], ...] for ECharts calendar heatmap."""
    daily: defaultdict[str, float] = defaultdict(float)
    for a in rides:
        daily[a["start_date_local"][:10]] += a["distance"] / 1000
    return [[date, round(val, 2)] for date, val in sorted(daily.items())]


def compute_stats(rides: list[dict]) -> dict:
    """Returns all-time aggregate stats and monthly distance breakdown."""
    total_distance_km = round(sum(a["distance"] for a in rides) / 1000, 1)
    total_elevation_m = round(sum(a["total_elevation_gain"] for a in rides))

    monthly: defaultdict[str, float] = defaultdict(float)
    for a in rides:
        monthly[a["start_date_local"][:7]] += a["distance"] / 1000

    monthly_list = [
        {"month": k, "distance_km": round(v, 1)}
        for k, v in sorted(monthly.items())
    ]

    return {
        "total_rides": len(rides),
        "total_distance_km": total_distance_km,
        "total_elevation_m": total_elevation_m,
        "monthly": monthly_list,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


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
    rides = [a for a in activities if a.get("type") in RIDE_TYPES]
    print(f"Found {len(rides)} cycling activities out of {len(activities)} total")

    calendar_data = compute_calendar_data(rides)
    stats = compute_stats(rides)

    data_dir = REPO_ROOT / "_data"
    write_json(data_dir / "strava_calendar.json", calendar_data)
    write_json(data_dir / "strava_stats.json", stats)

    ASSETS_DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_json(ASSETS_DATA_DIR / "strava_calendar.json", calendar_data)

    print(f"\nDone. {stats['total_rides']} rides · "
          f"{stats['total_distance_km']} km · "
          f"{stats['total_elevation_m']} m elevation")


if __name__ == "__main__":
    main()
