# pml-book1-dashboard

A minimal reproduction of the [pyprobml figure dashboard](https://github.com/probml/pyprobml/blob/workflow_testing_indicator/dashboard_figures_book1.md) for *Probabilistic Machine Learning: An Introduction* (Book 1).

**Dashboard:** [dashboard_figures_book1.md](https://github.com/sclkim1/pml-book1-dashboard/blob/workflow_testing_indicator/dashboard_figures_book1.md)
(same layout as upstream's; every link points to this repository: notebook links open the notebook
here on GitHub, not in Colab, and the ✅/❌ icons and logs come from this repository's test run).

## How it works

On every push to `main` (or a manual run from the Actions tab), `.github/workflows/dashboard.yml`:

1. runs every notebook listed in `internal/figures_url_mapping_book1.csv` (`tests/test_notebooks.py`), saving a ✅/❌ icon and an error log for each one in `test_results/`;
2. builds `dashboard_figures_book1.md` (`scripts/create_figure_dashboard.py`);
3. publishes both to the `workflow_testing_indicator` branch.

## Running locally

See [REPRODUCE.md](REPRODUCE.md) for building the pinned conda environment
(`requirements-local.txt`), running the notebooks on Windows, and every setup problem found along the way.
See [JUPYTER.md](JUPYTER.md) for opening and checking the notebooks by hand in JupyterLab.

## Adding chapters

```
python scripts/sync_from_pyprobml.py --chapters 1 2 3
git add -A && git commit -m "Add chapter 3" && git push
```

Notebooks are copied from [probml/pyprobml](https://github.com/probml/pyprobml) (MIT License).
