# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A [Quarto](https://quarto.org/) academic website for Claudius Gräbner-Radkowitsch. The site is built from `.qmd` files and deployed statically. The output lives in `_site/`.

## Build commands

```bash
# Activate the Python virtual environment first (required for the pre-render script)
source academicwebsite/bin/activate

# Full render (also runs the bibliography pre-render script automatically)
quarto render

# Preview with live reload
quarto preview --render all --no-watch-inputs --no-browse

# Convenience wrapper (activates venv + preview)
bash render_web.sh
```

The Python venv (`academicwebsite/`) uses Python 3.9.6 and must be active before rendering so Quarto can run the pre-render script.

## Architecture: bibliography generation

The most important non-obvious system is the **auto-generated bibliography pipeline**:

1. `_quarto.yml` declares `pre-render: scripts/create_bibliography.py`, so Quarto runs it before every build.
2. The script reads `.bib` files and injects formatted Markdown into `.qmd` files **in place**, between HTML comment anchors.

The anchor pattern used in `.qmd` files:
```html
<!-- references -->
...auto-generated content replaced here on every render...
<!-- /references -->
```

**Do not manually edit content between these anchor comments** — it will be overwritten on the next render.

| BibTeX source | Target `.qmd` | Anchor |
|---|---|---|
| `research/publications/publications.bib` | `research/publications/index.qmd` | `references` |
| `research/publications/nonacademic.bib` | `research/publications/index.qmd` | `nonacademicpubs` |
| `research/wp/workingpaper.bib` | `research/wp/index.qmd` | `workingpapers` |
| `talks/keynotes.bib` | `talks/index.qmd` | `keynotes` |
| `talks/podcasts.bib` | `talks/index.qmd` | `podcasts` |

To add/update a publication, talk, or podcast: **edit the corresponding `.bib` file**, then re-render.

The script (`scripts/create_bibliography.py`) handles four BibTeX entry types for publications (`article`, `book`, `incollection`, `misc`) and two custom styles (`keynotes`, `podcasts`). The author's name is detected case-insensitively and bolded in output.

## Site structure

- `_quarto.yml` — site config: navigation, HTML theme (cosmo), CSS
- `index.qmd` — home page (trestles template with bio)
- `about.qmd` — extended about page
- `posts.qmd` — blog listing page; individual posts in `posts/` (frozen: won't re-execute unless forced)
- `research/publications/` — publications page + `.bib` sources
- `research/wp/` — working papers
- `research/projects/` — research projects
- `talks/` — keynotes, invited talks, podcasts + `.bib` sources
- `teaching/` — teaching overview; `teaching/abm-de/` is an embedded course
- `styles.css` — minimal custom CSS overrides
- `img/` — images; `data/` — static file downloads (e.g. PGP key)
- `_extensions/` — Quarto extensions (e.g. `academicons` for ORCID/Google Scholar icons)
