"""Browser tests for the site's interactive features, run against the built site in _site.

Every page is loaded in headless Chromium and must run without JavaScript errors, blocked
scripts (a wrong integrity hash), or missing local files. Then each interactive feature is
driven the way a visitor would: carousel arrows, chart tabs, filters, search, toggles.

Run after `bundle exec jekyll build` and `purgecss -c purgecss.config.js` (the deploy purges
unused CSS, which can strip classes that only JavaScript adds, so test what goes live):
    python3 -m pytest tests/test_interactive.py

Set CHROMIUM_PATH to use a specific browser. Where jsDelivr is blocked (some sandboxes), set
CDN_FALLBACK=npm to serve CDN files from the npm registry instead; CI uses the real CDN.
"""

import functools
import http.server
import os
import re
import sys
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
sys.path.insert(0, str(ROOT / "scripts"))

playwright = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.skipif(not (SITE / "index.html").exists(), reason="site not built")

PAGES = sorted(
    "/" + str(p.relative_to(SITE)).removesuffix("index.html")
    for p in SITE.rglob("*.html")
    if not p.relative_to(SITE).parts[0] == "assets" and not p.name.startswith("google")
)

# Local files a page requests on purpose knowing they may not exist.
EXPECTED_MISSING = [
    re.compile(r"/assets/img/projects/fun/travel/travel-\d+\.webp$"),  # gallery probes for photos
]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def base_url():
    handler = functools.partial(QuietHandler, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="session")
def browser():
    with playwright.sync_playwright() as p:
        path = os.environ.get("CHROMIUM_PATH")
        b = p.chromium.launch(executable_path=path) if path else p.chromium.launch()
        yield b
        b.close()


def npm_route(route):
    import check_sri

    url = route.request.url
    try:
        body = check_sri.from_npm(url)
    except Exception:
        return route.abort()
    ctype = "text/css" if url.endswith(".css") else "application/javascript"
    route.fulfill(body=body, content_type=ctype, headers={"access-control-allow-origin": "*"})


class Page:
    """A browser page that records JavaScript errors, blocked scripts, and missing local files."""

    def __init__(self, browser, base_url, width=1280):
        self.base = base_url
        self.page = browser.new_page(viewport={"width": width, "height": 900})
        self.problems: list[str] = []
        # Analytics and citation badges are third-party code, not site features.
        self.page.route(re.compile(r"https?://([^/]*\.)?(goatcounter\.com|gc\.zgo\.at|cloudfront\.net"
                                   r"|dimensions\.ai|altmetric\.com)/"), lambda r: r.abort())
        if os.environ.get("CDN_FALLBACK") == "npm":
            self.page.route("https://cdn.jsdelivr.net/npm/**", npm_route)
        self.page.on("pageerror", lambda e: self.problems.append(f"JavaScript error: {e}"))
        self.page.on("console", self._console)
        self.page.on("response", self._response)

    def _console(self, msg):
        if msg.type == "error" and ("integrity" in msg.text or "Refused to" in msg.text):
            self.problems.append(f"blocked resource: {msg.text[:200]}")

    def _response(self, resp):
        if resp.url.startswith(self.base) and resp.status >= 400:
            path = resp.url[len(self.base):]
            if not any(p.search(path) for p in EXPECTED_MISSING):
                self.problems.append(f"{resp.status} for {path}")

    def open(self, path):
        self.page.goto(self.base + path, wait_until="load")
        self.page.wait_for_timeout(300)
        return self.page

    def assert_clean(self):
        assert self.problems == [], "\n".join(self.problems)


@pytest.fixture
def site(browser, base_url):
    pages = []

    def make(width=1280):
        p = Page(browser, base_url, width)
        pages.append(p)
        return p

    yield make
    for p in pages:
        p.page.close()


# ---------------------------------------------------------------- every page


@pytest.mark.parametrize("path", PAGES)
def test_page_loads_cleanly(site, path):
    p = site()
    p.open(path)
    p.assert_clean()


# ---------------------------------------------------------------- features


def swiper_index(page, selector):
    return page.evaluate(f"document.querySelector('{selector}').swiper?.realIndex")


def test_cocktail_carousel_arrows_and_dots(site):
    p = site()
    page = p.open("/projects/fun_cocktails/")
    sel = ".cocktail-gallery-swiper"
    assert swiper_index(page, sel) == 0, "Swiper did not start on the cocktails page"
    first = page.locator(f"{sel} .swiper-slide-active img").get_attribute("src")

    page.click(f"{sel} .swiper-button-next")
    page.wait_for_timeout(500)
    assert swiper_index(page, sel) == 1
    assert page.locator(f"{sel} .swiper-slide-active img").get_attribute("src") != first
    assert page.locator(f"{sel} .swiper-slide-active").is_visible()

    page.click(f"{sel} .swiper-button-prev")
    page.wait_for_timeout(500)
    assert swiper_index(page, sel) == 0

    page.locator(f"{sel} .swiper-pagination-bullet").nth(2).click()
    page.wait_for_timeout(500)
    assert swiper_index(page, sel) == 2
    p.assert_clean()


