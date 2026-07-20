#!/usr/bin/env python3
"""
Script to generate an academic CV publication list from BibTeX files.
Creates a PDF with publications grouped by type in Harvard citation style.
"""

import bibtexparser
from collections import defaultdict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
import os

# --- Paths (resolved relative to this script, not the working directory) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(BASE_DIR, "fonts")
# Repo root anchor: this script lives in <repo>/scripts/, so the parent of
# BASE_DIR is the repository root. Input bib files and output PDFs are resolved
# relative to it so the build works regardless of the current directory.
REPO_ROOT = os.path.dirname(BASE_DIR)

# --- Shared visual design (kept in sync with the Word tabular CV) ---
# Font family: Inter (bundled in fonts/, OFL licensed). Registering it as a
# family lets ReportLab's <b>/<i> markup map to the right weight files.
FONT_REGULAR = "Inter"
FONT_BOLD = "Inter-Bold"
FONT_SEMIBOLD = "Inter-SemiBold"
FONT_ITALIC = "Inter-Italic"

INK = colors.HexColor("#1a1a1a")      # near-black for primary text
MUTED = colors.HexColor("#666666")    # grey for affiliation / footer
RULE = colors.HexColor("#8a8a8a")     # section-heading and header rules


def register_fonts():
    """Register the bundled Inter font family with ReportLab (idempotent)."""
    if FONT_REGULAR in pdfmetrics.getRegisteredFontNames():
        return
    variants = {
        "Inter": "Inter-Regular.ttf",
        "Inter-Bold": "Inter-Bold.ttf",
        "Inter-Italic": "Inter-Italic.ttf",
        "Inter-BoldItalic": "Inter-BoldItalic.ttf",
        "Inter-SemiBold": "Inter-SemiBold.ttf",
    }
    for name, filename in variants.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, filename)))
    pdfmetrics.registerFontFamily(
        "Inter",
        normal="Inter",
        bold="Inter-Bold",
        italic="Inter-Italic",
        boldItalic="Inter-BoldItalic",
    )
    # Make Inter ReportLab's default base font so its built-in Helvetica is
    # never referenced (not even as an unused, non-printing default).
    from reportlab import rl_config
    rl_config.canvas_basefontname = FONT_REGULAR


def fix_strings(string):
    """Replaces LaTeX special characters with proper Unicode characters.
    
    Parameters
    ----------
    string : str
        The string to be modified.

    Returns
    -------
    str
        The input string with LaTeX characters replaced with Unicode
    """
    replacements = {
        '{\\"a}': 'ä', '{\\\"a}': 'ä', r'\"a': 'ä',
        '{\\"u}': 'ü', '{\\\"u}': 'ü', r'\"u': 'ü',
        '{\\"o}': 'ö', '{\\\"o}': 'ö', r'\"o': 'ö',
        '{\\"A}': 'Ä', '{\\\"A}': 'Ä', r'\"A': 'Ä',
        '{\\"U}': 'Ü', '{\\\"U}': 'Ü', r'\"U': 'Ü',
        '{\\"O}': 'Ö', '{\\\"O}': 'Ö', r'\"O': 'Ö',
        '{\\ss}': 'ß', '\\ss': 'ß',
        "{\\'e}": 'é', r"\'e": 'é',
        '{\\`e}': 'è', r'\`e': 'è',
        '{\\^e}': 'ê', r'\^e': 'ê',
        '{\\~n}': 'ñ', r'\~n': 'ñ',
        r'\&': '&', r'\%': '%', r'\_': '_', r'\#': '#',
    }
    
    for latex, unicode_char in replacements.items():
        string = string.replace(latex, unicode_char)

    # LaTeX dash conventions: "--" is an en dash, "---" an em dash. Convert the
    # longer sequence first so it isn't half-consumed by the en-dash rule.
    string = string.replace('---', '—').replace('--', '–')

    # Remove remaining curly braces
    string = string.replace('{', '').replace('}', '')
    return string


def import_bibtex(bibtex_file_location):
    """Read a BibTeX file and create year-based dict.

    Parameters
    ----------
    bibtex_file_location : str
        Path to a BibTeX document

    Returns
    -------
    dict
        Keys are years, values are BibTeX entries.
    """
    with open(bibtex_file_location, 'r', encoding='utf-8') as bibtex_file:
        bibtex_str = bibtex_file.read()
    
    bib_database = bibtexparser.loads(bibtex_str)
    entries = bib_database.entries
    entries.sort(key=lambda x: x.get('year', '0000'), reverse=True)
    
    entries_by_year = defaultdict(list)
    for entry in entries:
        entries_by_year[entry.get('year', 'Unknown')].append(entry)
    
    return entries_by_year


