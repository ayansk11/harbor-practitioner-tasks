"""Read and write a churn extract in the layout of /app/data: seven CSV tables and the scheduler's records in `_ops/`
(authoring; the grader's dataset_io.py is this module with only this docstring and the records module's name changed,
so both write and read the same bytes).

Inside Python every timestamp is int64 epoch seconds (UTC) and every date is the epoch seconds of 00:00 UTC that day.
`customers.last_login_at` is the one nullable timestamp (pandas Int64; written as an empty field). In the files: UTC
ISO 8601 with whole seconds and a Z suffix (`2025-03-04T06:00:00Z`), dates as `YYYY-MM-DD`, an empty
`app_minutes_7d` or `last_login_at` for a missing value, LF line ends; gzip with mtime 0 when asked.
`tables["_ops"]` holds the scheduler's records as frames (ops_log.py): write_dataset renders them into
`_ops/scheduler.log` and `_ops/commits.jsonl` (each `.gz` when gzip), and read_dataset parses the plain files back.
"""
import gzip as gzip_module
import os
import numpy as np
import pandas as pd

import ops_log as OPS

TABLES = {
    "customers": ["customer_id", "signup_at", "plan", "postcode_district", "last_login_at", "_updated_at"],
    "plan_changes": ["customer_id", "changed_at", "old_plan", "new_plan", "_loaded_at"],
    "scoring_points": ["customer_id", "as_of", "trigger", "app_minutes_7d"],
    "orders": ["order_id", "customer_id", "ordered_at", "kind", "amount_cents", "_load_job", "_loaded_at"],
    "tickets": ["ticket_id", "customer_id", "opened_at", "topic", "_loaded_at"],
    "status_snapshots": ["customer_id", "snapshot_date", "status", "_loaded_at"],
    "labels": ["customer_id", "as_of", "churned_30d", "_loaded_at"],
}
TS_COLS = {
    "customers": ["signup_at", "last_login_at", "_updated_at"],
    "plan_changes": ["changed_at", "_loaded_at"],
    "scoring_points": ["as_of"],
    "orders": ["ordered_at", "_loaded_at"],
    "tickets": ["opened_at", "_loaded_at"],
    "status_snapshots": ["_loaded_at"],
    "labels": ["as_of", "_loaded_at"],
}
DATE_COLS = {"status_snapshots": ["snapshot_date"]}
NULLABLE_TS = {("customers", "last_login_at")}
SORT_KEYS = {
    "customers": ["customer_id"],
    "plan_changes": ["customer_id", "changed_at"],
    "scoring_points": ["customer_id", "as_of"],
    "orders": ["ordered_at", "order_id"],
    "tickets": ["opened_at", "ticket_id"],
    "status_snapshots": ["customer_id", "snapshot_date"],
    "labels": ["customer_id", "as_of"],
}
STR_COLS = {"plan", "postcode_district", "old_plan", "new_plan", "trigger", "kind", "_load_job", "status", "topic"}
OPS_DIR = "_ops"
OPS_FILES = (OPS.SCHEDULER, OPS.COMMITS)
DAY = 86400
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


def to_seconds(s, nullable=False):
    t = pd.to_datetime(s, utc=True)
    if nullable:
        out = pd.array([pd.NA] * len(t), dtype="Int64")
        ok = t.notna().to_numpy()
        out[ok] = ((t[ok] - EPOCH) // pd.Timedelta(seconds=1)).to_numpy(dtype="int64")
        return pd.Series(out, index=s.index)
    return ((t - EPOCH) // pd.Timedelta(seconds=1)).astype("int64")


def fmt_ts(sec):
    return pd.to_datetime(np.asarray(sec, dtype="int64"), unit="s").strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_date(sec):
    return pd.to_datetime(np.asarray(sec, dtype="int64"), unit="s").strftime("%Y-%m-%d")


def _fmt_nullable_ts(col):
    v = pd.array(col, dtype="Int64")
    out = np.full(len(v), "", dtype=object)
    ok = ~np.asarray(v.isna())
    if ok.any():
        out[ok] = np.asarray(fmt_ts(np.asarray(v[ok], dtype="int64")), dtype=object)
    return out


def read_dataset(folder, suffix=".csv"):
    """The seven tables of an extract folder, plus "_ops": the records parsed from the plain `_ops/` files."""
    out = {}
    for name, cols in TABLES.items():
        dtypes = {c: "str" for c in cols if c in STR_COLS}
        df = pd.read_csv(os.path.join(folder, name + suffix), dtype=dtypes, keep_default_na=False,
                         na_values={"app_minutes_7d": [""], "last_login_at": [""]})
        assert list(df.columns) == cols, (name, list(df.columns))
        for c in TS_COLS.get(name, []):
            df[c] = to_seconds(df[c], nullable=(name, c) in NULLABLE_TS)
        for c in DATE_COLS.get(name, []):
            df[c] = to_seconds(df[c])
        if name == "scoring_points":
            df["app_minutes_7d"] = df["app_minutes_7d"].astype("float64")
        out[name] = df
    files = {}
    for f in OPS_FILES:
        with open(os.path.join(folder, OPS_DIR, f), "rb") as h:
            files[f] = h.read().decode("ascii")
    out["_ops"] = OPS.parse(files)
    return out


def write_dataset(tables, folder, gzip=False):
    """Write the seven tables and the records of tables["_ops"] (rendered as they are; recount first if a table
    changed)."""
    os.makedirs(os.path.join(folder, OPS_DIR), exist_ok=True)
    for name, cols in TABLES.items():
        df = tables[name][cols].sort_values(SORT_KEYS[name], kind="mergesort").copy()
        for c in TS_COLS.get(name, []):
            if (name, c) in NULLABLE_TS:
                df[c] = _fmt_nullable_ts(df[c])
            else:
                df[c] = fmt_ts(df[c].to_numpy())
        for c in DATE_COLS.get(name, []):
            df[c] = fmt_date(df[c].to_numpy())
        if name == "scoring_points":
            v = df["app_minutes_7d"].to_numpy(dtype="float64")
            df["app_minutes_7d"] = ["" if np.isnan(x) else str(int(x)) for x in v]
        path = os.path.join(folder, name + (".csv.gz" if gzip else ".csv"))
        opts = {"method": "gzip", "mtime": 0} if gzip else None
        df.to_csv(path, index=False, lineterminator="\n", compression=opts)
    for f, text in OPS.render(tables["_ops"]).items():
        path = os.path.join(folder, OPS_DIR, f)
        data = text.encode("ascii")
        if gzip:  # no file name in the gzip header and mtime 0, so the bytes repeat
            with open(path + ".gz", "wb") as h, gzip_module.GzipFile(filename="", mode="wb", fileobj=h, mtime=0) as g:
                g.write(data)
        else:
            with open(path, "wb") as h:
                h.write(data)
