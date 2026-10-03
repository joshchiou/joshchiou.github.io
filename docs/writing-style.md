# Writing style

Rules for every piece of visible text on the site: page prose, card summaries, publication
summaries, news items, data-file descriptions, alt text, button labels, and strings in JavaScript.
They also apply to this repo's docs. Commit messages and code comments should follow them too.

## The two hard rules

1. **American English.** analyze, color, modeling, center, gray, traveled, catalog, program,
   license (noun and verb), percent. The site declares `lang: en-US` in `_config.yml`.
2. **No em dashes (—).** Rewrite the sentence instead of swapping in another dash:
   - an aside → commas or parentheses: "Joshua Chiou (Director, Genomics at Lilly)"
   - an explanation or list → a colon: "Home bartending notes: classic recipes, amaro obsessions, and tiki detours."
   - two thoughts → two sentences: "We don't chase bucket lists. We'd rather return somewhere we love."
   - a link followed by a description → a comma or colon: `**Related:** [UK Biobank Pharma Proteomics Project](…), the pQTL resource that…`
   - a missing value in a stat tile → "n/a"
   - a title separator → a pipe: "Projects | Joshua Chiou"

   En dashes (–) are fine only in number and date ranges (2019–2023, pages 455–466). Don't use
   double hyphens (--) as dashes either.

To check, run `grep -rn "—" _pages _projects _news _data _includes _layouts _config.yml _bibliography assets/js`.
It should return nothing outside vendored libraries.

## Voice

- First person singular, present tense for current work ("I lead translational proteomics…"),
  past tense for finished work ("I completed my PhD…").
- Write for a scientist in a neighboring field: precise terms where they matter, no jargon for its
  own sake, acronyms spelled out on first use on each page ("UK Biobank Pharma Proteomics Project
  (UKB-PPP)", "type 1 diabetes (T1D)").
- Plain and specific. Say what was measured or found, with numbers when there are numbers. Avoid
  hype words such as groundbreaking, cutting-edge, novel (unless it is the paper's own claim), and
  leverage.
- Claims match the paper. For unpublished work, say only what is already public, such as the EASD
  abstract, and call exploratory results exploratory.

## Plain, not polished

Write the way you'd explain the work to a colleague over coffee. Two failure modes to watch for:
prose that sounds machine-made (stacked nouns, "-ing" chains, every sentence the same length) and
prose that reaches for effect (taglines, framing, significance statements).

- Say what you did and what you found. Cut sentences that only tell the reader the work matters
  ("opening new avenues for…", "shifted the field's view…", "providing a framework for…").
- Prefer verbs to noun phrases: "we mapped pQTLs", not "characterization of pQTLs was performed";
  "linked", not "provided linkage".
- One idea per sentence. Break up chains of "revealing…, linking…, enabling…".
- No taglines or wordplay closers ("Three trips, three different Frances.") and no rhetorical
  framing ("has long been understood as…", "challenged this view").
- Phrases to avoid, with what to write instead:

  | Avoid                                    | Write                                        |
  | ---------------------------------------- | -------------------------------------------- |
  | has long been understood as              | is usually described as                      |
  | opening new avenues for                  | (cut, or name the specific next step)        |
  | is unusually informative                 | is useful because…                           |
  | at the intersection of                   | (say what you do)                            |
  | foundational resource, comprehensive map | widely used dataset, one of the largest maps |
  | an artifact that would mislead           | a side effect of weight loss                 |
  | toolkit, connective layer, framework     | the methods, the pipeline                    |
  | leverage, enable, drive delivery of      | use, let, build                              |
  | previously underappreciated              | (cut, or say who missed it and why)          |
  | tick a new box, chase bucket lists       | keep adding new places                       |

- Humor is fine where it's clearly intended (the Claire timeline, the cycling card). Keep it
  specific and dry rather than cute.

## Names and terms

- **Lilly** in prose; "Eli Lilly and Company" only where a legal name is needed. Josh's title is
  "Director, Genomics" (capitalized as a title).
- Drug names are lowercase (tirzepatide, semaglutide); trial names keep their capitals
  (SURMOUNT-5). Gene symbols are italic where the format allows.
- "Exocrine pancreas" means acinar and ductal cells; don't shorten it to acinar.
- Journal names are italic: _Nature_, _Nature Genetics_.
- Doses and units take a space: 15 mg, 2.4 mg.
- Numbers: commas in thousands (54,000), numerals for 10 and above, and for any measurement.
- Dates in prose: "October 1, 2026" or "Oct 2026". Front-matter dates stay in ISO format.

## Punctuation and capitalization

- Serial (Oxford) comma: "lights, climate, and media".
- Headings inside pages: sentence case ("Design principles", "Countries and cities"). Project
  titles: title case. Navigation labels and homepage section labels: lowercase. CV section names:
  title case (they are also lookup keys, so don't rename them casually).
- Use "and" in prose and headings; "&" only in short labels where space is tight (the homepage
  tagline, CV section names).
- Straight quotes in code and data files are fine; Markdown and Liquid output them as written.

## Patterns by content type

**Card summary** (`description` in a project's front matter): one line, no period needed if it is a
fragment, under about 120 characters. Example: "Pre-competitive consortium mapping the genetic
architecture of the human plasma proteome."

**TL;DR box** on a project page: one sentence saying what the project is for.

**Publication `tldr`**: one plain-language sentence, past tense, starting with a verb, saying what
was done and what it showed. Example: "Measured about 3,000 blood proteins in 54,000 UK Biobank
participants and mapped more than 14,000 genetic variants that influence their levels, most of
them previously unknown."

**News item**: one or two sentences, past tense, starting with a verb ("Promoted to…", "Gave an
oral presentation at…"), linking the thing itself.

**Repository description**: one short sentence on what the repo contains, then the role where it adds something ("Author."
or "Maintainer."), under about 60 characters in total so the card doesn't cut it off.

**Image credit** (`img_credit`): "Figure adapted from Sun et al., _Nature_ 2023 (Fig. 2a), CC BY
4.0." For synthetic illustrations: "Illustration with synthetic data; it shows no study results."

**Link text** names the destination ("EASD 2026", "r-mmrm"), never "click here" or a bare URL,
except where the URL itself is the name (a dashboard address).

## What not to publish

- Slides or figures without employer clearance. The EASD 2026 deck (© Lilly) is not cleared. The
  Festival of Genomics 2025 deck is on hold until Josh says otherwise.
- Results from work that is not yet public beyond what the abstract states.
- Anything that implies a synthetic illustration shows real data.