def format_author_names(authors, bold_name='Gräbner'):
    """Format author names with bold emphasis for specified author.

    Parameters
    ----------
    authors : str
        The author field from a BibTeX file
    bold_name : str
        Last name to be bolded (default: 'Gräbner')
    
    Returns
    -------
    str
        Author names formatted with HTML bold tags
    """
    authors = fix_strings(authors)
    authors = authors.split(" and ")
    authors = [author.split(", ") for author in authors]
    
    # Format as "LastName FirstInitial."
    formatted = []
    for author in authors:
        if len(author) > 1:
            formatted_author = f"{author[0]} {author[1][0]}."
        else:
            formatted_author = author[0]
        
        # Bold the specified name
        if bold_name.lower() in formatted_author.lower():
            formatted_author = f"<b>{formatted_author}</b>"
        
        formatted.append(formatted_author)
    
    return ", ".join(formatted)


def render_article(entry):
    """Format a journal article in Harvard style.

    Parameters
    ----------
    entry : dict
        A BibTeX entry of type 'article'

    Returns
    -------
    str
        HTML-formatted citation string
    """
    authors = format_author_names(entry.get("author", ""))
    title = fix_strings(entry.get("title", ""))
    journal = fix_strings(entry.get("journal", ""))
    volume = entry.get("volume", "")
    pages = fix_strings(entry.get("pages", ""))
    number = entry.get("number", "")
    year = entry.get("year", "") or "n.d."
    doi = entry.get("doi", "")

    citation = f"{authors} ({year}). {title}"
    if journal:
        citation += f", <i>{journal}</i>"

    if volume:
        citation += f", <b>{volume}</b>"
    if number:
        citation += f"({number})"
    if pages:
        citation += f": {pages}"
    if doi:
        citation += f". doi: {doi}"
    else:
        citation += "."
    
    return citation


def render_book(entry):
    """Format a book in Harvard style.

    Parameters
    ----------
    entry : dict
        A BibTeX entry of type 'book'

    Returns
    -------
    str
        HTML-formatted citation string
    """
    authors = None
    editors = None
    
    if "author" in entry:
        authors = format_author_names(entry["author"])
    if "editor" in entry:
        editors = format_author_names(entry["editor"])
    
    title = fix_strings(entry.get("title", ""))
    address = fix_strings(entry.get("address", ""))
    publisher = fix_strings(entry.get("publisher", ""))
    year = entry.get("year", "")
    url = entry.get("url", "")

    citation = f" ({year}). <i>{title}</i>. {address}: {publisher}"
    
    if authors:
        citation = authors + citation
    elif editors:
        citation = f"{editors} (Eds.)" + citation
    
    if url:
        citation += f". Available online"
    else:
        citation += "."
    
    return citation


def render_chapter(entry):
    """Format a book chapter in Harvard style.

    Parameters
    ----------
    entry : dict
        A BibTeX entry of type 'incollection'

    Returns
    -------
    str
        HTML-formatted citation string
    """
    authors = format_author_names(entry.get("author", ""))
    editors = format_author_names(entry.get("editor", ""))
    title = fix_strings(entry.get("title", ""))
    booktitle = fix_strings(entry.get("booktitle", ""))
    address = fix_strings(entry.get("address", ""))
    publisher = fix_strings(entry.get("publisher", ""))
    year = entry.get("year", "")
    pages = fix_strings(entry.get("pages", ""))

    citation = f"{authors} ({year}). {title}, in: {editors} (Eds.): <i>{booktitle}</i>. {address}: {publisher}"
    
    if pages:
        citation += f", pp. {pages}"
    
    citation += "."
    return citation


def render_misc(entry):
    """Format a misc publication (blog post, etc.) in Harvard style.

    Parameters
    ----------
    entry : dict
        A BibTeX entry of type 'misc'

    Returns
    -------
    str
        HTML-formatted citation string
    """
    authors = format_author_names(entry.get("author", ""))
    title = fix_strings(entry.get("title", ""))
    journal = fix_strings(entry.get("journal", ""))
    year = entry.get("year", "")
    month = entry.get("month", "")

    citation = f"{authors} ({year}). {title}, in: <i>{journal}</i>, {month}"

    # No "Link" text here: it isn't a working hyperlink in the PDF, so it is
    # dropped from the CV (the website keeps its links via create_bibliography.py).
    citation += "."
    return citation


