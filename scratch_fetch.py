"""Temporary: fetch figures for selected PMC articles and gallery photos."""
import re
from pathlib import Path

import requests
import yaml

OUT = Path("scratch-figures")
PMCIDS = ["PMC10567551", "PMC10560508", "PMC9037575", "PMC6505525", "PMC10550816"]
UA = {"User-Agent": "Mozilla/5.0 (joshchiou.github.io figure fetch)"}


def get(url, **kw):
    r = requests.get(url, headers=UA, timeout=60, **kw)
    r.raise_for_status()
    return r


def save(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    print(f"saved {path} ({len(content) // 1024} KB)")


for pmcid in PMCIDS:
    d = OUT / pmcid
    # 1) Europe PMC full-text XML -> figure ids, labels, captions
    try:
        xml = get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML").text
        (d).mkdir(parents=True, exist_ok=True)
        (d / "fulltext.xml").write_text(xml)
        hrefs = re.findall(r'<graphic[^>]*xlink:href="([^"]+)"', xml)
        print(pmcid, "graphics:", hrefs)
    except Exception as e:
        print(pmcid, "fullTextXML failed:", e)
        hrefs = []
    got = 0
    for h in hrefs:
        stem = h.rsplit(".", 1)[0]
        for ext in (".jpg", ".png", ".gif", ""):
            url = f"https://europepmc.org/articles/{pmcid}/bin/{stem}{ext}"
            try:
                r = get(url)
                if r.headers.get("content-type", "").startswith("image"):
                    save(d / (stem + (ext or ".img")), r.content)
                    got += 1
                    break
            except Exception:
                continue
    # 2) Fallback: images linked from the PMC article page
    if got == 0:
        try:
            page = get(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/").text
            urls = sorted(set(re.findall(r'https://cdn\.ncbi\.nlm\.nih\.gov/pmc/blobs/[^"\']+\.(?:jpg|png|gif)', page)))
            print(pmcid, "pmc page images:", len(urls))
            for u in urls:
                try:
                    save(d / u.rsplit("/", 1)[-1], get(u).content)
                except Exception as e:
                    print("  failed", u, e)
        except Exception as e:
            print(pmcid, "PMC page failed:", e)

# Gallery photos already on the images-v1 release
for yml in ("_data/bike_gallery.yml", "_data/cocktail_gallery.yml", "_data/bikes.yml"):
    try:
        items = yaml.safe_load(Path(yml).read_text()) or []
    except Exception as e:
        print(yml, e)
        continue
    for item in items:
        for key in ("url", "image"):
            u = item.get(key) if isinstance(item, dict) else None
            if u and u.startswith("https://"):
                try:
                    save(OUT / "photos" / u.rsplit("/", 1)[-1], get(u).content)
                except Exception as e:
                    print("  failed", u, e)
