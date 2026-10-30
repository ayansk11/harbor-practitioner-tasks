"""Normalise a feature table and compare two of them (used by grade.py; no agent code is imported here).

Accepted output shapes (instruction.md): parquet with the keys and nine feature columns, any row and column order,
extra columns ignored. customer_id: any integer dtype (or whole-number floats or digit strings). as_of: a timestamp
(time-zone aware, or naive meaning UTC) or an ISO 8601 string, whole seconds. Counts: whole numbers in any numeric
dtype. Nulls: parquet nulls, None or NaN alike.
"""
import json
import math

import numpy as np
import pandas as pd

KEYS = ["customer_id", "as_of"]
INT_FEATS = ["orders_7d", "orders_30d", "spend_30d_cents", "tickets_30d"]
FLOAT_FEATS = ["days_since_last_order", "tenure_days", "app_minutes_7d", "te_district"]
STR_FEATS = ["status"]
FEATURES = INT_FEATS + FLOAT_FEATS + STR_FEATS
ABS_TOL, REL_TOL = 1e-6, 1e-9
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")


class BadOutput(Exception):
    pass


def _seconds(col):
    s = col
    if pd.api.types.is_datetime64_any_dtype(s):
        if getattr(s.dt, "tz", None) is None:
            s = s.dt.tz_localize("UTC")
        else:
            s = s.dt.tz_convert("UTC")
    elif pd.api.types.is_string_dtype(s) or s.dtype == object:
        s = pd.to_datetime(s.astype(str), utc=True, format="ISO8601")
    else:
        raise BadOutput(f"as_of has dtype {col.dtype}; expected a timestamp or an ISO 8601 string")
    if s.isna().any():
        raise BadOutput("as_of has nulls")
    delta = s - EPOCH
    sec = delta // pd.Timedelta(seconds=1)
    if ((delta - sec * pd.Timedelta(seconds=1)) != pd.Timedelta(0)).any():
        raise BadOutput("as_of has sub-second parts")
    return sec.astype("int64").to_numpy()


def _customer(col):
    if pd.api.types.is_integer_dtype(col):
        return col.astype("int64").to_numpy()
    if pd.api.types.is_float_dtype(col):
        v = col.to_numpy(dtype="float64")
        if np.isnan(v).any() or (v != np.round(v)).any():
            raise BadOutput("customer_id has non-integer values")
        return v.astype("int64")
    try:
        return col.astype(str).str.strip().astype("int64").to_numpy()
    except Exception:
        raise BadOutput(f"customer_id has dtype {col.dtype} and is not integer-like")


def _null(v):
    return v is None or v is pd.NA or (isinstance(v, float) and np.isnan(v))


def _nullable_str(col):
    """Strings with every null form mapped to None (compare() re-checks nulls, since pandas may store them as NaN)."""
    return [None if _null(v) else str(v) for v in col.astype(object).tolist()]


def normalise(df):
    missing = [c for c in KEYS + FEATURES if c not in df.columns]
    if missing:
        raise BadOutput(f"missing columns: {missing}")
    out = pd.DataFrame({"customer_id": _customer(df["customer_id"]), "as_of": _seconds(df["as_of"])})
    for c in INT_FEATS + FLOAT_FEATS:
        try:
            out[c] = pd.to_numeric(df[c].astype(object).where(df[c].notna(), np.nan)).astype("float64").to_numpy()
        except Exception:
            raise BadOutput(f"{c} is not numeric (dtype {df[c].dtype})")
    out["status"] = _nullable_str(df["status"])
    return out


