# Reproducing the dashboard

This repository reproduces the [pyprobml Book 1 figure dashboard](https://github.com/probml/pyprobml/blob/workflow_testing_indicator/dashboard_figures_book1.md)
for chapters 1–2 (29 dashboard rows, 28 notebooks). The dashboard can be built two ways:

| | Where | Environment | Result |
|---|---|---|---|
| **A. GitHub Actions** | `ubuntu-latest` runner, on every push to `main` | `requirements.txt` (unpinned) | published to the [`workflow_testing_indicator`](../../tree/workflow_testing_indicator) branch |
| **B. Local conda env** | Windows 11, conda env `pyprobml` | `requirements-local.txt` (pinned) | `test_results/` + `workflow_testing_indicator/dashboard_figures_book1.md` |

Section 1 sets up the tools, section 2 builds the local environment, section 3 runs it, and
section 4 lists every problem found along the way, its cause and its fix.

---

## 1. Tools (Windows)

| Tool | Version used | Install | Why |
|---|---|---|---|
| Git | 2.55.0 | `winget install --id Git.Git -e --source winget` | Git **2.9.0** crashed silently on every HTTPS connection (see 4.1) |
| GitHub CLI | 2.102.0 | `winget install --id GitHub.cli -e --source winget` | creating the repo / checking runs; `--source winget` avoids the msstore certificate error (see 4.2) |
| Anaconda | existing install, `base` = Python 3.10.9 | — | local environment |
| MiKTeX | existing install (`latex`, `dvipng` on PATH) | <https://miktex.org> | `bimodal_dist_plot` and `gamma_dist_plot` force LaTeX rendering (see 4.9) |

After installing Git or the GitHub CLI, open a **new** terminal so the updated `PATH` is picked up, then log in:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

## 2. Build the local environment

All commands run from the repository root in PowerShell.

```powershell
git clone https://github.com/sclkim1/pml-book1-dashboard.git
cd pml-book1-dashboard

# 2.1 Create the env as a clone of Anaconda base (Python 3.10.9, close to Colab's 3.10)
conda create -n pyprobml --clone base -y
$py = "$HOME\anaconda3\envs\pyprobml\python.exe"

# 2.2 Repair setuptools inherited from base (see 4.4)
& $py -m pip install -U pip "setuptools<81" wheel backports.tarfile

# 2.3 Install the pinned, mutually compatible package set (see 4.3, 4.5-4.8, 4.10)
& $py -m pip install -r requirements-local.txt

# 2.4 Register the env as a Jupyter kernel named "pyprobml"
& $py -m ipykernel install --user --name pyprobml --display-name "Python (pyprobml)"

# 2.5 Smoke test: every library imports and computes
& $py -c "import numpy, scipy, matplotlib, pandas, sklearn, seaborn, jax, optax, chex, distrax, tensorflow as tf, tensorflow_probability, tensorflow_datasets, torch, torchvision, bokeh, probml_utils; print('OK', tf.__version__, float(tf.reduce_sum(tf.ones(3))), float(torch.ones(3).sum()), float(jax.numpy.ones(3).sum()))"
```

Expected output of 2.5: `OK 2.12.1 3.0 3.0 3.0`.

pip prints dependency-conflict warnings about `conda-repo-cli`, `gensim` and `optree`. Those
packages come from Anaconda base and are not used by the notebooks; the warnings can be ignored.

> **Clone of base vs. fresh env.** Cloning base is what was tested here. A fresh env
> (`conda create -n pyprobml python=3.10 -y`, then steps 2.3–2.5) should also work with
> `requirements-local.txt`, and would skip the setuptools repair in 2.2, but it was **not tested**.

### 2.6 Pre-download slow or broken datasets

Two notebooks download datasets the first time they run. On this network both downloads failed
inside the notebook (see 4.11 and 4.12), so they are downloaded beforehand into the cache
folders the libraries check first. The notebooks then skip their own download.

```powershell
# CIFAR-10 for cifar_viz_tf (Keras cache). ~163 MB; the server is slow (~60-80 KB/s here)
New-Item -ItemType Directory -Force "$HOME\.keras\datasets" | Out-Null
curl.exe -L -C - --retry 5 -o "$HOME\.keras\datasets\cifar-10-batches-py.tar.gz" https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz

# EMNIST for emnist_viz_jax (torchvision cache, root="~/data"). ~536 MB
New-Item -ItemType Directory -Force "$HOME\data\EMNIST\raw" | Out-Null
curl.exe -L --fail --retry 5 -o "$HOME\data\EMNIST\raw\gzip.zip" https://biometrics.nist.gov/cs_links/EMNIST/gzip.zip

# Verify EMNIST: must be 561,753,746 bytes, MD5 58c8d27c78d21e728a6bc7b3cc06412e
(Get-Item "$HOME\data\EMNIST\raw\gzip.zip").Length
(Get-FileHash "$HOME\data\EMNIST\raw\gzip.zip" -Algorithm MD5).Hash
```

Use `curl.exe` (Windows' own curl), not `curl` from Git Bash: in PowerShell `curl` is an
alias for `Invoke-WebRequest`.

## 3. Run

```powershell
$env:NB_KERNEL = "pyprobml"        # run notebooks with the conda env's kernel (default: python3)
$env:PYTHONIOENCODING = "utf-8"
$env:TF_CPP_MIN_LOG_LEVEL = "2"    # optional: quieter TensorFlow logs

# Execute every notebook in internal/figures_url_mapping_book1.csv
& $py -m pytest -n 4 -s -p no:cacheprovider tests/test_notebooks.py

# Build the dashboard markdown
& $py scripts/create_figure_dashboard.py --user_name sclkim1/pml-book1-dashboard
```

- Each notebook writes `test_results/notebooks/book1/<chap>/<name>.png` (✅/❌ icon), and a
  `.log` with the error when it fails.
- The dashboard is written to `workflow_testing_indicator/dashboard_figures_book1.md`.
  Its icons link to the `workflow_testing_indicator` branch on GitHub, i.e. to the **CI** results.
  To view local results, look at `test_results/`.
- A failing notebook fails its pytest case, but the run continues with the others.

To re-run a single notebook: add `-k <name>`, e.g. `-k iris_kmeans`.

---

## 4. Problems found and how they were fixed

Each entry: **symptom → cause → fix**. Entries 4.1–4.2 are tooling; 4.3–4.10 are the Python
environment; 4.11–4.12 are datasets; 4.13 is a CI-only difference.

### 4.1 `git push` fails with exit code 128 and no message
- **Cause:** the installed Git was 2.9.0 (2016). Its `git-remote-https` helper (and Git Bash's
  `curl`, which segfaulted) cannot negotiate TLS with GitHub. Even `git ls-remote` on a public repo failed.
- **Fix:** upgrade Git: `winget install --id Git.Git -e --source winget` (→ 2.55.0).

### 4.2 `winget install GitHub.cli` fails: `0x8a15005e : 서버 인증서가 필요한 값과 일치하지 않습니다`
- **Cause:** the `msstore` source failed its certificate check; winget then refuses to choose between sources.
- **Fix:** add `--source winget`.

### 4.3 First local run: 6 passed, 22 failed (`numpy.core.multiarray failed to import`, `DLL load failed`)
- **Cause:** every notebook guards its imports with
  `try: import X` / `except ImportError: %pip install X`. Packages missing from the env
  (TensorFlow, TFP, optax, …) were therefore installed **by the notebooks, during the run, unpinned**.
  `pip install tensorflow` pulled in TensorFlow 2.21 and **numpy 2.2.6**, which broke scipy,
  matplotlib and pandas (built against numpy 1.x) for every notebook running afterwards.
- **Fix:** `requirements-local.txt` preinstalls everything any notebook would install, at
  compatible versions, so no notebook's `except ImportError` branch ever runs.
  Verified by comparing `pip freeze` before and after a full run: **no differences**.

### 4.4 `pip install` fails: `Can not execute setup.py since setuptools is not available`
- **Cause:** the setuptools copied from Anaconda base imports `backports.tarfile`, but an old
  `backports` package from base shadows it, so setuptools itself fails to import. This breaks
  any package that ships as source only (here `promise`, a dependency of tensorflow-datasets).
- **Fix:** `pip install -U pip "setuptools<81" wheel backports.tarfile` (step 2.2).

### 4.5 `ResolutionImpossible: distrax==0.1.3 and numpy==1.26.4`
- **Cause:** `probml-utils` (used by almost every notebook) pins `distrax==0.1.3`, which requires
  **`numpy<1.23`**. This is also why CI got numpy 1.22.4 and then failed with
  `Matplotlib requires numpy>=1.23; you have 1.22.4`.
- **Fix:** build the env around `numpy==1.22.4`, and choose every other package to match:
  `scipy==1.10.1`, `matplotlib==3.5.3`, `tensorflow==2.12.1`
  (TF ≥ 2.14 requires numpy ≥ 1.23.5), `tensorflow-probability==0.20.1`, `tensorflow-datasets==4.9.2`.

### 4.6 `AttributeError: jax.core.Shape is deprecated` when importing chex
- **Cause:** every chex release that accepts numpy < 1.23 (≤ 0.1.8) uses `jax.core.Shape`,
  which newer jax removed. chex 0.1.8 is also yanked on PyPI.
- **Fix:** `jax==0.4.23`, `jaxlib==0.4.23` (has a Windows wheel, accepts numpy ≥ 1.22),
  `chex==0.1.7`, `optax==0.2.1`.

### 4.7 `module 'tensorflow' has no attribute '__version__'`
- **Cause:** uninstalling TF 2.21 (installed by a notebook in 4.3) deleted
  `tensorflow/__init__.py`, which `tensorflow-intel` 2.12.1 also owns. `tensorflow` became an empty namespace package.
- **Fix:** `pip install --force-reinstall --no-deps tensorflow-intel==2.12.1`.
  Only needed in an env where a different TensorFlow was installed before; a new env from
  `requirements-local.txt` does not need it.

### 4.8 `cannot import name 'runtime_version' from 'google.protobuf'` (tensorflow_datasets)
- **Cause:** the latest `tensorflow-metadata` is generated with protobuf 5; TF 2.12 needs protobuf < 5.
- **Fix:** `tensorflow-metadata==1.13.1`.

### 4.9 `bimodal_dist_plot`, `gamma_dist_plot`: `latex could not be found` (CI only)
- **Cause:** these two notebooks set `os.environ["LATEXIFY"] = ""` themselves, which makes
  `probml_utils.latexify()` turn on `text.usetex`. They need a LaTeX installation regardless of the test settings.
- **Fix (local):** MiKTeX was already installed; both pass. In CI they still fail; see 4.13.

### 4.10 `iris_kmeans`: `AttributeError: 'NoneType' object has no attribute 'split'`
- **Cause:** `threadpoolctl` 2.2.0 from Anaconda base crashes while inspecting the OpenBLAS
  library that scikit-learn's KMeans loads.
- **Fix:** `threadpoolctl==3.5.0`.

### 4.11 `cifar_viz_tf` (and anything queued after it) hangs with an idle kernel
- **Symptom:** the run never finishes; the notebook kernel uses no CPU. Notebooks queued on the
  same pytest worker (here `quantile_plot`) look hung too, but pass when run alone.
- **Cause:** Keras downloads CIFAR-10 from `www.cs.toronto.edu`, which served ~60–80 KB/s here
  (163 MB ≈ 35–45 min), and Keras's downloader has no timeout.
- **Fix:** download the file into the Keras cache first (step 2.6).

### 4.12 `emnist_viz_jax`: `RuntimeError: File not found or corrupted.`
- **Cause:** torchvision 0.16.2 downloads EMNIST from `www.itl.nist.gov/…/gzip.zip`, which no
  longer serves the file. Current torchvision uses `biometrics.nist.gov` with the same MD5.
  (The first download from the new URL once returned an HTML error page instead of the zip;
  re-downloading gave the correct file, so always check the size and MD5.)
- **Fix:** download from `biometrics.nist.gov` into `~/data/EMNIST/raw/gzip.zip` (step 2.6).
  torchvision verifies the MD5 and skips its own download.

### 4.13 Differences between the CI run and the local run
CI (`.github/workflows/dashboard.yml`) still uses the original unpinned `requirements.txt` and has
no LaTeX, so it is affected by 4.3, 4.5, 4.9 and 4.12. The fixes above have **not** been applied to CI.

## 5. Results

| Run | Environment | Passed | Failed |
|---|---|---|---|
| CI, run [38333885122](../../actions/runs/38333885122) | `ubuntu-latest`, `requirements.txt` | 15 | 13 |
| Local, first attempt | clone of base + `requirements.txt` | 6 | 22 |
| Local, after fixes 4.3–4.12 | `pyprobml` + `requirements-local.txt` + pre-downloaded datasets | 27 | 0 |

The last local row combines the full run (24 passed) with individual re-runs after each fix
(`iris_kmeans`, `emnist_viz_jax`, `quantile_plot`). `cifar_viz_tf` has not been run yet: its
dataset (4.11) was still downloading. A single clean run of all 28 notebooks is still to be done.
