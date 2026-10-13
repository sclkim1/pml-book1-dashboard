import ast
import csv
import os
import re
import shutil
import sys
from time import time

import nbformat
import pytest
from nbclient import NotebookClient

# Global variables
TIMEOUT = 1200  # seconds
TEST_DIR = "test_results"
MAPPING_CSV = "internal/figures_url_mapping_book1.csv"
KERNEL_NAME = os.environ.get("NB_KERNEL", "python3")  # e.g. NB_KERNEL=pyprobml for a local conda env
os.environ["FIG_DIR"] = "figures"
os.environ["DUAL_SAVE"] = ""  # To save both .pdf and .png
# pymc3's theano-pymc reads numpy.distutils.__config__.blas_opt_info (gone in numpy>=1.22.2) unless
# blas__ldflags is set. On Windows, link the MinGW runtime statically: otherwise modules compiled with
# a g++ on PATH (e.g. Strawberry Perl's) need DLLs Python cannot find. See REPRODUCE.md.
os.environ.setdefault("THEANO_FLAGS", "blas__ldflags=" + (",gcc__cxxflags=-static" if sys.platform == "win32" else ""))


def notebooks_from_mapping(csv_name):
    """
    notebooks/book1/<chap>/<nb_name>.ipynb for every url in the figure mapping
    """
    paths = []
    with open(csv_name) as fp:
        for row in csv.DictReader(fp):
            for url in ast.literal_eval(row["url"]):
                path = "/".join(["notebooks"] + url.split("/")[-3:])
                if path not in paths:
                    paths.append(path)
    return paths


def ignored_names(txt_name="internal/ignored_notebooks.txt"):
    """
    file names of notebooks upstream does not execute (matched by name only, like upstream)
    """
    if not os.path.exists(txt_name):
        return set()
    with open(txt_name) as fp:
        return {line.strip().split("/")[-1] for line in fp if line.strip()}


IGNORED = ignored_names()
# Skip ignored notebooks, and notebooks the upstream mapping lists but upstream does not have
notebooks = [
    nb for nb in notebooks_from_mapping(MAPPING_CSV) if nb.split("/")[-1] not in IGNORED and os.path.exists(nb)
]


# To make error messages human readable
# https://stackoverflow.com/a/38662876
def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


# Outputs upstream notebooks write to the filesystem root, which only root (upstream's CI container)
# can do. Rewritten in memory before execution, so the notebook files stay identical to upstream.
# savefig() without the leading "/" saves into FIG_DIR like every other notebook. See REPRODUCE.md 4.17.
SOURCE_REWRITES = {
    'savefig("/PcaTrainFaceImages.png")': 'savefig("PcaTrainFaceImages.png")',  # pcaImageDemo
}


def apply_rewrites(nb):
    for cell in nb.cells:
        if cell.cell_type == "code":
            for old, new in SOURCE_REWRITES.items():
                cell.source = cell.source.replace(old, new)
    return nb


# To update workflow status for a figure
def save_status(notebook, icon):
    full_path = os.path.join(TEST_DIR, notebook)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    shutil.copy(f"tests/icons/{icon}.png", full_path.replace(".ipynb", ".png"))


@pytest.mark.parametrize("notebook", notebooks)
def test_run_notebooks(notebook):
    init = time()
    try:
        nb = apply_rewrites(nbformat.read(notebook, as_version=4))
        NotebookClient(nb, timeout=TIMEOUT, kernel_name=KERNEL_NAME).execute()
        save_status(notebook, "right")
        print("passed in {:.2f} seconds: {} ".format(time() - init, notebook))
    except Exception as e:
        save_status(notebook, "wrong")
        print("failed after {:.2f} seconds: {} ".format(time() - init, notebook))
        with open(os.path.join(TEST_DIR, notebook.replace(".ipynb", ".log")), "w") as f:
            f.write(escape_ansi(str(e)))
        raise e
