#!/usr/bin/env python3
"""Check that the numbers the site shows match their source files and each other.

Recomputes every displayed count from the source data (papers.bib, _config.yml, and the
_data files), independently of the Liquid and Ruby code that renders them, and compares
the results with the built HTML. Also checks the data files for internal consistency.

Usage:
    python3 scripts/check_site.py            # data checks, plus the built site if _site exists
    python3 scripts/check_site.py --site _site   # require the built site

Exits non-zero if any check fails. Stale data (a refresh workflow that has stopped
running) is reported as a warning, not a failure, so it never blocks a deploy.
"""

import argparse
import html
import json
import os
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data"
STALE_DAYS = {"scholar_stats.json": 14, "github_stats.json": 14}
NO_RIDES_DAYS = 45  # warn when the cycling data has no ride this recent

failures: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def expect_equal(label: str, shown, expected) -> None:
    if str(shown) != str(expected):
        fail(f"{label}: page shows {shown!r}, expected {expected!r}")


def liquid_round(x: float) -> int:
    """Ruby's round: halves go away from zero (Python's round() goes to even)."""
    return int(math.floor(x + 0.5))


# ---------------------------------------------------------------- sources


def parse_bib(path: Path) -> list[dict]:
    """Minimal BibTeX reader: entry type, key, and top-level `field = {value}` pairs."""
    text = path.read_text(encoding="utf-8")
    entries = []
    for m in re.finditer(r"^@(\w+)\{([^,\s]+),", text, re.MULTILINE):
        start = m.end()
        depth, i = 1, start
        while depth and i < len(text):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        body = text[start : i - 1]
        fields: dict[str, str] = {}
        for f in re.finditer(r"^\s*(\w+)\s*=\s*", body, re.MULTILINE):
            j = f.end()
            if body[j] == "{":
                d, k = 1, j + 1
                while d and k < len(body):
                    d += {"{": 1, "}": -1}.get(body[k], 0)
                    k += 1
                value = body[j + 1 : k - 1]
            else:
                value = re.match(r"[^,\n]*", body[j:]).group(0)
            fields.setdefault(f.group(1).lower(), value.strip())
        entries.append({"type": m.group(1).lower(), "key": m.group(2), **fields})
    return entries


def load_json(name: str) -> dict:
    return json.loads((DATA / name).read_text())


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def counted(entries: list[dict]) -> list[dict]:
    """Entries the site counts as publications: everything but `counted = {false}` (the thesis)."""
    return [e for e in entries if e.get("counted") != "false"]


# ---------------------------------------------------------------- data checks


def check_bib(entries: list[dict], config: dict) -> None:
    keys = [e["key"] for e in entries]
    for key in sorted({k for k in keys if keys.count(k) > 1}):
        fail(f"papers.bib: duplicate key {key}")

    dois = [e["doi"].lower() for e in entries if e.get("doi")]
    for doi in sorted({d for d in dois if dois.count(d) > 1}):
        fail(f"papers.bib: duplicate DOI {doi}")

    for e in entries:
        required = ["title", "author", "year"] + (["journal"] if e["type"] == "article" else [])
        for field in required:
            if not e.get(field):
                fail(f"papers.bib: {e['key']} has no {field}")
        if e.get("year") and not re.fullmatch(r"\d{4}", e["year"]):
            fail(f"papers.bib: {e['key']} year {e['year']!r} is not a four-digit year")

    selected = [e for e in entries if e.get("selected") == "true"]
    previews = [e["preview"] for e in selected if e.get("preview")]
    for p in sorted({p for p in previews if previews.count(p) > 1}):
        fail(f"papers.bib: selected papers share the thumbnail {p}")
    for e in selected:
        if e.get("preview") and not (ROOT / e["preview"]).exists():
            fail(f"papers.bib: {e['key']} preview {e['preview']} does not exist")

    # A top journal spelled differently in one entry would silently drop out of the count.
    top = config.get("top_journals") or []
    for e in entries:
        journal = e.get("journal", "")
        for name in top:
            if journal != name and journal.lower() == name.lower():
                fail(f"papers.bib: {e['key']} journal {journal!r} should be spelled {name!r}")


