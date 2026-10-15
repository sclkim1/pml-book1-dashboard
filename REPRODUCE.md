# Reproducing the dashboard

This repository reproduces the [pyprobml Book 1 figure dashboard](https://github.com/probml/pyprobml/blob/workflow_testing_indicator/dashboard_figures_book1.md)
for **all 22 chapters of Book 1**: 245 dashboard rows, the same header as the original
(245 notebooks; 43 latexified and 51 jaxified, see 4.18). Of these rows:

- **172 notebooks are executed**;
- 8 rows (6 notebooks) are on upstream's `internal/ignored_notebooks.txt`; like upstream, they are
  not executed and the dashboard shows "skipped (upstream ignore list)";
- 10 rows (9 notebooks) point to notebooks that do not exist upstream; the dashboard shows
  "notebook missing upstream" (4.18).

The dashboard can be built two ways:

| | Where | Environment | Result |
|---|---|---|---|
| **A. GitHub Actions** | `ubuntu-latest` runner, on every push to `main` | `requirements-local.txt` (pinned) + TeX Live + pre-downloaded datasets | published to the [`workflow_testing_indicator`](../../tree/workflow_testing_indicator) branch |
| **B. Local conda env** | Windows 11, conda env `pyprobml-fresh` | `requirements-local.txt` (pinned) + MiKTeX + tools from `scripts/windows_admin_setup.ps1` + pre-downloaded datasets | `test_results/` + `workflow_testing_indicator/dashboard_figures_book1.md` |

Both use the same pinned package list (`requirements-local.txt`, despite the name) and the same
dataset fixes. `requirements.txt` is the original, unpinned pyprobml list, kept for reference.

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
| wget | 1.21.4 | `scripts/windows_admin_setup.ps1` (winget `JernejSimoncic.Wget`) | notebooks run `!wget` (4.23) |
| unzip | Git's `unzip.exe` | `scripts/windows_admin_setup.ps1` (`~\bin\unzip.cmd` wrapper) | `matrix_factorization_recommender` runs `!unzip` (4.23) |
| Graphviz | 16.1.0 | `scripts/windows_admin_setup.ps1` (winget `Graphviz.Graphviz`) | `hbayes_maml` renders a graph with `dot` (4.23) |
| a MinGW `g++` on PATH | Strawberry Perl's (`C:\Strawberry\c\bin`) | existing install | optional, but without it the three slow pymc3 notebooks time out (4.20) |

After installing Git or the GitHub CLI, open a **new** terminal so the updated `PATH` is picked up, then log in:

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh auth setup-git
```

### 1.1 Machine setup for chapters 3–22

Several notebooks write to hardcoded absolute paths or call Linux command-line tools.
`scripts/windows_admin_setup.ps1` prepares both; run it **once, as administrator**, from your own
account (it gives that account write access):

```powershell
Start-Process powershell -Verb RunAs -Wait -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File scripts\windows_admin_setup.ps1'
```

| It creates / installs | For |
|---|---|
| `C:\Users\kpmurphy\github\bookv2\figures` (= `/Users/kpmurphy/...`) | 5 notebooks (4.17) |
| wget, Graphviz (winget); `~\bin\unzip.cmd`; Graphviz and `~\bin` added to your user PATH | 4.23 |

Then, without admin rights, give wget a CA bundle (4.23) and open a new terminal:

```powershell
Copy-Item (& $py -c "import certifi; print(certifi.where())") "$HOME\bin\cacert.pem"   # after step 2.1
Set-Content "$HOME\.wgetrc" "ca_certificate = $HOME\bin\cacert.pem" -Encoding ascii
[Environment]::SetEnvironmentVariable("WGETRC", "$HOME\.wgetrc", "User")
```

## 2. Build the local environment

All commands run from the repository root in PowerShell.

```powershell
git clone https://github.com/sclkim1/pml-book1-dashboard.git
cd pml-book1-dashboard

# 2.1 Create a fresh env (tested with Python 3.10.22; Colab used 3.10)
conda create -n pyprobml-fresh python=3.10 -y
$py = "$HOME\anaconda3\envs\pyprobml-fresh\python.exe"
& $py -m pip install -U pip

# 2.2 Install the pinned, mutually compatible package set (4.3, 4.5-4.8, 4.10, 4.14, 4.15, 4.19-4.21)
& $py -m pip install -r requirements-local.txt

# 2.3 minepy (MIC_correlation_2d): source-only, built with the pinned setuptools (4.22)
& $py -m pip install --no-build-isolation minepy==1.2.6

# 2.3b one-line fixes to installed distrax and causalgraphicalmodels (4.27)
& $py scripts/patch_packages.py

# 2.3c adasls and haven-ai for sgd_comparison, not pip-installable as is (4.29)
& $py scripts/install_sgd_comparison.py

# 2.3d scikit-surprise: no Windows wheels; built against the pinned numpy (4.33)
& $py -m pip install --no-build-isolation scikit-surprise==1.1.4 surprise==0.1

# 2.4 Register the env as a Jupyter kernel named "pyprobml-fresh"
& $py -m ipykernel install --user --name pyprobml-fresh --display-name "Python (pyprobml-fresh)"

# 2.5 Smoke test: every library imports and computes (pymc3 needs THEANO_FLAGS, 4.20)
$env:THEANO_FLAGS = "blas__ldflags=,gcc__cxxflags=-static"
& $py -c "import numpy, scipy, matplotlib, pandas, sklearn, seaborn, jax, optax, chex, distrax, tensorflow as tf, tensorflow_probability, tensorflow_datasets, torch, torchvision, bokeh, probml_utils, pymc3, numpyro, statsmodels, minepy; print('OK', tf.__version__, float(tf.reduce_sum(tf.ones(3))), float(torch.ones(3).sum()), float(jax.numpy.ones(3).sum()))"
& $py -m pip check
```

Expected output of 2.5: `OK 2.12.1 3.0 3.0 3.0`, then `No broken requirements found.`

> **Clone of Anaconda base instead.** The first local runs used `conda create -n pyprobml --clone base`.
> That needs a setuptools repair first (4.4:
> `pip install -U pip "setuptools<81" wheel backports.tarfile`) and inherits whatever else is
> in base, which hid 4.14 and 4.15. It was verified for chapters 1–2 only. Use the fresh env.

### 2.6 Pre-download slow or broken datasets

Two notebooks download datasets the first time they run. On this network both downloads failed
inside the notebook (see 4.11 and 4.12), so they are downloaded beforehand into the cache
folders the libraries check first. The notebooks then skip their own download.

```powershell
# CIFAR-10 for cifar_viz_tf (Keras cache). ~163 MB
# Hugging Face mirror: ~16 MB/s here (the original server gave ~62 KB/s, see 4.11)
New-Item -ItemType Directory -Force "$HOME\.keras\datasets" | Out-Null
curl.exe -L --fail --retry 5 -o "$HOME\.keras\datasets\cifar-10-batches-py.tar.gz" https://huggingface.co/cloneofsimo/test_model/resolve/main/cifar-10-python.tar.gz
# Fallback, original server (slow):
#   curl.exe -L -C - --retry 5 -o "$HOME\.keras\datasets\cifar-10-batches-py.tar.gz" https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz

# Verify CIFAR-10: must be 170,498,071 bytes, MD5 c58f30108f718f92721af3b95e74349a
(Get-Item "$HOME\.keras\datasets\cifar-10-batches-py.tar.gz").Length
(Get-FileHash "$HOME\.keras\datasets\cifar-10-batches-py.tar.gz" -Algorithm MD5).Hash

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
$env:NB_KERNEL = "pyprobml-fresh"  # run notebooks with the conda env's kernel (default: python3)
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
- `tests/test_notebooks.py` sets `THEANO_FLAGS` for the pymc3 notebooks (4.20) unless you set it yourself.
- A full run of the 172 notebooks took 16 min here (44 min the first time, while theano compiled
  and caches were filled).
- Notebooks download checkpoints and datasets (`*.ckpt`, `ml-1m.zip`, …) into the repository
  folder; they are not committed.

To re-run a single notebook: add `-k <name>`, e.g. `-k iris_kmeans`.

### 3.1 Open the notebooks in JupyterLab

See [JUPYTER.md](JUPYTER.md): the `pml-jupyter` env (this section's recipe under another name),
the kernel's `THEANO_FLAGS`, and how a notebook run by hand differs from the test runner.

---

## 4. Problems found and how they were fixed

Each entry: **symptom → cause → fix**. Entries 4.1–4.2 are tooling; 4.3–4.10 are the Python
environment; 4.11–4.12 are datasets; 4.13 is CI; 4.14–4.15 appeared only in a fresh env / CI;
4.16–4.17 are hardcoded paths; 4.18–4.24 came with chapters 3–22; 4.25 is a flaky download;
4.26 came from checking chapters 1–2 by hand in JupyterLab, 4.27 from chapter 3.

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
- **Fix:** locally, MiKTeX was already installed. CI installs TeX Live (4.13).

### 4.10 `iris_kmeans`: `AttributeError: 'NoneType' object has no attribute 'split'`
- **Cause:** `threadpoolctl` 2.2.0 from Anaconda base crashes while inspecting the OpenBLAS
  library that scikit-learn's KMeans loads.
- **Fix:** `threadpoolctl==3.5.0`.

### 4.11 `cifar_viz_tf` (and anything queued after it) hangs with an idle kernel
- **Symptom:** the run never finishes; the notebook kernel uses no CPU. Notebooks queued on the
  same pytest worker (here `quantile_plot`) look hung too, but pass when run alone.
- **Cause:** Keras downloads CIFAR-10 from `www.cs.toronto.edu`, which served ~60–80 KB/s here
  (163 MB ≈ 35–45 min), and Keras's downloader has no timeout.
- **Fix:** download the file into the Keras cache first (step 2.6), from a faster mirror.
  Measured here (15 s samples):

  | Mirror | Speed | Identical file |
  |---|---|---|
  | `www.cs.toronto.edu/~kriz/` (original, used by Keras) | ~62 KB/s | — |
  | `dataset.bj.bcebos.com/cifar/` (PaddlePaddle's mirror) | ~108 KB/s | not checked |
  | `huggingface.co/cloneofsimo/test_model` | **~16 MB/s** | ✅ size and MD5 match the original |

  The Hugging Face copy is in a personal repository, not an official mirror, so check the size
  and MD5 after downloading; Keras also verifies the hash before using the file.

### 4.12 `emnist_viz_jax`: `RuntimeError: File not found or corrupted.`
- **Cause:** torchvision 0.16.2 downloads EMNIST from `www.itl.nist.gov/…/gzip.zip`, which no
  longer serves the file. Current torchvision uses `biometrics.nist.gov` with the same MD5.
  (The first download from the new URL once returned an HTML error page instead of the zip;
  re-downloading gave the correct file, so always check the size and MD5.)
- **Fix:** download from `biometrics.nist.gov` into `~/data/EMNIST/raw/gzip.zip` (step 2.6).
  torchvision verifies the MD5 and skips its own download.

### 4.13 CI used the unpinned setup (15–17 of 28 passed, varying between runs)
- **Cause:** the first CI version installed the unpinned `requirements.txt` and had no LaTeX
  or dataset fixes, so it hit 4.3, 4.5, 4.9, 4.11 and 4.12.
- **Fix:** `.github/workflows/dashboard.yml` now applies the same fixes as the local setup:

  | Local (Windows) | CI (Ubuntu) |
  |---|---|
  | `pip install -r requirements-local.txt` | same, but `torch==2.1.2`/`torchvision==0.16.2` first from the CPU-only index `https://download.pytorch.org/whl/cpu` (the default Linux wheels bundle ~2.5 GB of CUDA libraries) |
  | MiKTeX | apt: `texlive-latex-base texlive-latex-extra texlive-fonts-recommended cm-super dvipng` |
  | step 2.6 downloads + MD5 check | same URLs and MD5 checks; files cached between runs (`actions/cache`, key `datasets-v3`) |
  | `minepy` with `--no-build-isolation` (2.3) | same |
  | `scripts/windows_admin_setup.ps1`: hardcoded folder (4.17) | `sudo mkdir` + `chown` of `/Users/kpmurphy/github/bookv2/figures` |
  | `linreg_poly_vs_degree` edited (4.16) | same |
  | `SOURCE_REWRITES` in `tests/test_notebooks.py` (4.17) | same |
  | `scripts/windows_admin_setup.ps1`: wget, unzip, Graphviz (4.23) | preinstalled on the runner (wget, unzip), apt `graphviz` |
  | `THEANO_FLAGS` with `gcc__cxxflags=-static` (4.20) | `blas__ldflags=` only; the runner's g++ works normally |

  The workflow also has a `concurrency` group: a new push cancels a still-running older
  run, so a stale run cannot overwrite the published dashboard.

### 4.14 Fresh env / CI: every notebook fails, `cannot import name 'TypeAliasType' from 'typing_extensions'` or `Kernel died before replying to kernel_info`
- **Cause:** `tensorflow==2.12.1` requires `typing-extensions<4.6`, but current Jupyter kernel
  packages need ≥ 4.6. The env cloned from base was unaffected because base already had older
  Jupyter packages; a fresh env (and CI) installed the newest ones, and the kernel crashed at startup.
- **Fix:** pin the kernel stack to the versions that worked locally: `typing-extensions==4.5.0`,
  `ipykernel==6.19.2`, `ipython==8.10.0`, `jupyter-client==7.3.4`, `jupyter-core==5.2.0`,
  `nbclient==0.5.13`, `nbformat==5.7.0`, `jsonschema==4.17.3`, `pyzmq==23.2.0`, `tornado==6.1`,
  `traitlets==5.7.1`. The `jupyter` meta-package was removed from the list; `probml-utils` still installs it as a
  dependency, but the kernel pins above keep it compatible.

### 4.15 Fresh env: every notebook fails, `'RcParams' object has no attribute '_get'`
- **Cause:** `matplotlib-inline` ≥ 0.1.7 (the inline plot backend) calls `rcParams._get`, which
  only exists in matplotlib ≥ 3.7; we pin matplotlib 3.5.3 (4.5). Again hidden in the clone of
  base, which had 0.1.6.
- **Fix:** `matplotlib-inline==0.1.6`.

### 4.16 CI: `linreg_poly_vs_degree` fails, `PermissionError: [Errno 13] Permission denied: '/teamspace'`
- **Cause:** the upstream notebook hardcodes
  `os.environ["FIG_DIR"] = "/teamspace/studios/this_studio/pyprobml/notebooks/figures"`
  (the author's cloud workspace). Upstream CI runs in a container as root, which can create
  `/teamspace`; the GitHub runner user cannot. On Windows the path becomes `C:\teamspace\…`,
  which a normal user can create, so it passes locally, **but leaves 15 figure PDFs in
  `C:\teamspace`**. Delete that folder after local runs if you don't want it.
- **First fix:** keep the notebook identical to upstream and create the folder: `sudo mkdir -p /teamspace`
  + `chown` on CI, `C:\teamspace` via the admin script on Windows.
- **Current fix (the only notebook edited in this repository):** one line, the original kept as a comment:
  ```python
  #os.environ["FIG_DIR"] = "/teamspace/studios/this_studio/pyprobml/notebooks/figures"
  os.environ["FIG_DIR"] = "figures"  # relative to the working folder (REPRODUCE.md 4.16)
  ```
  The figures go to `figures/` in the folder the notebook runs in: the repository root for the test
  runner, `notebooks/book1/01/figures/` in JupyterLab (JUPYTER.md). No `/teamspace` folder, admin
  rights or `sudo` needed. `./notebooks/figures` was tried first, but it is also relative to the
  working folder and ended up in `notebooks/book1/01/notebooks/figures/` in JupyterLab.
  `scripts/sync_from_pyprobml.py` lists the notebook in `LOCAL_EDITS` and does not overwrite it.

### 4.17 `/Users/kpmurphy/...` and `/PcaTrainFaceImages.png`: `PermissionError` / `FileNotFoundError`
- **Notebooks:** `gaussEvec`, `discrim_analysis_dboundaries_plot2`, `iris_logreg_loss_surface`,
  `seq_logo_demo`, `regtreeSurfaceDemo` set `FIG_DIR = "/Users/kpmurphy/github/bookv2/figures"`
  (the author's laptop); `pcaImageDemo` calls `savefig("/PcaTrainFaceImages.png")`, i.e. the filesystem root.
- **Cause:** as in 4.16, only root (upstream's container) can create these. On Windows they become
  `C:\Users\kpmurphy\...` and `C:\PcaTrainFaceImages.*`; creating either needs admin rights.
  Pre-creating the root files as admin did not work either: files in `C:\` inherit a
  *High Mandatory Level (no write-up)* integrity label, so a file created by an elevated process
  stays unwritable for normal processes even with write permission granted.
- **Fix:**
  - `/Users/kpmurphy/...` (5 notebooks): `scripts/windows_admin_setup.ps1` creates the folder and
    grants your account modify access; CI uses `sudo mkdir` + `chown`. `C:\Users\kpmurphy` is an
    ordinary folder, not a user profile.
  - `/PcaTrainFaceImages.png`: `tests/test_notebooks.py` rewrites `savefig("/PcaTrainFaceImages.png")`
    to `savefig("PcaTrainFaceImages.png")` **in memory** before running the notebook
    (`SOURCE_REWRITES`), so the figure goes to `figures/` like all others. The notebook file stays
    identical to upstream. No admin rights or `sudo` needed.

### 4.18 Upstream figure mapping points to moved or missing notebooks
- **Symptom:** `File not found: notebooks/book1/21/gmm_2d.ipynb` while building the dashboard.
- **Cause:** `internal/figures_url_mapping_book1_excluded_dummy_nb.csv` upstream lists some
  notebooks in the wrong chapter folder (e.g. `21/gmm_2d` is really `03/gmm_2d`), and some that
  do not exist anywhere (e.g. `bootstrapDemoBer`, five chapter 17 GP notebooks). On the original
  dashboard these rows link to status icons that can never exist.
- **Fix:** `scripts/sync_from_pyprobml.py` re-points a url when exactly one Book 1 notebook has that
  file name, and prints each change (10 urls). The other 9 notebooks are not executed and the
  dashboard shows "notebook missing upstream". Because the dashboard can now read the moved
  notebooks, its header says 43 latexified / 51 jaxified instead of upstream's 36 / 47.

### 4.19 Chapters 3–22 need 15 more libraries, which notebooks would pip-install mid-run
- **Cause:** same mechanism as 4.3: pymc3, numpyro, statsmodels, catboost, GPy, pytorch-lightning,
  imageio, … are imported by 1–7 notebooks each and were not in the env.
- **Fix:** pinned in `requirements-local.txt` (section "Chapters 3-22"). Found by scanning all
  notebooks for `pip install` lines and for imports that are not installed. A `pip freeze`
  comparison before/after the full run showed no changes.

### 4.20 pymc3 (7 notebooks): import errors, then timeouts on Windows
| Symptom | Cause | Fix |
|---|---|---|
| pymc3 3.11.5 cannot be installed | it requires `numpy<1.22.2` and `scipy<1.8`; jax needs scipy ≥ 1.9 | `pymc3==3.11.4` (no such caps) + `theano-pymc==1.1.2` |
| `module 'numpy.distutils.__config__' has no attribute 'blas_opt_info'` | theano-pymc reads a numpy setting removed in numpy 1.22.2 (the reason 3.11.5 capped numpy) | `THEANO_FLAGS=blas__ldflags=` (theano then skips that lookup) |
| Windows: `DLL load failed while importing m31975b…` | theano compiled C modules with the `g++` on PATH (Strawberry Perl's); they need MinGW runtime DLLs, and Python ≥ 3.8 does not search PATH for extension DLLs | add `gcc__cxxflags=-static` (runtime linked into each module) |
| without C compilation (`cxx=`): 3 notebooks hit the 20 min timeout | pure-Python theano is too slow for `gp_classify_*` and `gmm_identifiability_pymc3` | keep compiling, with `-static` (first run compiles; cached afterwards) |

`tests/test_notebooks.py` sets `THEANO_FLAGS` to `blas__ldflags=` (Linux) or
`blas__ldflags=,gcc__cxxflags=-static` (Windows) unless it is already set. Without any MinGW `g++`
on PATH, theano falls back to pure Python and those 3 notebooks time out.

### 4.21 arviz / numba / setuptools for pymc3-era code
| Symptom | Cause | Fix |
|---|---|---|
| `module 'arviz' has no attribute 'from_pymc3'` | pymc3 3.11 calls it; arviz removed it after 0.12 | `arviz==0.12.1` |
| `No module named 'pkg_resources'` (importing arviz) | setuptools ≥ 81 no longer includes `pkg_resources` | `setuptools<81` |
| `TypingError: Failed in nopython mode pipeline` in `az.plot_kde` (`multi_collinear_legs_numpyro`, `gmm_identifiability_pymc3`) | current numba cannot compile arviz 0.12's KDE code | `numba==0.56.4` (Colab era) |

### 4.22 `minepy`: `Failed to build 'minepy'`, `No module named 'pkg_resources'`
- **Cause:** minepy is source-only and its `setup.py` imports `pkg_resources`; pip builds it in an
  isolated env with the newest setuptools, which no longer has it. Putting minepy in
  `requirements-local.txt` made the whole install fail.
- **Fix:** install it separately with `pip install --no-build-isolation minepy==1.2.6` (step 2.3), so it
  builds with the pinned setuptools. Needs a C compiler (one was available here; the runner has gcc).

### 4.23 Windows: `!wget`, `!unzip`, Graphviz `dot` not found
- **Notebooks:** `ae_mnist_conv`, `vae_mnist_conv_lightning` (download checkpoints with `!wget`),
  `matrix_factorization_recommender` (`!wget` + `!unzip` MovieLens), `hbayes_maml` (graphviz needs the `dot` program).
- **Cause:** Linux tools, not present on Windows. A failing `!` command does not stop the notebook,
  so the error appears later (`No such file or directory: 'ae-mnist-conv-latent-dim-20.ckpt'`).
  After installing wget, MovieLens still failed: wget's built-in CA store cannot verify
  `files.grouplens.org`'s certificate chain (`InCommon Intermediate CA`), exit code 5.
- **Fix:** `scripts/windows_admin_setup.ps1` installs wget and Graphviz and an `unzip.cmd` wrapper
  around Git's `unzip.exe`; wget is pointed at `certifi`'s CA bundle via `~\.wgetrc` and the
  `WGETRC` user variable (section 1.1). The Ubuntu runner has wget/unzip and system CA certificates.

### 4.24 `ae_mnist_tf` vs. `seq_logo_demo`: no pandas version satisfies both (known failure)
| pandas | `ae_mnist_tf`: `pd.set_option("precision", 2)` | `seq_logo_demo`: `pd.DataFrame(<jax array>)` |
|---|---|---|
| 1.3.5 | ✅ | ❌ object dtype → logomaker `ufunc 'isfinite' not supported` |
| 1.4.4, 1.5.3 | ❌ `OptionError: Pattern matched multiple keys` | ✅ float32 |

- **Cause:** pandas ≥ 1.4 added a second option matching "precision"; pandas < 1.4 does not treat
  jax 0.4 arrays as arrays. Upstream passed both with Colab's pandas 1.3.5 **and** jax 0.3, which is
  not an option here (no Windows wheels; chex/optax need jax 0.4).
- **Decision:** `pandas==1.5.3` (verified with chapters 1–2, no extra downgrades of xarray /
  xarray-einstats). `ae_mnist_tf` remained a failure until 4.26 edited its `set_option` line.

### 4.25 CI: random notebooks fail with `ValueError: Unknown mat file type, version 104, 116`
- **Symptom:** CI run [38358185226](../../actions/runs/38358185226) gave 162/172: `fisher_discrim_vowel`,
  `lassoPathProstate`, `hclust_yeast_demo` failed, although they passed in the run before.
- **Cause:** 18 notebooks (11 of them executed) download data/images with
  `https://github.com/<owner>/<repo>/blob/<ref>/<path>?raw=true`, which github.com redirects to
  `raw.githubusercontent.com`. github.com intermittently answers these with a **503 HTML page**
  (reproduced locally: 503, 503, then 200 for the same URL), and the notebooks pass the response to
  `loadmat` without checking the status: "version 104, 116" is `ht` from `<html>`.
  `raw.githubusercontent.com` returned 200 every time.
- **Fix:** `REGEX_REWRITES` in `tests/test_notebooks.py` rewrites such URLs in memory (like 4.17) to
  `https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>`, the file the redirect would
  reach. The notebook files stay identical to upstream. All 11 executed notebooks pass with it locally.

### 4.26 JupyterLab check of chapters 1–2: notebooks the dashboard never runs are broken
- **Symptom:** running every notebook of chapters 1–2 by hand (JUPYTER.md) failed in `tfidf_demo`
  (`'CountVectorizer' object has no attribute 'get_feature_names'`, then `np.matrix is not supported`)
  and `prob` (`OptionError: Pattern matched multiple keys`, then `HTTP Error 404`).
- **Cause:** the test runner only executes notebooks in the figure mapping, minus the ignore list:
  28 of the 35 notebooks in chapters 1–2. `tfidf_demo` is not mapped (upstream committed it with
  the same error in its outputs); `prob` is ignored. They were written for older libraries:
  scikit-learn < 1.2 (`get_feature_names()`, `np.matrix` input), pandas < 1.4 (`"precision"`
  option, see 4.24), and a data file since moved from `pyprobml/master/data` to `probml-data`.
- **Fix:** one-line edits in the notebooks (listed in `LOCAL_EDITS` of `sync_from_pyprobml.py`):

  | Notebook | Edit |
  |---|---|
  | `tfidf_demo` | `get_feature_names()` → `get_feature_names_out()`; `.todense()` → `.toarray()`, and `keepdims=True` in the row-norm check (np.matrix sums kept 2-D) |
  | `prob` | `pd.set_option("precision", 2)` → `"display.precision"`; `timemachine.txt` URL → `probml/probml-data/main/data/` |
  | `autodiff_tf`, `pca`, `ae_mnist_tf` | same `"display.precision"` edit (found by searching all notebooks); fixes the known failure `ae_mnist_tf` |

  | `linalg` | same `"display.precision"` edit; `from jax.experimental import optimizers` → `jax.example_libraries` (moved; the notebook only imports it) |
  | `linreg_sklearn` | same `"display.precision"` edit; `sklearn.datasets.load_boston()` (removed in scikit-learn 1.2) → the same data read from its original source `http://lib.stat.cmu.edu/datasets/boston`, as scikit-learn's deprecation notice suggests, wrapped in a `Bunch` with `data`, `target`, `feature_names` |

  `linalg` and `linreg_sklearn` were found later (a by-hand run hit the pandas line); both pass.
- **Check:** all 35 notebooks of chapters 1–2 pass when executed like JupyterLab (each in its own
  folder, kernel `pml-jupyter`, without the test runner's rewrites), 2.8 min.

### 4.27 Chapter 3 by hand: `module 'jax' has no attribute 'xla'`, `cannot import name 'Iterable' from 'collections'`
Neither notebook is run by the dashboard (not in the figure mapping); found in JupyterLab.

- **`mix_bernoulli_sgd_mnist`: `AttributeError: module 'jax' has no attribute 'xla'`**, inside distrax
  (`distrax/_src/utils/jittable.py`, `_is_jax_data`) when a distrax object passes through
  `jax.lax.scan` (`probml_utils.mix_bernoulli_lib.BMM.fit_sgd`).
  - **Cause:** `probml-utils` pins `distrax==0.1.3`, which calls `jax.xla.abstractify`; jax 0.4.23
    (4.6) removed `jax.xla`. distrax 0.1.5 fixed it by calling `jax.interpreters.xla.abstractify`,
    which jax 0.4.23 has, but installing it pulls jax 0.6 and numpy 2 (breaks 4.5).
  - **Fix:** apply distrax 0.1.5's one-line change to the installed distrax.
- **`sprinkler_pgm`: the notebook `%pip install`ed `causalgraphicalmodels` mid-run (4.3), which then
  failed with `ImportError: cannot import name 'Iterable' from 'collections'`.**
  - **Cause:** `causalgraphicalmodels` and `pgmpy` were not in `requirements-local.txt`.
    causalgraphicalmodels 0.0.4 (its latest release) imports `collections.Iterable`, removed in
    Python 3.10. The notebook uses `pgmpy.models.BayesianModel`, an old name.
  - **Fix:** pin `causalgraphicalmodels==0.0.4` and `pgmpy==0.1.23` (has `BayesianModel`, installs
    nothing else; 0.1.26 pulls xgboost and google-generativeai), and patch the import to
    `collections.abc`.
  - Needs Graphviz's `dot` (4.23). A shell started before `windows_admin_setup.ps1` added
    Graphviz to the PATH fails with `ExecutableNotFound: failed to execute WindowsPath('dot')`;
    open a new terminal before starting JupyterLab.
- **Patches:** `scripts/patch_packages.py` applies both one-line edits to the installed packages
  (step 2.3b; CI runs it after the installs). Idempotent; rerun it after reinstalling a package.
- **Check:** all 12 notebooks of chapter 3 pass when executed like JupyterLab.

### 4.28 JupyterLab: one `%pip install pymc` broke the whole env (`cannot import name copy_if_needed`)
- **Symptom:** after running `laplace_approx_beta_binom_pymc4` by hand, it and then other notebooks
  failed inside scipy: `ImportError: cannot import name copy_if_needed`; pip had printed
  `distrax 0.1.3 requires numpy<1.23 ..., but you have numpy 1.26.4`.
- **Cause:** the notebook's `try: import pymc / except: %pip install pymc` installed pymc 5.25.1,
  and pip upgraded numpy 1.22.4 → 1.26.4, scipy 1.10.1 → 1.15.3, pandas 1.5.3 → 2.3.3,
  matplotlib 3.5.3 → 3.10.9, arviz 0.12.1 → 0.23.4 (plus 10 new packages). 4.3 again, but by hand:
  the automated runs never hit it because the notebooks they execute have their packages pinned.
- **Repair:** `pip uninstall` the 10 new packages and `pip install --no-deps` the 5 old versions
  (a running kernel locks numpy's/scipy's DLLs on Windows: shut it down first); `pip freeze` was
  then identical to the snapshot taken before.
- **Prevention:** a pip constraints file with the env's `pip freeze`, set in the env's `pip.ini`
  (JUPYTER.md section 1): pip can add packages but not change installed versions. With it,
  `pip install pymc` resolves to **pymc 4.2.2** (+ aesara), which keeps all pins and runs the
  notebook (73 s); pinned in `requirements-local.txt`. The by-hand checks run with
  `PIP_NO_INDEX=1`, so a notebook cannot install anything at all.

### 4.29 JupyterLab check of chapters 4–8, 10–22: packages notebooks would `%pip install`
- **Check:** the 252 notebooks of these chapters run like JupyterLab (own folder, kernel
  `pml-jupyter`, `PIP_NO_INDEX=1`): 186 pass. The 6 failing dashboard notebooks also fail upstream
  (4.24 table); 53 of the failures are in `internal/ignored_notebooks.txt`.
- **Fixed** (the notebooks outside the dashboard and the ignore list, plus a pin each; installed
  under the lock of 4.28, which kept every existing version):

  | Notebook | Error | Fix |
  |---|---|---|
  | `bootstrap_demo_bernoulli` | `NameError: latexify` (`jaxtyping` missing) | `jaxtyping==0.3.7` |
  | `gp_kernel_plot` | `tinygp` missing; with tinygp 0.3 `Cannot set attribute scale` (kernels became equinox modules) | `tinygp==0.2.4`, `jaxopt==0.8.5` |
  | `layer_norm_jax`, `lecun1989_with_commentary` | no `flax` | `flax==0.8.4` (newest without a jax upgrade) |
  | `cifar10_cnn_lightning` | no `pl_bolts` | `lightning-bolts==0.7.0`; then trains > 20 min on CPU (fine by hand) |
  | `linreg_pymc3` | `az.plot_hpd` removed | notebook edit: `az.plot_hdi(..., hdi_prob=...)` |
  | `bayes_intro` (was ignored) | arviz 0.12: `credible_interval` renamed, `plot_joint` removed, `plot_ppc` returns one Axes for one variable | notebook edit: `hdi_prob=`, `plot_pair(..., marginals=True)`, `np.ravel(ax)[0]`; removed from the ignore list (`UNIGNORED`) |
  | `autodiff_jax` (was ignored) | `Gradient only defined for scalar-output functions`: the `has_aux` cell uses `x`, which the cell before set to a vector (notebook bug) | notebook edit: `x = 2.0`, `y = 3.0` at the start of the cell; removed from the ignore list (`UNIGNORED`) |
  | `flax_intro` (was ignored) | `flax.optim` removed (flax 0.6); `pyprobml/scripts/fit_flax.py` deleted upstream (404); `variables.pop` returns one value (flax >= 0.7 uses dicts) | notebook edit: `optax.sgd(momentum=0.9)` with `update`/`apply_updates`, a short `fit_model` with optax in place of `fit_flax.py`, `flax.core.pop(variables, ...)`, `!pip install` of flax at head and `superimport` commented out; removed from the ignore list (`UNIGNORED`) |
  | `opt_flax` (was ignored) | `flax.optim` removed; `config.enable_omnistaging` removed from jax; `pyprobml/scripts/fit_flax.py` deleted upstream; `google.colab` | notebook edit: `optax.sgd(momentum=0.9)` passed to the same short optax `fit_model` as in `flax_intro`; flax-at-head install, `enable_omnistaging()`, pyprobml clone and Colab cell commented out; removed from the ignore list (`UNIGNORED`) |
  | `opt_jax` (was ignored) | `AssertionError`: 5 epochs of SGD do not reach sklearn's nearly unregularized MLE (iris is nearly separable), so probabilities differ by > 0.1; `jax.experimental.optimizers` moved | notebook edit: assert the same predicted classes (`> 0.5`), old assert kept as a comment; `jax.example_libraries.optimizers`; removed from the ignore list (`UNIGNORED`) |
  | `logreg_jax` (was ignored) | `jax.experimental.optimizers` moved | notebook edit: `jax.example_libraries.optimizers`; removed from the ignore list (`UNIGNORED`) |
  | `logreg_pytorch` (was ignored) | `Can't call numpy() on Tensor that requires grad` (plotting the stored loss tensors) | notebook edit: `loss_trace.append(loss.item())` in the 4 training cells; removed from the ignore list (`UNIGNORED`) |
  | `groupLassoDemo` (dashboard; failed upstream too) | `%pip install spams` builds from source and fails (`No module named 'distutils.msvccompiler'`): no Windows/py3.10 wheel | `spams-bin==2.6.14` (prebuilt wheels for Windows and manylinux, same `import spams`, works with numpy 1.22); no notebook edit; passes in the test runner |
  | `mlp_1d_regression_hetero_tfp` (dashboard; failed upstream too) | `'Normal' object has no attribute 'shape'`: Keras >= 2.11 reads `.shape` of the model output, and `call` returned a raw `tfd.Normal` | notebook edit: the Normal is built by a `tfp.layers.DistributionLambda` (created in `__init__`), old `return` kept as a comment; the learned stddev matches the true noise (0.29/0.49/1.11 vs 0.25/0.5/1.25); passes in the test runner |
  | `sparse_mlp` (dashboard; failed upstream too) | `jax.experimental.stax` moved; `dot.view()` opened an external image viewer; `%cd /pyprobml/scripts` (Colab path) | notebook edit: `jax.example_libraries.stax`, `dot` shown inline (`dot.view()` kept as a comment), `%cd` commented out; passes in the test runner |
  | `pcaStandardization` (dashboard; failed upstream too) | `Reader needs file name or open file-like object`: reads `../data/heightWeight/heightWeight.mat`, which only exists in a pyprobml checkout | notebook edit: download it from `raw.githubusercontent.com/probml/probml-data` (as `height_weight_whiten_plot` does), old lines kept as comments; passes in the test runner |
  | `bnn_hierarchical_pymc3` (was ignored) | pymc3 3.11 / theano-pymc API changes, and `tt.batched_dot` compiles to BLAS `dgemm`, which theano cannot link on Windows with `blas__ldflags=` (4.20) | notebook edit: `MRG_RandomStream as MRG_RandomStreams` from `theano.sandbox.rng_mrg`; `sample_ppc` → `sample_posterior_predictive`; `batched_dot` → broadcasting `(a[..., None] * b[:, None]).sum(axis=2)`; `nuts_kwargs={...}` → `target_accept=0.9`; `varnames` → `var_names`; trace plot converted with `log_likelihood=False` (the model input is the prediction grid by then); removed from the ignore list |
  | `gmm_chooseK_pymc3` (dashboard; failed upstream too) | arviz 0.12.1 (pinned for pymc3) with pandas 1.5: `az.compare` sets a whole row with `.at` (`InvalidIndexError`), then `az.plot_compare` reads row 0 with `[0]`, a label lookup for the integer model names (`KeyError: 0`) | `scripts/patch_packages.py` patches arviz: `.loc` and `.iloc[0]` (as later arviz does); no notebook edit; passes in the test runner |
  | `lrschedule_tf` (dashboard, fig 8.17; failed upstream too) | `Axis limits cannot be NaN or Inf`: one pixel is 0 in all 1000 training images, its std is 0, so standardizing gave NaN and every loss was NaN; then `pd` used but never imported | notebook edit: `pixel_stds[pixel_stds == 0] = 1`, `import pandas as pd`; passes in the test runner |
  | `sgd_comparison` | `sls`/`sps`/`adasls` missing; `adasls` setup.py broken (missing comma, `sklearn` dummy package); `%pip install haven` installs an unrelated package into the same `haven/` folder; haven-ai 0.7 has no `haven_utils.exp_utils`; `google.colab.data_table` | `sls`/`sps` pinned by commit, `scikit-image==0.22.0`, `opencv-python-headless==4.11.0.86`; `scripts/install_sgd_comparison.py` installs adasls (setup.py fixed) and haven-ai 0.6.7 (both without `sklearn`); notebook edit: Colab import commented out, table shown with pandas |

- **flax also revives** 7 ignored notebooks: `multi_gpu_training_jax`, `conv2d_jax`, `lenet_jax`,
  `attention_jax`, `multi_head_attention_jax`, `positional_encoding_jax`, `rnn_jax`; they are removed
  from `internal/ignored_notebooks.txt` (and by `sync_from_pyprobml.py`, `UNIGNORED`), so the test
  runner now runs the three with book figures (`conv2d_jax`, `positional_encoding_jax`, `rnn_jax`:
  all pass; `positional_encoding_jax` needs `wget` on PATH for `d2l.py`). The other ignored
  flax notebooks still fail: API changes
  (`gru_jax`, `lstm_jax`, `nmt_attention_jax`, `batchnorm_jax`), cp949 decoding of the d2l data
  files (`*_sentiment_jax`, `nmt_jax`, `transformers_jax`), downloads (`bert_jax`, SNLI `Icon\r`),
  > 20 min on CPU (`densenet_jax`, `resnet_jax`), pickling in DataLoader workers (`skipgram_jax`).
- **Left as is** (ignored, upstream or platform problems): cp949 errors in the torch NLP notebooks,
  CUDA-only `multi_gpu_training_torch`, > 20 min torch CIFAR training, missing `xgboost`/
  `surprise`/`augmax` in notebooks of the ignore list, old APIs (`stax`, `optimizers`, `plot_hpd`
  in ignored notebooks).

### 4.30 Windows: `!mkdir figures # for saving plots` creates folders `#`, `for`, `saving`, `plots`
- **Symptom:** in JupyterLab, cells print (Korean Windows, often garbled) "A subdirectory or file
  figures already exists. Error occurred while processing: figures." and the same for `#`, `for`,
  `saving`, `plots`; empty folders with those names appear next to the notebooks.
- **Cause:** 41 notebooks (chapters 9, 11, 13–15, 19, 20) run `!mkdir figures # for saving plots`.
  `!` runs cmd.exe on Windows, which has no `#` comments, so mkdir gets five folder names. The
  notebook keeps running (shell errors do not stop a cell).
- **Fix:** `scripts/fix_shell.py` (first named `fix_mkdir.py`) replaces the line with
  `import os; os.makedirs("figures", exist_ok=True)`, which works everywhere and is silent when
  `figures` exists; `sync_from_pyprobml.py` runs it after every sync. Delete old junk folders with
  `Get-ChildItem notebooks -Recurse -Directory | Where-Object Name -in "#","for","saving","plots" | Remove-Item`.
- **Same for `!ls`:** cmd.exe has no `ls` ("'ls' is not recognized as an internal or external
  command", garbled in Korean Windows because cmd.exe writes cp949 and the kernel, with
  `PYTHONIOENCODING=utf-8`, reads UTF-8). `fix_shell.py` also replaces `!ls [-l] [dir]` with
  `import os; print(sorted(os.listdir(...)))` in the 7 notebooks that use it (`sparse_mlp`,
  `cifar10_cnn_lightning`, `ae_mnist_gdl_tf`, `vae_celeba_tf`, `vae_mnist_conv_lightning`,
  `matrix_factorization_recommender`, `matrix_factorization_recommender_surprise_lib`).
- **`!unzip`** (`matrix_factorization_recommender*`, `vae_celeba_tf`, `finetune_cnn_jax`): on a
  rerun the files exist and unzip waits for a "replace? [y]es/[n]o" answer, so the cell hangs until
  the 20-min timeout. `fix_shell.py` adds `-n` (never overwrite: existing files are skipped, so a
  rerun does not extract the 261 MB `hotdog.zip` again; first `-o`, changed in 4.33) to every
  `!unzip`. No `#` comment on that line: cmd.exe would pass it to unzip as file names.

### 4.31 Windows: `UnicodeDecodeError: 'cp949' codec can't decode byte 0xe2 ...` (11 notebooks)
- **Symptom:** `word_analogies_*` (GloVe vectors), `cnn1d_sentiment_*`, `rnn_sentiment_*`, `nmt_*`,
  `nmt_attention_torch` and `transformers_*` (d2l text corpora) fail when they read their data.
- **Cause:** they `open(path)` without `encoding=`. On Windows that means the locale code page
  (cp949 on Korean Windows), not UTF-8 as on Linux. `PYTHONIOENCODING` only covers stdin/stdout.
- **Fix:** Python UTF-8 mode, `PYTHONUTF8=1`: set by `tests/test_notebooks.py` (inherited by the
  kernel) and in the `pml-jupyter` kernel spec for JupyterLab (JUPYTER.md). No notebook edits, so
  upstream copies keep working.
- **Then flax >= 0.7 / jax API changes** in the jax versions (notebook edits, `LOCAL_EDITS`):
  - `grads.copy({...})` → `{**grads, ...}` (`cnn1d_sentiment_jax`, `rnn_sentiment_jax`): gradients
    are plain dicts now, and `dict.copy()` takes no arguments.
  - `nn.GRUCell.initialize_carry(rng, batch_dims, size)` →
    `nn.GRUCell(features=size, parent=None).initialize_carry(rng, batch_dims + (size,))`, same for
    `OptimizedLSTMCell` (`'int' object is not subscriptable`), and `nn.GRUCell()(state, x)` →
    `nn.GRUCell(features=state.shape[-1])(state, x)` (`missing ... argument: 'features'`); LSTM:
    `features=carry[1].shape[-1]`. In `nmt_jax`, `nmt_attention_jax`, `rnn_sentiment_jax`,
    `gru_jax`, `lstm_jax`.
  - `state[-1].tile(...)` → `jnp.tile(state[-1], ...)` (`nmt_jax`): jax arrays have no `.tile`.
- **Result:** `word_analogies_*`, `cnn1d_sentiment_*`, `nmt_*`, `nmt_attention_*`,
  `transformers_*`, `gru_jax` and `lstm_jax` pass and are removed from the ignore list
  (`UNIGNORED`). `rnn_sentiment_torch` and `rnn_sentiment_jax` run now, but their training cell
  exceeds the 20-min timeout on CPU; they stay ignored.

### 4.32 Big data files downloaded or extracted again on every run
- **Symptom:** reruns of the chapter 15/20 d2l notebooks spend minutes re-extracting IMDb
  (100k files), GloVe, SNLI, ...; `!wget URL` cells download the file again as `name.1`,
  `name.2`, ... (`hotdog.zip` 261 MB, MovieLens, CelebA, checkpoints). Two notebooks running at
  once can also read a half-extracted file: `word_analogies_jax` got 161,068 of 400,000 GloVe
  lines (`ValueError: setting an array element with a sequence ... inhomogeneous shape`).
- **Cause:** d2l's `download()` keeps an archive whose SHA-1 matches, but `download_extract()`
  calls `extractall` every time. wget without `-O` never overwrites a file and saves a numbered copy.
- **Fix (no download options in the notebooks themselves, so done by rewrites after every sync):**
  - `scripts/fix_download.py` (18 notebooks): extract only if `<archive>.extracted` is missing,
    and write that marker after a complete extraction (an interrupted one is redone).
    Delete the marker to force a new extraction.
  - `scripts/fix_shell.py`: `!wget URL` without `-O` → `!wget -nc URL` (no-clobber: an existing
    file is kept, 7 notebooks). Lines with `-O` (small `d2l.py`, images) still download.
  - Delete a file in `notebooks/book1/data/` (or next to the notebook) to download it again.

### 4.33 Missing packages: xgboost, augmax, surprise (4 ignored notebooks)
- **Symptom:** `No module named 'xgboost'` (`feature_importance_trees_tutorial`), `'augmax'`
  (`image_augmentation_jax`, `finetune_cnn_jax`), `'surprise'`
  (`matrix_factorization_recommender_surprise_lib`).
- **Fix:** pinned in `requirements-local.txt`, all checked with a dry run against the lock (4.28):
  `xgboost==2.0.3`, `lime==0.2.0.1`, `shap==0.44.1` (newest for numba 0.56 / numpy 1.22),
  `augmax==0.3.4` (newest for jax 0.4.23), `jax-resnet==0.0.4`. scikit-surprise has no Windows
  wheels: `pip install --no-build-isolation scikit-surprise==1.1.4 surprise==0.1` builds it with
  MSVC against the env's numpy 1.22 (step 2.3d; build isolation would compile against numpy 2).
- **Then Colab-only code and prompts** (notebook edits, `LOCAL_EDITS`):
  - `image_augmentation_jax`: `!wget ... -O cat_dog.jpg` and `cv2.imread("cat_dog.jpg")` instead of
    `/content/cat_dog.jpg` and `!mv` (wget names the file `cat_dog.jpg?raw=true`).
  - `finetune_cnn_jax`: `hotdog.zip` and `hotdog/...` next to the notebook instead of `/content/`.
  - both: `montage(..., multichannel=True)` → `channel_axis=-1` (removed in scikit-image 0.22).
  - `image_augmentation_jax` loads `tfds.load("cifar10")`: the first download from cs.toronto.edu
    can take longer than the 20-min cell timeout (~60 KB/s here). Download it once beforehand:
    `& $py -c "import tensorflow_datasets as tfds; tfds.builder('cifar10').download_and_prepare()"`;
    tfds then loads it from `~\tensorflow_datasets`.
- **Result:** `feature_importance_trees_tutorial` and `matrix_factorization_recommender_surprise_lib`
  pass and are removed from the ignore list. `finetune_cnn_jax` runs, but its training cell exceeds
  the 20-min timeout on CPU and stays ignored. `image_augmentation_jax` passes (17 s) once
  CIFAR-10 is in `~\tensorflow_datasets` (the download took 53 min here). Removed from the ignore
  list, so the dashboard shows figure 19.1.
  - `matrix_factorization_recommender_surprise_lib`: `Dataset.load_builtin("ml-1m", prompt=False)`;
    otherwise surprise asks "download? [Y/n]" with `input()` (`StdinNotImplementedError`).

### 4.34 Old library APIs: `knn_demo`, `batchnorm_jax`, `vae_mnist_gdl_tf` (ignored notebooks)
- `knn_demo`: `No module named 'sklearn.datasets.samples_generator'` (removed in scikit-learn
  0.24) → `from sklearn.datasets import make_blobs`.
- `batchnorm_jax`: `batch_stats, params = variables.pop("params")` used `FrozenDict.pop`, which
  returned (rest, popped); flax >= 0.7 returns plain dicts → `params = variables["params"]` and
  `batch_stats = {k: v for k, v in variables.items() if k != "params"}`.
- `vae_mnist_gdl_tf`: `KeyError: The optimizer cannot recognize variable encoder_conv_0/kernel:0`.
  One Adam optimizer trains several models; TF >= 2.11 optimizers bind to the first model's
  variables → `tf.keras.optimizers.legacy.Adam(1e-3)`, which keeps per-variable slots as before.
- **Result:** all three pass (notebook edits, `LOCAL_EDITS`) and are removed from the ignore list.

### 4.35 `bert_*`: `BadZipFile: File is not a zip file` (wikitext-2)
- **Cause:** the d2l `DATA_HUB` URL `https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-v1.zip`
  is gone: S3 answers with a 487-byte XML `PermanentRedirect` error, and d2l's `download()` saves
  it as `data/wikitext-2-v1.zip`.
- **Fix:** `bert_jax`, `bert_torch` download from `https://wikitext.smerity.com/wikitext-2-v1.zip`,
  the same file (SHA-1 `3c914d17...` matches `DATA_HUB`). `scripts/fix_download.py` also adds
  `r.raise_for_status()` after `requests.get` in d2l's `download()` (24 notebooks), so a dead link
  fails at the download with the HTTP error instead of a bad file later.

### 4.36 `vae_celeba_tf`: `'rm' is not recognized`, `ERROR 404`, `No such file ... .csv`
- **Cause:** `!rm {csv_name}` / `!rm {zip_name}` / `!rm *.jpg` (no `rm` in cmd.exe; garbled Korean
  message), the CSV URL has `/tree/` (raw.githubusercontent.com has no such path: 404), and the zip
  is no longer in pyprobml (404). Both files are in `probml-data/main/data/CelebA/`.
- **Fix (notebook edits, `LOCAL_EDITS`):** both downloads from
  `https://raw.githubusercontent.com/probml/probml-data/main/data/CelebA/`; the `!rm` lines dropped
  (they only forced a new 34 MB download and re-extraction; `wget -nc` and `unzip -n` keep existing
  files); the `!ls` replacement lists only non-`.jpg` files (not the 20000 images); the Colab-only
  `%tensorflow_version` / `IS_COLAB` lines removed.
- **Then** the same optimizer `KeyError` as `vae_mnist_gdl_tf` (4.34): one Adam trains several
  models → `tf.keras.optimizers.legacy.Adam(1e-3)` (4 places).
- **Result:** passes (about 25 min in total, no cell over the timeout); removed from the ignore list.

### 4.37 Windows: d2l notebooks hang at the first loop over a `DataLoader` (cell timeout)
- **Symptom:** `bert_*` (in `load_data_wiki`), `entailment_attention_mlp_*`, `skipgram_*`: the
  cell that first iterates the data never finishes (20-min timeout), long before training.
- **Cause:** they define their own torch `Dataset` classes in the notebook and read them with
  `DataLoader(..., num_workers=4)`. Windows starts worker processes fresh ("spawn"), and they cannot
  load classes defined in a notebook, so the loop waits forever. DataLoaders over torchvision
  datasets (MNIST, ...) work: those classes can be imported.
- **Fix:** `scripts/fix_workers.py` (6 notebooks, run after every sync):
  `num_workers = 0 if os.name == "nt" else 4`, so Windows loads data in the main process and
  Linux (CI) keeps the workers.
- **Then** `entailment_attention_mlp_*`: `OSError: [Errno 22] Invalid argument:
  '..\\data\\snli_1.0\\Icon\r'`. The SNLI zip was made on macOS and contains `Icon\r` files; a
  name with a carriage return cannot be created on Windows. `fix_download.py` now extracts only
  entries without `\r` in their names (18 notebooks with `download_extract`).
- **Then** `bert_*` hang again while building the SNLI dataset: `SNLIBERTDataset._preprocess` runs
  `multiprocessing.Pool(4).map(self._mp_worker, ...)` on a notebook-defined class (same spawn
  problem; the kernel died, leaving 4 idle workers). `fix_workers.py` now maps in the main process
  on Windows and keeps the Pool on Linux.
- **Results:** `skipgram_jax`, `skipgram_torch`, `entailment_attention_mlp_torch`, `bert_torch`
  (171 s on the GPU, 4.39) pass and are removed from the ignore list (`UNIGNORED`);
  `entailment_attention_mlp_jax` reaches training but 4 epochs over SNLI exceed the 20-min cell
  timeout on CPU, and `bert_jax` was not yet retested (both stay ignored).

### 4.38 `cnn_cifar_pytorch`: `'_SingleProcessDataLoaderIter' object has no attribute 'next'`
- **Cause:** `dataiter.next()`; torch >= 1.13 DataLoader iterators only support the built-in
  `next()` (the Python 2 style `.next()` method was removed).
- **Fix (notebook edits, `LOCAL_EDITS`):** `next(dataiter)` in `cnn_cifar_pytorch` (2 places) and
  `cifar10_cnn_lightning` (1 place).
- `cifar10_cnn_lightning` also had Colab/TPU code and APIs removed since it was written:
  - the `USE_TPU` / `COLAB_TPU_ADDR` / `torch_xla` setup and the Linux-only
    `!grep Model: /proc/driver/nvidia/...` → `ACCELERATOR = "gpu" if torch.cuda.is_available() else "cpu"`;
    the TPU branch of the batch-size choice removed;
  - the two `from google.colab import files` cells (`files.download` / `files.upload`) removed;
  - `Trainer(progress_bar_refresh_rate=10, tpu_cores=..., gpus=...)` (removed in Lightning 1.7 / 2.0)
    → `Trainer(accelerator=ACCELERATOR, devices=1, callbacks=[TQDMProgressBar(refresh_rate=10), ...])`;
  - `accuracy(preds, y)` → `accuracy(preds, y, task="multiclass", num_classes=10)` (torchmetrics >= 0.11);
  - `OneCycleLR(..., steps_per_epoch=len(self.train_dataloader()))` →
    `total_steps=self.trainer.estimated_stepping_batches` (the data come from the datamodule);
  - `resnet18(pretrained=False, ...)` → `weights=None`.
- **Results:** `cnn_cifar_pytorch` passes (346 s on CPU; it was listed as a timeout, but failed on
  `.next()`) and is removed from the ignore list; `cifar10_cnn_lightning` (not ignored) passes in
  872 s on the GPU.

### 4.39 PyTorch on the GPU (local env only)
- Many remaining failures are cell timeouts of torch training (`resnet_torch`, `densenet_torch`,
  `rnn_sentiment_torch`, ...): `requirements-local.txt` installs `torch==2.1.2` from PyPI, the CPU
  build on Windows, so an NVIDIA GPU (here an RTX 3090 Ti, driver 560.81, CUDA 12.6) is unused.
- **Fix:** `pip install --no-deps --force-reinstall torch==2.1.2+cu121 torchvision==0.16.2+cu121
  --index-url https://download.pytorch.org/whl/cu121` (same versions, same dependencies; the Windows
  wheels bundle the CUDA libraries). `pip check` is clean, and the pinned constraint `torch==2.1.2`
  accepts `+cu121`; the lock is regenerated afterwards (JUPYTER.md 1).
- `requirements-local.txt` and CI keep the CPU build. TensorFlow >= 2.11 and JAX have no native
  Windows GPU support (WSL2 only), so `*_tf` / `*_jax` notebooks still run on the CPU.
- **Result:** `multi_gpu_training_torch` (54 s; calls `torch.cuda.synchronize()`) and
  `finetune_cnn_torch` (88 s; hours on a CPU) pass unchanged and are removed from the ignore list.
  Neither is in the figure mapping, so the CI (CPU) test does not run them.

### 4.40 `pre_trained_image_classifier_torch`: `UnidentifiedImageError: cannot identify image file 'img.jpg'`
- **Cause:** `!wget https://github.com/probml/pyprobml/blob/master/images/cat_dog.jpg?raw=true -q -O img.jpg`:
  the images left pyprobml (404), and `wget -q -O` leaves an empty `img.jpg` without a message.
  The class list `pyprobml/master/data/imagenet_classes.txt` is gone the same way, and the last
  cell used `percentage`, which the notebook never defines.
- **Fix (notebook edits, `LOCAL_EDITS`):** the image from
  `raw.githubusercontent.com/probml/probml-notebooks/main/images/cat_dog.jpg` (as
  `image_augmentation_jax`), the class list from `probml-data/main/data/imagenet_classes.txt`
  (1000 lines) read with `requests` (`raise_for_status()`; the `urllib` copy gave bytes labels),
  `percentage = softmax(out, dim=1)[0] * 100`, and `resnet101(weights=ResNet101_Weights.IMAGENET1K_V1)`
  instead of the deprecated `pretrained=True`. The notebook keeps its key order (edited with `json`,
  not `nbformat.write`, which sorts keys and rewrote the whole file).
- **Result:** passes; removed from the ignore list.

## 5. Results

### 5.1 All of Book 1 (172 executed notebooks)

| Run | Environment | Passed | Failed |
|---|---|---|---|
| Upstream pyprobml dashboard (for comparison) | their CI | 165 | 7 |
| Local, first full run | `pyprobml-exp` (fresh env + 15 libraries, before 4.20–4.24) | 151 | 21 |
| Local, clean run, rebuilt env | `pyprobml-fresh` from `requirements-local.txt` + 2.3, Windows 11, 16 min | **164** | 8 |
| CI, run [38352919703](../../actions/runs/38352919703) | `ubuntu-latest`, pinned setup, 31 min | **165** | 7 |

The 8 local failures:

| Notebook | Reason |
|---|---|
| `lrschedule_tf`, `groupLassoDemo` (needs `spams`), `mlp_1d_regression_hetero_tfp`, `sparse_mlp` (`jax.experimental.stax` removed), `pcaStandardization`, `gmm_chooseK_pymc3` | **also fail upstream** |
| `ae_mnist_tf` | pandas trade-off (4.24); passes since the `"display.precision"` edit (4.26) |
| `pcaImageDemo` | could not write `C:\PcaTrainFaceImages.pdf`; passes since the in-memory rewrite (4.17) |

(Later: `lrschedule_tf`, `groupLassoDemo`, `mlp_1d_regression_hetero_tfp`, `sparse_mlp`, `pcaStandardization` and `gmm_chooseK_pymc3` pass since the fixes of 4.29, and `ae_mnist_tf` since 4.26 (rechecked in JupyterLab and with the runner): all dashboard notebooks pass locally.)

CI fails exactly the 6 upstream failures plus `ae_mnist_tf`. So 165 pass both on CI and locally
(after 4.17's rewrite): the same number as upstream; the sets differ by one notebook each way
(`mix_bernoulli_em_mnist` fails upstream but passes here; `ae_mnist_tf` the opposite).
`pip freeze` was identical before and after the run.

### 5.2 Chapters 1–2 (28 notebooks)

| Run | Environment | Passed | Failed |
|---|---|---|---|
| CI, run [38333885122](../../actions/runs/38333885122) | `ubuntu-latest`, `requirements.txt` | 15 | 13 |
| CI, pinned setup, first try, run [38341210973](../../actions/runs/38341210973) | `ubuntu-latest`, `requirements-local.txt` before 4.14/4.15 | 0 | 28 |
| CI, pinned setup with 4.14/4.15, run [38342131247](../../actions/runs/38342131247) | `ubuntu-latest`, `requirements-local.txt` + TeX Live + datasets | 27 | 1 (4.16) |
| CI, pinned setup with 4.14–4.16, run [38342585490](../../actions/runs/38342585490) | same + writable `/teamspace` | **28** | **0** |
| Local, first attempt | clone of base + `requirements.txt` | 6 | 22 |
| Local, after fixes 4.3–4.12 | `pyprobml` + `requirements-local.txt` + pre-downloaded datasets | **28** | **0** |
| Local, fresh env (no Anaconda base) | `pyprobml-fresh` (Python 3.10.22) + `requirements-local.txt` with 4.14/4.15 | **28** | **0** |

The two local "after fixes" rows are single clean runs of all 28 notebooks (`pytest -n 4`,
Windows 11; 49 s and 44 s). For the clone-of-base run, `pip freeze` was identical before and
after, so no notebook installed anything.
