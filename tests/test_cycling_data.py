"""Tests for scripts/cycling_data.py: the Apple Health export reader, the Shortcut payload, the
merge rules, and the rebuilt page data."""

import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import cycling_data  # noqa: E402

# Trimmed from the structure of a real export.xml (iOS 17+): distance in WorkoutStatistics,
# elevation as metadata in centimeters, plus a running workout and a record to skip.
EXPORT = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE HealthData [
<!ELEMENT HealthData (ExportDate,Me,(Record|Workout)*)>
]>
<HealthData locale="en_US">
 <ExportDate value="2026-10-04 09:00:00 -0400"/>
 <Me HKCharacteristicTypeIdentifierDateOfBirth=""/>
 <Record type="HKQuantityTypeIdentifierDistanceCycling" unit="mi" value="1.2"
   startDate="2026-07-10 08:00:00 -0400" endDate="2026-07-10 08:05:00 -0400"/>
 <Workout workoutActivityType="HKWorkoutActivityTypeCycling" duration="42.5" durationUnit="min"
   sourceName="Apple Watch" startDate="2026-07-10 08:00:00 -0400" endDate="2026-07-10 08:42:30 -0400">
  <MetadataEntry key="HKTimeZone" value="America/New_York"/>
  <MetadataEntry key="HKElevationAscended" value="6100 cm"/>
  <WorkoutStatistics type="HKQuantityTypeIdentifierDistanceCycling" startDate="2026-07-10 08:00:00 -0400"
    endDate="2026-07-10 08:42:30 -0400" sum="9.0" unit="mi"/>
 </Workout>
 <Workout workoutActivityType="HKWorkoutActivityTypeCycling" duration="30" durationUnit="min"
   totalDistance="14.0" totalDistanceUnit="km" startDate="2024-09-01 10:00:00 -0400"
   endDate="2024-09-01 10:30:00 -0400"/>
 <Workout workoutActivityType="HKWorkoutActivityTypeCycling" duration="40" durationUnit="min"
   sourceName="Fitness" startDate="2026-07-11 23:25:00 +0200" endDate="2026-07-12 00:05:00 +0200">
  <MetadataEntry key="HKTimeZone" value="America/New_York"/>
  <MetadataEntry key="HKElevationAscended" value="6900 cm"/>
  <WorkoutStatistics type="HKQuantityTypeIdentifierDistanceCycling" sum="8.5" unit="mi"/>
 </Workout>
 <Workout workoutActivityType="HKWorkoutActivityTypeCycling" duration="37" durationUnit="min"
   sourceName="Fitness" startDate="2026-07-11 14:05:00 +0200" endDate="2026-07-11 14:42:00 +0200">
  <MetadataEntry key="HKTimeZone" value="America/New_York"/>
  <WorkoutStatistics type="HKQuantityTypeIdentifierDistanceCycling" sum="8.8" unit="mi"/>
 </Workout>
 <Workout workoutActivityType="HKWorkoutActivityTypeRunning" duration="25" durationUnit="min"
   startDate="2026-07-11 07:00:00 -0400" endDate="2026-07-11 07:25:00 -0400">
  <WorkoutStatistics type="HKQuantityTypeIdentifierDistanceWalkingRunning" sum="3.1" unit="mi"/>
 </Workout>
