# Academic website

Quarto site for Claudius Gräbner-Radkowitsch. See `CLAUDE.md` for the site
build and the auto-generated bibliography pipeline.

## Building the CV / publication-list PDFs (standalone)

`scripts/build_cv_pdf.py` reads the same `.bib` files the website uses and
produces two PDFs in `data/`:

- `data/Publication_List.pdf` — the formatted publication list.
- `data/GraebnerRadkowitsch-CV_full.pdf` — the tabular CV
  (`cv/GraebnerRadkowitsch-CV.pdf`) with the publication list appended and
  continuous page numbers (only written with `--merge`).

**This is fully independent of the website.** It does *not* render the Quarto
site, is *not* part of the Quarto pre-render pipeline, and touches nothing
outside `data/`. You can run it on its own whenever the bib files change.

### One-time setup

The generator needs the project virtual environment with `reportlab`, `pypdf`,
and `bibtexparser` installed:

```bash
source academicwebsite/bin/activate
pip install reportlab pypdf bibtexparser
```

For the combined CV, export your Word CV (`cv/GraebnerRadkowitsch-CV.docx`) to
`cv/GraebnerRadkowitsch-CV.pdf` first. Without it, only
`data/Publication_List.pdf` is produced. (`cv/*.docx` and
`cv/GraebnerRadkowitsch-CV.pdf` are git-ignored and stay local.)

### Run it

Easiest — double-click **`cv/Build_CV.command`** in Finder. It cd's to the repo
root, activates the venv, runs the generator with `--merge`, and waits for a
keypress. (First run: right-click → Open to clear the Gatekeeper warning.)

Or from a terminal at the repo root:

```bash
source academicwebsite/bin/activate

python scripts/build_cv_pdf.py            # data/Publication_List.pdf only
python scripts/build_cv_pdf.py --merge    # also writes data/GraebnerRadkowitsch-CV_full.pdf
```

Paths are resolved relative to the repo root, so it works from any working
directory. To publish updated PDFs on the website afterwards, render the site
as usual (`quarto render`) and commit `data/*.pdf`.
