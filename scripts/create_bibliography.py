
#%%
import bibtexparser
from collections import defaultdict
import os

# %%
def fix_strings(string):
    """Replaces irritating symbols in strings

    Replacement concerns mostly Umlaute and my name.
    
    Parameters
    ----------
    string : str
        The string to be modified

    Returns
    -------
    str
        The input string with irritating symbols replaced

    Raises
    ------
    ValueError
        _description_
    ValueError
        _description_
    """
    string = string.replace('{\\"a}', 'ä')
    string = string.replace('{\\"u}', 'ü')
    string = string.replace('{\\"o}', 'ö')
    string = string.replace('{\\"A}', 'Ä')
    string = string.replace('{\\"U}', 'Ü')
    string = string.replace('{\\"O}', 'Ö')
    string = string.replace('{', '')
    string = string.replace('}', '')
    return string

# %%
def import_bibtex(bibtex_file_location) -> dict:
    """Read a bibtex file a create year-based dict

    Parameters
    ----------
    bibtex_file : str
        Path to a bibtex document

    Returns
    -------
    dict
        Keys are years, values bibtex entries.
    """
    with open(bibtex_file_location, 'r') as bibtex_file:
        bibtex_str = bibtex_file.read()
    bib_database = bibtexparser.loads(bibtex_str)
    entries = bib_database.entries
    entries.sort(key=lambda x: x['year'], reverse=True)
    entries_by_year = defaultdict(list)
    for entry in entries:
        entries_by_year[entry['year']].append(entry)
    return entries_by_year
#%%
if False:
    filename = "../research/publications/publications.bib"
    parsed_bibtex = import_bibtex(filename)

#%%
def format_author_names(authors):
    """_summary_

    Parameters
    ----------
    authors : str
        The author field from a bibtex file
    
    Returns
    -------
    str
        Author names formatted in markdown
    """
    my_name_1 =  'gräbner-radkowitsch'
    my_name_2 =  'gräbner'

    authors = fix_strings(authors)
    authors = authors.split(" and ")
    authors = [author.split(", ") for author in authors]
    # authors = [f"{author[0]} {author[1][0]}." for author in authors]
    authors = [f"{author[0]} {author[1][0]}." if len(author)>1 else author[0] for author in authors]
    authors = [f"**{author}**" if my_name_1.lower() in author.lower() else author for author in authors]
    authors = [f"**{author}**" if my_name_2.lower() in author.lower() and my_name_1.lower() not in author.lower() else author for author in authors]
    authors = ", ".join(authors)
    return authors

#%% 
# test_entry = parsed_bibtex["2020"][1]

def render_article(entry) -> str:
    """Turns a bibtex entry for an article into markdown text

    Parameters
    ----------
    entry : dict
        A bibtex entry from a file parsed by `import_bibtex`; should by of type 'article'

    Returns
    -------
    str
        A markdown string in the Harvard citation style
    """
    authors = format_author_names(entry["author"])
    title = fix_strings(entry.get("title"))
    journal = fix_strings(entry.get("journal"))
    volume = entry.get("volume")
    pages = entry.get("pages")
    number = entry.get("number")
    year = entry.get("year")
    doi = entry.get("doi")

    # Further formatting:
    md_line = f"{authors} ({year}). {title}, _{journal}_"
    if volume:
        md_line += f", **{volume}**"
    if number:
         md_line += f"({number})"
    if pages:   
        md_line += f": {pages}"
    if doi:
        return md_line + f". doi: [{doi}](https://doi.org/{doi})"
    
    return md_line + "."
# render_article(test_entry)

#%%
# test_entry_book = parsed_bibtex["2019"][4]

def render_book(entry):
    """Turns a bibtex entry for a book into markdown text

    Parameters
    ----------
    entry : dict
        A bibtex entry from a file parsed by `import_bibtex`; should by of type 'book'

    Returns
    -------
    str
        A markdown string in the Harvard citation style
    """
    try:
        authors = format_author_names(entry["author"])
    except KeyError:
        authors = None
    try:
        editors = format_author_names(entry["editor"])
    except KeyError:
        editors = None
   
    title = fix_strings(entry.get("title"))
    address = fix_strings(entry.get("address"))
    publisher = fix_strings(entry.get("publisher"))
    year = entry.get("year")

    # Further formatting:
    md_line = f" ({year}). _{title}_. {address}: {publisher}."
    if authors:
        md_line = f"{authors}" + md_line
    elif editors:
         md_line = f"{editors} (Eds.)" + md_line
    else:
        raise ValueError(f"No author or editor for entry {entry['ID']}")
    
    return md_line + "."

#%%
# test_entry_chapter = parsed_bibtex["2022"][3]

