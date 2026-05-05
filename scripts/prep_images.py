#!/usr/bin/env python3
"""
prep_images.py — Convert photos to web-ready WebP, strip all metadata.

Usage:
    python3 scripts/prep_images.py <input_dir> <output_dir> [options]

Options:
    --quality INT      WebP quality, 1-100 (default: 82)
    --max-width INT    Resize if wider than this many pixels (default: 1600)
    --max-height INT   Resize if taller than this many pixels (default: 1200)
    --keep-names       Keep original filenames (just change extension to .webp)
    --dry-run          Show what would be done without writing files

Examples:
    # Convert a folder of phone photos for a travel gallery:
    python3 scripts/prep_images.py ~/Downloads/trip assets/img/travel/europe-2026

    # High-quality project images, wider max:
    python3 scripts/prep_images.py ~/photos/lab assets/img/projects --quality 88 --max-width 2000

    # Preview only:
    python3 scripts/prep_images.py ~/Downloads/trip assets/img/travel --dry-run
"""

import argparse
import io
import os
import sys
import re
from pathlib import Path

try:
    from PIL import Image, ExifTags
except ImportError:
    sys.exit("Pillow not found. Run: pip install Pillow")

try:
    import piexif
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_HEIF = True
except ImportError:
    HAS_HEIF = False

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.tiff', '.tif', '.bmp', '.webp', '.heic', '.heif'}

# EXIF orientation tag
ORIENTATION_TAG = 274  # 0x0112


def safe_name(stem: str) -> str:
    """Lowercase, replace spaces/special chars with hyphens."""
    stem = stem.lower().strip()
    stem = re.sub(r'[^a-z0-9]+', '-', stem)
    stem = stem.strip('-')
    return stem or 'image'


def correct_orientation(img: Image.Image) -> Image.Image:
    """Rotate image so it displays correctly after EXIF is stripped."""
    try:
        exif = img.getexif()
        orientation = exif.get(ORIENTATION_TAG)
        rotations = {3: 180, 6: 270, 8: 90}
        if orientation in rotations:
            img = img.rotate(rotations[orientation], expand=True)
    except Exception:
        pass
    return img


def strip_metadata(img: Image.Image) -> Image.Image:
    """Return a clean copy with no EXIF, ICC profile, or other metadata."""
    # Re-encode through a buffer to drop all ancillary chunks
    buf = io.BytesIO()
    # Save as PNG first (lossless, strips EXIF) then re-open
    clean = Image.new(img.mode if img.mode in ('RGB', 'RGBA', 'L') else 'RGB', img.size)
    clean.paste(img)
    return clean


def process_image(src: Path, dst: Path, quality: int, max_width: int, max_height: int,
                  keep_names: bool, dry_run: bool, index: int) -> dict:
    """Process a single image. Returns a result dict."""
    stem = src.stem if keep_names else f'{index:03d}-{safe_name(src.stem)}'
    out_path = dst / f'{stem}.webp'

    src_size_kb = src.stat().st_size / 1024

    if dry_run:
        return {'src': str(src), 'dst': str(out_path), 'src_kb': src_size_kb, 'dry_run': True}

    try:
        img = Image.open(src)

        # Fix orientation before stripping EXIF
        img = correct_orientation(img)

        # Convert palette/transparency modes
        if img.mode == 'P':
            img = img.convert('RGBA')
        if img.mode == 'RGBA':
            # Flatten transparency onto white background for WebP lossy
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if over limits (preserve aspect ratio)
        w, h = img.size
        if w > max_width or h > max_height:
            img.thumbnail((max_width, max_height), Image.LANCZOS)

        # Strip metadata: save to buffer without any info dict, then re-open
        buf = io.BytesIO()
        img.save(buf, format='WEBP', quality=quality, method=6)
        buf.seek(0)

        # Verify the output has no EXIF
        check = Image.open(buf)
        has_exif = bool(check.getexif())
        buf.seek(0)

        dst.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(buf.read())

        out_size_kb = out_path.stat().st_size / 1024
        savings_pct = int((1 - out_size_kb / src_size_kb) * 100) if src_size_kb > 0 else 0

        return {
            'src': str(src),
            'dst': str(out_path),
            'src_kb': src_size_kb,
            'out_kb': out_size_kb,
            'savings_pct': savings_pct,
            'dims': f'{check.width}×{check.height}',
            'exif_stripped': not has_exif,
            'ok': True,
        }

    except Exception as e:
        return {'src': str(src), 'dst': str(out_path), 'error': str(e), 'ok': False}


