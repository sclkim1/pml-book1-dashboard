"""Fix the d2l download helpers in notebooks (REPRODUCE.md 4.32, 4.35).

- `download_extract()` (chapters 15 and 20) keeps a downloaded archive whose SHA-1 matches, but runs
  `extractall` on every run: IMDb (100k files), GloVe, SNLI, ... are extracted again each time, and
  two notebooks sharing `../data` can read a half-written file. Extract once and write
  `<archive>.extracted` afterwards; an interrupted extraction has no marker and is redone.
- `download()` saves whatever the server sends: a dead link (e.g. wikitext-2's old S3 bucket) is
  saved as a 487-byte XML error page and fails later with "File is not a zip file". Add
  `r.raise_for_status()` so it fails at the download with the HTTP error.
- Archives made on macOS can contain `Icon\r` files (SNLI): a name with a carriage return cannot be
  created on Windows (`OSError: [Errno 22] Invalid argument: '..\\data\\snli_1.0\\Icon\r'`).
  Skip such entries when extracting.

Usage: python scripts/fix_download.py <notebook.ipynb>...   (edits the files as text)
"""
import re
import sys

# the JSON source line `    fp.extractall(base_dir)\n` (indent of the JSON line kept)
EXTRACT = re.compile(rb'( *)"    fp\.extractall\(base_dir\)\\n",(\r?\n)')

# the JSON source line `    r = requests.get(url, stream=True, verify=True)\n`, not yet followed by raise_for_status
REQUEST = re.compile(rb'( *)"    r = requests\.get\(url, stream=True, verify=True\)\\n",(\r?\n)(?! *"    r\.raise_for_status)')


# the extraction inside the extract-once block (8 spaces): skip names with a carriage return
EXTRACT_ALL = re.compile(rb'( *)"        fp\.extractall\(base_dir\)\\n",(\r?\n)')


def extract_all_new(m):
    ind, nl = m.group(1), m.group(2)
    lines = [
        rb"        # skip macOS Icon\\r files (fix_download.py): such names cannot be created on Windows",
        rb"        names = fp.namelist() if ext == \".zip\" else fp.getmembers()",
        rb"        fp.extractall(base_dir, members=[m for m in names if \"\\r\" not in getattr(m, \"name\", m)])",
    ]
    return b"".join(ind + b'"' + line + rb'\n",' + nl for line in lines)


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


def request_new(m):
    ind, nl = m.group(1), m.group(2)
    return (m.group(0)
            + ind + rb'"    r.raise_for_status()  # fix_download.py: do not save an error page as the file\n",' + nl)


changed = 0
for path in sys.argv[1:]:
    with open(path, "rb") as f:
        text = f.read()
    new, n1 = EXTRACT.subn(extract_new, text)
    new, n2 = REQUEST.subn(request_new, new)
    new, n3 = EXTRACT_ALL.subn(extract_all_new, new)
    if n1 or n2 or n3:
        with open(path, "wb") as f:
            f.write(new)
        changed += 1
print(f"download helpers fixed in {changed} notebooks")