def check_scholar(stats: dict) -> None:
    for field in ("citations", "h_index", "i10_index"):
        if not isinstance(stats.get(field), int) or stats[field] < 0:
            fail(f"scholar_stats.json: {field} is {stats.get(field)!r}, expected a count")
            return
    c, h, i10 = stats["citations"], stats["h_index"], stats["i10_index"]
    # h papers with at least h citations each means at least h*h citations in total.
    if h * h > c:
        fail(f"scholar_stats.json: h-index {h} needs at least {h * h} citations, has {c}")
    if h >= 10 and i10 < h:
        fail(f"scholar_stats.json: i10-index {i10} is below h-index {h}")


def check_cycling(stats: dict) -> None:
    monthly_km = sum(m.get("distance_km", 0) for m in stats.get("monthly", []))
    total_km = stats.get("total_distance_km", 0)
    if stats.get("monthly") and abs(monthly_km - total_km) > 0.05 * len(stats["monthly"]) + 0.1:
        fail(f"cycling_stats.json: monthly distances sum to {monthly_km:.1f} km, total is {total_km} km")
    if stats.get("longest_ride_km", 0) > total_km:
        fail("cycling_stats.json: longest ride is longer than the total distance")


def check_travel(countries: list, cities: list) -> None:
    names = [c["name"] for c in countries]
    for n in sorted({n for n in names if names.count(n) > 1}):
        fail(f"travel_countries.yml: {n} is listed twice")
    for c in countries:
        for field in ("continent", "flag"):
            if not c.get(field):
                fail(f"travel_countries.yml: {c['name']} has no {field}")
    pairs = [(c["name"], c.get("country"), c.get("state")) for c in cities]
    for p in sorted({p for p in pairs if pairs.count(p) > 1}, key=str):
        fail(f"travel_cities.yml: {p[0]} ({p[1]}) is listed twice")
    for c in cities:
        if c.get("country") not in names:
            fail(f"travel_cities.yml: {c['name']} is in {c.get('country')!r}, which is not in travel_countries.yml")


def check_freshness() -> None:
    now = datetime.now(timezone.utc)
    for name, days in STALE_DAYS.items():
        stamp = load_json(name).get("updated_at")
        if not stamp:
            continue
        age = (now - datetime.fromisoformat(stamp)).days
        if age > days:
            warnings.append(f"{name} was last updated {age} days ago ({stamp[:10]}); check its workflow")
    last_ride = load_json("cycling_stats.json").get("last_ride")
    if last_ride:
        age = (now.date() - datetime.fromisoformat(last_ride).date()).days
        if age > NO_RIDES_DAYS:
            warnings.append(f"no ride logged since {last_ride} ({age} days); is the ride Shortcut running?")


# ---------------------------------------------------------------- built-site checks


def read_page(site: Path, rel: str) -> str:
    path = site / rel
    if not path.exists():
        fail(f"built site has no {rel}")
        return ""
    return path.read_text(encoding="utf-8")


def texts(page: str, cls: str, tag: str = r"\w+") -> list[str]:
    pattern = rf'<{tag}[^>]*class="[^"]*\b{re.escape(cls)}\b[^"]*"[^>]*>([^<]*)<'
    return [html.unescape(t).strip() for t in re.findall(pattern, page)]


def entry_keys(fragment: str, keys: set[str]) -> list[str]:
    return [k for k in re.findall(r'<div id="([^"]+)" class="col-sm', fragment) if k in keys]


