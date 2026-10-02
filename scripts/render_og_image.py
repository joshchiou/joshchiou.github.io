#!/usr/bin/env python3
"""Render assets/img/og-image.svg to og-image.png (1200x630) with headless Chromium.

Usage: python3 scripts/render_og_image.py

Requires: pip install playwright && playwright install chromium
(or set CHROMIUM_PATH to an existing Chromium binary). Inter is fetched from
Google Fonts and inlined, so the PNG matches the site typography without the
browser needing network access.
"""

import base64
import os
import re
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "assets/img/og-image.svg"
PNG = ROOT / "assets/img/og-image.png"

HTML = """<!doctype html>
<html><head><meta charset="utf-8">
<style>{fonts}
html,body{{margin:0;padding:0;background:#0d1729}} svg{{display:block}}</style>
</head><body>{svg}</body></html>"""


FONTS_CSS = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700"
# A modern UA makes Google Fonts serve woff2.
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read()


def inline_fonts():
    """Return the Inter @font-face CSS (latin subset) with font files as data URIs."""
    css = fetch(FONTS_CSS).decode()
    blocks = re.findall(r"/\* latin \*/\s*(@font-face\s*{[^}]*})", css)
    out = []
    for block in blocks:
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        data = base64.b64encode(fetch(url)).decode()
        out.append(block.replace(url, f"data:font/woff2;base64,{data}"))
    return "\n".join(out)


def main():
    launch_args = {}
    if os.environ.get("CHROMIUM_PATH"):
        launch_args["executable_path"] = os.environ["CHROMIUM_PATH"]
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": 1200, "height": 630})
        page.set_content(HTML.format(fonts=inline_fonts(), svg=SVG.read_text()), wait_until="load")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(PNG), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
        browser.close()
    print(f"Wrote {PNG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
