#!/usr/bin/env python3
"""Check the integrity hashes of the third-party libraries in _config.yml.

Each library loaded from a CDN carries a Subresource Integrity hash. If the hash doesn't
match the file, the browser refuses to run it, and whatever depends on it silently stops
working (a wrong Swiper hash froze the photo carousels on the cocktails and travel pages).
This downloads every file and compares hashes.

Files come from the CDN URL. If the CDN can't be reached and the URL is a jsDelivr npm
URL, the file is read from the npm registry tarball instead, which jsDelivr serves
byte for byte.

Usage:
    python3 scripts/check_sri.py           # files that can't be downloaded are skipped
    python3 scripts/check_sri.py --strict  # ...or fail (CI, where the CDN is reachable)
"""

import argparse
import base64
import hashlib
import io
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
JSDELIVR = re.compile(r"https://cdn\.jsdelivr\.net/npm/((?:@[^/]+/)?[^@/]+)@([^/]+)/(.+)")
_tarballs: dict[tuple[str, str], tarfile.TarFile] = {}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "check_sri"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def from_npm(url: str) -> bytes:
    m = JSDELIVR.match(url)
    if not m:
        raise ValueError("not a jsDelivr npm URL")
    name, version, path = m.groups()
    if (name, version) not in _tarballs:
        base = name.split("/")[-1]
        tgz = fetch(f"https://registry.npmjs.org/{name}/-/{base}-{version}.tgz")
        _tarballs[(name, version)] = tarfile.open(fileobj=io.BytesIO(tgz))
    tar = _tarballs[(name, version)]
    for member in tar.getmembers():
        if member.name.partition("/")[2] == path:
            return tar.extractfile(member).read()
    raise FileNotFoundError(f"{path} is not in the npm package (jsDelivr generates it)")


def digest(data: bytes, algo: str) -> str:
    return base64.b64encode(hashlib.new(algo, data).digest()).decode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--strict", action="store_true", help="fail on files that can't be downloaded")
    args = parser.parse_args()
    libs = yaml.safe_load((ROOT / "_config.yml").read_text())["third_party_libraries"]
    failures, skipped, checked = [], [], 0
    for name, lib in libs.items():
        if not isinstance(lib, dict):
            continue
        pairs = []
        for kind, expected in (lib.get("integrity") or {}).items():
            url = (lib.get("url") or {}).get(kind)
            if isinstance(expected, dict) and isinstance(url, dict):
                pairs += [(f"{kind}.{sub}", h, url.get(sub)) for sub, h in expected.items()]
            else:
                pairs.append((kind, expected, url))
        for kind, expected, url in pairs:
            if not isinstance(url, str) or kind.endswith("map"):
                continue  # source maps aren't integrity-checked by browsers
            url = url.replace("{{version}}", str(lib.get("version", "")))
            try:
                try:
                    data = fetch(url)
                except Exception:
                    data = from_npm(url)
            except Exception as exc:
                (failures if args.strict else skipped).append(f"{name} {kind}: could not download {url} ({exc})")
                continue
            algo, _, value = expected.partition("-")
            actual = digest(data, algo)
            checked += 1
            if actual != value:
                failures.append(f"{name} {kind}: _config.yml has {expected}, file is {algo}-{actual} ({url})")

    for f in skipped:
        print(f"SKIP: {f}")
    for f in failures:
        print(f"FAIL: {f}")
    if failures:
        sys.exit(f"{len(failures)} integrity hash(es) wrong or unchecked")
    print(f"All {checked} checked integrity hashes match" + (f"; {len(skipped)} skipped." if skipped else "."))


if __name__ == "__main__":
    main()