def render_keynote(entry):
    """Format a keynote/invited talk.

    Parameters
    ----------
    entry : dict
        A BibTeX entry for a keynote

    Returns
    -------
    str
        HTML-formatted string describing the keynote
    """
    title = fix_strings(entry.get("title", ""))
    address = fix_strings(entry.get("address", ""))
    date = entry.get("abstract", "")  # Date stored in abstract field
    type_ = fix_strings(entry.get("type", ""))
    language = entry.get("langid", "").title()
    url = entry.get("url", "")
    
    if url:
        citation = f"{date}: {title}"
    else:
        citation = f"{date}: {title}"
    
    if entry.get("shorttitle"):
        german_title = fix_strings(entry.get("shorttitle"))
        citation += f" ({german_title})"
    
    citation += f", {type_} ({address}, language: {language})"
    
    if entry.get("annotation"):
        annotation = entry.get("annotation")
        citation += f". {annotation}"
    else:
        citation += "."
    
    return citation


def render_podcast(entry):
    """Format a podcast/interview entry.

    Parameters
    ----------
    entry : dict
        A BibTeX entry for a podcast/interview

    Returns
    -------
    str
        HTML-formatted string describing the podcast
    """
    time_content = entry.get("abstract", "")
    date = time_content[:10] if len(time_content) >= 10 else time_content
    kind = time_content[11:] if len(time_content) > 11 else ""
    
    title = fix_strings(entry.get("title", ""))
    collaborator = format_author_names(entry.get("collaborator", ""))
    language = entry.get("langid", "").title()

    citation = f"{date}: {title}, in: <i>{kind}</i> (by {collaborator}; language: {language})"

    # No "Link" text here: it isn't a working hyperlink in the PDF, so it is
    # dropped from the CV (the website keeps its links via create_bibliography.py).
    citation += "."
    
    return citation


def render_workingpaper(entry):
    """Format a working paper entry.

    Parameters
    ----------
    entry : dict
        A BibTeX entry for a working paper

    Returns
    -------
    str
        HTML-formatted citation string
    """
    authors = format_author_names(entry.get("author", ""))
    title = fix_strings(entry.get("title", ""))
    series = fix_strings(entry.get("journal", ""))
    volume = entry.get("volume", "")
    number = entry.get("number", "")
    year = entry.get("year", "")
    url = entry.get("url", "")

    citation = f"{authors} ({year}). {title}, <i>{series}</i>"

    paper_no = volume or number
    if paper_no:
        citation += f", No. {paper_no}"

    if url:
        citation += ". Available online."
    else:
        citation += "."

    return citation


def render_entry(entry, bibtex_style="publication"):
    """Render a BibTeX entry based on its type.

    Parameters
    ----------
    entry : dict
        A BibTeX entry
    bibtex_style : str
        Type of BibTeX file ('publication', 'workingpapers', 'keynotes', 'podcasts')

    Returns
    -------
    str
        HTML-formatted citation string
    """
    if bibtex_style == "keynotes":
        return render_keynote(entry)
    elif bibtex_style == "podcasts":
        return render_podcast(entry)
    elif bibtex_style == "workingpapers":
        return render_workingpaper(entry)
    elif bibtex_style == "publication":
        entry_type = entry.get("ENTRYTYPE", "")
        if entry_type == "article":
            return render_article(entry)
        elif entry_type == "book":
            return render_book(entry)
        elif entry_type == "incollection":
            return render_chapter(entry)
        elif entry_type == "misc":
            return render_misc(entry)
        else:
            print(f"Warning: Unknown entry type '{entry_type}' for entry {entry.get('ID', 'Unknown')}")
            return f"[Entry type '{entry_type}' not supported]"

    return "[Unknown bibtex_style]"


def _cv_page_count(cv_pdf):
    """Return the number of pages in ``cv_pdf``, or None if it can't be read.

    Resolves relative paths against this script's directory. Returns None
    when the file is missing or the optional ``pypdf`` package is absent.
    """
    if not os.path.isabs(cv_pdf):
        cv_pdf = os.path.join(BASE_DIR, cv_pdf)
    if not os.path.exists(cv_pdf):
        print(f"Note: CV file not found for merge: {cv_pdf}")
        return None
    try:
        from pypdf import PdfReader
    except ImportError:
        print("Note: 'pypdf' is not installed; skipping CV merge. "
              "Install it with: pip install pypdf")
        return None
    return len(PdfReader(cv_pdf).pages)


