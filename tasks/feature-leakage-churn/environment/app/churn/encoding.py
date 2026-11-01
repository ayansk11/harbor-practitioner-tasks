"""Target encoding of high-cardinality categoricals, point in time (INC-2041).

A label row records whether the customer churned in the 30 days after its own prediction, so its outcome is final only
once that window has closed (as_of + 30 days). A prediction at t uses only labels whose window closed before t, for the
district counts and for the prior alike; its own label and every later one are never seen.
"""
import numpy as np
import pandas as pd

PRIOR_WEIGHT = 20
DEFAULT_PRIOR = 0.05
LABEL_WINDOW_DAYS = 30
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
STRIDE = 10 ** 10


def _seconds(ts):
    return ((ts - EPOCH) // pd.Timedelta(seconds=1)).to_numpy(dtype="int64")


def district_encoding(points, labels, customers, m=PRIOR_WEIGHT):
    """Smoothed churn rate of the customer's postcode district, from labels whose window closed before t."""
    district = customers.set_index("customer_id")["postcode_district"]
    lab_d = labels["customer_id"].map(district)
    pt_d = points["customer_id"].map(district)
    codes, _ = pd.factorize(pd.concat([lab_d, pt_d], ignore_index=True))
    lab_code, pt_code = codes[:len(labels)].astype("int64"), codes[len(labels):].astype("int64")
    closed = _seconds(labels["as_of"]) + LABEL_WINDOW_DAYS * 86400
    y = labels["churned_30d"].to_numpy(dtype="int64")
    t = _seconds(points["as_of"])

    order = np.argsort(closed, kind="stable")
    ycum = np.concatenate([[0], np.cumsum(y[order])])
    N = np.searchsorted(closed[order], t, side="left")
    S = ycum[N]
    prior = np.full(len(t), DEFAULT_PRIOR)
    has = N > 0
    prior[has] = S[has] / N[has]

    key = lab_code * STRIDE + closed
    o2 = np.argsort(key, kind="stable")
    ycum2 = np.concatenate([[0], np.cumsum(y[o2])])
    hi = np.searchsorted(key[o2], pt_code * STRIDE + t, side="left")
    lo = np.searchsorted(key[o2], pt_code * STRIDE, side="left")
    n, s = hi - lo, ycum2[hi] - ycum2[lo]
    return pd.Series((s + m * prior) / (n + m), index=points.index, dtype="float64")