</HealthData>
"""


@pytest.fixture
def data(tmp_path, monkeypatch):
    archive = {
        "through": "2026-06-21",
        "total_rides": 2,
        "total_distance_km": 30.0,
        "total_elevation_m": 100,
        "longest_ride_km": 20.0,
        "monthly": [{"month": "2026-06", "distance_km": 30.0}],
        "calendar": [["2026-06-20", 10.0], ["2026-06-21", 20.0]],
    }
    (tmp_path / "cycling_strava_archive.json").write_text(json.dumps(archive))
    for name in ("ARCHIVE", "RIDES", "STATS", "CALENDAR"):
        monkeypatch.setattr(cycling_data, name, tmp_path / getattr(cycling_data, name).name)
    monkeypatch.setattr(cycling_data, "DATA", tmp_path)
    return tmp_path


def run(monkeypatch, *argv, payload=None):
    if payload is not None:
        monkeypatch.setenv("PAYLOAD", json.dumps(payload))
    monkeypatch.setattr(sys, "argv", ["cycling_data.py", *argv])
    cycling_data.main()


def export_zip(tmp_path):
    path = tmp_path / "export.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("apple_health_export/export.xml", EXPORT)
    return path


def test_reads_cycling_workouts_only(tmp_path):
    rides = cycling_data.health_rides(export_zip(tmp_path))
    assert rides[:2] == [
        {"date": "2026-07-10", "distance_km": 14.48, "moving_time_min": 42, "elevation_m": 61, "source": "apple_health"},
        {"date": "2024-09-01", "distance_km": 14.0, "moving_time_min": 30, "elevation_m": None, "source": "apple_health"},
    ]
    assert len(rides) == 4  # the running workout is skipped


def test_dates_use_the_workouts_own_time_zone(tmp_path):
    """Exported abroad (+0200), a Boston commute at 17:25 local reads 23:25; a later one would
    cross midnight. Both commutes on July 11 must stay on July 11 and stay separate."""
    rides = cycling_data.health_rides(export_zip(tmp_path))
    july11 = sorted(r["distance_km"] for r in rides if r["date"] == "2026-07-11")
    assert july11 == [13.68, 14.16]
    assert not any(r["date"] == "2026-07-12" for r in rides)


def test_import_skips_rides_in_the_strava_archive(data, monkeypatch):
    run(monkeypatch, "import-health", str(export_zip(data)))
    rides = json.loads((data / "cycling_rides.json").read_text())
    assert [r["date"] for r in rides] == ["2026-07-10", "2026-07-11", "2026-07-11"]
    stats = json.loads((data / "cycling_stats.json").read_text())
    assert stats["total_rides"] == 5
    assert stats["total_distance_km"] == 72.3
    assert stats["total_elevation_m"] == 230
    assert stats["last_ride"] == "2026-07-11"
    assert {"month": "2026-07", "distance_km": 42.3} in stats["monthly"]
    calendar = json.loads((data / "cycling_calendar.json").read_text())
    assert ["2026-07-10", 14.48] in calendar and ["2026-06-21", 20.0] in calendar


def test_import_twice_changes_nothing(data, monkeypatch):
    run(monkeypatch, "import-health", str(export_zip(data)))
    first = (data / "cycling_rides.json").read_text()
    run(monkeypatch, "import-health", str(export_zip(data)))
    assert (data / "cycling_rides.json").read_text() == first


SHORTCUT = {"start": "2026-07-10T08:00:00-04:00", "end": "2026-07-10T08:42:30-04:00", "distance": 9.0, "unit": "mi"}


def test_shortcut_ride_then_export_fills_elevation(data, monkeypatch):
    run(monkeypatch, "add-shortcut", payload=SHORTCUT)
    rides = json.loads((data / "cycling_rides.json").read_text())
    assert rides == [{"date": "2026-07-10", "distance_km": 14.48, "moving_time_min": 42,
                      "elevation_m": None, "source": "shortcut"}]
    assert json.loads((data / "cycling_stats.json").read_text())["rides_missing_elevation"] == 1

    run(monkeypatch, "import-health", str(export_zip(data)))
    rides = [r for r in json.loads((data / "cycling_rides.json").read_text()) if r["date"] == "2026-07-10"]
    assert len(rides) == 1 and rides[0]["elevation_m"] == 61 and rides[0]["source"] == "apple_health"

    run(monkeypatch, "add-shortcut", payload=SHORTCUT)  # a repeated post doesn't erase elevation
    rides = [r for r in json.loads((data / "cycling_rides.json").read_text()) if r["date"] == "2026-07-10"]
    assert len(rides) == 1 and rides[0]["elevation_m"] == 61


def test_two_commutes_on_one_day_are_two_rides(data, monkeypatch):
    run(monkeypatch, "add-shortcut", payload=SHORTCUT)
    evening = {"start": "2026-07-10T17:30:00-04:00", "end": "2026-07-10T18:20:00-04:00", "distance": 9.2, "unit": "mi"}
    run(monkeypatch, "add-shortcut", payload=evening)
    assert len(json.loads((data / "cycling_rides.json").read_text())) == 2


@pytest.mark.parametrize("bad", [
    {**SHORTCUT, "distance": -1},
    {**SHORTCUT, "distance": 900},
    {**SHORTCUT, "unit": "furlong"},
    {**SHORTCUT, "end": "2026-07-10T07:00:00-04:00"},
    {**SHORTCUT, "start": "not a date"},
    {"start": "2026-07-10T08:00:00-04:00"},
    {**SHORTCUT, "start": "2026-06-01T08:00:00-04:00", "end": "2026-06-01T09:00:00-04:00"},
])
def test_bad_payloads_are_rejected(data, monkeypatch, bad):
    with pytest.raises(SystemExit):
        run(monkeypatch, "add-shortcut", payload=bad)
    assert not (data / "cycling_rides.json").exists()


def test_real_data_rebuilds_to_the_committed_files(tmp_path, monkeypatch):
    for name in ("STATS", "CALENDAR"):
        monkeypatch.setattr(cycling_data, name, tmp_path / getattr(cycling_data, name).name)
    cycling_data.rebuild()
    committed = json.loads((ROOT / "_data" / "cycling_stats.json").read_text())
    rebuilt = json.loads((tmp_path / "cycling_stats.json").read_text())
    committed.pop("updated_at"), rebuilt.pop("updated_at")
    assert rebuilt == committed
    assert (tmp_path / "cycling_calendar.json").read_text() == (ROOT / "_data" / "cycling_calendar.json").read_text()
