# Handoff inputs for this repository

Repo-specific rules that apply on top of the `handoff` skill (`~/.claude/skills/handoff/`).
The skill owns the general method (harvesting, deduping, routing each learning to one store) and
the `STATUS.md` / `DECISIONS.md` formats. Only what is peculiar to this repo lives here.

## Where things go

- `docs/STATUS.md`: rewritten in place each session.
- `docs/DECISIONS.md`: append-only, `D-0NN` entries.
- `CLAUDE.md`: the map and the standing rules.
- `docs/site-guide.md`, `docs/design.md`, `docs/writing-style.md`: how the site works, how it
  looks, and how it reads. A new rule about page structure, visuals, or wording belongs in one of
  these, not in `DECISIONS.md`, unless it also needs its reasons recorded.

## Writing rules apply to the handoff files too

American English and no em dashes (see `CLAUDE.md`). Headings in `DECISIONS.md` use a colon,
`## D-013: Title`, not the em dash some other repos use, so the anchor is `#d-013-title`.

## Before committing

Run `npx prettier --check .` (Prettier formats Markdown tables, so run `--write` on the two files
first) and the em dash grep from `CLAUDE.md`, extended to `docs/`. Check that every
`DECISIONS.md#...` link in `STATUS.md` still matches a heading; nothing in CI checks anchors.

## `docs/STATUS.md` §2 states what is live

GitHub Pages serves whatever `deploy.yml` last built from `master`, so §2 says which commit is
deployed and whether that run succeeded, and names anything merged but not yet live (a failed
deploy, or a data workflow that ran without triggering one).

## Owner-only items

Josh holds the decisions on PR #49, uploading any talk deck, and deleting branches. List them as
open items; don't act on them without his say.
