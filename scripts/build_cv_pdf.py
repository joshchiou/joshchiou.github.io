#!/usr/bin/env python3
"""Render the built /cv/ page to a PDF so the downloadable CV always matches cv.yml.

Usage (after `bundle exec jekyll build`):
    python3 scripts/build_cv_pdf.py                 # writes _site/assets/pdf/CV.pdf
    python3 scripts/build_cv_pdf.py --out ~/CV.pdf  # write somewhere else

Requires: pip install playwright && playwright install chromium
(or set CHROMIUM_PATH to an existing Chromium binary). Layout comes from the
@media print rules in _sass/_custom.scss.
"""

import argparse
import functools
import http.server
import os
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(directory):
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", default=ROOT / "_site", type=Path, help="built site directory")
    parser.add_argument("--out", type=Path, help="output PDF (default: <site>/assets/pdf/CV.pdf)")
    args = parser.parse_args()

    site = args.site.resolve()
    if not (site / "cv" / "index.html").exists():
        raise SystemExit(f"{site}/cv/index.html not found; run `bundle exec jekyll build` first")
    out = (args.out or site / "assets/pdf/CV.pdf").expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    server = serve(site)
    launch_args = {}
    if os.environ.get("CHROMIUM_PATH"):
        launch_args["executable_path"] = os.environ["CHROMIUM_PATH"]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_args)
            page = browser.new_page()
            # Light theme regardless of the viewer's preference.
            page.add_init_script("localStorage.setItem('theme', 'light')")
            page.goto(f"http://127.0.0.1:{server.server_port}/cv/", wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            page.pdf(path=str(out), format="Letter", print_background=True, prefer_css_page_size=True)
            browser.close()
    finally:
        server.shutdown()
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