def main():
    parser = argparse.ArgumentParser(description='Convert images to web-ready WebP, strip metadata.')
    parser.add_argument('input_dir', help='Source folder containing images')
    parser.add_argument('output_dir', help='Destination folder for WebP output')
    parser.add_argument('--quality', type=int, default=82,
                        help='WebP quality 1-100 (default: 82)')
    parser.add_argument('--max-width', type=int, default=1600,
                        help='Max output width in pixels (default: 1600)')
    parser.add_argument('--max-height', type=int, default=1200,
                        help='Max output height in pixels (default: 1200)')
    parser.add_argument('--keep-names', action='store_true',
                        help='Preserve original filenames (just change ext to .webp)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would happen without writing files')
    args = parser.parse_args()

    src_dir = Path(args.input_dir).expanduser().resolve()
    dst_dir = Path(args.output_dir).expanduser().resolve()

    if not src_dir.exists():
        sys.exit(f'Input directory not found: {src_dir}')

    images = sorted(
        f for f in src_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS
    )

    if not images:
        sys.exit(f'No supported images found in {src_dir}')

    if not HAS_HEIF:
        heic = [f for f in images if f.suffix.lower() in {'.heic', '.heif'}]
        if heic:
            print(f'  Warning: {len(heic)} HEIC file(s) found but pillow-heif is not installed.')
            print('  Install it with: pip install pillow-heif\n')

    print(f'\n{"DRY RUN — " if args.dry_run else ""}Processing {len(images)} image(s)')
    print(f'  Quality: {args.quality}  Max: {args.max_width}×{args.max_height}px')
    print(f'  Output:  {dst_dir}\n')

    results = []
    for i, src in enumerate(images, start=1):
        r = process_image(src, dst_dir, args.quality, args.max_width, args.max_height,
                          args.keep_names, args.dry_run, i)
        results.append(r)

        if args.dry_run:
            print(f'  [{i:3d}] {src.name}  →  {Path(r["dst"]).name}  ({r["src_kb"]:.0f} KB)')
        elif r.get('ok'):
            exif_mark = '✓' if r['exif_stripped'] else '⚠ exif?'
            print(f'  [{i:3d}] {src.name}  →  {Path(r["dst"]).name}')
            print(f'        {r["src_kb"]:.0f} KB → {r["out_kb"]:.0f} KB  '
                  f'({r["savings_pct"]}% smaller)  {r["dims"]}  metadata: {exif_mark}')
        else:
            print(f'  [{i:3d}] ERROR {src.name}: {r.get("error")}')

    if not args.dry_run:
        ok = [r for r in results if r.get('ok')]
        errs = [r for r in results if not r.get('ok') and 'dry_run' not in r]
        total_in  = sum(r['src_kb'] for r in ok)
        total_out = sum(r['out_kb'] for r in ok)
        savings   = int((1 - total_out / total_in) * 100) if total_in > 0 else 0
        print(f'\nDone. {len(ok)} converted, {len(errs)} errors.')
        print(f'Total: {total_in/1024:.1f} MB → {total_out/1024:.1f} MB  ({savings}% smaller)\n')

        if errs:
            print('Errors:')
            for r in errs:
                print(f'  {Path(r["src"]).name}: {r["error"]}')


if __name__ == '__main__':
    main()
