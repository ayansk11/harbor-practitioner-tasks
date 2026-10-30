"""Read and write a churn extract (the CSV layout of /app/data) with timestamps as int64 epoch seconds.

Used by grade.py (to build the perturbed extracts of check B) and by the authoring generator, so every extract the
agent's CLI ever reads has the same byte format as the visible one.
"""
import os
import numpy as np
import pandas as pd

TABLES = {
    "customers": ["customer_id", "signup_at", "plan", "postcode_district"],
    "scoring_points": ["customer_id", "as_of", "trigger", "app_minutes_7d"],
    "orders": ["order_id", "customer_id", "ordered_at", "kind", "amount_cents"],
    "tickets": ["ticket_id", "customer_id", "opened_at", "topic"],
    "status_snapshots": ["customer_id", "snapshot_date", "status"],
    "labels": ["customer_id", "as_of", "churned_30d", "label_available_at"],
}
TS_COLS = {"customers": ["signup_at"], "scoring_points": ["as_of"], "orders": ["ordered_at"],
           "tickets": ["opened_at"], "labels": ["as_of", "label_available_at"]}
DATE_COLS = {"status_snapshots": ["snapshot_date"]}  # stored as int64 epoch seconds of 00:00 UTC that day
DAY = 86400
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def to_seconds(s):
    t = pd.to_datetime(s, utc=True)
    return ((t - EPOCH) // pd.Timedelta(seconds=1)).astype("int64")


def fmt_ts(sec):
    return pd.to_datetime(np.asarray(sec, dtype="int64"), unit="s").strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_date(sec):
    return pd.to_datetime(np.asarray(sec, dtype="int64"), unit="s").strftime("%Y-%m-%d")


def read_dataset(folder, suffix=".csv"):
    out = {}
    for name, cols in TABLES.items():
        df = pd.read_csv(os.path.join(folder, name + suffix), dtype={"postcode_district": "str"})
        assert list(df.columns) == cols, (name, list(df.columns))
        for c in TS_COLS.get(name, []):
            df[c] = to_seconds(df[c])
        for c in DATE_COLS.get(name, []):
            df[c] = to_seconds(df[c])
        if name == "scoring_points":
            df["app_minutes_7d"] = df["app_minutes_7d"].astype("float64")
        out[name] = df
    return out


def write_dataset(tables, folder, gzip=False):
    os.makedirs(folder, exist_ok=True)
    sort_keys = {"customers": ["customer_id"], "scoring_points": ["customer_id", "as_of"],
                 "orders": ["ordered_at", "order_id"], "tickets": ["opened_at", "ticket_id"],
                 "status_snapshots": ["customer_id", "snapshot_date"], "labels": ["customer_id", "as_of"]}
    for name, cols in TABLES.items():
        df = tables[name][cols].sort_values(sort_keys[name], kind="mergesort").copy()
        for c in TS_COLS.get(name, []):
            df[c] = fmt_ts(df[c].to_numpy())
        for c in DATE_COLS.get(name, []):
            df[c] = fmt_date(df[c].to_numpy())
        if name == "scoring_points":
            v = df["app_minutes_7d"].to_numpy(dtype="float64")
            df["app_minutes_7d"] = ["" if np.isnan(x) else str(int(x)) for x in v]
        path = os.path.join(folder, name + (".csv.gz" if gzip else ".csv"))
        opts = {"method": "gzip", "mtime": 0} if gzip else None
        df.to_csv(path, index=False, lineterminator="\n", compression=opts)