def check_site(site: Path, entries: list[dict], config: dict, scholar: dict) -> None:
    keys = {e["key"] for e in entries}
    selected = {e["key"] for e in entries if e.get("selected") == "true"}
    total = len(counted(entries))

    top = [(name, sum(1 for e in counted(entries) if e.get("journal") == name))
           for name in config.get("top_journals") or []]
    top_names = [name for name, count in top if count]
    top_total = sum(count for _, count in top)

    # Homepage
    home = read_page(site, "index.html")
    if home:
        stat = re.search(r'id="stat-papers">([^<]*)<', home)
        expect_equal("homepage publications stat", stat and stat.group(1).strip(), total)
        stat = re.search(r'id="stat-citations">([^<]*)<', home)
        expect_equal("homepage citations stat", stat and stat.group(1).strip(), scholar["citations"])
        nums = texts(home, "about-stat-num", "span")
        expect_equal("homepage h-index stat", nums[2] if len(nums) > 2 else None, scholar["h_index"])
        expect_equal("homepage top-journal line", (texts(home, "about-journals-count") or [None])[0],
                     f"{top_total} papers in")
        expect_equal("homepage journal pills", texts(home, "about-journal-pill"), top_names)
        for shown in texts(home, "publication-count"):
            expect_equal("homepage publication count", shown, f"{total} publications")
        expect_equal("homepage selected papers", sorted(entry_keys(home, keys)), sorted(selected))

    # Publications page: the Selected list, then the full list, then talks and press.
    pubs = read_page(site, "publications/index.html")
    if pubs:
        counts = texts(pubs, "publication-count")
        if not counts:
            fail("publications page: no publication count shown")
        for shown in counts:
            expect_equal("publications page count", shown, f"{total} publications")
        split = pubs.find("all-heading")
        if split < 0:
            fail("publications page: no 'All publications' heading")
        else:
            sel = entry_keys(pubs[:split], keys)
            full = entry_keys(pubs[split:], keys)
            expect_equal("publications page Selected entries", sorted(sel), sorted(selected))
            expect_equal("publications page entry count", len(full), len(entries))
            missing = sorted(keys - set(full))
            if missing:
                fail(f"publications page: entries missing from the full list: {', '.join(missing)}")

    # Code page
    code = read_page(site, "code/index.html")
    if code:
        gh = load_json("github_stats.json")
        expected = [gh.get(f, "n/a") if gh.get(f) is not None else "n/a"
                    for f in ("public_repos", "total_stars", "followers")]
        expect_equal("code page GitHub stats", texts(code, "gh-stat-val"), [str(v) for v in expected])

    # Travel page
    travel = read_page(site, "projects/fun_travel/index.html")
    if travel:
        countries = load_yaml(DATA / "travel_countries.yml")
        cities = load_yaml(DATA / "travel_cities.yml")
        continents = {c["continent"] for c in countries}
        expect_equal("travel page stats", texts(travel, "travel-stat-val"),
                     [str(len(countries)), str(len(continents)), str(len(cities))])

    # Cycling page
    cycling = read_page(site, "projects/fun_cycling/index.html")
    if cycling:
        s = load_json("cycling_stats.json")
        if s.get("total_rides"):
            miles = liquid_round(s["total_distance_km"] * 0.621371)
            kft = liquid_round(s["total_elevation_m"] * 3.28084) // 1000
            shown = [t.strip() for t in re.findall(r'<h3 class="mb-0">([^<]*)<', cycling)[:3]]
            expect_equal("cycling page stats", shown, [str(s["total_rides"]), str(miles), f"{kft}k"])


# ---------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", type=Path, help="built site to check (default: _site if present)")
    args = parser.parse_args()

    config = load_yaml(ROOT / "_config.yml")
    entries = parse_bib(ROOT / "_bibliography" / "papers.bib")
    scholar = load_json("scholar_stats.json")

    check_bib(entries, config)
    check_scholar(scholar)
    check_cycling(load_json("cycling_stats.json"))
    check_travel(load_yaml(DATA / "travel_countries.yml"), load_yaml(DATA / "travel_cities.yml"))
    check_freshness()

    site = args.site or (ROOT / "_site" if (ROOT / "_site").exists() else None)
    if args.site and not args.site.exists():
        fail(f"{args.site} does not exist; build the site first")
    elif site:
        check_site(site, entries, config, scholar)
    else:
        print("No built site found; checked the data files only.")

    for w in warnings:
        print(f"::warning::{w}" if "GITHUB_ACTIONS" in os.environ else f"WARNING: {w}")
    for f in failures:
        print(f"FAIL: {f}")
    if failures:
        sys.exit(f"{len(failures)} check(s) failed")
    print(f"All checks passed ({len(counted(entries))} publications counted, {len(entries)} listed; "
          f"site {'checked' if site else 'not built'}).")


if __name__ == "__main__":
    main()