def render_chapter(entry):
    """Turns a bibtex entry for a book chapter into markdown text

    Parameters
    ----------
    entry : dict
        A bibtex entry from a file parsed by `import_bibtex`; should by of type 'incollection'

    Returns
    -------
    str
        A markdown string in the Harvard citation style
    """
    authors = format_author_names(entry["author"])
    editors = format_author_names(entry["editor"])
    title = fix_strings(entry.get("title"))
    booktitle = fix_strings(entry.get("booktitle"))
    pages = entry["pages"]
    address = fix_strings(entry["address"])
    publisher = fix_strings(entry.get("publisher"))
    year = entry["year"]
    
    md_line = f"{authors} ({year}). {title}, in: {editors} (Eds.): _{booktitle}_. {address}: {publisher}, pp. {pages}"
    return md_line + "."

#%%
# TODO: Later also blogs, etc.: But better with different list?
def render_misc(entry):
    authors = format_author_names(entry["author"])
    title = fix_strings(entry.get("title"))
    journal = fix_strings(entry.get("journal"))
    year = entry["year"]
    month = entry["month"]
    url = entry["url"]
    
    md_line = f"{authors} ({year}). {title}, in: _{journal}_, {month}: [Link]({url})"
    return md_line + "."
    # TODO HIER WEITER
#%%
if False:
    filename2 = "../research/publications/nonacademic.bib"
    parsed_bibtex2 = import_bibtex(filename2)
#%%
def render_keynote(entry):
    """Turn a bibtex entry of a keynote into a markdown string

    This should be used for misc entries in a bibtex file that only
    contains keynotes.
    
    Parameters
    ----------
    entry : dict
        A bibtex entry from a file parsed by `import_bibtex`; should by of type 'incollection'

    Returns
    -------
    str
        Markdown code describing the keynote.
    """
    # authors = format_author_names(entry["author"])
    title = fix_strings(entry.get("title"))
    address = fix_strings(entry.get("address"))
    date = entry["abstract"]
    # month = entry["month"]
    type_ = fix_strings(entry.get("type"))
    language = entry["langid"].title()
    
    if entry.get("url"):
        url = entry["url"]  
        md_line = f"{date}: [{title}]({url})" 
    else:
        md_line = f"{date}: {title}" 
        
    if entry.get("shorttitle"):
        german_title = fix_strings(entry.get("shorttitle"))
        md_line += f" ({german_title})"
    
    md_line += f", {type_} ({address}, language: {language})"
    
    if entry.get("annotation"):
        annotation = entry.get("annotation")
        md_line += f". {annotation}"
    
    return md_line + "."
#%%
if False:
    filename2 = "../talks/keynotes.bib"
    parsed_bibtex2 = import_bibtex(filename2)
    render_keynote(parsed_bibtex2["2022"][0])

#%%
def render_podcast(entry):
    """Turn a bibtex entry of an interview/podcast into a markdown string

    This should be used for misc entries in a bibtex file that only
    contains interview/podcast.
    
    Parameters
    ----------
    entry : dict
        A bibtex entry from a file parsed by `import_bibtex`; should by of type 'incollection'

    Returns
    -------
    str
        Markdown code describing the interview/podcast.
    """
    time_content = entry.get("abstract")
    date = time_content[:10]
    kind = time_content[11:]
    title = fix_strings(entry.get("title"))
    collaborator = format_author_names(entry.get("collaborator"))
    language = entry.get("langid").title()
    
    md_line = f"{date}: {title}, in: _{kind}_ (by {collaborator}; language: {language})"
    if entry.get("url"):
        url = entry.get("url")
        md_line += f": [Link]({url})."
    else:
        md_line += f"."
    return md_line
#%%
if False:
    filename3 = "../talks/podcasts.bib"
    parsed_bibtex3 = import_bibtex(filename3)
    # entry_used = parsed_bibtex3["2023"][0]
    render_podcast(parsed_bibtex3["2022"][0])

#%%
def render_entry(entry, bibtex_style="publication"):
    """Render a bibtex entry into a markdown reference
    
    Wrapper that chooses the right formatting function for articles,
    books or chapters.

    Parameters
    ----------
    entry : dict
        A bibtex entry from a file parsed by `import_bibtex`.
    
    bibtex_style: str, by default: 'publication'
        Can be used to indicate the content of the bibtex file.
    
    Returns
    -------
    str
        A markdown string in the Harvard citation style

    Raises
    ------
    ValueError
        If the bibtex entry is not supported.
    """
    if bibtex_style == "keynotes":
        return render_keynote(entry)
    elif bibtex_style == "podcasts":
        return render_podcast(entry)
    elif bibtex_style == "publication":
        if entry["ENTRYTYPE"] == "article":
            return render_article(entry)
        elif entry["ENTRYTYPE"] == "book":
            return render_book(entry)
        elif entry["ENTRYTYPE"] == "incollection":
            return render_chapter(entry)
        elif entry["ENTRYTYPE"] == "misc":
            return render_misc(entry)
        else:
            raise ValueError()
    else:
        raise NotImplementedError()