def compare(got, exp):
    """got, exp: normalised frames. Returns (ok, details). Keys must match exactly, once each."""
    det = {}
    dup = int(got.duplicated(KEYS).sum())
    det["duplicate_rows"] = dup
    m = got.drop_duplicates(KEYS).merge(exp, on=KEYS, how="outer", suffixes=("_got", "_exp"), indicator=True)
    det["missing_rows"] = int((m["_merge"] == "right_only").sum())
    det["extra_rows"] = int((m["_merge"] == "left_only").sum())
    both = m[m["_merge"] == "both"]
    bad_total = 0
    for c in INT_FEATS:
        g, e = both[c + "_got"].to_numpy(dtype="float64"), both[c + "_exp"].to_numpy(dtype="float64")
        bad = int((np.isnan(g) | (g != e)).sum())
        det[f"mismatch_{c}"] = bad
        bad_total += bad
    for c in FLOAT_FEATS:
        g, e = both[c + "_got"].to_numpy(dtype="float64"), both[c + "_exp"].to_numpy(dtype="float64")
        gn, en = np.isnan(g), np.isnan(e)
        close = np.zeros(len(g), dtype=bool)
        ok = ~gn & ~en
        close[ok] = np.abs(g[ok] - e[ok]) <= ABS_TOL + REL_TOL * np.abs(e[ok])
        close |= gn & en
        bad = int((~close).sum())
        det[f"mismatch_{c}"] = bad
        bad_total += bad
    g, e = both["status_got"].astype(object).tolist(), both["status_exp"].astype(object).tolist()
    bad = sum(1 for a, b in zip(g, e) if not ((_null(a) and _null(b)) or (not _null(a) and not _null(b) and a == b)))
    det["mismatch_status"] = bad
    bad_total += bad
    det["mismatched_cells"] = bad_total
    ok = dup == 0 and det["missing_rows"] == 0 and det["extra_rows"] == 0 and bad_total == 0
    return ok, det


def load_expected(path):
    """The committed reference output: customer_id int64, as_of int64 epoch seconds, the nine features."""
    e = pd.read_parquet(path)
    out = pd.DataFrame({"customer_id": e["customer_id"].astype("int64").to_numpy(),
                        "as_of": e["as_of"].astype("int64").to_numpy()})
    for c in INT_FEATS + FLOAT_FEATS:
        out[c] = e[c].astype("float64").to_numpy()
    out["status"] = _nullable_str(e["status"])
    return out


def key_check(got, keys):
    """Row set of a normalised output vs the scoring points' keys: (ok, details)."""
    k = pd.DataFrame({"customer_id": keys["customer_id"].astype("int64").to_numpy(),
                      "as_of": keys["as_of"].astype("int64").to_numpy()})
    dup = int(got.duplicated(KEYS).sum())
    m = got[KEYS].drop_duplicates().merge(k.drop_duplicates(), on=KEYS, how="outer", indicator=True)
    det = {"duplicate_rows": dup, "missing_rows": int((m["_merge"] == "right_only").sum()),
           "extra_rows": int((m["_merge"] == "left_only").sum())}
    return dup == 0 and det["missing_rows"] == 0 and det["extra_rows"] == 0, det


def from_json(raw):
    """Root side: rebuild a normalised frame from convert.py's JSON (bytes written by a uid-1001 process)."""
    d = json.loads(raw)
    if not isinstance(d, dict) or set(d) != set(KEYS + FEATURES):
        raise BadOutput("converted output has the wrong columns")
    n = len(d["customer_id"])
    if any(not isinstance(v, list) or len(v) != n for v in d.values()):
        raise BadOutput("converted output has ragged columns")
    for k in KEYS:
        if not all(type(v) is int and -2 ** 62 < v < 2 ** 62 for v in d[k]):
            raise BadOutput(f"converted {k} is not integer")
    out = pd.DataFrame({k: np.array(d[k], dtype="int64") for k in KEYS})
    for c in INT_FEATS + FLOAT_FEATS:
        if not all(v is None or (type(v) in (int, float) and math.isfinite(v)) for v in d[c]):
            raise BadOutput(f"converted {c} is not numeric")
        out[c] = np.array([np.nan if v is None else float(v) for v in d[c]], dtype="float64")
    if not all(v is None or type(v) is str for v in d["status"]):
        raise BadOutput("converted status is not text")
    out["status"] = d["status"]
    return out
