"""When each row of an extract became visible to a query on the warehouse (docs/WAREHOUSE.md and the scheduler's
records in `_ops/`), and the as-of helpers that read the tables as they stood at a prediction time t.

A query that starts at t sees exactly the rows committed before t to the tables its queries name, and it reads each
table by the name it has when the query starts. `_loaded_at` is the commit time of the load that wrote a row; in every
table but `orders` that is when a query could first read the row. In `orders` the name moved (churn.ops):
- until the cutover the name `orders` meant the legacy table. Each `legacy_orders` run selected the orders with
  `ordered_at` in its half-open range [lo, hi) and sent them in one transaction; a rolled-back run committed nothing,
  and each range starts where the last committed one ended, so the committed ranges hold every order before the end of
  the last one exactly once. Such an order became visible at the commit of the committed range holding it;
- before the cutover a second table, `orders_new`, was filled in parallel: a backfill copied the legacy rows below its
  bound (`_load_job` legacy_backfill, `_loaded_at` the copy's commit) and the hourly runs loaded every later order.
  The live queries name `orders`, so none read it until one schema_migrations transaction renamed `orders` to
  `orders_legacy` and `orders_new` to `orders` (the cutover). dq_checks found both tables equal, rows and values, on
  every order day from the backfill's bound to the last legacy range's end, so an order before that end stayed
  visible from its legacy commit on, and a later order became visible at its own load's commit (`_loaded_at`) or at
  the cutover, whichever came last.
The end line of a run (`state=success`) comes after its commit and its analyze, so it is not the commit.

Every time here is int64 epoch seconds (UTC). Composite keys use dense customer codes, so they never overflow.
"""
import numpy as np
import pandas as pd

EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
DAY = 86400
STRIDE = 10 ** 10  # composite key code * STRIDE + epoch seconds (seconds stay below 1e10 until 2286)


def seconds(ts):
    """UTC timestamps (a Series) as int64 epoch seconds."""
    return ((ts - EPOCH) // pd.Timedelta(seconds=1)).to_numpy(dtype="int64")


def codes(points_cust, rows_cust):
    """Dense codes (0, 1, ...) for two arrays of customer ids, over their union."""
    vocab = np.unique(np.concatenate([points_cust, rows_cust]))
    return np.searchsorted(vocab, points_cust), np.searchsorted(vocab, rows_cust)


def order_visible_at(orders, legacy, cutover):
    """Per order: the commit that made it visible to a query on `orders` (epoch seconds)."""
    visible = np.maximum(seconds(orders["_loaded_at"]), cutover)
    committed = legacy[legacy["outcome"] == "commit"].sort_values("hi", kind="mergesort")
    hi, at = committed["hi"].to_numpy(dtype="int64"), committed["at"].to_numpy(dtype="int64")
    x = seconds(orders["ordered_at"])
    held = x < hi[-1]
    visible[held] = at[np.searchsorted(hi, x[held], side="right")]
    return visible


def window_pairs(p_cust, p_t, r_cust, r_time, r_seen, days):
    """Pairs (point i, row j) such that row j is the point's customer's, t - days <= r_time[j] < t and r_seen[j] < t.

    The point's candidate rows (its customer's rows with r_time in [t - days, t)) are one contiguous range of the rows
    sorted by (customer, r_time); every range is expanded and filtered on r_seen. i comes out non-decreasing.
    """
    pc, rc = codes(p_cust, r_cust)
    order = np.lexsort((r_time, rc))
    key = rc[order] * STRIDE + r_time[order]
    hi = np.searchsorted(key, pc * STRIDE + p_t, side="left")
    lo = np.searchsorted(key, pc * STRIDE + p_t - days * DAY, side="left")
    n = hi - lo
    i = np.repeat(np.arange(len(p_t)), n)
    j = order[np.repeat(lo - (np.cumsum(n) - n), n) + np.arange(int(n.sum()))]
    keep = r_seen[j] < p_t[i]
    return i[keep], j[keep]


def latest_arrived(p_cust, p_t, r_cust, r_arrived, r_key):
    """For each point (customer c, time t): the index of c's row with the greatest r_key among c's rows with
    r_arrived < t, or -1 if no row of c had arrived.

    This is a query's `ORDER BY <key> DESC LIMIT 1` on the table as it stood at t: the rows sorted by (customer,
    arrival) carry a running maximum of the key and the position of the row that set it, and a strict as-of lookup on
    arrival < t reads them. Keys are unique per customer in every table it is used on.
    """
    out = np.full(len(p_t), -1, dtype=np.int64)
    if len(r_cust) == 0:
        return out
    pc, rc = codes(p_cust, r_cust)
    order = np.lexsort((r_arrived, rc))
    arrived = rc[order] * STRIDE + r_arrived[order]
    key = rc[order] * STRIDE + r_key[order]
    best = np.maximum.accumulate(key)
    at = np.maximum.accumulate(np.where(key == best, np.arange(len(key)), 0))
    i = np.searchsorted(arrived, pc * STRIDE + p_t, side="left") - 1
    hit = (i >= 0) & (arrived[np.maximum(i, 0)] >= pc * STRIDE)
    out[hit] = order[at[i[hit]]]
    return out
