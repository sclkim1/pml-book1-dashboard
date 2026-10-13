"""
Replace Colab links to Book 1 notebooks with relative links to the notebooks in this repository,
so they open in JupyterLab (JUPYTER.md). Only links whose target notebook exists locally are changed.

Usage:
    python scripts/local_links.py notebooks/book1/02/fig_2_17.ipynb [...]
"""
import os
import re
import sys

COLAB = re.compile(r"https://colab\.research\.google\.com/github/probml/pyprobml/blob/master/(notebooks/book1/[^)\s\"\\]+\.ipynb)")


def local_links(path):
    with open(path, "rb") as fp:
        raw = fp.read().decode("utf-8")
    here = os.path.dirname(path)
    changed = []

    def repl(m):
        target = m.group(1)
        if not os.path.exists(target):
            return m.group(0)
        rel = os.path.relpath(target, here).replace(os.sep, "/")
        changed.append(rel)
        return rel

    new = COLAB.sub(repl, raw)
    if changed:
        with open(path, "wb") as fp:
            fp.write(new.encode("utf-8"))
    print(f"{path}: {len(changed)} link(s) -> {', '.join(changed) if changed else '-'}")


for p in sys.argv[1:]:
    local_links(p.replace("\\", "/"))
