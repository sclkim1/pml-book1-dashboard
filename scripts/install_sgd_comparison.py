"""Install adasls and haven-ai, which sgd_comparison.ipynb imports (REPRODUCE.md 4.29).

Neither can be pip-installed as is; their other dependencies are in requirements-local.txt.
- adasls (ada_sls): setup.py cannot be built, a missing comma joins two requirements
  ('tqdm>=0.0' 'numpy>=0.0'). Fetch a fixed commit and add the comma.
- haven-ai: 0.6.7 is the last release with haven.haven_utils.exp_utils, which the notebook imports.
  (The notebook also runs `%pip install haven`: an unrelated package that writes into the same
  haven/ folder; don't install it.)
Both list the 'sklearn' dummy package, which refuses to install (scikit-learn is listed too): drop
it from adasls' setup.py, install haven-ai without dependencies and drop it from its metadata, so
that `pip check` stays clean.
"""
import importlib.metadata
import io
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ADASLS_COMMIT = "a45f5ec624546daead048894be2d8048f0a2c02c"
ADASLS_URL = f"https://github.com/IssamLaradji/ada_sls/archive/{ADASLS_COMMIT}.zip"
HAVEN_AI = "0.6.7"


def pip_install(*args):
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", *args], check=True)


def installed(name):
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


if installed("adasls"):
    print("adasls already installed")
else:
    with tempfile.TemporaryDirectory() as tmp:
        with urllib.request.urlopen(ADASLS_URL) as r:
            zipfile.ZipFile(io.BytesIO(r.read())).extractall(tmp)
        src = Path(tmp) / f"ada_sls-{ADASLS_COMMIT}"
        setup = src / "setup.py"
        text = setup.read_text()
        assert "'tqdm>=0.0'\n" in text and "'sklearn>=0.0',\n" in text, "setup.py changed; check the fix"
        setup.write_text(text.replace("'tqdm>=0.0'\n", "'tqdm>=0.0',\n").replace("'sklearn>=0.0',\n", ""))
        pip_install("--no-build-isolation", str(src))
    print("adasls installed")

if installed("haven") is not None:
    sys.exit("the unrelated 'haven' package is installed: pip uninstall haven haven-ai, then rerun")
if installed("haven-ai") == HAVEN_AI:
    print("haven-ai already installed")
else:
    pip_install(f"haven-ai=={HAVEN_AI}")
    dist = importlib.metadata.distribution("haven-ai")
    metadata = Path(dist._path) / "METADATA"
    lines = metadata.read_text(encoding="utf-8").splitlines(keepends=True)
    metadata.write_text("".join(l for l in lines if not l.startswith("Requires-Dist: sklearn ")), encoding="utf-8")
    print("haven-ai installed")
