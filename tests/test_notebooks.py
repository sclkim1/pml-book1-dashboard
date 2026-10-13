import ast
import csv
import os
import re
import shutil
from time import time

import nbformat
import pytest
from nbclient import NotebookClient

# Global variables
TIMEOUT = 1200  # seconds
TEST_DIR = "test_results"
MAPPING_CSV = "internal/figures_url_mapping_book1.csv"
os.environ["FIG_DIR"] = "figures"
os.environ["DUAL_SAVE"] = ""  # To save both .pdf and .png


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


notebooks = notebooks_from_mapping(MAPPING_CSV)


# To make error messages human readable
# https://stackoverflow.com/a/38662876
def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


# To update workflow status for a figure
def save_status(notebook, icon):
    full_path = os.path.join(TEST_DIR, notebook)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    shutil.copy(f"tests/icons/{icon}.png", full_path.replace(".ipynb", ".png"))


@pytest.mark.parametrize("notebook", notebooks)
def test_run_notebooks(notebook):
    init = time()
    try:
        nb = nbformat.read(notebook, as_version=4)
        NotebookClient(nb, timeout=TIMEOUT, kernel_name="python3").execute()
        save_status(notebook, "right")
        print("passed in {:.2f} seconds: {} ".format(time() - init, notebook))
    except Exception as e:
        save_status(notebook, "wrong")
        print("failed after {:.2f} seconds: {} ".format(time() - init, notebook))
        with open(os.path.join(TEST_DIR, notebook.replace(".ipynb", ".log")), "w") as f:
            f.write(escape_ansi(str(e)))
        raise e
