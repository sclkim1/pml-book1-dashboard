# pml-book1-dashboard

A reproduction of the [pyprobml figure dashboard](https://github.com/probml/pyprobml/blob/workflow_testing_indicator/dashboard_figures_book1.md) for *Probabilistic Machine Learning: An Introduction* (Book 1), all 22 chapters.

**Dashboard:** [dashboard_figures_book1.md](https://github.com/sclkim1/pml-book1-dashboard/blob/workflow_testing_indicator/dashboard_figures_book1.md)
(same layout as upstream's; every link points to this repository: notebook links open the notebook
here on GitHub, not in Colab, and the ✅/❌ icons and logs come from this repository's test run).

| | Upstream | Here |
|---|---|---|
| Dashboard rows (figures) | 245 | 245 |
| Notebooks executed | 172 | 186 |
| Rows "notebook missing upstream" | 10 | 0 (renamed or moved notebooks remapped, [REPRODUCE.md](REPRODUCE.md) 4.44, 4.45) |
| Passing | 165 | 174 of 177 in the last full CI run (details in [REPRODUCE.md](REPRODUCE.md) 5.1) |

## How it works

On every push to `main` (or a manual run from the Actions tab), `.github/workflows/dashboard.yml`:

1. runs every notebook listed in `internal/figures_url_mapping_book1.csv` (`tests/test_notebooks.py`), saving a ✅/❌ icon and an error log for each one in `test_results/`;
2. builds `dashboard_figures_book1.md` (`scripts/create_figure_dashboard.py`);
3. publishes both to the `workflow_testing_indicator` branch.

A full run takes about an hour; a newer push cancels a run still in progress.

## Running locally

- [REPRODUCE.md](REPRODUCE.md): building the pinned conda environment (`requirements-local.txt`),
  running the notebooks on Windows, and every problem found along the way with its fix.
- [JUPYTER.md](JUPYTER.md): opening and checking the notebooks by hand in JupyterLab.
  [`notebooks/book1/dashboard_local.md`](notebooks/book1/dashboard_local.md) is the same dashboard
  with links that open the local notebooks in JupyterLab.

Notebooks are committed without outputs. A notebook saved in JupyterLab stores its outputs, which
contain local paths (e.g. your user name): don't commit it; undo it with `git checkout -- notebooks`
(JUPYTER.md section 6).

## Updating from upstream

```
python scripts/sync_from_pyprobml.py --chapters 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22
git add -A && git commit -m "Sync with pyprobml" && git push
```

The sync overwrites every notebook except those in its `LOCAL_EDITS` list, so commit or discard
your own changes first.

Notebooks are copied from [probml/pyprobml](https://github.com/probml/pyprobml) (MIT License).
