# Image GitHub Release & Galleries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add HEIC support to the image conversion script, publish all bike and cocktail photos as a GitHub release, populate bike fleet cards with images, and add Swiper carousels to the Cycling and Cocktails pages.

**Architecture:** `prep_images.py` gains optional HEIC support via `pillow-heif`; a new `publish_images.sh` script converts originals and uploads WebP files to GitHub release `images-v1`; data files reference the permanent release asset URLs; two static Jekyll-rendered Swiper carousels are added to existing project pages.

**Tech Stack:** Python 3 / Pillow / pillow-heif, bash / gh CLI, Jekyll / Liquid, Swiper.js (already vendored in al-folio via `images: slider: true` frontmatter)

---

## File Map

| Action | Path                         | Purpose                                                       |
| ------ | ---------------------------- | ------------------------------------------------------------- |
| Modify | `scripts/prep_images.py`     | Add HEIC/HEIF support                                         |
| Create | `scripts/requirements.txt`   | Pin Pillow + pillow-heif                                      |
| Create | `scripts/publish_images.sh`  | Convert → upload to GitHub release                            |
| Modify | `_data/bikes.yml`            | Add `image:` URL to 6 fleet entries                           |
| Create | `_data/bike_gallery.yml`     | 8 ride photos with captions                                   |
| Create | `_data/cocktail_gallery.yml` | 11 cocktail photos, no captions                               |
| Modify | `_sass/_projects.scss`       | Add `.swiper-slide-caption` style                             |
| Modify | `_projects/fun_cycling.md`   | Add `images: slider: true`, ride gallery section, Swiper init |
| Modify | `_projects/fun_cocktails.md` | Add `images: slider: true`, photos section, Swiper init       |

---

## Task 1: Add HEIC support to `scripts/prep_images.py`

**Files:**

- Modify: `scripts/prep_images.py`

- [ ] **Step 1: Add the pillow-heif import block**

Open `scripts/prep_images.py`. After the existing `piexif` try/except block (lines 39–42), add:

```python
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_HEIF = True
except ImportError:
    HAS_HEIF = False
```

- [ ] **Step 2: Add HEIC/HEIF to SUPPORTED_EXTS and emit a startup warning**

Change the existing `SUPPORTED_EXTS` line from:

```python
SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.bmp', '.webp'}
```

to:

```python
SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.bmp', '.webp', '.heic', '.heif'}
```

Then in `main()`, directly after the `images = sorted(...)` block (after line 172), add a one-time warning when HEIC files are found but `pillow-heif` is not installed:

```python
    if not HAS_HEIF:
        heic = [f for f in images if f.suffix.lower() in {'.heic', '.heif'}]
        if heic:
            print(f'  Warning: {len(heic)} HEIC file(s) found but pillow-heif is not installed.')
            print('  Install it with: pip install pillow-heif\n')
```

- [ ] **Step 3: Verify HEIC files appear in a dry-run**

```bash
python3 scripts/prep_images.py assets/img/originals/bike-photos /tmp/test-webp --dry-run --keep-names
```

