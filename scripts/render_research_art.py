#!/usr/bin/env python3
"""Write the homepage research theme diagrams to _includes/research_theme_art.liquid.

Each research card on the homepage carries a small inline SVG that sketches the idea behind the
theme instead of reusing a paper figure (the papers already appear under Selected publications and
on the project cards). The drawings are conceptual, with no data, axes, or labels. Colors come from
CSS custom properties (.research-theme-art in _sass/_custom.scss), so the same markup works in
light and dark mode.

Usage:
    python3 scripts/render_research_art.py

Edit the shapes here and re-run; don't edit the generated include by hand.
"""

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_includes" / "research_theme_art.liquid"

W, H = 320, 120


def f(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def dot(x, y, r, cls):
    return f'<circle class="{cls}" cx="{f(x)}" cy="{f(y)}" r="{f(r)}"/>'


def proteome() -> str:
    """Clinical trial proteomics: a panel of thousands of proteins, a few of which shift."""
    rng = random.Random(11)
    cols, rows, step = 17, 5, 17
    x0 = (W - (cols - 1) * step) / 2
    y0 = (H - (rows - 1) * step) / 2
    up = {(2, 1), (5, 3), (9, 0), (12, 2), (15, 4), (7, 4)}
    down = {(3, 4), (10, 3), (14, 1)}
    parts = []
    for c in range(cols):
        for r in range(rows):
            x, y = x0 + c * step, y0 + r * step
            if (c, r) in up:
                parts.append(dot(x, y, 4.6, "rt-accent"))
                parts.append(f'<path class="rt-accent-stroke" d="M{f(x)} {f(y - 7)}l0 -5m-2.5 2.5l2.5 -2.5l2.5 2.5"/>')
            elif (c, r) in down:
                parts.append(dot(x, y, 4.6, "rt-warm"))
                parts.append(f'<path class="rt-warm-stroke" d="M{f(x)} {f(y + 7)}l0 5m-2.5 -2.5l2.5 2.5l2.5 -2.5"/>')
            else:
                parts.append(dot(x, y, 2.4 + rng.random() * 0.8, "rt-muted"))
    return "".join(parts)


def genotype() -> str:
    """Population proteomics and genetics: a DNA variant shifts a protein's level."""
    parts = []
    # Double helix on the left.
    xa, xb, cy, amp = 22, 132, 60, 22
    n = 80
    for phase in (0, math.pi):
        pts = []
        for i in range(n + 1):
            x = xa + (xb - xa) * i / n
            y = cy + amp * math.sin((x - xa) / (xb - xa) * 2.5 * math.pi + phase)
            pts.append(f"{f(x)} {f(y)}")
        parts.append(f'<path class="rt-muted-stroke rt-thick" d="M{" L".join(pts)}"/>')
    for k in range(1, 12):
        x = xa + (xb - xa) * k / 12
        t = (x - xa) / (xb - xa) * 2.5 * math.pi
        y1, y2 = cy + amp * math.sin(t), cy + amp * math.sin(t + math.pi)
        cls = "rt-accent-stroke rt-thick" if k == 7 else "rt-muted-stroke"
        parts.append(f'<path class="{cls}" d="M{f(x)} {f(y1)}L{f(x)} {f(y2)}"/>')
    # Arrow.
    parts.append('<path class="rt-muted-stroke rt-thick" d="M148 60h26m-6 -6l6 6l-6 6"/>')
    # Protein level by genotype: three groups of points, rising.
    rng = random.Random(5)
    for i, (gx, med) in enumerate(((208, 84), (252, 63), (296, 40))):
        cls = "rt-accent" if i == 2 else "rt-muted"
        for _ in range(14):
            parts.append(dot(gx + rng.uniform(-11, 11), med + max(-13, min(13, rng.gauss(0, 6))), 3, cls))
        line_cls = "rt-accent-stroke rt-thick" if i == 2 else "rt-ink-stroke rt-thick"
        parts.append(f'<path class="{line_cls}" d="M{gx - 15} {med}h30"/>')
    parts.append('<path class="rt-muted-stroke" d="M188 108h126"/>')
    return "".join(parts)


def cell_types() -> str:
    """Diabetes genetics and single-cell epigenomics: a risk variant in one cell type's open chromatin."""
    parts = []
    # Chromatin accessibility track: a baseline with peaks; the peak under the variant is highlighted.
    base = 46
    peaks = [(44, 10, 6), (86, 16, 7), (130, 8, 5), (178, 13, 6), (236, 26, 7), (284, 9, 6)]
    pts = []
    for i in range(281):
        x = 20 + i
        y = base - sum(h * math.exp(-((x - px) ** 2) / (2 * s * s)) for px, h, s in peaks)
        pts.append(f"{f(x)} {f(y)}")
    parts.append(f'<path class="rt-muted-stroke rt-thick" d="M{" L".join(pts)}"/>')
    hx, hh, hs = peaks[4]
    hpts = [f"{f(x)} {f(base - hh * math.exp(-((x - hx) ** 2) / (2 * hs * hs)))}" for x in range(hx - 16, hx + 17)]
    parts.append(f'<path class="rt-accent-fill" d="M{hx - 16} {base} L{" L".join(hpts)} L{hx + 16} {base}Z"/>')
    # Variant marker above the peak.
    parts.append(f'<path class="rt-warm-stroke" stroke-dasharray="2 3" d="M{hx} 8V{base - hh - 2}"/>')
    parts.append(f'<path class="rt-warm" d="M{hx} 2l4.5 4.5l-4.5 4.5l-4.5 -4.5z"/>')
    # Cell clusters below; the one matching the peak is highlighted.
    rng = random.Random(3)
    for cx, cy, n, cls in ((62, 88, 20, "rt-muted"), (142, 90, 16, "rt-muted"), (236, 88, 22, "rt-accent")):
        for _ in range(n):
            a, r = rng.uniform(0, 2 * math.pi), 20 * math.sqrt(rng.random())
            parts.append(dot(cx + r * math.cos(a) * 1.5, cy + r * math.sin(a) * 0.85, 3, cls))
    return "".join(parts)


ART = {"proteome": proteome, "genotype": genotype, "cell-types": cell_types}


def main() -> None:
    lines = [
        "{% comment %}",
        "  Generated by scripts/render_research_art.py; edit the script, not this file.",
        "  Conceptual diagrams for the homepage research cards: include with art=<id>.",
        "{% endcomment %}",
        "{% case include.art %}",
    ]
    for key, fn in ART.items():
        lines.append(f"  {{% when '{key}' %}}")
        lines.append(
            f'    <svg class="research-theme-art" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet"'
            f' aria-hidden="true" focusable="false">{fn()}</svg>'
        )
    lines.append("{% endcase %}")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
