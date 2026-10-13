# Running the notebooks by hand in JupyterLab

How to open and check the notebooks interactively, with the same pinned environment the
automated test (`tests/test_notebooks.py`) uses. Commands are for PowerShell on Windows.

## 1. Build the environment (once)

Follow [REPRODUCE.md](REPRODUCE.md) section 2, with the env name `pml-jupyter`. JupyterLab 3.6 is
already in `requirements-local.txt` (via `jupyter`), compatible with the pinned kernel stack.

```powershell
cd C:\Users\kskim\pml-book1
conda create -n pml-jupyter python=3.10 -y
$py = "$HOME\anaconda3\envs\pml-jupyter\python.exe"
& $py -m pip install -U pip
& $py -m pip install -r requirements-local.txt     # if it fails (e.g. "Could not resolve host"),
                                                   # remove the env and start again
& $py -m pip install --no-build-isolation minepy==1.2.6
& $py scripts/patch_packages.py                    # REPRODUCE.md 4.27
& $py -m ipykernel install --user --name pml-jupyter --display-name "Python (pml-jupyter)"
& $py -m pip check                                 # -> No broken requirements found.
```

Then give the kernel the settings the test runner sets for the pymc3 notebooks
(REPRODUCE.md 4.20):

```powershell
$f = "$env:APPDATA\jupyter\kernels\pml-jupyter\kernel.json"
$k = Get-Content $f -Raw | ConvertFrom-Json
$k | Add-Member -Force env ([ordered]@{ THEANO_FLAGS = "blas__ldflags=,gcc__cxxflags=-static"; PYTHONIOENCODING = "utf-8" })
$k | ConvertTo-Json -Depth 5 | Set-Content $f -Encoding utf8
```

Many notebooks save figures to `figures/` or `../figures/` relative to the folder they run in, without
creating it (`FileNotFoundError: ... 'figures\\cifar10-data.pdf'`). The test runner runs from the
repository root, where `figures/` exists; JupyterLab runs each notebook in its own folder. The
repository therefore contains an empty `figures/` folder (with a `.gitkeep` file) in every notebook
folder and in `notebooks/book1/`; the figures saved into them are ignored by git. If a folder is
missing (e.g. for newly synced notebooks), create them with:

```powershell
Get-ChildItem notebooks\book1 -Recurse -Filter *.ipynb |
    Where-Object { $_.DirectoryName -notmatch "ipynb_checkpoints" } |
    Select-Object -ExpandProperty DirectoryName -Unique |
    ForEach-Object { New-Item -ItemType Directory -Force "$_\figures", "$(Split-Path $_)\figures" | Out-Null }
```

For chapters 3–22, also do the machine setup (REPRODUCE.md 1.1) and the dataset pre-downloads (2.6).

## 2. Start JupyterLab

```powershell
& "$HOME\anaconda3\envs\pml-jupyter\Scripts\jupyter-lab.exe" --notebook-dir C:\Users\kskim\pml-book1\notebooks\book1
```

The browser opens `http://localhost:8888/lab`; if not, open the `http://localhost:8888/lab?token=...`
link printed in the terminal. Keep the terminal open while working.
(Alternative: `conda activate pml-jupyter`, then `jupyter lab --notebook-dir ...`.)

## 3. Open a notebook and pick the kernel

1. In the left file panel, open a chapter folder (`01`, `02`, ...) and double-click a `.ipynb`.
2. **Check the kernel name at the top right: it must be `Python (pml-jupyter)`.** If it shows
   `Python 3` or anything else: *Kernel → Change Kernel… → Python (pml-jupyter)*.
   Only this kernel has the pinned packages and `THEANO_FLAGS`.

## 4. Run and check

- *Run → Restart Kernel and Run All Cells…*: a clean full run, like the automated test.
- `Shift+Enter`: run one cell.
- `[*]` next to a cell = still running; `[5]` = done.
- The notebook works if every cell finishes without a red error and the figures appear.

To compare, run the same chapters with the test runner (results in `test_results/`):

```powershell
$env:NB_KERNEL = "pml-jupyter"
& "$HOME\anaconda3\envs\pml-jupyter\python.exe" -m pytest -n 4 -q -p no:cacheprovider tests/test_notebooks.py -k "iris_plot or iris_kmeans"
```

The test runner only runs the notebooks of the figure mapping (28 of the 35 in chapters 1–2).
Checked by hand / like JupyterLab: **all 35 notebooks of chapters 1–2 pass** in `pml-jupyter`
(after the edits of REPRODUCE.md 4.26).

### Links between notebooks

The figure notebooks (`fig_<chapter>_<n>.ipynb`) only hold a caption with links to the notebooks
that generate the figure, and some notebooks link to related ones. Upstream links point to Google
Colab; `scripts/local_links.py` replaced them with relative links (e.g. `beta_dist_plot.ipynb`,
`../03/gmm_2d.ipynb`), which open the local notebook in JupyterLab: 50 links in 35 notebooks.

- Only markdown links are changed; the "Open in Colab" badges at the top of notebooks are kept.
- Links to old paths (`notebooks/rnn_torch.ipynb`, `probml-notebooks`) or the wrong chapter point
  to the only local notebook with that file name.
- 13 links stay on Colab: their notebooks (`text_preproc_torch`, `jax_intro`, `datasets`, `opt`,
  `bagging_boosting_trees_and_forests`) are not in this repository.
- `scripts/sync_from_pyprobml.py` runs `local_links.py` after every sync.

## 5. Differences from the automated test

| | Test runner (`pytest`) | JupyterLab |
|---|---|---|
| Working folder | repository root | the notebook's folder (`notebooks/book1/<chap>/`) |
| `FIG_DIR` | `figures` → figures are saved as files | not set → figures are only shown inline |
| `github.com/...?raw=true` downloads | rewritten to `raw.githubusercontent.com` (REPRODUCE.md 4.25) | original URL: GitHub sometimes answers 503 (e.g. `Unknown mat file type`); re-run the cell |
| `pcaImageDemo` `savefig("/PcaTrainFaceImages.png")` | redirected (4.17) | original code: `PermissionError` |
| Time limit | 20 min per notebook | none |

## 6. Keep the repository clean

- Files the notebooks write (datasets, checkpoints, figures) land next to the notebook; git ignores
  everything under `notebooks/` except `.ipynb` files.
- **Saving a notebook stores its outputs in the `.ipynb`**, which then differs from upstream. Don't
  save, or undo it with `git checkout -- notebooks`.

## 7. Stop

- Stop a long cell: *Kernel → Interrupt* (or press `I`, `I`).
- Quit: *File → Shut Down*, or `Ctrl+C` twice in the terminal.

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` | wrong kernel (section 3) |
| `FileNotFoundError: ... 'figures\\<name>.pdf'` | the `figures` folder is missing; create it (section 1) |
| A cell starts `%pip install ...` | wrong kernel; interrupt it — unpinned installs break the env (REPRODUCE.md 4.3) |
| `blas_opt_info` error in pymc3 notebooks | kernel lacks `THEANO_FLAGS` (section 1) |
| Kernel dies / keeps restarting | `& $py -m pip check` must print `No broken requirements found.` |
| `PermissionError` for `C:\Users\kpmurphy\...` | run `scripts/windows_admin_setup.ps1` as admin (REPRODUCE.md 1.1) |