Expected: all 14 bike files listed including `.heic`/`.HEIC` ones (or a warning that pillow-heif is missing, depending on whether it's installed). No crash.

- [ ] **Step 4: Commit**

```bash
git add scripts/prep_images.py
git commit -m "feat: add HEIC/HEIF support to prep_images.py"
```

---

## Task 2: Create `scripts/requirements.txt`

**Files:**

- Create: `scripts/requirements.txt`

- [ ] **Step 1: Write the file**

```
Pillow>=10.0
pillow-heif>=0.16
```

- [ ] **Step 2: Install and verify**

```bash
pip install -r scripts/requirements.txt
python3 -c "import pillow_heif; print('pillow-heif ok')"
```

Expected output: `pillow-heif ok`

- [ ] **Step 3: Commit**

```bash
git add scripts/requirements.txt
git commit -m "chore: add scripts/requirements.txt with Pillow and pillow-heif"
```

---

## Task 3: Create `scripts/publish_images.sh`

**Files:**

- Create: `scripts/publish_images.sh`

- [ ] **Step 1: Write the script**

```bash
#!/usr/bin/env bash
set -euo pipefail

REPO="joshchiou/joshchiou.github.io"
TAG="images-v1"
TITLE="Site Images v1"
NOTES="Converted WebP images for site galleries"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SITE_DIR="$(dirname "$SCRIPT_DIR")"

BIKE_SRC="$SITE_DIR/assets/img/originals/bike-photos"
COCKTAIL_SRC="$SITE_DIR/assets/img/originals/cocktail-photos"
BIKE_OUT="$SITE_DIR/assets/img/originals/bike-webp"
COCKTAIL_OUT="$SITE_DIR/assets/img/originals/cocktail-webp"

echo "==> Converting bike photos..."
python3 "$SCRIPT_DIR/prep_images.py" "$BIKE_SRC" "$BIKE_OUT" --keep-names

echo ""
echo "==> Converting cocktail photos..."
python3 "$SCRIPT_DIR/prep_images.py" "$COCKTAIL_SRC" "$COCKTAIL_OUT" --keep-names

echo ""
if ! gh release view "$TAG" --repo "$REPO" &>/dev/null; then
  echo "==> Creating release $TAG..."
  gh release create "$TAG" --repo "$REPO" --title "$TITLE" --notes "$NOTES"
else
  echo "==> Release $TAG already exists — uploading/overwriting assets..."
fi

echo "==> Uploading bike WebP files..."
gh release upload "$TAG" --repo "$REPO" --clobber "$BIKE_OUT"/*.webp

echo "==> Uploading cocktail WebP files..."
gh release upload "$TAG" --repo "$REPO" --clobber "$COCKTAIL_OUT"/*.webp

BASE="https://github.com/$REPO/releases/download/$TAG"
echo ""
echo "Done!"
echo "Base URL: $BASE"
echo ""
echo "Sample URLs:"
echo "  $BASE/bikes-daily-driver.webp"
echo "  $BASE/IMG_0579.webp"
```

- [ ] **Step 2: Make executable and do a dry-run conversion check**

```bash
chmod +x scripts/publish_images.sh
python3 scripts/prep_images.py assets/img/originals/bike-photos /tmp/bike-webp-test --keep-names --dry-run
```

Expected: 14 files listed (including HEIC), no errors.

- [ ] **Step 3: Commit**

```bash
git add scripts/publish_images.sh
git commit -m "feat: add publish_images.sh to convert and upload WebP images to GitHub release"
```

---

## Task 4: Run the publish script

This task is manual execution — no code changes, no commit.

- [ ] **Step 1: Run the publish script**

```bash
bash scripts/publish_images.sh
```

Expected: both conversion summaries printed, then upload confirmation. Final output includes `Base URL: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1`.

- [ ] **Step 2: Verify assets on GitHub**

```bash
gh release view images-v1 --repo joshchiou/joshchiou.github.io --json assets --jq '.assets[].name' | sort
```

Expected: 19 `.webp` filenames listed — 6 fleet bikes + 8 ride photos + 11 cocktail photos (some PORTRAIT filenames included).

> If any HEIC files failed to convert (error line in output), ensure `pillow-heif` is installed (`pip install pillow-heif`) and re-run.

---

## Task 5: Update `_data/bikes.yml` with fleet image URLs

**Files:**

- Modify: `_data/bikes.yml`

- [ ] **Step 1: Replace `image: null` with the release URL for each bike**

The base URL for all assets is:
`https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/`

Apply these six changes (change each `image: null` to the corresponding URL):

| Entry                                             | New value                                                                                                          |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Lemond Zurich (Daily driver)                      | `image: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-daily-driver.webp`      |
| Lemond Tourmalet (Backup bike)                    | `image: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-backup-bike.webp`       |
| Lemond Etape (Wife's main bike)                   | `image: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-wifes-bike.webp`        |
| Specialized Stumpjumper 1998 (Gravel bike)        | `image: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-gravel-bike.webp`       |
| Specialized Stumpjumper 1996 (Wife's gravel bike) | `image: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-wifes-gravel-bike.webp` |
| Lemond Buenos Aires (Tall bike)                   | `image: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-tall-bike.webp`         |

- [ ] **Step 2: Verify Jekyll builds without error**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Expected: `Build complete!` — no YAML or Liquid errors.

- [ ] **Step 3: Commit**

```bash
git add _data/bikes.yml
git commit -m "data: add fleet bike image URLs from images-v1 release"
```

---

## Task 6: Create `_data/bike_gallery.yml`

**Files:**

- Create: `_data/bike_gallery.yml`

- [ ] **Step 1: Write the file**

```yaml
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-gravel-acadia-carriage-road.webp
  caption: "Acadia · Carriage Road"
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-gravel-acadia-eagle-lake.webp
  caption: "Acadia · Eagle Lake"
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-gravel-beaver-brook.webp
  caption: "Beaver Brook"
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-road-dorchester.webp
  caption: "Dorchester"
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-road-nahant.webp
  caption: "Nahant"
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-travel-antibes-nice.webp
  caption: "Antibes · Nice"
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-travel-bangkok.webp
  caption: "Bangkok"
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/bikes-travel-sun-moon-lake.webp
  caption: "Sun Moon Lake"
```

- [ ] **Step 2: Verify Jekyll builds without error**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Expected: `Build complete!`

- [ ] **Step 3: Commit**

```bash
git add _data/bike_gallery.yml
git commit -m "data: add bike ride gallery data file"
```

---

## Task 7: Create `_data/cocktail_gallery.yml`

**Files:**

- Create: `_data/cocktail_gallery.yml`

- [ ] **Step 1: Write the file**

```yaml
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-bar-goto-nyc.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-bar-moonshiner-paris.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-bar-neroli-paris.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-logo-claires-cocktails.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-original-claires-cocktails-2023.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-original-claires-cocktails-2024.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-original-mix.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-original-peaflower-sour.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-original-whiskey-sour.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-restaurant-cha-yen-watertown.webp
- url: https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/cocktails-restaurant-season-to-taste-cambridge.webp
```

- [ ] **Step 2: Verify Jekyll builds without error**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Expected: `Build complete!`

- [ ] **Step 3: Commit**

```bash
git add _data/cocktail_gallery.yml
git commit -m "data: add cocktail gallery data file"
```

---

## Task 8: Add `.swiper-slide-caption` style to `_sass/_projects.scss`

**Files:**

- Modify: `_sass/_projects.scss`

- [ ] **Step 1: Append the caption style at the end of the file**

Add at the very end of `_sass/_projects.scss`:

```scss
/*******************************************************************************
 * Gallery carousel caption
 ******************************************************************************/

.swiper-slide-caption {
  text-align: center;
  font-size: 0.82rem;
  color: var(--global-text-color-light);
  padding: 0.4rem 0 0.25rem;
}
```

- [ ] **Step 2: Verify Jekyll builds without error**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Expected: `Build complete!`

- [ ] **Step 3: Commit**

```bash
git add _sass/_projects.scss
git commit -m "style: add swiper-slide-caption for gallery carousels"
```

---

## Task 9: Add ride gallery carousel to `fun_cycling.md`

**Files:**

- Modify: `_projects/fun_cycling.md`

- [ ] **Step 1: Add `images: slider: true` to the frontmatter**

Change the frontmatter from:

```yaml
---
layout: page
title: Cycling
description: Strava-powered cycling stats — activity calendar and all-time totals.
img: assets/img/projects/fun/cycling.svg
importance: 2
category: fun
chart:
  echarts: true
---
```

to:

```yaml
---
layout: page
title: Cycling
description: Strava-powered cycling stats — activity calendar and all-time totals.
img: assets/img/projects/fun/cycling.svg
importance: 2
category: fun
chart:
  echarts: true
images:
  slider: true
---
```

- [ ] **Step 2: Add the Ride photos section between the fleet carousel and Stats**

Find this line in the file (between the closing `</div>` of the bike carousel and `### Stats`):

```
</div>


### Stats
```

Replace it with:

```
</div>

### Ride photos

<div class="swiper bike-gallery-swiper mb-4">
  <div class="swiper-wrapper">
    {% for photo in site.data.bike_gallery %}
    <div class="swiper-slide">
      <img src="{{ photo.url }}" alt="{{ photo.caption }}" loading="lazy" style="width:100%;display:block;">
      <div class="swiper-slide-caption">{{ photo.caption }}</div>
    </div>
    {% endfor %}
  </div>
  <div class="swiper-pagination"></div>
  <div class="swiper-button-prev"></div>
  <div class="swiper-button-next"></div>
</div>


### Stats
```

- [ ] **Step 3: Add `initRideGallery()` to the existing script block**

In the existing `<script>` block at the bottom of the page, find the line that reads `// ── Toggle buttons ──`. Insert the new function immediately before that comment line:

```javascript
// ── Ride gallery ─────────────────────────────────────────────────────────
function initRideGallery() {
  var el = document.querySelector(".bike-gallery-swiper");
  if (el && typeof Swiper !== "undefined") {
    new Swiper(".bike-gallery-swiper", {
      slidesPerView: 1,
      pagination: { el: ".bike-gallery-swiper .swiper-pagination", clickable: true },
      navigation: {
        nextEl: ".bike-gallery-swiper .swiper-button-next",
        prevEl: ".bike-gallery-swiper .swiper-button-prev",
      },
      autoHeight: true,
    });
  }
}
```

Then update the two boot call sites at the bottom of the same script block. Change:

```javascript
if (document.readyState === "complete") {
  initAllCharts();
  initBikeCarousel();
  showPaceStat();
} else {
  window.addEventListener("load", function () {
    initAllCharts();
    initBikeCarousel();
    showPaceStat();
  });
}
```

to:

```javascript
if (document.readyState === "complete") {
  initAllCharts();
  initBikeCarousel();
  initRideGallery();
  showPaceStat();
} else {
  window.addEventListener("load", function () {
    initAllCharts();
    initBikeCarousel();
    initRideGallery();
    showPaceStat();
  });
}
```

- [ ] **Step 4: Verify Jekyll builds without error**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Expected: `Build complete!`

- [ ] **Step 5: Confirm gallery renders in the built HTML**

```bash
grep -c 'bike-gallery-swiper' _site/projects/fun_cycling/index.html
```

Expected: `3` (the container div, pagination, navigation each reference the class once, plus the script).

- [ ] **Step 6: Commit**

```bash
git add _projects/fun_cycling.md
git commit -m "feat: add ride photo gallery carousel to Cycling page"
```

---

## Task 10: Add photos carousel to `fun_cocktails.md`

**Files:**

- Modify: `_projects/fun_cocktails.md`

- [ ] **Step 1: Add `images: slider: true` to the frontmatter**

Change the frontmatter from:

```yaml
---
layout: page
title: Cocktails
description: Notes from the house bar.
img: assets/img/projects/fun/cocktails.svg
importance: 3
category: fun
---
```

to:

```yaml
---
layout: page
title: Cocktails
description: Notes from the house bar.
img: assets/img/projects/fun/cocktails.svg
importance: 3
category: fun
images:
  slider: true
---
```

- [ ] **Step 2: Append the Photos section at the end of the file**

Add after the closing `</div>` of the recipe grid:

```html
### Photos

<div class="swiper cocktail-gallery-swiper mb-4">
  <div class="swiper-wrapper">
    {% for photo in site.data.cocktail_gallery %}
    <div class="swiper-slide">
      <img src="{{ photo.url }}" alt="Cocktail" loading="lazy" style="width:100%;display:block;" />
    </div>
    {% endfor %}
  </div>
  <div class="swiper-pagination"></div>
  <div class="swiper-button-prev"></div>
  <div class="swiper-button-next"></div>
</div>

<script>
  window.addEventListener("load", function () {
    if (typeof Swiper !== "undefined") {
      new Swiper(".cocktail-gallery-swiper", {
        slidesPerView: 1,
        pagination: { el: ".cocktail-gallery-swiper .swiper-pagination", clickable: true },
        navigation: {
          nextEl: ".cocktail-gallery-swiper .swiper-button-next",
          prevEl: ".cocktail-gallery-swiper .swiper-button-prev",
        },
        autoHeight: true,
      });
    }
  });
</script>
```

- [ ] **Step 3: Verify Jekyll builds without error**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | tail -5
```

Expected: `Build complete!`

- [ ] **Step 4: Confirm gallery renders in the built HTML**

```bash
grep -c 'cocktail-gallery-swiper' _site/projects/fun_cocktails/index.html
```

Expected: `3` or more.

- [ ] **Step 5: Commit**

```bash
git add _projects/fun_cocktails.md
git commit -m "feat: add cocktail photo gallery carousel to Cocktails page"
```

---

## Task 11: Final verification

- [ ] **Step 1: Full production build**

```bash
bundle exec jekyll build --strict_front_matter 2>&1 | grep -E "Error|Warning|Build"
```

Expected: `Build complete!` with no errors.

- [ ] **Step 2: Check fleet card images render**

```bash
grep 'bikes-daily-driver.webp\|bikes-backup-bike.webp\|bikes-tall-bike.webp' _site/projects/fun_cycling/index.html
```

Expected: 3 matches (one per fleet card image).

- [ ] **Step 3: Check both gallery slides rendered**

```bash
grep -c 'releases/download/images-v1' _site/projects/fun_cycling/index.html && \
grep -c 'releases/download/images-v1' _site/projects/fun_cocktails/index.html
```

Expected: `8` and `11`.

- [ ] **Step 4: Commit if anything was missed**

If no changes needed, skip. Otherwise:

```bash
git add -p
git commit -m "fix: address final verification issues"
```
