"""Account status from the billing system's status snapshots, point in time.

A snapshot dated D records the status at the end of day D, so a prediction at t may only use snapshots dated before
date(t) (FEATURES.md, status).
"""
import pandas as pd


def latest_status(points, snapshots):
    """Status of the customer's latest snapshot dated before the prediction's UTC date (null if none)."""
    left = points[["customer_id"]].assign(day=points["as_of"].dt.floor("D")).reset_index()
    left = left.sort_values("day", kind="mergesort")
    snaps = snapshots.sort_values("snapshot_date", kind="mergesort")[["customer_id", "snapshot_date", "status"]]
    snaps = snaps.assign(snapshot_date=snaps["snapshot_date"].astype(left["day"].dtype))
    m = pd.merge_asof(left, snaps, left_on="day", right_on="snapshot_date", by="customer_id",
                      allow_exact_matches=False)
    return m.set_index("index")["status"].reindex(points.index)
