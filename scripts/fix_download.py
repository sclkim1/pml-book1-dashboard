"""Extract d2l data archives only once (REPRODUCE.md 4.32).

The d2l helper `download_extract()` (chapters 15 and 20) keeps a downloaded archive whose SHA-1
matches, but runs `extractall` on every run: IMDb (100k files), GloVe, SNLI, ... are extracted
again each time, and two notebooks sharing `../data` can read a half-written file. Extract once
and write `<archive>.extracted` afterwards; an interrupted extraction has no marker and is redone.

Usage: python scripts/fix_download.py <notebook.ipynb>...   (edits the files as text)
"""
import re
import sys

# the JSON source line `    fp.extractall(base_dir)\n` (indent of the JSON line kept)
EXTRACT = re.compile(rb'( *)"    fp\.extractall\(base_dir\)\\n",(\r?\n)')


def extract_new(m):
    ind, nl = m.group(1), m.group(2)
    lines = [
        rb"    # extract once (fix_download.py): the marker is written after a complete extraction",
        rb"    done = fname + \".extracted\"",
        rb"    if not os.path.exists(done):",
        rb"        fp.extractall(base_dir)",
        rb"        open(done, \"w\").close()",
    ]
    return b"".join(ind + b'"' + line + rb'\n",' + nl for line in lines)


changed = 0
for path in sys.argv[1:]:
    with open(path, "rb") as f:
        text = f.read()
    new, n = EXTRACT.subn(extract_new, text)
    if n:
        with open(path, "wb") as f:
            f.write(new)
        changed += 1
print(f"download_extract fixed in {changed} notebooks")
