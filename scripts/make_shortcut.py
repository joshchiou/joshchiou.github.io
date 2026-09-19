#!/usr/bin/env python3
"""Generate an importable iOS Shortcut that posts a ride to the repo.

Building the HTTP half of this in the Shortcuts UI is the tedious part: method,
two headers, and the request-body plumbing. A .shortcut file is a property list,
so it can be written here instead and imported on the phone.

    python3 scripts/make_shortcut.py            # writes post-ride.shortcut
    python3 scripts/make_shortcut.py --out /tmp/x.shortcut

UNVERIFIED. It was not possible to test this on a device, so the action
identifiers and the variable wiring between the two actions are written from the
documented format rather than confirmed by import. If it fails to import, delete
it and build the two actions by hand — the file cannot do any harm beyond not
working. The structure is validated here only as far as "it is a well-formed
plist that round-trips".

What it generates, deliberately kept to the part that is easy to get right:

    1. Text            — a fixed JSON payload containing one test ride
    2. Get Contents of URL — POST it to the repository dispatch endpoint

That is enough to prove the token, the headers and the endpoint work from the
phone. Reading Health is left out on purpose: those actions are the ones this
script is least able to get right, and they are two taps to add. Once the test
ride shows up on the site, replace the fixed date and distance in action 1 with
variables from a Health action placed above it.

Importing an unsigned shortcut needs Settings -> Shortcuts -> Allow Untrusted
Shortcuts, which only appears once at least one shortcut has been run.
"""

import argparse
import json
import plistlib
import uuid
from pathlib import Path

DISPATCH_URL = "https://api.github.com/repos/joshchiou/joshchiou.github.io/dispatches"
TOKEN_PLACEHOLDER = "REPLACE_WITH_YOUR_TOKEN"

# A recognisable test ride: an odd distance and a round time make it easy to
# spot and delete afterwards.
TEST_PAYLOAD = {
    "event_type": "new-rides",
    "client_payload": {
        "rides": [
            {
                "start": "2026-01-01T12:00:00",
                "distance_km": 3.21,
                "elevation_m": 0,
                "duration_min": 10,
            }
        ]
    },
}


def _text_token(value: str) -> dict:
    return {"Value": {"string": value}, "WFSerializationType": "WFTextTokenString"}


def _header_item(key: str, value: str) -> dict:
    return {"WFItemType": 0, "WFKey": _text_token(key), "WFValue": _text_token(value)}


def build_shortcut(token: str) -> dict:
    text_uuid = str(uuid.uuid4()).upper()
    body = json.dumps(TEST_PAYLOAD, indent=2)

    actions = [
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.gettext",
            "WFWorkflowActionParameters": {"UUID": text_uuid, "WFTextActionText": body},
        },
        {
            "WFWorkflowActionIdentifier": "is.workflow.actions.downloadurl",
            "WFWorkflowActionParameters": {
                "WFURL": DISPATCH_URL,
                "WFHTTPMethod": "POST",
                "WFHTTPBodyType": "File",
                "ShowHeaders": True,
                # Feed the Text action's output in as the request body.
                "WFRequestVariable": {
                    "Value": {
                        "OutputName": "Text",
                        "OutputUUID": text_uuid,
                        "Type": "ActionOutput",
                    },
                    "WFSerializationType": "WFTextTokenAttachment",
                },
                "WFHTTPHeaders": {
                    "Value": {
                        "WFDictionaryFieldValueItems": [
                            _header_item("Authorization", f"Bearer {token}"),
                            _header_item("Accept", "application/vnd.github+json"),
                        ]
                    },
                    "WFSerializationType": "WFDictionaryFieldValue",
                },
            },
        },
    ]

    return {
        "WFWorkflowClientVersion": "2605",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {
            "WFWorkflowIconStartColor": 2071128575,
            "WFWorkflowIconGlyphNumber": 59446,
        },
        "WFWorkflowImportQuestions": [],
        "WFWorkflowTypes": ["NCWidget"],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowActions": actions,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="post-ride.shortcut", help="output path")
    ap.add_argument("--token", default=TOKEN_PLACEHOLDER,
                    help="embed a token now instead of editing it on the phone "
                         "(the file then contains a secret — treat it accordingly)")
    args = ap.parse_args()

    shortcut = build_shortcut(args.token)
    out = Path(args.out)
    out.write_bytes(plistlib.dumps(shortcut, fmt=plistlib.FMT_BINARY))

    # Only a sanity check: confirms a well-formed plist, not that iOS accepts it.
    reparsed = plistlib.loads(out.read_bytes())
    assert reparsed["WFWorkflowActions"][0]["WFWorkflowActionParameters"]["UUID"]
    assert reparsed["WFWorkflowActions"][1]["WFWorkflowActionParameters"]["WFURL"] == DISPATCH_URL

    print(f"Wrote {out} ({out.stat().st_size} bytes) — plist round-trips cleanly.")
    if args.token == TOKEN_PLACEHOLDER:
        print(f"\nAfter importing, edit the Authorization header and replace "
              f"{TOKEN_PLACEHOLDER}.")
    else:
        print("\nThis file contains your token. Don't commit it or share it.")
    print("\nGet it onto the phone via iCloud Drive or AirDrop, then open it in Files.")
    print("Settings -> Shortcuts -> Allow Untrusted Shortcuts must be on "
          "(it appears only after you've run one shortcut).")
    print("Running it should post the test ride and return 204 with an empty body.")


if __name__ == "__main__":
    main()
