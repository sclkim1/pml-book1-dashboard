"""Replace `!mkdir figures # for saving plots` in notebooks (REPRODUCE.md 4.30).

On Windows `!` runs cmd.exe, which has no `#` comments: mkdir creates folders named `#`, `for`,
`saving`, `plots` next to the notebook, and prints "already exists" errors for them. Use
os.makedirs instead, which works everywhere and is silent when `figures` exists.

Usage: python scripts/fix_mkdir.py <notebook.ipynb>...   (edits the files as text)
"""
import re
import sys

PATTERN = re.compile(rb'"!mkdir figures +# for saving plots')
NEW = (rb'"import os; os.makedirs(\"figures\", exist_ok=True)'
       rb'  # for saving plots (!mkdir makes folders \"#\", \"for\", ... on Windows)')

changed = 0
for path in sys.argv[1:]:
    with open(path, "rb") as f:
        text = f.read()
    new, n = PATTERN.subn(NEW, text)
    if n:
        with open(path, "wb") as f:
            f.write(new)
        changed += 1
print(f"!mkdir fixed in {changed} notebooks")
