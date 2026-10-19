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
import shutil
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
    "notebooks/book1/13/sparse_mlp.ipynb",
    "notebooks/book1/20/pcaStandardization.ipynb",
    "notebooks/book1/13/bnn_hierarchical_pymc3.ipynb",
    # flax >= 0.7 / jax API (REPRODUCE.md 4.31)
    "notebooks/book1/15/cnn1d_sentiment_jax.ipynb",
    "notebooks/book1/15/rnn_sentiment_jax.ipynb",
    "notebooks/book1/15/nmt_jax.ipynb",
    "notebooks/book1/15/nmt_attention_jax.ipynb",
    "notebooks/book1/15/gru_jax.ipynb",
    "notebooks/book1/15/lstm_jax.ipynb",
    # Colab paths and input() prompts removed (REPRODUCE.md 4.33)
    "notebooks/book1/19/image_augmentation_jax.ipynb",
    "notebooks/book1/19/finetune_cnn_jax.ipynb",
    "notebooks/book1/22/matrix_factorization_recommender_surprise_lib.ipynb",
    # sklearn / flax / keras API changes (REPRODUCE.md 4.34)
    "notebooks/book1/16/knn_demo.ipynb",
    "notebooks/book1/14/batchnorm_jax.ipynb",
    "notebooks/book1/20/vae_mnist_gdl_tf.ipynb",
    # wikitext-2 from wikitext.smerity.com (REPRODUCE.md 4.35)
    "notebooks/book1/15/bert_jax.ipynb",
    "notebooks/book1/15/bert_torch.ipynb",
    # CelebA from probml-data, no !rm, no Colab (REPRODUCE.md 4.36)
    "notebooks/book1/20/vae_celeba_tf.ipynb",
    # no !mkdir / %cd /content/scripts (Colab) (REPRODUCE.md 4.48)
    "notebooks/book1/20/vae_mnist_conv_lightning.ipynb",
    # DataLoader iterators have no .next() (REPRODUCE.md 4.38)
    "notebooks/book1/14/cnn_cifar_pytorch.ipynb",
    "notebooks/book1/14/cifar10_cnn_lightning.ipynb",
    # moved image / class-list URLs, undefined `percentage` (REPRODUCE.md 4.40)
    "notebooks/book1/19/pre_trained_image_classifier_torch.ipynb",
    # undefined `ndims_input` (REPRODUCE.md 4.41)
    "notebooks/book1/13/mlp_cifar_pytorch.ipynb",
    # Book 2 copy (OTHER_BOOK): x_test shape for tinygp 0.2.4 (REPRODUCE.md 4.45)
    "notebooks/book1/17/gpr_demo_noise_free.ipynb",
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
    # pymc3 3.11 API and BLAS-free batched_dot (REPRODUCE.md 4.29)
    "notebooks/misc/bnn_hierarchical_pymc3.ipynb",
    # UTF-8 mode, flax/jax fixes (REPRODUCE.md 4.31)
    "notebooks/book1/15/cnn1d_sentiment_jax.ipynb",
    "notebooks/book1/15/cnn1d_sentiment_torch.ipynb",
    "notebooks/book1/15/nmt_attention_jax.ipynb",
    "notebooks/book1/15/nmt_attention_torch.ipynb",
    "notebooks/book1/15/nmt_jax.ipynb",
    "notebooks/book1/15/nmt_torch.ipynb",
    "notebooks/book1/15/transformers_jax.ipynb",
    "notebooks/book1/15/transformers_torch.ipynb",
    "notebooks/book1/20/word_analogies_jax.ipynb",
    "notebooks/book1/20/word_analogies_torch.ipynb",
    "notebooks/book1/15/gru_jax.ipynb",
    "notebooks/book1/15/lstm_jax.ipynb",
    # packages pinned, Colab/input() fixes (REPRODUCE.md 4.33)
    "notebooks/misc/matrix_factorization_recommender_surprise_lib.ipynb",
    "notebooks/misc/feature_importance_trees_tutorial.ipynb",
    "notebooks/book1/19/image_augmentation_jax.ipynb",
    # sklearn / flax / keras API changes (REPRODUCE.md 4.34)
    "notebooks/misc/knn_demo.ipynb",
    "notebooks/misc/vae_mnist_gdl_tf.ipynb",
    "notebooks/book1/14/batchnorm_jax.ipynb",
    # moved data URLs, legacy Adam, no Colab (REPRODUCE.md 4.35, 4.36, 4.40)
    "notebooks/misc/vae_celeba_tf.ipynb",
    "notebooks/misc/pre_trained_image_classifier_torch.ipynb",
    # no DataLoader workers / Pool on Windows, SNLI Icon\r (REPRODUCE.md 4.37)
    "notebooks/book1/20/skipgram_jax.ipynb",
    "notebooks/book1/20/skipgram_torch.ipynb",
    "notebooks/book1/15/entailment_attention_mlp_torch.ipynb",
    "notebooks/book1/15/bert_torch.ipynb",
    # dataiter.next() -> next(dataiter) (REPRODUCE.md 4.38)
    "notebooks/misc/cnn_cifar_pytorch.ipynb",
    # need CUDA: pass with the CUDA build of torch (REPRODUCE.md 4.39)
    "notebooks/book1/13/multi_gpu_training_torch.ipynb",
    "notebooks/book1/19/finetune_cnn_torch.ipynb",
    # torch training on the GPU, CIFAR-10 pre-copied, `ndims_input` fix (REPRODUCE.md 4.41)
    "notebooks/book1/14/resnet_torch.ipynb",
    "notebooks/book1/14/densenet_torch.ipynb",
    "notebooks/book1/15/rnn_sentiment_torch.ipynb",
    "notebooks/book1/19/image_augmentation_torch.ipynb",
    "notebooks/misc/mlp_cifar_pytorch.ipynb",
    # the last two dashboard notebooks upstream ignores: pass unchanged (REPRODUCE.md 4.46)
    "notebooks/book1/09/naive_bayes_mnist_jax.ipynb",
    "notebooks/book1/15/kernel_regression_attention.ipynb",
}

