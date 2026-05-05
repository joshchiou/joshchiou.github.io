# Image GitHub Release & Galleries Design

**Date:** 2026-05-04
**Status:** Approved

## Overview

Convert original photos (including HEIC) to web-ready WebP, publish them as assets on a
GitHub release (`images-v1`), and wire them into two new Swiper carousels — a cocktail
photo gallery on the Cocktails page and a ride photo gallery on the Cycling page — while
also populating the existing bike fleet cards with their corresponding images.

## 1. HEIC Support in `prep_images.py`

Add `pillow-heif` as an optional import using the same guard pattern already used for
`piexif`. On import success, call `pillow_heif.register_heif_opener()` so Pillow can
open `.heic`/`.heif` files transparently. Extend `SUPPORTED_EXTS` with `.heic` and
`.heif`. If `pillow-heif` is not installed, emit a one-time warning at startup and skip
HEIC files rather than crashing.

A `scripts/requirements.txt` lists `Pillow` and `pillow-heif` as dependencies.

## 2. Publish Script — `scripts/publish_images.sh`

Single command that converts originals and uploads to the GitHub release:

1. Run `prep_images.py assets/img/originals/bike-photos assets/img/originals/bike-webp --keep-names`
2. Run `prep_images.py assets/img/originals/cocktail-photos assets/img/originals/cocktail-webp --keep-names`
3. Create release `images-v1` (title "Site Images v1") if it does not already exist via `gh release create`
4. Upload all WebP files from both output dirs with `gh release upload --clobber` (idempotent re-runs)
5. Print the base download URL on completion

Output dirs (`assets/img/originals/bike-webp/`, `assets/img/originals/cocktail-webp/`) live
under `assets/img/originals/` which is already untracked, so nothing enters git.

Requires: `gh` CLI authenticated, `pillow-heif` installed.

## 3. Data Files

### `_data/bikes.yml` — fleet card image URLs

Add `image:` field to each bike pointing to the release asset URL. Mapping:

| Bike | File |
|------|------|
| Lemond Zurich (Daily driver) | `bikes-daily-driver.webp` |
| Lemond Tourmalet (Backup) | `bikes-backup-bike.webp` |
| Lemond Etape (Wife's main) | `bikes-wifes-bike.webp` |
| Specialized Stumpjumper 1998 (Gravel) | `bikes-gravel-bike.webp` |
| Specialized Stumpjumper 1996 (Wife's gravel) | `bikes-wifes-gravel-bike.webp` |
| Lemond Buenos Aires (Tall bike) | `bikes-tall-bike.webp` |

Base URL: `https://github.com/joshchiou/joshchiou.github.io/releases/download/images-v1/`

### `_data/bike_gallery.yml` — ride photos (new file)

8 entries with `url` and `caption`:

| File | Caption |
|------|---------|
| `bikes-gravel-acadia-carriage-road.webp` | Acadia · Carriage Road |
| `bikes-gravel-acadia-eagle-lake.webp` | Acadia · Eagle Lake |
| `bikes-gravel-beaver-brook.webp` | Beaver Brook |
| `bikes-road-dorchester.webp` | Dorchester |
| `bikes-road-nahant.webp` | Nahant |
| `bikes-travel-antibes-nice.webp` | Antibes · Nice |
| `bikes-travel-bangkok.webp` | Bangkok |
| `bikes-travel-sun-moon-lake.webp` | Sun Moon Lake |

### `_data/cocktail_gallery.yml` — cocktail photos (new file)

11 entries with `url` only (source filenames are meaningless camera IDs, no captions).

`--keep-names` preserves the original stem exactly (no lowercasing, no hyphenation).
Resulting filenames:
`20240511_152817.webp`, `IMG_0579.webp`, `IMG_1344.webp`, `IMG_1495.webp`,
`IMG_1704.webp`, `IMG_1776.webp`, `IMG_2086.webp`, `IMG_2979.webp`,
`IMG_5214.webp`, `PXL_20210220_072803154.PORTRAIT.webp`,
`PXL_20240524_161029474.PORTRAIT.webp`

## 4. Page Updates

### `fun_cycling.md`

- Add `images: slider: true` to frontmatter (loads Swiper CSS/JS)
- Add a **"Ride photos"** section between the fleet carousel and Stats
- Static Swiper carousel rendered by Jekyll from `_data/bike_gallery.yml`
- Each slide: `<img>` tag with release URL + caption overlay div
- Swiper initialized via a small inline `<script>` at the bottom of the page (NOT the
  travel page's JS-based dynamic approach — slides are rendered by Jekyll at build time,
  so `new Swiper('.bike-gallery-swiper', { pagination, navigation, autoHeight: true })`
  is all that's needed)

### `fun_cocktails.md`

- Add `images: slider: true` to frontmatter
- Add a **"Photos"** section at the bottom of the page
- Static Swiper carousel from `_data/cocktail_gallery.yml`
- No captions; otherwise identical markup/init to the bike gallery (statically rendered,
  small inline init script)

## 5. Image Parameters

All conversions use `prep_images.py` defaults:
- Quality: 82
- Max width: 1600 px
- Max height: 1200 px
- `--keep-names` (preserves descriptive filenames)

## Out of Scope

- Automating the release publish via GitHub Actions (manual script only)
- Adding `.gitignore` rules (originals dir already untracked)
- Captions for cocktail photos