#%%
def generate_md_reflist_by_year(parsed_bibtex: dict, bibtex_style="publication") -> str:
    """Create a markdown string with references sorted by year

    Parameters
    ----------
    parsed_bibtex : dict
        A bibtex file that was parsed by `import_bibtex`.

    Returns
    -------
    str
        Markdown code for a bibliography.
    """
    md = ""
    for year, entries in sorted(parsed_bibtex.items(), reverse=True):
        md += f"## {year}\n\n" # The year as heading
        for entry in entries: # The single entries formatted as before
            md += f"- {render_entry(entry, bibtex_style=bibtex_style)}\n\n"

    # determine number of years and entries
    years = len(parsed_bibtex)
    total_entries = 0
    for year, entries in parsed_bibtex.items():
        total_entries += len(entries)

    print("Processed " + str(total_entries) + " entries from " + str(years) + " years.")
    return md

# %%
def save_md_bibliography(parsed_bibtex, destination_path, bibtex_style="publication", destination_div="publications"):
    """Generates a bibliography and saves it into a quarto file

    Parameters
    ----------
    parsed_bibtex : dict
        A bibtex file that was parsed by `import_bibtex`.
    destination_path : str
        The path to the file into which the bibliography should be written.
    destination_div : str, optional
        An anchor in the `destination_path` to indicate where the bibliography should
        be inserted, by default "publications" such that the text is written in the
        lines between `<!-- references -->` and `<!-- /references -->`
    bibtex_style : str, by default: 'publication'
        Can signal particular style of the bibtex file used.

    Returns
    -------
    None
    """
    with open(destination_path, 'r') as file:
        md = file.read()

    start = md.find(f"<!-- {destination_div} -->")
    end = md.find(f"<!-- /{destination_div} -->")
    
    md = md[:start] + f"<!-- {destination_div} -->\n\n" + generate_md_reflist_by_year(
        parsed_bibtex, bibtex_style=bibtex_style) + md[end:]

    with open(destination_path, 'w') as file:
        file.write(md)
        
    return None

# %%
# destination_path = "../research/publications/index.qmd"
if __name__ == "__main__":
    # import os
    # if not os.getenv("QUARTO_PROJECT_RENDER_ALL"):
    #     exit()

    destination_file: str = "research/publications/index.qmd"
    destination_file_keynotes: str = "talks/index.qmd"
    
    bibtex_file_academic: str = "research/publications/publications.bib"
    bibtex_file_nonacademic: str = "research/publications/nonacademic.bib"
    bibtex_file_keynotes: str = "talks/keynotes.bib"
    bibtex_file_podcasts: str = "talks/podcasts.bib"

    print(f"Rendering academic bibliography...")
    print("Reading BibTeX file from " + bibtex_file_academic)
    parsed_bibtex = import_bibtex(bibtex_file_academic)

    print("Writing bibliography to " + destination_file)
    save_md_bibliography(
        parsed_bibtex, destination_file, 
        bibtex_style="publication", 
        destination_div="references")
    print("Done.")
    
    print(f"Rendering non-academic bibliography...")
    print("Reading BibTeX file from " + bibtex_file_nonacademic)
    parsed_bibtex = import_bibtex(bibtex_file_nonacademic)

    print("Writing bibliography to " + destination_file)
    save_md_bibliography(
        parsed_bibtex, destination_file, 
        bibtex_style="publication", 
        destination_div="nonacademicpubs")
    print("Done.")
    
    print(f"Rendering list of keynotes...")
    print("Reading BibTeX file from " + bibtex_file_keynotes)
    parsed_bibtex = import_bibtex(bibtex_file_keynotes)

    print("Writing bibliography to " + destination_file_keynotes)
    save_md_bibliography(
        parsed_bibtex, destination_file_keynotes, 
        bibtex_style="keynotes", 
        destination_div="keynotes")
    print("Done.")
    
    print(f"Rendering list of podcasts and interviews...")
    print("Reading BibTeX file from " + bibtex_file_podcasts)
    parsed_bibtex = import_bibtex(bibtex_file_podcasts)
    print("Writing bibliography to " + destination_file_keynotes)
    save_md_bibliography(
        parsed_bibtex, destination_file_keynotes, 
        bibtex_style="podcasts", 
        destination_div="podcasts")
    print("Done.")
    
