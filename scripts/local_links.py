"""
Replace Colab links to notebooks with relative links to the notebooks in this repository, so they
open in JupyterLab (JUPYTER.md).

- Only markdown links, [text](https://colab...), are changed; "Open in Colab" badges
  (HTML <a href=...>) and bare URLs are kept.
- The target is the same path in this repository, or else the only Book 1 notebook with that file
  name (links to old pyprobml / probml-notebooks paths, or to the wrong chapter). Links whose
  notebook is not in this repository, or whose name is ambiguous, are kept.
- The file is edited as text, so nothing else in it changes.

Usage:
    python scripts/local_links.py notebooks/book1/02/fig_2_17.ipynb [...]
"""
import glob
import os
import re
import sys

COLAB = re.compile(
    r"(?<=\]\()https://colab\.research\.google\.com/github/probml/(?:pyprobml|probml-notebooks)/blob/[^/]+/"
    r"([^)\s\"\\#]+\.ipynb)(?:#[^)\s\"\\]*)?(?=\))"
)
BY_NAME = {}
for p in glob.glob("notebooks/book1/**/*.ipynb", recursive=True):
    if "ipynb_checkpoints" not in p:
        BY_NAME.setdefault(os.path.basename(p), []).append(p.replace(os.sep, "/"))


def find_local(target):
    if target.startswith("notebooks/book1/") and os.path.exists(target):
        return target
    candidates = BY_NAME.get(os.path.basename(target), [])
    return candidates[0] if len(candidates) == 1 else None


def local_links(path):
    with open(path, "rb") as fp:
        raw = fp.read().decode("utf-8")
    here = os.path.dirname(path)
    changed, kept = [], []

    def repl(m):
        local = find_local(m.group(1))
        if local is None:
            kept.append(m.group(1))
            return m.group(0)
        rel = os.path.relpath(local, here).replace(os.sep, "/")
        changed.append(rel)
        return rel

    new = COLAB.sub(repl, raw)
    if changed:
        with open(path, "wb") as fp:
            fp.write(new.encode("utf-8"))
    if changed or kept:
        print(f"{path}: {len(changed)} link(s) -> {', '.join(changed) or '-'}" + (f"; kept {', '.join(kept)}" if kept else ""))


for p in sys.argv[1:]:
    if "ipynb_checkpoints" not in p:
        local_links(p.replace("\\", "/"))