def test_travel_map_bars_and_gallery(site):
    p = site()
    page = p.open("/projects/fun_travel/")
    page.wait_for_function("document.querySelectorAll('#travel-map-svg path').length > 50", timeout=10000)
    visited = page.evaluate("window._travelData.countries.length")
    assert visited > 0

    rows = page.locator("#travel-bars-wrap > *")
    assert rows.count() > 0, "country bars did not render"

    if page.locator("#travelSwiper").is_visible():  # only shown once travel photos exist
        before = swiper_index(page, "#travelSwiper")
        page.click("#travelSwiper .swiper-button-next")
        page.wait_for_timeout(500)
        assert swiper_index(page, "#travelSwiper") != before
    p.assert_clean()


def test_cycling_charts_and_bike_carousel(site):
    p = site()
    page = p.open("/projects/fun_cycling/")
    page.wait_for_function("typeof echarts !== 'undefined'", timeout=10000)
    page.wait_for_selector("#cycling-calendar canvas, #cycling-calendar svg", timeout=10000)

    for view in ("monthly", "cumulative", "calendar"):
        page.click(f".chart-view-btn[data-view='{view}']")
        page.wait_for_timeout(300)
        assert page.locator(f"#cycling-{view}").is_visible(), f"{view} chart not shown"
        assert page.locator(f"#cycling-{view} canvas, #cycling-{view} svg").count() > 0, f"{view} chart empty"
        for other in {"monthly", "cumulative", "calendar"} - {view}:
            assert not page.locator(f"#cycling-{other}").is_visible()

    if page.locator("#bikeNext").is_visible():
        start = page.evaluate("window._bikeCarouselCur()")
        page.click("#bikeNext")
        page.wait_for_timeout(400)
        assert page.evaluate("window._bikeCarouselCur()") != start
        page.click("#bikePrev")
        page.wait_for_timeout(400)
        assert page.evaluate("window._bikeCarouselCur()") == start
    p.assert_clean()


def test_home_assistant_chips(site):
    p = site()
    page = p.open("/projects/fun_home_assistant/")
    chip = page.locator(".hass-chip").first
    chip.click()
    detail = page.locator(".hass-node-detail.open")
    assert detail.count() == 1 and detail.inner_text().strip()
    chip.click()
    assert page.locator(".hass-node-detail.open").count() == 0
    p.assert_clean()


def test_code_page_filters(site):
    p = site()
    page = p.open("/code/")
    items = page.locator("#contrib-list .contribution-item")
    if items.count() == 0:
        pytest.skip("no contributions listed")
    buttons = page.locator(".contrib-filter-btn[data-filter-type]")
    for i in range(buttons.count()):
        btn = buttons.nth(i)
        btn.click()
        kind = btn.get_attribute("data-filter-type")
        visible = [it for it in items.all() if it.is_visible()]
        if kind:
            assert all(it.get_attribute("data-type") == kind for it in visible)
        assert visible or page.locator("#contrib-empty").is_visible()
    p.assert_clean()


def test_publication_search_and_toggles(site):
    p = site()
    page = p.open("/publications/")
    entries = page.locator(".publications ol.bibliography > li")
    total = entries.count()
    page.fill("#bibsearch", "proteom")
    page.wait_for_timeout(600)
    shown = sum(1 for e in entries.all() if e.is_visible())
    assert 0 < shown < total, f"search for 'proteom' shows {shown} of {total}"
    page.fill("#bibsearch", "")
    page.wait_for_timeout(600)

    # Abstract and Cite buttons appear once entries carry abstracts or bibtex_show.
    for kind in ("abstract", "bibtex"):
        if page.locator(f"a.{kind}").count():
            page.locator(f"a.{kind}").first.click()
            assert page.locator(f".{kind}.hidden.open").count() == 1
    p.assert_clean()


def test_homepage_count_up_ends_on_real_numbers(site):
    import check_site

    p = site()
    page = p.open("/")
    page.locator("#stat-papers").scroll_into_view_if_needed()
    page.wait_for_timeout(1800)
    total = len(check_site.parse_bib(ROOT / "_bibliography" / "papers.bib"))
    citations = check_site.load_json("scholar_stats.json")["citations"]
    assert page.inner_text("#stat-papers").replace(",", "") == str(total)
    assert page.inner_text("#stat-citations").replace(",", "") == str(citations)
    p.assert_clean()


def test_theme_toggle(site):
    p = site()
    page = p.open("/")
    seen = set()
    for _ in range(3):
        page.click("#light-toggle")
        seen.add(page.evaluate("document.documentElement.getAttribute('data-theme')"))
    assert {"light", "dark"} <= seen
    p.assert_clean()


def test_mobile_menu(site):
    p = site(width=390)
    page = p.open("/")
    toggler = page.locator(".navbar-toggler")
    assert toggler.is_visible()
    toggler.click()
    page.wait_for_timeout(500)
    assert page.locator("#navbarNav a.nav-link", has_text="publications").is_visible()
    p.assert_clean()


def test_site_search_opens(site):
    p = site()
    page = p.open("/")
    page.wait_for_function("customElements.get('ninja-keys') !== undefined", timeout=10000)
    page.click("#search-toggle")
    page.wait_for_timeout(400)
    assert page.evaluate("document.querySelector('ninja-keys').visible") is True
    page.keyboard.type("publications")
    page.wait_for_timeout(300)
    page.keyboard.press("Enter")
    page.wait_for_url("**/publications/", timeout=5000)
    p.assert_clean()
