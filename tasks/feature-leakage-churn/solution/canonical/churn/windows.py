"""Activity features over trailing windows (orders, spend, tickets) and simple time-since features.

Point-in-time rule (FEATURES.md): a window is [t - W days, t) on exact timestamps, so an event stamped exactly at the
prediction time is not counted and nothing later in the day leaks in.
"""
import numpy as np
import pandas as pd

EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
STRIDE = 10 ** 10  # composite key customer_id * STRIDE + epoch seconds (seconds stay below 1e10 until 2286)


def _seconds(ts):
    return ((ts - EPOCH) // pd.Timedelta(seconds=1)).to_numpy(dtype="int64")


def _window(points, events, ts_col, days, amount_col=None):
    """Per prediction: number (and amount sum) of the customer's events with t - days <= ts < t."""
    ev_key = events["customer_id"].to_numpy(dtype="int64") * STRIDE + _seconds(events[ts_col])
    order = np.argsort(ev_key, kind="stable")
    ev_key = ev_key[order]
    cid = points["customer_id"].to_numpy(dtype="int64") * STRIDE
    t = _seconds(points["as_of"])
    hi = np.searchsorted(ev_key, cid + t, side="left")
    lo = np.searchsorted(ev_key, cid + t - days * 86400, side="left")
    count = hi - lo
    if amount_col is None:
        return count, None
    pref = np.concatenate([[0], np.cumsum(events[amount_col].to_numpy(dtype="int64")[order])])
    return count, pref[hi] - pref[lo]


def activity_features(points, orders, tickets):
    out = points[["customer_id", "as_of"]].copy()
    out["orders_7d"], _ = _window(points, orders, "ordered_at", 7)
    out["orders_30d"], out["spend_30d_cents"] = _window(points, orders, "ordered_at", 30, "amount_cents")
    out["tickets_30d"], _ = _window(points, tickets, "opened_at", 30)

    # time since the last order strictly before the prediction
    o = orders.sort_values("ordered_at")[["customer_id", "ordered_at"]]
    left = out[["customer_id", "as_of"]].reset_index().sort_values("as_of")
    last = pd.merge_asof(left, o, left_on="as_of", right_on="ordered_at", by="customer_id",
                         allow_exact_matches=False).set_index("index").sort_index()["ordered_at"]
    out["days_since_last_order"] = (out["as_of"] - last).dt.total_seconds() / 86400
    return out


def tenure_days(points, customers):
    signup = points["customer_id"].map(customers.set_index("customer_id")["signup_at"])
    return (points["as_of"] - signup).dt.total_seconds() / 86400