# Copies of a notebook in the chapter folder of a figure upstream maps to another chapter's notebook:
# {copy: (source, [figure keys])}. The copy is remade from the synced source, and those figures point
# to the copy (REPRODUCE.md 4.42).
LOCAL_COPIES = {
    # Figure 10.1 (logistic regression on iris) is made by book1/02/iris_logreg.ipynb
    "notebooks/book1/10/iris_logreg.ipynb": ("notebooks/book1/02/iris_logreg.ipynb", ["10.1"]),
}

# Notebooks renamed upstream whose old name the upstream mapping still uses: {old path: new path}
# (REPRODUCE.md 4.44)
RENAMED = {
    # pyprobml d5193aa (2023-01-20, "Latexify bootstrap demo"); Figure 4.23
    "notebooks/book1/04/bootstrapDemoBer.ipynb": "notebooks/book1/04/bootstrap_demo_bernoulli.ipynb",
    # pyprobml 07371db (2022-07-20); Figures 8.23, 17.2, 17.3
    "notebooks/book1/08/emLogLikelihoodMax.ipynb": "notebooks/book1/08/em_log_likelihood_max.ipynb",
    "notebooks/book1/17/gpKernelPlot.ipynb": "notebooks/book1/17/gp_kernel_plot.ipynb",
    # pyprobml 0f63b7c (2022-06-30); Figure 13.14
    "notebooks/book1/13/activation_fun_deriv_jax.ipynb": "notebooks/book1/13/activation_fun_deriv.ipynb",
}

