# Design

The visual rules the site follows. The goal is a quiet, professional academic site: one typeface,
one accent color, generous white space, and real figures from the work instead of decoration.

## Foundations

- **Template.** al-folio. Upstream styles in `_sass/` stay untouched; every site-specific style
  goes in `_sass/_custom.scss`, which is imported last. Each block there starts with a comment
  naming what it styles.
- **Layout.** Content column max width 900px (`max_width` in `_config.yml`). Project-page prose
  is held to about 70 characters per line.
- **Typeface.** Inter (Google Fonts) for everything, with system sans-serif fallbacks. Numbers that
  line up in columns (years, stats, counts) use tabular figures.
- **Color.** One accent color, the theme color, used for links, focus rings, and hover states:

  | Token                                    | Light     | Dark      |
  | ---------------------------------------- | --------- | --------- |
  | `--global-theme-color`                   | `#1d6aa5` | `#3fb0d4` |
  | `--global-hover-color`                   | `#175a8c` | `#6cc4e0` |
  | `--global-text-color-light` (muted text) | `#6b6b6b` | `#a0a0a0` |

  These replace al-folio's defaults, which fail WCAG AA contrast. Any new color must meet 4.5:1
  for text against both the light and the dark background.

- **Dark mode.** Supported on every page. The toggle sets `data-theme` on `<html>` (handled by
  `assets/js/theme.js`), so dark styles key on `html[data-theme="dark"]`, not on the
  `prefers-color-scheme` media query. Check every change in both modes.
- **Icons.** Font Awesome, used sparingly (social links, buttons, the star on Selected). No emoji
  in headings or body text; the travel page's country flags are the exception.

## Components

| Component           | Where                               | Rules                                                                                                         |
| ------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Project card        | `/projects/`                        | 16:10 image, title (1.15rem, weight 600), one-line muted summary, small lift on hover                         |
| Research theme card | Homepage                            | 5:2 image on top, short title, one-sentence summary, links to the project; border turns accent color on hover |
| Project page        | `/projects/*/`                      | TL;DR box, `##` sections (1.5rem, weight 600), "Related:" line, image credit line                             |
| Selected paper      | `/publications/`                    | 4:3 thumbnail at left, title, plain-language `tldr`, authors, venue, link buttons                             |
| Talk                | `/publications/`                    | Year, title, venue, outlined link buttons for slides or video                                                 |
| Repo card           | `/code/`                            | Name, one-sentence description, language dot, stars, forks                                                    |
| Stat tile           | Code, cycling, Home Assistant pages | Large number with a small label; missing values show "n/a"                                                    |

Section labels on the projects and publications pages ("work", "fun", "Selected", "All
publications", "Talks and presentations", "Press") share one style: left-aligned, 1.2rem bold,
text color, with a 2px rule; only the Selected star uses the accent. Thumbnails and TL;DRs appear
only in Selected lists; everywhere else publication entries use the full width so titles line up.
On short pages the footer sits at the bottom of the window.

Headings: page titles in the navigation and the homepage section labels ("research", "selected
publications", "news") are lowercase, which is al-folio's style. Headings inside pages use sentence
case. Project titles use title case. CV section names use title case; the publications page shows
the CV's "Talks & Presentations" section under the sentence-case heading "Talks and presentations".

## Images

- **Project cards** are 16:10. Paper cards use a cropped panel from the paper, with annotation text
  removed so the figure reads at card size, and an `img_credit` line on the page. Photos are real
  photos. Work without public figures gets an illustration drawn from synthetic data (see below).
- **Homepage research theme images** are 5:2 (1200x480) in `assets/img/research_themes/`: two
  panels side by side on white, ideally from two different papers, each fitted whole into its half
  so nothing is cropped at any screen width, with a thin gray vertical divider (4px, `#c4c4c4`) between them. `img_credit` in `_data/research_themes.yml` names the
  sources. Never point a theme card at a 16:10 card image; it gets cropped on phones.
- **Publication thumbnails** are 4:3, in `assets/img/publication_preview/` or reused from the
  project cards. Each selected paper should have its own; don't reuse one thumbnail for several papers.
- **Formats.** WebP for photos and dense figures, through `scripts/prep_images.py` (responsive
  480/800/1400px versions). SVG only for simple drawings. Link previews (`og_image`) are JPG,
  because social sites don't reliably read WebP or SVG.
- **Alt text.** Card images sit next to their title, so they use empty alt text. Any image that
  carries information on its own needs a real description.

## Illustrations and charts

Drawn illustrations (Lilly, Pfizer, Home Assistant, travel) come from scripts, never from hand
editing:

- They show real chart forms from the work (trajectories, volcano plots, Manhattan plots, maps) but
  use synthetic data, carry no axis labels, and imply no results. The credit line says so.
- They use the dataviz skill's reference palette: surface `#fcfcfb`, blue `#2a78d6`, orange
  `#eb6834`, yellow `#eda100`, gray `#c9c8c3` for context marks. Assign hues in that order and
  validate any new palette with the skill's `validate_palette.js`.
- The Lilly card (and its homepage version) uses Lilly colors instead: red `#e0241a` (the logo red)
  and blue `#2e5a94`, one step lighter than the deck navy `#0c376d` so the pair passes the
  validator.
- Thin lines, small round markers with a 1–2px surface-colored outline, no gridlines beyond a few
  faint guides.

## Motion and accessibility

- Motion is subtle: a small hover lift on cards and a fade-in on scroll (`.animate-in`, enabled
  only once `html.anim-ready` is set). Everything respects `prefers-reduced-motion`.
- Keyboard focus is always visible (2px accent-color outline).
- Links in prose are underlined, so they don't rely on color alone.
- Heading levels go in order: `##` under the page title, then `###`. Card titles inside a section
  are `h3`. (The CV layout is upstream al-folio and still skips levels.)
- Before shipping a visual change, run axe-core on the changed pages in light and dark mode and fix
  anything serious, and take screenshots at 1280px and 390px wide.

## Analytics

GoatCounter, which is privacy-friendly and sets no cookies. No other trackers.
