"""
One-line fixes to installed packages whose pinned versions are incompatible with the rest of the
pinned set (REPRODUCE.md 4.27). Idempotent; rerun after reinstalling a package.

Usage (with the env's python):
    python scripts/patch_packages.py
"""
import importlib.util
import pathlib

PATCHES = {
    # distrax 0.1.3 (pinned by probml-utils) calls jax.xla, removed in jax 0.4.23.
    # Backport of distrax 0.1.5's fix (0.1.5 itself needs jax 0.6 / numpy 2).
    "distrax": [("jax.xla.abstractify(", "jax.interpreters.xla.abstractify(")],
    # causalgraphicalmodels 0.0.4 (latest release): collections.Iterable is gone since Python 3.10.
    "causalgraphicalmodels": [("from collections import Iterable", "from collections.abc import Iterable")],
    # arviz 0.12.1 (pinned for pymc3) sets a whole row of az.compare's table with .at, which
    # pandas 1.5 rejects (InvalidIndexError); later arviz uses .loc (gmm_chooseK_pymc3, REPRODUCE.md 4.29).
    # plot_compare reads the first row with [0], a label lookup when the models have integer names.
    "arviz": [
        ("df_comp.at[val] = (", "df_comp.loc[val] = ("),
        ('comp_df[f"{information_criterion}_scale"][0]', 'comp_df[f"{information_criterion}_scale"].iloc[0]'),
    ],
}

for package, edits in PATCHES.items():
    spec = importlib.util.find_spec(package)
    if spec is None:
        print(f"{package}: not installed")
        continue
    patched = 0
    for path in pathlib.Path(spec.origin).parent.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        new = text
        for old, repl in edits:
            new = new.replace(old, repl)
        if new != text:
            path.write_text(new, encoding="utf-8")
            patched += 1
            print(f"patched {path}")
    print(f"{package}: {patched} file(s) patched" if patched else f"{package}: already patched")
