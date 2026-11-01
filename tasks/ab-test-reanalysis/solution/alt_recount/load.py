"""Export reader (alt_recount solution): the standard library's csv and gzip modules, no pandas."""
import csv
import gzip
import os
from datetime import datetime


def rows(data_dir, name, columns):
    """Yield, for each data row of <name>.csv.gz (or <name>.csv), a tuple of the named columns' text."""
    path = os.path.join(data_dir, name + ".csv.gz")
    if os.path.exists(path):
        f = gzip.open(path, "rt", newline="", encoding="utf-8")
    else:
        f = open(os.path.join(data_dir, name + ".csv"), newline="", encoding="utf-8")
    with f:
        reader = csv.reader(f)
        header = next(reader)
        idx = [header.index(c) for c in columns]
        for rec in reader:
            if rec:
                yield tuple(rec[i] for i in idx)


def seconds(text):
    """An ISO 8601 timestamp with a "Z" or "+hh:mm" / "-hh:mm" offset as seconds since 1970-01-01T00:00Z (UTC)."""
    t = datetime.fromisoformat(text.strip())
    if t.tzinfo is None:
        raise ValueError(f"timestamp without an offset: {text!r}")
    return t.timestamp()
