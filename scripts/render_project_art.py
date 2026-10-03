#!/usr/bin/env python3
"""Render the illustrated project card images (16:10 SVGs) from synthetic data.

Cards for work without publishable figures (Lilly, Pfizer) and Home Assistant are
drawn as data-shaped illustrations: real chart forms from the work, but synthetic,
unlabeled data that implies no real results.

Usage:
    python3 scripts/render_project_art.py   # writes the Lilly, Pfizer, and Home Assistant card images
                                            # and the homepage clinical trial proteomics image

Requires: pip install numpy matplotlib pillow
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Reference palette (dataviz skill), light surface
SURFACE = "#fcfcfb"
INK_MUTED = "#8a8985"
GRID = "#e4e3df"
BLUE = "#2a78d6"  # categorical 1
ORANGE = "#eb6834"  # categorical 2
YELLOW = "#eda100"  # categorical 4
YELLOW_DARK = "#c98500"
NEUTRAL = "#c9c8c3"
# Lilly brand colors for the Lilly card, sampled from the EASD 2026 deck. The red is the
# logo red; the blue is one step lighter than the deck's navy (#0c376d) so it passes the
# dataviz palette checks (lightness band, CVD separation) against the red.
LILLY_RED = "#e0241a"
LILLY_BLUE = "#2e5a94"
NEUTRAL_DARK = "#a3a29d"

plt.rcParams.update({"svg.fonttype": "none", "svg.hashsalt": "joshchiou", "figure.facecolor": SURFACE, "axes.facecolor": SURFACE})


def canvas(size=(8, 5)):
    return plt.figure(figsize=size)  # 16:10 by default


def clean_axes(ax, baseline=True):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_visible(baseline)
    ax.spines["bottom"].set_color(GRID)
    ax.spines["bottom"].set_linewidth(1.2)
    ax.set_xticks([])
    ax.set_yticks([])


def save(fig, rel, dpi=200):
    """SVG for light drawings; WebP for scatter-heavy ones to keep files small."""
    out = ROOT / rel
    if out.suffix == ".webp":
        from io import BytesIO

        from PIL import Image

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, facecolor=SURFACE)
        Image.open(buf).convert("RGB").save(out, "WEBP", quality=90, method=6)
    else:
        fig.savefig(out, format="svg", facecolor=SURFACE, metadata={"Date": None})
    plt.close(fig)
    print(f"Wrote {rel}")


def lilly(rng, rel="assets/img/projects/work/lilly-proteomics.webp", size=(8, 5), dpi=200):
    """Two-arm longitudinal protein trajectories + a volcano plot."""
    fig = canvas(size)
    weeks = np.array([0, 24, 72])

    ax = fig.add_axes([0.06, 0.12, 0.52, 0.78])
    clean_axes(ax)
    for color, drop in ((LILLY_BLUE, 0.9), (LILLY_RED, 1.6)):
        mean = np.array([0, -drop * 0.8, -drop])
        for _ in range(28):
            noise = rng.normal(0, 0.28, 3)
            noise[0] = rng.normal(0, 0.15)
            ax.plot(weeks, mean + noise, color=color, lw=0.8, alpha=0.16, solid_capstyle="round")
        sd = np.array([0.04, 0.16, 0.2])
        ax.fill_between(weeks, mean - sd, mean + sd, color=color, alpha=0.18, lw=0)
        ax.plot(weeks, mean, color=color, lw=2.6, solid_capstyle="round", zorder=3)
        ax.scatter(weeks, mean, s=70, color=color, edgecolor=SURFACE, linewidth=2, zorder=4)
    for w in weeks:
        ax.axvline(w, color=GRID, lw=1, zorder=0)
    ax.set_xlim(-6, 78)
    ax.set_ylim(-2.6, 0.9)

    ax2 = fig.add_axes([0.64, 0.12, 0.32, 0.78])
    clean_axes(ax2)
    n = 1400
    fc = rng.normal(0, 0.17, n)
    fc[:90] += np.where(rng.uniform(size=90) < 0.7, 1, -1) * rng.uniform(0.15, 0.45, 90)
    p = np.abs(fc) * rng.uniform(9, 17, n) + rng.exponential(0.25, n)
    sig = p > 3.2
    up, down = sig & (fc > 0), sig & (fc < 0)
    ax2.scatter(fc[~sig], p[~sig], s=7, color=NEUTRAL, lw=0, alpha=0.8)
    ax2.scatter(fc[up], p[up], s=16, color=LILLY_RED, edgecolor=SURFACE, linewidth=0.6, zorder=3)
    ax2.scatter(fc[down], p[down], s=16, color=LILLY_BLUE, edgecolor=SURFACE, linewidth=0.6, zorder=3)
    ax2.axhline(3.2, color=GRID, lw=1, ls=(0, (4, 3)), zorder=0)
    ax2.axvline(0, color=GRID, lw=1, zorder=0)
    lim = np.abs(fc).max() * 1.08
    ax2.set_xlim(-lim, lim)
    ax2.set_ylim(0, p.max() * 1.08)
    save(fig, rel, dpi)


def pfizer(rng):
    """Manhattan plot zooming into a colocalized GWAS / pQTL locus."""
    fig = canvas()
    top = fig.add_axes([0.05, 0.6, 0.9, 0.34])
    clean_axes(top)
    sizes = np.array([248, 242, 198, 190, 181, 171, 159, 145, 138, 134, 135, 133, 114, 107, 102, 90, 83, 80, 59, 64, 47, 51])
    starts = np.concatenate([[0], np.cumsum(sizes)[:-1]])
    peaks = {2: 0.45, 6: 0.3, 10: 0.62, 16: 0.5}
    hi_chrom, hi_pos = 10, 0.62
    for c, (s, L) in enumerate(zip(starts, sizes)):
        k = int(L * 1.6)
        x = s + rng.uniform(0, L, k)
        y = rng.exponential(1.0, k)
        if c in peaks:
            px = s + peaks[c] * L
            height = 14 if c == hi_chrom else rng.uniform(7.5, 10)
            m = int(k * 0.35)
            dx = rng.laplace(0, L * 0.09, m)
            xx = px + dx
            yy = height * np.exp(-np.abs(dx) / (L * 0.1)) * rng.beta(4, 1.6, m) + rng.exponential(0.4, m)
            x, y = np.concatenate([x, xx]), np.concatenate([y, yy])
        col = NEUTRAL if c % 2 == 0 else NEUTRAL_DARK
        top.scatter(x, y, s=4, color=col, lw=0)
        if c == hi_chrom:
            px = s + hi_pos * L
            sel = (np.abs(x - px) < L * 0.2) & (y > 3.5)
            top.scatter(x[sel], y[sel], s=10, color=BLUE, lw=0, zorder=3)
    top.axhline(7.3, color=GRID, lw=1, ls=(0, (4, 3)))
    top.set_xlim(-10, starts[-1] + sizes[-1] + 10)
    top.set_ylim(0, 15.5)
    peak_x = starts[hi_chrom] + hi_pos * sizes[hi_chrom]

    # Zoom connectors
    conn = fig.add_axes([0, 0, 1, 1], facecolor="none")
    conn.set_axis_off()
    conn.set_xlim(0, 1)
    conn.set_ylim(0, 1)
    px_fig = 0.05 + 0.9 * (peak_x + 10) / (starts[-1] + sizes[-1] + 20)
    conn.add_patch(Polygon([[px_fig - 0.012, 0.6], [px_fig + 0.012, 0.6], [0.95, 0.47], [0.05, 0.47]], closed=True, color=BLUE, alpha=0.06, lw=0))

    # Colocalized locus: GWAS (blue) above, pQTL (orange) below, shared lead variant
    pos = np.sort(rng.uniform(0, 1, 260))
    lead = 0.52
    r2 = np.clip(np.exp(-np.abs(pos - lead) / 0.07) + rng.normal(0, 0.08, pos.size), 0, 1)
    for i, (color, y0, h) in enumerate(((BLUE, 0.27, 0.19), (ORANGE, 0.05, 0.19))):
        ax = fig.add_axes([0.05, y0, 0.9, h])
        clean_axes(ax)
        strength = (12 if i == 0 else 30) * r2 * rng.uniform(0.6, 1, pos.size) + rng.exponential(0.6, pos.size)
        rgb = np.array(matplotlib.colors.to_rgb(color))
        cols = [tuple(rgb * a + np.array(matplotlib.colors.to_rgb(NEUTRAL)) * (1 - a)) for a in r2]
        order = np.argsort(r2)
        ax.scatter(pos[order], strength[order], s=[10 + 26 * r for r in r2[order]], c=[cols[j] for j in order], edgecolor=SURFACE, linewidth=0.5)
        li = np.argmin(np.abs(pos - lead))
        ax.scatter([pos[li]], [strength.max() * 1.02], s=70, marker="D", color=color, edgecolor=SURFACE, linewidth=1.5, zorder=4)
        ax.axvline(pos[li], color=GRID, lw=1.2, ls=(0, (4, 3)), zorder=0)
        ax.set_xlim(-0.01, 1.01)
        ax.set_ylim(0, strength.max() * 1.18)
    save(fig, "assets/img/projects/work/pfizer-targets.webp")


def home_assistant(rng):
    """A day of solar generation vs. home consumption, with a house glyph."""
    fig = canvas()
    ax = fig.add_axes([0.05, 0.1, 0.9, 0.62])
    clean_axes(ax)
    t = np.linspace(0, 24, 289)
    solar = np.clip(np.exp(-((t - 13) / 3.1) ** 2 / 1), 0, None) * 6.2
    solar *= 1 - 0.18 * np.exp(-((t - 15.2) / 0.35) ** 2)  # a passing cloud
    load = 0.55 + 1.6 * np.exp(-((t - 7.5) / 1.1) ** 2) + 2.3 * np.exp(-((t - 19) / 1.6) ** 2)
    load += np.convolve(rng.normal(0, 0.18, t.size), np.ones(9) / 9, mode="same")
    ax.fill_between(t, 0, solar, color=YELLOW, alpha=0.35, lw=0)
    ax.plot(t, solar, color=YELLOW_DARK, lw=2.4, solid_capstyle="round")
    ax.fill_between(t, 0, np.minimum(solar, load), color=YELLOW, alpha=0.35, lw=0)
    ax.plot(t, load, color=BLUE, lw=2.4, solid_capstyle="round")
    for h in (6, 12, 18):
        ax.axvline(h, color=GRID, lw=1, zorder=0)
    ax.set_xlim(0, 24)
    ax.set_ylim(0, 7.4)

    # House glyph with rooftop panels, top left
    g = fig.add_axes([0.06, 0.66, 0.2, 0.3], facecolor="none")
    g.set_axis_off()
    g.set_xlim(0, 10)
    g.set_ylim(0, 10)
    g.set_aspect("equal")
    ink = "#52514e"
    g.add_patch(Polygon([[1.5, 1], [1.5, 5], [8.5, 5], [8.5, 1]], closed=True, fill=False, ec=ink, lw=2, joinstyle="round"))
    g.add_patch(Polygon([[0.6, 4.8], [5, 8.6], [9.4, 4.8]], closed=False, fill=False, ec=ink, lw=2, joinstyle="round", capstyle="round"))
    for i in range(3):  # panels on the right roof slope
        x0, y0 = 5.6 + i * 1.1, 7.9 - i * 0.95
        g.add_patch(Polygon([[x0, y0], [x0 + 0.95, y0 - 0.82], [x0 + 0.95 - 0.55, y0 - 1.3], [x0 - 0.55, y0 - 0.48]], closed=True, color=BLUE, alpha=0.85, lw=0))
    g.add_patch(Polygon([[4.2, 1], [4.2, 3.3], [5.8, 3.3], [5.8, 1]], closed=True, fill=False, ec=ink, lw=2))
    sun = plt.Circle((1.4, 8.6), 0.9, color=YELLOW, alpha=0.9, lw=0)
    g.add_patch(sun)
    save(fig, "assets/img/projects/fun/home-assistant.svg")


def main():
    lilly(np.random.default_rng(7))
    # 5:2 version for the homepage research theme card
    lilly(np.random.default_rng(7), "assets/img/research_themes/clinical-trial-proteomics.webp", (10, 4), 120)
    pfizer(np.random.default_rng(11))
    home_assistant(np.random.default_rng(3))


if __name__ == "__main__":
    main()
