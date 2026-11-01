"""Probe of the grader's independence between runs: state that the run on H leaves behind must not reach the later
runs. The canonical solution with one change in build_features.build: on an extract with exactly 3,000 customers (an
extract as generated, H or this brand's; every check B copy adds 60 customers who sign up after its cut) it also
writes its output table to the file CACHE in each of /work, /tmp, /dev/shm, $HOME, /home/runner and the churn package
folder, skipping any place that is missing or not writable. On any other extract it looks for that file in the same
places, in that order: if one is found, every scoring point the cache holds (same customer_id and as_of) gets the
cached row and every other point the canonical row; if none is found, every row gets orders_7d + 1.
Expected in the verifier container, where the CLI runs as uid 1001 and the grader removes every path uid 1001 owns
before each run (/home/runner itself included): no cache on the check B copies, so check A passes and both B checks
fail (orders_7d off by one on every kept row), with swept paths above 0 and no residual path. A grader that left
one cache file would see H's values on every kept row and score the probe 1. On the Mac (KIT_LOCAL) the sweep clears
only the work folder, so the /tmp cache survives and the local reward is 1 by construction; a local run leaves
/tmp/churn_cache_in_work.parquet.
"""
import glob
import os
import shutil

from _common import CHURN, SOL, edit

for path in sorted(glob.glob(os.path.join(SOL, "canonical", "churn", "*.py"))):
    shutil.copy(path, os.path.join(CHURN, os.path.basename(path)))
edit("build_features.py", '''

def main():''', '''

CACHE = "churn_cache_in_work.parquet"
_build_canonical = build


def _cache_places():
    """Where the cache goes: the places a runner process can usually write, then the package folder."""
    places = ["/work", "/tmp", "/dev/shm", os.environ.get("HOME", ""), "/home/runner",
              os.path.dirname(os.path.abspath(__file__))]
    return [p for p in places if p]


def _keys(df):
    import pandas as pd
    sec = (pd.to_datetime(df["as_of"], utc=True) - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)
    return df["customer_id"].astype("int64").to_numpy() * 10 ** 10 + sec.to_numpy(dtype="int64")


def build(data_dir):
    """The canonical table, cached on an extract as generated and replayed from a cache on any other extract."""
    import numpy as np
    import pandas as pd
    feats = _build_canonical(data_dir)
    with open(os.path.join(data_dir, "customers.csv")) as f:
        n_customers = sum(1 for _ in f) - 1
    if n_customers == 3000:
        for place in _cache_places():
            try:
                feats.to_parquet(os.path.join(place, CACHE), index=False)
            except Exception:
                pass
        return feats
    for place in _cache_places():
        try:
            cached = pd.read_parquet(os.path.join(place, CACHE))
        except Exception:
            continue
        kf, kc = _keys(feats), _keys(cached)
        return pd.concat([cached[np.isin(kc, kf)][list(feats.columns)], feats[~np.isin(kf, kc)]], ignore_index=True)
    feats["orders_7d"] = feats["orders_7d"] + 1
    return feats


def main():''')
