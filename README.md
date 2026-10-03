# joshchiou.github.io

Personal website of Joshua Chiou: [joshchiou.github.io](https://joshchiou.github.io).

Built on [al-folio](https://github.com/alshedivat/al-folio) by Maruan Al-Shedivat et al.

## Local development

```bash
bundle install
bundle exec jekyll serve
```

Site runs at `http://localhost:4000`.

Or with Docker:

```bash
docker compose up
```

## Structure

| Path | Purpose |
|---|---|
| `_pages/about.md` | Landing page |
| `_data/cv.yml` | CV data |
| `_bibliography/papers.bib` | Publications (jekyll-scholar) |
| `_news/*.md` | News items |
| `_projects/*.md` | Project cards |
| `_data/contributions.yml` | Open-source PR list |
| `scripts/update_strava.py` | Strava data pipeline |
| `scripts/parse_location_history.py` | Google Maps Timeline parser for travel map |

## Documentation

- [CLAUDE.md](CLAUDE.md): start here. Quick reference, build, data pipelines.
- [docs/site-guide.md](docs/site-guide.md): how the site is laid out and how to make common changes.
- [docs/design.md](docs/design.md): visual design rules.
- [docs/writing-style.md](docs/writing-style.md): writing rules (American English, no em dashes).
