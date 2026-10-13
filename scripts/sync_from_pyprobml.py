"""
Copy a subset of Book 1 notebooks, the figure mapping and status icons from probml/pyprobml.

Usage:
    python scripts/sync_from_pyprobml.py --chapters 1 2
"""
import argparse
import csv
import io
import json
import os
import urllib.request

UPSTREAM = "probml/pyprobml"
BRANCH = "master"
RAW = f"https://raw.githubusercontent.com/{UPSTREAM}/{BRANCH}"


def fetch(url):
    with urllib.request.urlopen(url) as r:
        return r.read()


def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fp:
        fp.write(data)


parser = argparse.ArgumentParser(description="sync notebooks from pyprobml")
parser.add_argument("--chapters", type=int, nargs="+", default=[1, 2])
args = parser.parse_args()
chapters = {str(c) for c in args.chapters}

# Chapter names (kept in full; the dashboard only shows chapters with notebooks)
save("internal/chapter_no_to_name_mapping_book1.csv", fetch(f"{RAW}/internal/chapter_no_to_name_mapping_book1.csv"))

# Figure -> notebook mapping, filtered to the selected chapters
text = fetch(f"{RAW}/internal/figures_url_mapping_book1_excluded_dummy_nb.csv").decode()
rows = [row for row in csv.DictReader(io.StringIO(text)) if row["key"].split(".")[0] in chapters]
out = io.StringIO()
writer = csv.DictWriter(out, fieldnames=["key", "url"], lineterminator="\n")
writer.writeheader()
writer.writerows(rows)
save("internal/figures_url_mapping_book1.csv", out.getvalue().encode())
print(f"{len(rows)} figures mapped")

# Notebooks
tree = json.loads(fetch(f"https://api.github.com/repos/{UPSTREAM}/git/trees/{BRANCH}?recursive=1"))["tree"]
prefixes = tuple(f"notebooks/book1/{int(c):02d}/" for c in chapters)
notebooks = [t["path"] for t in tree if t["path"].startswith(prefixes) and t["path"].endswith(".ipynb")]
for path in notebooks:
    save(path, fetch(f"{RAW}/{path}"))
print(f"{len(notebooks)} notebooks copied")

for icon in ["right", "wrong"]:
    save(f"tests/icons/{icon}.png", fetch(f"{RAW}/tests/icons/{icon}.png"))
