#!/usr/bin/env python3
"""Create a Zenodo *draft* for a talk's slides. Never publishes.

Creates a deposition with the metadata in a JSON file, reserves a DOI, uploads
the PDF, and prints the draft URL. Review the draft on zenodo.org and click
Publish yourself; published records can be versioned but not deleted.

Usage:
    python3 scripts/zenodo_deposit.py docs/talks/festival-of-genomics-2025.zenodo.json slides.pdf
    python3 scripts/zenodo_deposit.py META.json slides.pdf --dry-run    # print the request only
    python3 scripts/zenodo_deposit.py META.json slides.pdf --sandbox    # use sandbox.zenodo.org

Requires ZENODO_TOKEN: a personal access token with the deposit:write scope
(leave deposit:actions off so this token cannot publish).
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("requests not installed. Run: pip install requests")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("metadata", type=Path, help="JSON file with Zenodo deposition metadata")
    parser.add_argument("pdf", type=Path, help="slides PDF to upload")
    parser.add_argument("--sandbox", action="store_true", help="use sandbox.zenodo.org for testing")
    parser.add_argument("--dry-run", action="store_true", help="print the request without sending it")
    args = parser.parse_args()

    metadata = json.loads(args.metadata.read_text())
    metadata["prereserve_doi"] = True
    if not args.pdf.is_file():
        sys.exit(f"{args.pdf} not found")

    if args.dry_run:
        print(json.dumps({"metadata": metadata}, indent=2))
        print(f"\nWould upload {args.pdf} ({args.pdf.stat().st_size / 1e6:.1f} MB)")
        return

    token = os.environ.get("ZENODO_TOKEN")
    if not token:
        sys.exit("ZENODO_TOKEN is not set")
    base = "https://sandbox.zenodo.org" if args.sandbox else "https://zenodo.org"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.post(f"{base}/api/deposit/depositions", json={"metadata": metadata}, headers=headers, timeout=60)
    if resp.status_code >= 400:
        sys.exit(f"Creating the draft failed ({resp.status_code}): {resp.text}")
    draft = resp.json()

    with args.pdf.open("rb") as fh:
        upload = requests.put(f"{draft['links']['bucket']}/{args.pdf.name}", data=fh, headers=headers, timeout=600)
    if upload.status_code >= 400:
        sys.exit(f"Uploading {args.pdf.name} failed ({upload.status_code}): {upload.text}\nDraft: {draft['links']['html']}")

    doi = draft["metadata"].get("prereserve_doi", {}).get("doi", "(not reserved)")
    print(f"Draft created (not published): {draft['links']['html']}")
    print(f"Reserved DOI: {doi}")
    print("Review the draft on Zenodo and click Publish when it looks right.")


if __name__ == "__main__":
    main()
