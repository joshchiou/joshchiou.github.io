"""Temporary: fetch figures for selected PMC articles and gallery photos."""
import re
from pathlib import Path

import requests
import yaml

OUT = Path("scratch-figures")
PMCIDS = []  # done in the first run
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
# Publisher (Springer Nature) figure images, by DOI and file prefix
SPRINGER = {
    "sun2023plasma": ("10.1038/s41586-023-06592-6", "41586_2023_6592"),
    "chiou2021interpreting": ("10.1038/s41586-021-03552-w", "41586_2021_3552"),
    "chiou2021single": ("10.1038/s41588-021-00823-0", "41588_2021_823"),
    "greenwald2019pancreatic": ("10.1038/s41467-019-09975-4", "41467_2019_9975"),
    "wang2023integrating": ("10.1038/s41588-023-01397-9", "41588_2023_1397"),
}
for key, (doi, prefix) in SPRINGER.items():
    art = "art%3A" + doi.replace("/", "%2F")
    for n in range(1, 9):
        for ext in ("png", "jpg"):
            url = f"https://media.springernature.com/full/springer-static/image/{art}/MediaObjects/{prefix}_Fig{n}_HTML.{ext}"
            try:
                r = get(url)
                if r.headers.get("content-type", "").startswith("image"):
                    save(OUT / "springer" / key / f"Fig{n}.{ext}", r.content)
                    break
            except Exception as e:
                if ext == "jpg":
                    print("  missing", key, n, e)

for yml in ():  # photos done in the first run
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
