"""
Copy a subset of Book 1 notebooks, the figure mapping and status icons from probml/pyprobml.

Usage:
    python scripts/sync_from_pyprobml.py --chapters 1 2
"""
import argparse
import ast
import csv
import io
import json
import os
import subprocess
import sys
import urllib.request

# Notebooks edited in this repository: not overwritten by a sync
LOCAL_EDITS = {
    "notebooks/book1/01/linreg_poly_vs_degree.ipynb",
    # REPRODUCE.md 4.26
    "notebooks/book1/01/tfidf_demo.ipynb",
    "notebooks/book1/02/prob.ipynb",
    "notebooks/book1/08/autodiff_tf.ipynb",
    "notebooks/book1/20/pca.ipynb",
    "notebooks/book1/20/ae_mnist_tf.ipynb",
    "notebooks/book1/07/linalg.ipynb",
    "notebooks/book1/11/supplementary/linreg_sklearn.ipynb",
    # REPRODUCE.md 4.29
    "notebooks/book1/11/supplementary/linreg_pymc3.ipynb",
    "notebooks/book1/08/sgd_comparison.ipynb",
    "notebooks/book1/04/bayes_intro.ipynb",
    "notebooks/book1/08/autodiff_jax.ipynb",
    "notebooks/book1/13/flax_intro.ipynb",
    "notebooks/book1/08/opt_flax.ipynb",
    "notebooks/book1/08/opt_jax.ipynb",
    "notebooks/book1/10/logreg_jax.ipynb",
    "notebooks/book1/10/logreg_pytorch.ipynb",
    "notebooks/book1/08/lrschedule_tf.ipynb",
    "notebooks/book1/13/mlp_1d_regression_hetero_tfp.ipynb",
}

# Notebooks upstream ignores that run here (flax pinned, REPRODUCE.md 4.29): dropped from the list
UNIGNORED = {
    "notebooks/book1/13/multi_gpu_training_jax.ipynb",
    "notebooks/book1/14/conv2d_jax.ipynb",
    "notebooks/book1/14/lenet_jax.ipynb",
    "notebooks/book1/15/attention_jax.ipynb",
    "notebooks/book1/15/multi_head_attention_jax.ipynb",
    "notebooks/book1/15/positional_encoding_jax.ipynb",
    "notebooks/book1/15/rnn_jax.ipynb",
    # arviz API fixed in the notebook (REPRODUCE.md 4.29); upstream lists its old path
    "notebooks/misc/bayes_intro.ipynb",
    # notebook bug fixed (x overwritten by a vector before the has_aux cell)
    "notebooks/misc/autodiff_jax.ipynb",
    # ported from flax.optim / fit_flax.py to optax
    "notebooks/misc/flax_intro.ipynb",
    "notebooks/misc/opt_flax.ipynb",
    "notebooks/misc/opt_jax.ipynb",
    "notebooks/misc/logreg_jax.ipynb",
    "notebooks/misc/logreg_pytorch.ipynb",
}

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

# Notebooks upstream does not execute in CI (matched by file name, as upstream does)
ignored = fetch(f"{RAW}/internal/ignored_notebooks.txt").decode().splitlines(keepends=True)
save("internal/ignored_notebooks.txt", "".join(l for l in ignored if l.strip() not in UNIGNORED).encode())

tree = json.loads(fetch(f"https://api.github.com/repos/{UPSTREAM}/git/trees/{BRANCH}?recursive=1"))["tree"]
book1_notebooks = [t["path"] for t in tree if t["path"].startswith("notebooks/book1/") and t["path"].endswith(".ipynb")]


def fix_url(url):
    """
    The upstream mapping has a few urls whose notebook lives in another chapter folder
    (e.g. book1/21/gmm_2d.ipynb is really book1/03/gmm_2d.ipynb). If exactly one Book 1
    notebook has that file name, point the url there.
    """
    path = "notebooks/" + "/".join(url.split("/")[-3:])
    if path in book1_notebooks:
        return url
    candidates = [p for p in book1_notebooks if p.split("/")[-1] == path.split("/")[-1]]
    if len(candidates) != 1:
        print(f"WARNING: {path} not found upstream; left as is")
        return url
    print(f"fixed mapping: {path} -> {candidates[0]}")
    return url.replace(path, candidates[0])


# Figure -> notebook mapping, filtered to the selected chapters
text = fetch(f"{RAW}/internal/figures_url_mapping_book1_excluded_dummy_nb.csv").decode()
rows = [row for row in csv.DictReader(io.StringIO(text)) if row["key"].split(".")[0] in chapters]
for row in rows:
    row["url"] = str([fix_url(url) for url in ast.literal_eval(row["url"])])
out = io.StringIO()
writer = csv.DictWriter(out, fieldnames=["key", "url"], lineterminator="\n")
writer.writeheader()
writer.writerows(rows)
save("internal/figures_url_mapping_book1.csv", out.getvalue().encode())
print(f"{len(rows)} figures mapped")

# Notebooks: everything in the selected chapters, plus mapped notebooks that live elsewhere
prefixes = tuple(f"notebooks/book1/{int(c):02d}/" for c in chapters)
mapped = {"notebooks/" + "/".join(url.split("/")[-3:]) for row in rows for url in ast.literal_eval(row["url"])}
notebooks = sorted({p for p in book1_notebooks if p.startswith(prefixes)} | (mapped & set(book1_notebooks)))
for path in notebooks:
    if path in LOCAL_EDITS and os.path.exists(path):
        print(f"kept local edit: {path}")
        continue
    save(path, fetch(f"{RAW}/{path}"))
print(f"{len(notebooks)} notebooks synced")

# Colab links between notebooks -> local links, as in the committed notebooks (JUPYTER.md)
subprocess.run([sys.executable, "scripts/local_links.py", *notebooks], check=True)
# `!mkdir figures # for saving plots` -> os.makedirs (REPRODUCE.md 4.30)
subprocess.run([sys.executable, "scripts/fix_mkdir.py", *notebooks], check=True)

for icon in ["right", "wrong"]:
    save(f"tests/icons/{icon}.png", fetch(f"{RAW}/tests/icons/{icon}.png"))
