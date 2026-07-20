#!/bin/bash
#
# Double-click this file to (re)generate the publication list AND the combined
# CV (tabular CV + publication list) from the .bib files in this repository,
# writing data/Publication_List.pdf and data/GraebnerRadkowitsch-CV_full.pdf.
#
# Requires an up-to-date cv/GraebnerRadkowitsch-CV.pdf (export it from Word
# after any edits to cv/GraebnerRadkowitsch-CV.docx). Without it, only the
# publication list is produced.
#

# Move to the repository root (this script lives in <repo>/cv/).
cd "$(dirname "$0")/.." || exit 1

echo "==============================================="
echo " Generating combined CV (data/GraebnerRadkowitsch-CV_full.pdf)"
echo "==============================================="
echo

# Activate the project's Python virtual environment.
if [ -f "academicwebsite/bin/activate" ]; then
    source academicwebsite/bin/activate
else
    echo "ERROR: virtual environment 'academicwebsite/' not found."
    echo "Create it and install the dependencies (reportlab, pypdf, bibtexparser)."
    echo
    read -n 1 -s -r -p "Press any key to close..."
    exit 1
fi

# Warn if the CV PDF is missing (the merge is only produced when it exists).
if [ ! -f "cv/GraebnerRadkowitsch-CV.pdf" ]; then
    echo "NOTE: cv/GraebnerRadkowitsch-CV.pdf not found."
    echo "The publication list will still be created; export your tabular CV"
    echo "from Word to cv/GraebnerRadkowitsch-CV.pdf to also get the merged"
    echo "data/GraebnerRadkowitsch-CV_full.pdf."
    echo
fi

# Run the generator. It always writes the standalone publication list first,
# then (with --merge) appends it to the CV as a second output if cv/1-CV.pdf
# is present.
python scripts/build_cv_pdf.py --merge
STATUS=$?

echo
if [ $STATUS -eq 0 ]; then
    echo "Done. data/Publication_List.pdf has been updated."
    if [ -f "cv/GraebnerRadkowitsch-CV.pdf" ]; then
        echo "      data/GraebnerRadkowitsch-CV_full.pdf (CV + publication list) has been updated."
    else
        echo "      data/GraebnerRadkowitsch-CV_full.pdf was NOT written (cv/GraebnerRadkowitsch-CV.pdf missing)."
    fi
else
    echo "Something went wrong (exit code $STATUS). See the messages above."
fi

echo
read -n 1 -s -r -p "Press any key to close..."
echo
