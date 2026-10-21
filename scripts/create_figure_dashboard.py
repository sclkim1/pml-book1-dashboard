"""
Build dashboard_figures_book1.md, following probml/pyprobml .github/scripts/create_figure_dashboard.py

Usage:
    python scripts/create_figure_dashboard.py --user_name owner/repo
"""
import argparse
import ast
import os

import nbformat
import pandas as pd


def get_chap_mapping(csv_name):
    """
    return mapping of chap_no to chap_name
    """
    df = pd.read_csv(csv_name, dtype=str)
    return dict(zip(df["chap_no"], df["chap_name"]))


def chap_to_urls_mapping(csv_name):
    """
    return like {"1": {"1.3": [url1], "1.4": [url1, url2]}, "2": {...}}
    """
    df = pd.read_csv(csv_name, dtype=str)
    chap_nb = {}
    for key, url in zip(df["key"], df["url"]):
        chap_no = key.split(".")[0]
        chap_nb.setdefault(chap_no, {})[key] = ast.literal_eval(url)
    return chap_nb


def check_latexify(code):
    return "latexify" in code


def check_jaxify(code):
    return "import jax" in code or "import flax" in code or "from jax" in code or "from flax" in code


def check_fun_to_notebook(notebook, fun):
    """
    fun should take one argument: code
    """
    try:
        nb = nbformat.read(notebook, as_version=4)
    except FileNotFoundError:
        print("File not found:", notebook)
        return False
    return any(fun(cell["source"]) for cell in nb.cells)


def get_path_from_url(url, base_path="notebooks"):
    """
    extract book_no/chap_name/nb_name.ipynb from url
    """
    return os.path.join(base_path, *url.split("/")[-3:])


parser = argparse.ArgumentParser(description="create figure dashboard")
parser.add_argument("--user_name", type=str, help="owner/repo", default="sclkim1/pml-book1-dashboard")
parser.add_argument("--branch", type=str, default="main")
parser.add_argument("--out_dir", type=str, default="workflow_testing_indicator")
parser.add_argument(
    "--local",
    action="store_true",
    help="write notebooks/book1/dashboard_local.md, linking the local notebooks (for JupyterLab)",
)
args = parser.parse_args()
user, repo = args.user_name.split("/")  # github.repository gives owner/repo

repo_root = f"https://github.com/{user}/{repo}"
# notebook links open this repository's notebook on GitHub (upstream links to Colab, which is not used here)
nb_root = f"{repo_root}/blob/{args.branch}"
# --local: the file sits in notebooks/book1 (JupyterLab's root, JUPYTER.md section 2) and links
# relative to it, so JupyterLab's Markdown Preview opens the notebook in this checkout
LOCAL_DIR = "notebooks/book1"


def nb_link(path):
    if args.local:
        return os.path.relpath(path, LOCAL_DIR).replace(os.sep, "/")
    return f"{nb_root}/{path}"
run_root = f"https://raw.githubusercontent.com/{user}/{repo}/workflow_testing_indicator"
get_run = (
    lambda path: f'<img width="20" alt="image" src={run_root}/{path.replace(".ipynb", ".png")}>, [log]({run_root}/{path.replace(".ipynb", ".log")})'
)
right_emoji = "&#9989;"
wrong_emoji = "&#10060;"
skipped = "skipped (upstream ignore list)"
missing = "notebook missing upstream"


def ignored_names(txt_name="internal/ignored_notebooks.txt"):
    """
    file names of notebooks upstream does not execute (matched by name only, like upstream)
    """
    if not os.path.exists(txt_name):
        return set()
    with open(txt_name) as fp:
        return {line.strip().split("/")[-1] for line in fp if line.strip()}


ignored = ignored_names()

book_no = 1
total_cnt = 0
latexify_cnt = 0
jaxify_cnt = 0
chap_urls_mapping = chap_to_urls_mapping(f"internal/figures_url_mapping_book{book_no}.csv")
chap_no_chap_name_mapping = get_chap_mapping(f"internal/chapter_no_to_name_mapping_book{book_no}.csv")

