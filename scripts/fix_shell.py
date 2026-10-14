"""Replace Unix shell commands in notebooks that fail on Windows (REPRODUCE.md 4.30).

On Windows `!` runs cmd.exe, and its (Korean) error messages show up garbled in the notebook:
- `!mkdir figures # for saving plots`: cmd.exe has no `#` comments, so mkdir creates folders named
  `#`, `for`, `saving`, `plots` and prints "already exists" errors. Use os.makedirs instead, which
  works everywhere and is silent when `figures` exists.
- `!ls [-l] [dir]`: there is no `ls` in cmd.exe. Use os.listdir instead.
- `!unzip ...`: on a rerun the files exist and unzip waits for a "replace? [y]es/[n]o" answer, so
  the cell hangs. Add `-o` (overwrite). (Not Windows-specific.)

Usage: python scripts/fix_shell.py <notebook.ipynb>...   (edits the files as text)
"""
import re
import sys

MKDIR = re.compile(rb'"!mkdir figures +# for saving plots')
MKDIR_NEW = (rb'"import os; os.makedirs(\"figures\", exist_ok=True)'
             rb'  # for saving plots (!mkdir makes folders \"#\", \"for\", ... on Windows)')

# a whole source line `!ls`, `!ls -l`, `!ls <dir>` or `!ls -l <dir>` (JSON string, optional \n)
LS = re.compile(rb'"!ls(?: -l)?(?: ([^"\\ ]+))?(?=(?:\\n)?")')


UNZIP = re.compile(rb'"( *)!unzip (?!-o )')


def ls_new(m):
    path = m.group(1)
    arg = rb'\"' + path + rb'\"' if path else b""
    return rb'"import os; print(sorted(os.listdir(' + arg + rb')))  # was ' + m.group(0)[1:] + rb' (no ls on Windows)'


changed = 0
for path in sys.argv[1:]:
    with open(path, "rb") as f:
        text = f.read()
    new, n1 = MKDIR.subn(MKDIR_NEW, text)
    new, n2 = LS.subn(ls_new, new)
    new, n3 = UNZIP.subn(rb'"\1!unzip -o ', new)
    if n1 or n2 or n3:
        with open(path, "wb") as f:
            f.write(new)
        changed += 1
print(f"shell commands fixed in {changed} notebooks")
