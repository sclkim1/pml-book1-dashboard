"""
Remove the "Open in Colab" badges and point the remaining Colab links elsewhere: this repository
does not use Colab (REPRODUCE.md 4.49). Run after local_links.py, which already turned links to
notebooks in this repository into relative links.

- A markdown cell that holds only a badge is deleted; a badge next to other text is removed.
- https://colab.research.google.com/github/<owner>/<repo>/blob/<branch>/<path> (also the typo
  "giathub") becomes:
  - in markdown, a relative link when the notebook is in this repository (a bare URL becomes
    [name](relative path));
  - otherwise the same notebook on GitHub, https://github.com/<owner>/<repo>/blob/<branch>/<path>.
- Kept: links to private Colab notebooks (colab.research.google.com/drive/..., there is no other
  copy) and Colab's own pages in upstream outputs.
- Only cell sources change. The JSON layout (indent, line endings) is kept; a notebook with mixed
  line endings is edited as text (links only).

Usage:
    python scripts/no_colab.py notebooks/book1/01/emnist_viz_jax.ipynb [...]
"""
import glob
import json
import os
import re
import sys

BADGE = re.compile(
    r'<a href="https://colab\.research\.google\.com/[^"]+"[^>]*>\s*<img src="https://colab\.research\.google\.com/'
    r'assets/colab-badge\.svg"[^>]*/?>\s*</a>'
    r"|\[!\[Open [Ii]n Colab\]\(https://colab\.research\.google\.com/assets/colab-badge\.svg\)\]\([^)\s]+\)"
)
COLAB = re.compile(r"https://colab\.research\.google\.com/gi[a-z]*hub/([^/\s]+/[^/\s]+/blob/[^/\s]+/)([^)\s\"'<>#\\]+)(#[^)\s\"'<>\\]*)?")
# a whole markdown cell holding only an HTML badge, in the notebook's JSON text
TEXT_BADGE_CELL = re.compile(
    r'(?<=\n) *\{\r?\n *"cell_type": "markdown",\r?\n(?:(?! *"cell_type")[^\n]*\r?\n)*? *"source": \[\r?\n'
    r' *"<a href=\\"https://colab\.research\.google\.com/[^\n]*colab-badge\.svg[^\n]*</a>"\r?\n *\]\r?\n *\},\r?\n'
)
MD_LINK = re.compile(r"\]\($")  # the URL is the target of a markdown link
# notebooks moved since the link was written (the old path is 404 on GitHub, as it was on Colab)
MOVED = {
    "probml/pyprobml/blob/master/book1/intro/datasets.ipynb": "probml/pyprobml/blob/master/notebooks/tutorials/datasets.ipynb",
    "probml/pyprobml/blob/master/notebooks/text_preproc_torch.ipynb": "probml/pyprobml/blob/master/notebooks/tutorials/text_preproc_torch.ipynb",
}
BY_NAME = {}
for p in glob.glob("notebooks/book1/**/*.ipynb", recursive=True):
    if "ipynb_checkpoints" not in p:
        BY_NAME.setdefault(os.path.basename(p), []).append(p.replace(os.sep, "/"))


def find_local(target):
    if target.startswith("notebooks/book1/") and os.path.exists(target):
        return target
    candidates = BY_NAME.get(os.path.basename(target), [])
    return candidates[0] if len(candidates) == 1 and target.endswith(".ipynb") else None


def relink(text, here, markdown, log):
    def repl(m):
        local = find_local(m.group(2)) if markdown else None
        if local:
            rel = os.path.relpath(local, here).replace(os.sep, "/")
            log.append(rel)
            if MD_LINK.search(text[: m.start()]):
                return rel
            return f"[{os.path.basename(local)}]({rel})"
        log.append("github")
        target = MOVED.get(m.group(1) + m.group(2), m.group(1) + m.group(2))
        return f"https://github.com/{target}{m.group(3) or ''}"

    return COLAB.sub(repl, text)


def layout(raw, nb):
    nl = "\r\n" if "\r\n" in raw else "\n"
    for indent in (1, 2, 4):
        for ascii_ in (False, True):
            s = json.dumps(nb, indent=indent, ensure_ascii=ascii_).replace("\n", nl)
            for end in ("", nl):
                if s + end == raw:
                    return lambda nb: json.dumps(nb, indent=indent, ensure_ascii=ascii_).replace("\n", nl) + end
    return None


def no_colab(path):
    raw = open(path, encoding="utf-8", newline="").read()
    if "colab.research.google.com" not in raw:
        return
    here = os.path.dirname(path)
    nb = json.loads(raw)
    dump = layout(raw, nb)
    badges, links = [], []
    if dump is None:  # mixed line endings: edit the text (badge-only cells, links)
        new = TEXT_BADGE_CELL.sub("", raw)
        badges = [1] * TEXT_BADGE_CELL.subn("", raw)[1]
        new = relink(new, here, False, links)
        if "colab-badge" in new:
            print(f"{path}: WARNING mixed line endings, badge left in place")
        assert len(json.loads(new)["cells"]) == len(nb["cells"]) - len(badges)
    else:
        cells = []
        for c in nb["cells"]:
            src = orig = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
            if c["cell_type"] == "markdown" and BADGE.search(src):
                src = BADGE.sub("", src)
                badges.append(1)
                if not src.strip():
                    continue  # the cell held only the badge
                src = src.lstrip("\n")
            src = relink(src, here, c["cell_type"] == "markdown", links)
            if src != orig:  # unchanged cells keep their exact source
                c["source"] = src.splitlines(keepends=True) if isinstance(c["source"], list) else src
            cells.append(c)
        nb["cells"] = cells
        new = dump(nb)
    if new != raw:
        open(path, "w", encoding="utf-8", newline="").write(new)
        local = sum(l != "github" for l in links)
        print(f"{path}: {len(badges)} badge(s) removed, {local} link(s) local, {len(links) - local} to GitHub")


for p in sys.argv[1:]:
    if "ipynb_checkpoints" not in p:
        no_colab(p.replace("\\", "/"))