md_content = ""
for chap_no, urls_list in chap_urls_mapping.items():
    notebooks = []
    base_str = f"<details open>\n<summary>Chapter: {chap_no}_{chap_no_chap_name_mapping[chap_no]}</summary>\n\n"
    print(f"*** {chap_no}-{chap_no_chap_name_mapping[chap_no]}: {len(urls_list)} figures found! ****")
    for fig_no, urls in urls_list.items():
        for url in urls:
            path = get_path_from_url(url).replace(os.sep, "/")
            nb_name = path.split("/")[-1]
            is_latexify = check_fun_to_notebook(path, check_latexify)
            is_jaxify = check_fun_to_notebook(path, check_jaxify)
            latexify_cnt += is_latexify
            jaxify_cnt += is_jaxify
            notebooks.append(
                {
                    # no link for a notebook that does not exist (it would be a dead link)
                    "nb_name": f"[{nb_name}]({nb_link(path)})" if os.path.exists(path) else nb_name,
                    "fig_no": fig_no,
                    "workflow": missing if not os.path.exists(path) else skipped if nb_name in ignored else get_run(path),
                    "latexify": right_emoji if is_latexify else wrong_emoji,
                    "jaxify": right_emoji if is_jaxify else wrong_emoji,
                }
            )

    if notebooks:
        md_content += base_str + pd.DataFrame(notebooks).to_markdown(index=None, disable_numparse=True) + "\n</details>\n\n"
        total_cnt += len(notebooks)

# Notebooks this repository adds (no book figure, so not in the upstream mapping or the counts above;
# executed by tests/test_notebooks.py like the others, REPRODUCE.md 4.51)
extra_csv = f"internal/extra_notebooks_book{book_no}.csv"
if os.path.exists(extra_csv):
    extra = []
    for row in pd.read_csv(extra_csv, dtype=str).itertuples():
        path = f"notebooks/book{book_no}/{int(row.chap):02d}/{row.notebook}"
        extra.append(
            {
                "nb_name": f"[{row.notebook}]({nb_link(path)})" if os.path.exists(path) else row.notebook,
                "chapter": row.chap,
                "description": row.description,
                "workflow": get_run(path) if os.path.exists(path) else "notebook missing",
                "latexify": right_emoji if check_fun_to_notebook(path, check_latexify) else wrong_emoji,
                "jaxify": right_emoji if check_fun_to_notebook(path, check_jaxify) else wrong_emoji,
            }
        )
    if extra:
        md_content += (
            f"## Additional notebooks\n\n{len(extra)} notebooks added in this repository (not upstream, no book figure),"
            " listed in `internal/extra_notebooks_book1.csv` and executed like the others.\n\n"
            + pd.DataFrame(extra).to_markdown(index=None, disable_numparse=True)
            + "\n\n"
        )
        print(f"{len(extra)} additional notebooks")

headline = f"## Instructions\n\n* Notebooks are copied from [probml/pyprobml](https://github.com/probml/pyprobml) with `scripts/sync_from_pyprobml.py`. See the [repository]({repo_root}) for details.\n"
if args.local:
    headline += (
        "* Local dashboard for JupyterLab (open with *Markdown Preview*): notebook links open the notebooks in this"
        " checkout; the workflow icons and logs are the last GitHub Actions run. Rebuild with"
        " `python scripts/create_figure_dashboard.py --local` (in the repository root).\n"
    )
headline += f"\n## Book{book_no}Dashboard\n"
md_content = (
    headline
    + f"""Total Notebooks | Latexified | Jaxified |
| -- | -- |  -- |
| {total_cnt} | {latexify_cnt} | {jaxify_cnt} |

"""
    + md_content
)

out_path = f"{LOCAL_DIR}/dashboard_local.md" if args.local else os.path.join(args.out_dir, f"dashboard_figures_book{book_no}.md")
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
with open(out_path, "w", encoding="utf-8") as fp:
    fp.write(md_content)
print(f"{total_cnt} notebooks, {latexify_cnt} latexified, {jaxify_cnt} jaxified")
