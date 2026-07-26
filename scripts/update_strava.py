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

import argparse
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

# Backfilled rides from Apple Health (see scripts/parse_apple_health.py). These
# cover periods that never reached Strava, so they are merged with the API
# results on every run rather than written into the output files once — a run
# that only wrote API data would otherwise erase them.
HEALTH_RIDES_PATH = REPO_ROOT / "_data" / "health_rides.json"

# Two records describe the same ride if they start within this many minutes of
# each other and their distances agree within the tolerance below. Matching on
# start time (not date) matters: a commute produces two rides on the same day,
# and collapsing them by date would silently halve the count.
DEDUPE_MINUTES = 25
DEDUPE_DISTANCE_RATIO = 0.25


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


def _start_dt(a: dict) -> datetime | None:
    """Local start time, for duplicate detection."""
    raw = (a.get("start_date_local") or a.get("start_date") or "").strip()
    if not raw:
        return None
    cleaned = raw.replace("Z", "")
    try:
        return datetime.fromisoformat(cleaned).replace(tzinfo=None)
    except ValueError:
        return None


def load_health_rides() -> list[dict]:
    """Backfilled Apple Health rides, already in Strava's activity shape."""
    if not HEALTH_RIDES_PATH.exists():
        return []
    try:
        data = json.loads(HEALTH_RIDES_PATH.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARNING: could not read {HEALTH_RIDES_PATH.name} ({e}); ignoring backfill")
        return []
    if not isinstance(data, list):
        print(f"WARNING: {HEALTH_RIDES_PATH.name} is not a list; ignoring backfill")
        return []
    return data


def _is_duplicate(candidate: dict, existing: list[dict]) -> bool:
    """True if `candidate` looks like a ride already present in `existing`."""
    cand_dt = _start_dt(candidate)
    cand_km = _distance_km(candidate)
    if cand_dt is None:
        return False
    for other in existing:
        other_dt = _start_dt(other)
        if other_dt is None:
            continue
        if abs((cand_dt - other_dt).total_seconds()) > DEDUPE_MINUTES * 60:
            continue
        other_km = _distance_km(other)
        # Distances rarely match exactly: Health and Strava disagree slightly on
        # GPS smoothing and auto-pause. Compare proportionally, and treat two
        # zero-distance records at the same time as the same ride.
        if max(cand_km, other_km) == 0:
            return True
        if abs(cand_km - other_km) / max(cand_km, other_km) <= DEDUPE_DISTANCE_RATIO:
            return True
    return False


def merge_with_backfill(api_rides: list[dict]) -> tuple[list[dict], int, int]:
    """Combine Strava rides with the Health backfill.

    Strava wins on conflicts: its records carry richer fields (speed, commute
    flag, names) and are what "View on Strava" links to. Returns
    (merged, added, skipped_as_duplicate).
    """
    health = [r for r in load_health_rides() if _is_ride(r)]
    if not health:
        return api_rides, 0, 0

    merged = list(api_rides)
    added = skipped = 0
    for rec in health:
        if _is_duplicate(rec, merged):
            skipped += 1
            continue
        merged.append(rec)
        added += 1
    return merged, added, skipped


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

    # Which sources actually contributed, so the page can credit them accurately
    # instead of inferring it from arithmetic that deduping would skew.
    by_source: defaultdict[str, int] = defaultdict(int)
    for a in rides:
        by_source[a.get("source") or "strava"] += 1

    return {
        "total_rides": len(rides),
        "ride_sources": dict(sorted(by_source.items())),
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


def months_covered(rides: list[dict]) -> set[str]:
    return {_local_date(a)[:7] for a in rides if _local_date(a)}


def check_month_coverage(rides: list[dict]) -> list[str]:
    """Months that the previous dataset covered but the new one doesn't.

    Guards the Strava-to-Apple-Health switchover: if Health is missing a period
    that Strava had, rebuilding would quietly erase those rides from the site.
    """
    existing = load_existing_stats()
    previous = {m["month"] for m in existing.get("monthly", []) if m.get("month")}
    return sorted(previous - months_covered(rides))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true",
                    help="skip the Strava API and build purely from _data/health_rides.json")
    ap.add_argument("--force", action="store_true",
                    help="write even if the new data drops months the old data covered")
    args = ap.parse_args()

    if args.offline:
        # Strava's API needs a paid Developer Program subscription as of
        # 30 June 2026; this path keeps the cycling page working without it.
        print("Offline mode: building from the Apple Health backfill only.")
        api_rides: list[dict] = []
    else:
        for var in ("STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET", "STRAVA_REFRESH_TOKEN"):
            if not os.environ.get(var):
                print(f"Error: environment variable {var} is not set")
                sys.exit(1)

        print("Refreshing Strava access token...")
        token = get_access_token()

        print("Fetching all activities...")
        activities = fetch_all_activities(token)
        api_rides = [a for a in activities if _is_ride(a)]
        print(f"Found {len(api_rides)} cycling activities out of {len(activities)} total")

    # Merge before the guard below, not after: once the backfill is in place the
    # published total includes it, so comparing an API-only count against that
    # total would look like a collapse on every single run.
    rides, added, dupes = merge_with_backfill(api_rides)
    if added or dupes:
        print(f"Apple Health backfill: +{added} rides, {dupes} already in Strava "
              f"→ {len(rides)} total")

    # Two regression guards, both skipped by --force. Whether declining to write
    # is an error depends on why we ran:
    #
    #   * A scheduled API poll can preserve and exit 0 — tomorrow's run fixes a
    #     transient truncation, and failing daily would be noise.
    #   * An --offline rebuild runs because the backfill just changed, so the
    #     caller is waiting for a specific update. Silently doing nothing there
    #     would report success while the site stayed stale, so it exits non-zero
    #     and lets the workflow raise an issue.
    def refuse(lines: list[str]) -> None:
        for line in lines:
            print(line)
        if args.offline:
            sys.exit(1)

    if not args.force:
        # Month-level check first: it is the more specific, more actionable
        # signal, and a source switch can keep the total healthy while losing a
        # particular stretch.
        lost_months = check_month_coverage(rides)
        if lost_months:
            refuse([
                f"\nDeclining to write: {len(lost_months)} month(s) in the current data "
                "have no rides in the new dataset:",
                f"  {', '.join(lost_months)}",
                "Those rides are probably in Strava but outside the Apple Health export.",
                "Check the export reaches back far enough, or pass --force to accept the loss.",
            ])
            return

        # Ride history is append-only in practice, so a sharp drop in the total
        # means an incomplete fetch rather than real data. Loose rather than
        # "any decrease" so deleting one stray ride can't wedge the pipeline.
        previous_rides = load_existing_stats().get("total_rides", 0)
        if previous_rides > 0 and len(rides) < previous_rides * RIDE_COUNT_DROP_TOLERANCE:
            refuse([
                f"Only {len(rides)} rides available vs {previous_rides} previously — "
                "treating as incomplete and preserving the existing data files.",
            ])
            return
    elif check_month_coverage(rides):
        print(f"WARNING (--force): dropping months {', '.join(check_month_coverage(rides))}")

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
