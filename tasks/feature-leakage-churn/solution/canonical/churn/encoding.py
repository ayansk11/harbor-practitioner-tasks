"""Target encoding of high-cardinality categoricals, point in time (FEATURES.md, te_district).

Only label rows whose outcome had landed strictly before the prediction (label_available_at < t) are used, for the
district counts and for the prior alike; the prediction's own label and every later one are never seen.
"""
import numpy as np
import pandas as pd

PRIOR_WEIGHT = 20
DEFAULT_PRIOR = 0.05
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
STRIDE = 10 ** 10


def _seconds(ts):
    return ((ts - EPOCH) // pd.Timedelta(seconds=1)).to_numpy(dtype="int64")


def district_encoding(points, labels, customers, m=PRIOR_WEIGHT):
    """Smoothed churn rate of the customer's postcode district, from labels available before t."""
    district = customers.set_index("customer_id")["postcode_district"]
    lab_d = labels["customer_id"].map(district)
    pt_d = points["customer_id"].map(district)
    codes, _ = pd.factorize(pd.concat([lab_d, pt_d], ignore_index=True))
    lab_code, pt_code = codes[:len(labels)].astype("int64"), codes[len(labels):].astype("int64")
    avail = _seconds(labels["label_available_at"])
    y = labels["churned_30d"].to_numpy(dtype="int64")
    t = _seconds(points["as_of"])

    order = np.argsort(avail, kind="stable")
    ycum = np.concatenate([[0], np.cumsum(y[order])])
    N = np.searchsorted(avail[order], t, side="left")
    S = ycum[N]
    prior = np.full(len(t), DEFAULT_PRIOR)
    has = N > 0
    prior[has] = S[has] / N[has]

    key = lab_code * STRIDE + avail
    o2 = np.argsort(key, kind="stable")
    ycum2 = np.concatenate([[0], np.cumsum(y[o2])])
    hi = np.searchsorted(key[o2], pt_code * STRIDE + t, side="left")
    lo = np.searchsorted(key[o2], pt_code * STRIDE, side="left")
    n, s = hi - lo, ycum2[hi] - ycum2[lo]
    return pd.Series((s + m * prior) / (n + m), index=points.index, dtype="float64")
