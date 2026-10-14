"""Load data in the main process on Windows (REPRODUCE.md 4.37).

d2l notebooks define their own torch `Dataset` classes (`_WikiTextDataset`, `SNLIDataset`,
`RandomGenerator`, ...) and read them with `DataLoader(..., num_workers=4)`. On Windows, worker
processes are started fresh ("spawn") and cannot load classes defined in a notebook, so the first
loop over the loader waits forever (cell timeout). Use `num_workers = 0` on Windows only; Linux
(CI) keeps the workers. DataLoaders over torchvision datasets (MNIST, ...) work and are not changed.

Usage: python scripts/fix_workers.py <notebook.ipynb>...   (edits the files as text)
"""
import re
import sys

COMMENT = rb"  # fix_workers.py: no workers on Windows (notebook-defined Dataset)"
# a source line `num_workers = 4` (optional comment), e.g. inside load_data_wiki / load_data_snli
ASSIGN = re.compile(rb'"( *)num_workers = (\d+)(?: *#[^"\\]*)?\\n"')
# `batch_size, max_len, num_workers = 256, 128, 4`
TUPLE = re.compile(rb'"( *)(batch_size, max_len, num_workers = \d+, \d+, )(\d+)\\n"')


def assign_new(m):
    return (b'"' + m.group(1) + b'num_workers = 0 if os.name == \\"nt\\" else ' + m.group(2) + COMMENT + b'\\n"')


def tuple_new(m):
    return (b'"' + m.group(1) + m.group(2) + b'(0 if os.name == \\"nt\\" else ' + m.group(3) + b")" + COMMENT + b'\\n"')


changed = 0
for path in sys.argv[1:]:
    with open(path, "rb") as f:
        text = f.read()
    new, n1 = ASSIGN.subn(assign_new, text)
    new, n2 = TUPLE.subn(tuple_new, new)
    if n1 or n2:
        with open(path, "wb") as f:
            f.write(new)
        changed += 1
print(f"DataLoader workers fixed in {changed} notebooks")