# Book 1 figures whose notebook upstream deleted from Book 1 as a duplicate of a Book 2 notebook
# (pyprobml 1f5d3f4, 2022-08-06): {copy in the Book 1 chapter folder: (Book 2 notebook, [figure keys])}.
# The copy is downloaded from upstream and those figures point to it (REPRODUCE.md 4.45).
OTHER_BOOK = {
    "notebooks/book1/11/linreg_post_pred_plot.ipynb": ("notebooks/book2/03/linreg_post_pred_plot.ipynb", ["11.21"]),
    "notebooks/book1/17/gpr_demo_ard.ipynb": ("notebooks/book2/18/gpr_demo_ard.ipynb", ["17.1"]),
    "notebooks/book1/17/gpr_demo_noise_free.ipynb": ("notebooks/book2/18/gpr_demo_noise_free.ipynb", ["17.7"]),
    "notebooks/book1/17/gpr_demo_change_hparams.ipynb": ("notebooks/book2/18/gpr_demo_change_hparams.ipynb", ["17.8"]),
    "notebooks/book1/17/gpr_demo_marglik.ipynb": ("notebooks/book2/18/gpr_demo_marglik.ipynb", ["17.9"]),
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
    if RENAMED.get(path) in book1_notebooks:
        print(f"fixed mapping (renamed): {path} -> {RENAMED[path]}")
        return url.replace(path, RENAMED[path])
    candidates = [p for p in book1_notebooks if p.split("/")[-1] == path.split("/")[-1]]
    if len(candidates) != 1:
        print(f"WARNING: {path} not found upstream; left as is")
        return url
    print(f"fixed mapping: {path} -> {candidates[0]}")
    return url.replace(path, candidates[0])


# Figure -> notebook mapping, filtered to the selected chapters
text = fetch(f"{RAW}/internal/figures_url_mapping_book1_excluded_dummy_nb.csv").decode()
rows = [row for row in csv.DictReader(io.StringIO(text)) if row["key"].split(".")[0] in chapters]
other_book = {key: copy for copy, (_, keys) in OTHER_BOOK.items() for key in keys}
for row in rows:
    if row["key"] in other_book:
        urls = [f"https://colab.research.google.com/github/{UPSTREAM}/blob/{BRANCH}/{other_book[row['key']]}"]
    else:
        urls = [fix_url(url) for url in ast.literal_eval(row["url"])]
    for copy, (source, keys) in LOCAL_COPIES.items():
        if row["key"] in keys:
            urls = [url.replace(source, copy) for url in urls]
    row["url"] = str(urls)
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
for copy, (source, keys) in OTHER_BOOK.items():
    if copy not in mapped:
        continue
    if copy in LOCAL_EDITS and os.path.exists(copy):
        print(f"kept local edit: {copy}")
    else:
        save(copy, fetch(f"{RAW}/{source}"))
        print(f"downloaded {source} -> {copy} (figures {', '.join(keys)})")
    notebooks.append(copy)
print(f"{len(notebooks)} notebooks synced")

# Colab links between notebooks -> local links, as in the committed notebooks (JUPYTER.md)
subprocess.run([sys.executable, "scripts/local_links.py", *notebooks], check=True)
# `!mkdir figures # ...` -> os.makedirs, `!ls` -> os.listdir, `!wget -nc` (REPRODUCE.md 4.30, 4.32)
subprocess.run([sys.executable, "scripts/fix_shell.py", *notebooks], check=True)
# d2l download helpers: extract once, raise_for_status (REPRODUCE.md 4.32, 4.35)
subprocess.run([sys.executable, "scripts/fix_download.py", *notebooks], check=True)
# torch DataLoader workers: none on Windows (REPRODUCE.md 4.37)
subprocess.run([sys.executable, "scripts/fix_workers.py", *notebooks], check=True)

for copy, (source, keys) in LOCAL_COPIES.items():
    if os.path.exists(source):
        shutil.copyfile(source, copy)
        print(f"copied {source} -> {copy} (figures {', '.join(keys)})")

# Dashboard for JupyterLab, linking the local notebooks (JUPYTER.md)
subprocess.run([sys.executable, "scripts/create_figure_dashboard.py", "--local"], check=True)

for icon in ["right", "wrong"]:
    save(f"tests/icons/{icon}.png", fetch(f"{RAW}/tests/icons/{icon}.png"))