def _merge_pdfs(cv_pdf, pub_list_pdf, merged_output):
    """Concatenate the CV and the publication list into ``merged_output``."""
    from pypdf import PdfWriter, PdfReader
    if not os.path.isabs(cv_pdf):
        cv_pdf = os.path.join(BASE_DIR, cv_pdf)
    writer = PdfWriter()
    for source in (cv_pdf, pub_list_pdf):
        for page in PdfReader(source).pages:
            writer.add_page(page)
    with open(merged_output, "wb") as fh:
        writer.write(fh)


def create_pdf_publication_list(output_filename,
                                publications_bib,
                                nonacademic_bib,
                                workingpapers_bib,
                                keynotes_bib,
                                podcasts_bib,
                                author_name="Prof. Dr. Claudius Gräbner-Radkowitsch",
                                affiliation="Department of Pluralist Economics, Europa-University Flensburg; Institute for the\nComprehensive Analysis of the Economy, Johannes Kepler University Linz",
                                header_cols=(
                                    ("Europa-University Flensburg", "Johannes Kepler University Linz"),
                                    ("Email: claudius@claudius-graebner.com", "Web: www.claudius-graebner.com"),
                                ),
                                footer_title="Publication list",
                                merge_with_cv=None,
                                merged_output="CV_full.pdf"):
    """Create a PDF publication list from BibTeX files.

    Parameters
    ----------
    output_filename : str
        Path for the output PDF file
    publications_bib : str
        Path to academic publications BibTeX file
    nonacademic_bib : str
        Path to non-academic publications BibTeX file
    workingpapers_bib : str
        Path to working papers BibTeX file
    keynotes_bib : str
        Path to keynotes BibTeX file
    podcasts_bib : str
        Path to podcasts/interviews BibTeX file
    author_name : str
        Author's name for the title
    affiliation : str
        Author's institutional affiliation
    header_cols : tuple
        Rows of (left, right) strings for the running page header.
    footer_title : str
        Document label shown in the running footer.
    merge_with_cv : str or None
        If set, path to a CV PDF that the finished publication list is
        appended to (producing ``merged_output`` with continuous page
        numbers). Requires the optional ``pypdf`` package.
    merged_output : str
        Output path for the combined CV + publication list PDF.
    """

    register_fonts()

    # If merging, find out how many pages the CV has so the appended list can
    # continue its page numbering (e.g. "6/13" rather than "1/8").
    cv_pages = _cv_page_count(merge_with_cv) if merge_with_cv else None

    # --- Running header and footer, matching the Word tabular CV ---
    def draw_header_footer(canv, page_num, total_pages):
        width, height = A4
        left, right = 2 * cm, width - 2 * cm

        # Header: name, two-column affiliation, then a rule.
        canv.setFillColor(INK)
        canv.setFont(FONT_SEMIBOLD, 10.5)
        canv.drawCentredString(width / 2, height - 1.15 * cm, author_name)
        canv.setFont(FONT_REGULAR, 7.5)
        canv.setFillColor(MUTED)
        y = height - 1.5 * cm
        for col_left, col_right in header_cols:
            canv.drawCentredString(width / 2, y, f"{col_left}   |   {col_right}")
            y -= 0.32 * cm
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.6)
        canv.line(left, y + 0.05 * cm, right, y + 0.05 * cm)

        # Footer: document label (left) and page number (right).
        canv.setFont(FONT_REGULAR, 8)
        canv.setFillColor(MUTED)
        canv.drawString(left, 1.2 * cm, f"{author_name} – {footer_title}")
        canv.drawRightString(right, 1.2 * cm, f"{page_num}/{total_pages}")

    # Two-pass canvas so the footer can show the correct total page count.
    # ``offset`` shifts numbering when the list is appended to the CV, so the
    # merged document reads e.g. "6/13" while the standalone list reads "1/8".
    def make_numbered_canvas(offset):
        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_pages = []

            def showPage(self):
                self._saved_pages.append(dict(self.__dict__))
                self._startPage()

            def save(self):
                total = len(self._saved_pages) + offset
                for i, state in enumerate(self._saved_pages, start=1):
                    self.__dict__.update(state)
                    draw_header_footer(self, i + offset, total)
                    super().showPage()
                super().save()
        return NumberedCanvas

    # Define styles
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = FONT_REGULAR

    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=19,
        textColor=INK,
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName=FONT_SEMIBOLD
    )

    # Author style
    author_style = ParagraphStyle(
        'Author',
        parent=styles['Normal'],
        fontSize=12,
        textColor=INK,
        spaceAfter=3,
        alignment=TA_LEFT,
        fontName=FONT_BOLD
    )

    # Affiliation style
    affiliation_style = ParagraphStyle(
        'Affiliation',
        parent=styles['Normal'],
        fontSize=9.5,
        textColor=MUTED,
        spaceAfter=20,
        leading=13,
        alignment=TA_LEFT,
        fontName=FONT_REGULAR
    )

    # Section heading style
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=INK,
        spaceAfter=2,
        spaceBefore=14,
        fontName=FONT_SEMIBOLD
    )

    # Citation style. A small hanging indent (first line flush, wrapped lines
    # indented) makes it easier to see where each entry begins.
    citation_style = ParagraphStyle(
        'Citation',
        parent=styles['Normal'],
        fontSize=10.5,
        textColor=INK,
        spaceAfter=8,
        leading=14,
        alignment=TA_LEFT,
        fontName=FONT_REGULAR,
        leftIndent=0.4*cm,
        firstLineIndent=-0.4*cm,
        bulletIndent=0
    )

    toc_style = ParagraphStyle(
        'TOC',
        parent=styles['Normal'],
        fontSize=10.5,
        textColor=INK,
        leftIndent=0.5*cm,
        spaceAfter=3
    )

    # Load BibTeX files
    print(f"Loading academic publications from {publications_bib}...")
    academic_pubs = import_bibtex(publications_bib)

    print(f"Loading working papers from {workingpapers_bib}...")
    workingpapers = import_bibtex(workingpapers_bib)

    print(f"Loading non-academic publications from {nonacademic_bib}...")
    nonacademic_pubs = import_bibtex(nonacademic_bib)

    print(f"Loading keynotes from {keynotes_bib}...")
    keynotes = import_bibtex(keynotes_bib)

    print(f"Loading podcasts/interviews from {podcasts_bib}...")
    podcasts = import_bibtex(podcasts_bib)

    # Separate academic publications by type
    books = defaultdict(list)
    articles = defaultdict(list)
    chapters = defaultdict(list)

    for year, entries in academic_pubs.items():
        for entry in entries:
            entry_type = entry.get("ENTRYTYPE", "")
            if entry_type == "book":
                books[year].append(entry)
            elif entry_type == "article":
                articles[year].append(entry)
            elif entry_type == "incollection":
                chapters[year].append(entry)

    def make_elements():
        """Build a fresh list of flowables (one per rendered PDF)."""
        els = []

        def add_section(title):
            """Append a section heading followed by a full-width rule."""
            heading = Paragraph(title, section_style)
            rule = HRFlowable(width="100%", thickness=0.6, color=RULE,
                              spaceBefore=2, spaceAfter=6)
            els.append(KeepTogether([heading, rule]))

        def add_entries(grouped, style):
            """Append every entry of a section, newest year first."""
            if grouped:
                for year in sorted(grouped.keys(), reverse=True):
                    for entry in grouped[year]:
                        els.append(Paragraph(render_entry(entry, style), citation_style))
            else:
                els.append(Paragraph("<i>No entries</i>", citation_style))

        # Title block
        els.append(Paragraph("Publication list", title_style))
        els.append(Paragraph(author_name, author_style))
        els.append(Paragraph(affiliation, affiliation_style))
        els.append(Spacer(1, 0.3*cm))

        # Table of contents
        els.append(Paragraph("<b>Table of contents</b>", styles['Normal']))
        for toc_line in (
            "1 Peer-reviewed books",
            "2 Peer-reviewed journal articles",
            "3 Peer-reviewed chapters",
            "4 Working papers",
            "5 Other publications",
            "6 Keynotes and invited talks",
            "7 Podcasts and interviews",
        ):
            els.append(Paragraph(toc_line, toc_style))
        els.append(Spacer(1, 0.5*cm))

        # Sections
        sections = [
            ("1 Peer-reviewed books", books, "publication"),
            ("2 Peer-reviewed journal articles", articles, "publication"),
            ("3 Peer-reviewed chapters", chapters, "publication"),
            ("4 Working papers", workingpapers, "workingpapers"),
            ("5 Other publications", nonacademic_pubs, "publication"),
            ("6 Keynotes and invited talks", keynotes, "keynotes"),
            ("7 Podcasts and interviews", podcasts, "podcasts"),
        ]
        for i, (heading, grouped, style) in enumerate(sections):
            add_section(heading)
            add_entries(grouped, style)
            if i < len(sections) - 1:
                els.append(Spacer(1, 0.3*cm))

        return els

    def render(path, offset):
        """Render the publication list to ``path`` with a page-number offset."""
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.7*cm,
            bottomMargin=2*cm,
            title=f"{author_name} – {footer_title}",
            author=author_name,
        )
        doc.build(make_elements(), canvasmaker=make_numbered_canvas(offset))

    # Standalone publication list, always numbered from 1.
    print(f"Generating PDF: {output_filename}")
    render(output_filename, 0)
    print(f"PDF created successfully!")

    # Optionally append the publication list to the tabular CV. The list is
    # re-rendered with the CV's page count as an offset so the combined
    # document has continuous page numbers.
    if merge_with_cv:
        if cv_pages is None:
            print(f"Skipping merge: could not read '{merge_with_cv}' "
                  f"(is pypdf installed and the file present?).")
        else:
            import tempfile
            fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
            os.close(fd)
            try:
                render(tmp_path, cv_pages)
                _merge_pdfs(merge_with_cv, tmp_path, merged_output)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            print(f"Combined CV written to: {merged_output}")

    # Count statistics
    total_books = sum(len(entries) for entries in books.values())
    total_articles = sum(len(entries) for entries in articles.values())
    total_chapters = sum(len(entries) for entries in chapters.values())
    total_workingpapers = sum(len(entries) for entries in workingpapers.values())
    total_nonacademic = sum(len(entries) for entries in nonacademic_pubs.values())
    total_keynotes = sum(len(entries) for entries in keynotes.values())
    total_podcasts = sum(len(entries) for entries in podcasts.values())

    print(f"\nStatistics:")
    print(f"  Books: {total_books}")
    print(f"  Journal articles: {total_articles}")
    print(f"  Book chapters: {total_chapters}")
    print(f"  Working papers: {total_workingpapers}")
    print(f"  Other publications: {total_nonacademic}")
    print(f"  Keynotes and invited talks: {total_keynotes}")
    print(f"  Podcasts and interviews: {total_podcasts}")
    print(f"  Total: {total_books + total_articles + total_chapters + total_workingpapers + total_nonacademic + total_keynotes + total_podcasts}")


