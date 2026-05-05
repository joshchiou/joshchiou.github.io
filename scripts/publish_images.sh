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
echo "  $BASE/cocktails-bar-goto-nyc.webp"
