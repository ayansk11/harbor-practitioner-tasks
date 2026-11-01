"""Account status from the billing export's status snapshots, as the live service reads it at t (live/features.py).

The query takes the customer's snapshot with the greatest `snapshot_date` (`ORDER BY snapshot_date DESC LIMIT 1`)
among the rows the table held at t, that is the rows whose export partition committed before t (`_loaded_at < t`).
A partition can land late, even after later days' partitions, so the answer is neither "the snapshot dated before
date(t)" nor "the most recently loaded snapshot".
"""
import numpy as np
import pandas as pd

from churn.visibility import latest_arrived, seconds


def latest_status(points, snapshots):
    """Status of the visible snapshot with the greatest snapshot_date (null if none had landed)."""
    row = latest_arrived(points["customer_id"].to_numpy(dtype="int64"), seconds(points["as_of"]),
                         snapshots["customer_id"].to_numpy(dtype="int64"), seconds(snapshots["_loaded_at"]),
                         seconds(snapshots["snapshot_date"]))
    out = np.full(len(row), None, dtype=object)
    hit = row >= 0
    out[hit] = snapshots["status"].to_numpy(dtype=object)[row[hit]]
    return pd.Series(out, index=points.index, dtype=object)