if __name__ == "__main__":
    import sys

    # Optional flag: append the publication list to the tabular CV, producing
    # a single CV_full.pdf. Off by default.
    #   python create_bibliography.py            -> Publication_List.pdf only
    #   python create_bibliography.py --merge    -> also writes CV_full.pdf
    merge_requested = "--merge" in sys.argv
    cv_pdf = os.path.join(REPO_ROOT, "cv/GraebnerRadkowitsch-CV.pdf")

    # File paths (the Zotero auto-export bib files that already live in the repo;
    # resolved against REPO_ROOT so they are never duplicated).
    publications_bib = os.path.join(REPO_ROOT, "research/publications/publications.bib")
    nonacademic_bib = os.path.join(REPO_ROOT, "research/publications/nonacademic.bib")
    workingpapers_bib = os.path.join(REPO_ROOT, "research/wp/workingpaper.bib")
    keynotes_bib = os.path.join(REPO_ROOT, "talks/keynotes.bib")
    podcasts_bib = os.path.join(REPO_ROOT, "talks/podcasts.bib")

    output_pdf = os.path.join(REPO_ROOT, "data/Publication_List.pdf")
    merged_output = os.path.join(REPO_ROOT, "data/GraebnerRadkowitsch-CV_full.pdf")

    # Check if files exist
    required_files = [publications_bib, nonacademic_bib, workingpapers_bib, keynotes_bib, podcasts_bib]
    missing_files = [f for f in required_files if not os.path.exists(f)]

    if missing_files:
        print("Error: The following required files are missing:")
        for f in missing_files:
            print(f"  - {f}")
        print("\nPlease ensure all BibTeX files are present in the data/ directory.")
    else:
        create_pdf_publication_list(
            output_filename=output_pdf,
            publications_bib=publications_bib,
            nonacademic_bib=nonacademic_bib,
            workingpapers_bib=workingpapers_bib,
            keynotes_bib=keynotes_bib,
            podcasts_bib=podcasts_bib,
            merge_with_cv=cv_pdf if merge_requested else None,
            merged_output=merged_output,
        )
