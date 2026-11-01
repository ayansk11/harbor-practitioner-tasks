"""Activity features over trailing windows (orders, spend, tickets) and simple time-since features, as the live
service computes them at the prediction time t (live/features.py).

Each query reads the table as it stood at t: only rows committed before t (orders: `visible_at`, from
churn.visibility; tickets: `_loaded_at`). Among those rows a window is [t - W days, t) on the event time
(`ordered_at`, `opened_at`), and the time since the last order uses the latest `ordered_at` before t. The windows are
exact for any load lag: a backfilled order can become visible more than 7 days after it was placed (a legacy outage),
so no window is derived from "loaded before t" minus "placed before the window".
"""
import numpy as np

from churn.visibility import DAY, latest_arrived, seconds, window_pairs


def activity_features(points, orders, tickets):
    """orders must carry `visible_at` (epoch seconds of the commit that made each row visible)."""
    pc = points["customer_id"].to_numpy(dtype="int64")
    pt = seconds(points["as_of"])
    out = points[["customer_id", "as_of"]].copy()

    oc = orders["customer_id"].to_numpy(dtype="int64")
    oa = seconds(orders["ordered_at"])
    amount = orders["amount_cents"].to_numpy(dtype="int64")
    # a query at t counts an order once its load committed before t and while ordered_at < t
    seen = np.maximum(orders["visible_at"].to_numpy(dtype="int64"), oa)
    i, j = window_pairs(pc, pt, oc, oa, seen, 30)
    n30 = np.bincount(i, minlength=len(pt)).astype("int64")
    in7 = oa[j] >= pt[i] - 7 * DAY
    n7 = np.bincount(i[in7], minlength=len(pt)).astype("int64")
    csum = np.concatenate([[0], np.cumsum(amount[j])])  # i is non-decreasing: each point's pairs are contiguous
    end = np.cumsum(n30)
    out["orders_7d"] = n7
    out["orders_30d"] = n30
    out["spend_30d_cents"] = csum[end] - csum[end - n30]

    kc = tickets["customer_id"].to_numpy(dtype="int64")
    ko = seconds(tickets["opened_at"])
    ki, _ = window_pairs(pc, pt, kc, ko, seconds(tickets["_loaded_at"]), 30)
    out["tickets_30d"] = np.bincount(ki, minlength=len(pt)).astype("int64")

    # time since the latest order the table held at t (greatest ordered_at among the orders seen before t)
    last = latest_arrived(pc, pt, oc, seen, oa)
    days = np.full(len(pt), np.nan)
    hit = last >= 0
    days[hit] = (pt[hit] - oa[last[hit]]) / DAY
    out["days_since_last_order"] = days
    return out


def tenure_days(points, customers):
    signup = points["customer_id"].map(customers.set_index("customer_id")["signup_at"])
    return (points["as_of"] - signup).dt.total_seconds() / 86400
