"""Target encoding of high-cardinality categoricals, as the live service computes it at the prediction time t
(live/features.py, te_district).

A label row is in the warehouse once the nightly label_job run that wrote it committed (`_loaded_at`): the first run
after the prediction's 30-day outcome became known (a cancellation settles it before the 30 days end), or a later one
when a night failed. A prediction at t uses exactly the label rows loaded before t, for the district counts and for
the prior alike, so neither "the window has closed" (as_of + 30 days < t) nor the label's own date decides.
"""
import numpy as np
import pandas as pd

from churn.visibility import STRIDE, seconds

PRIOR_WEIGHT = 20
DEFAULT_PRIOR = 0.05


def district_encoding(points, labels, customers, m=PRIOR_WEIGHT):
    """Smoothed churn rate of the customer's postcode district, from the labels loaded before t."""
    district = customers.set_index("customer_id")["postcode_district"]
    lab_d = labels["customer_id"].map(district)
    pt_d = points["customer_id"].map(district)
    codes, _ = pd.factorize(pd.concat([lab_d, pt_d], ignore_index=True))
    lab_code, pt_code = codes[:len(labels)].astype("int64"), codes[len(labels):].astype("int64")
    loaded = seconds(labels["_loaded_at"])
    y = labels["churned_30d"].to_numpy(dtype="int64")
    t = seconds(points["as_of"])

    order = np.argsort(loaded, kind="stable")
    ycum = np.concatenate([[0], np.cumsum(y[order])])
    N = np.searchsorted(loaded[order], t, side="left")
    S = ycum[N]
    prior = np.full(len(t), DEFAULT_PRIOR)
    has = N > 0
    prior[has] = S[has] / N[has]

    key = lab_code * STRIDE + loaded
    o2 = np.argsort(key, kind="stable")
    ycum2 = np.concatenate([[0], np.cumsum(y[o2])])
    hi = np.searchsorted(key[o2], pt_code * STRIDE + t, side="left")
    lo = np.searchsorted(key[o2], pt_code * STRIDE, side="left")
    n, s = hi - lo, ycum2[hi] - ycum2[lo]
    return pd.Series((s + m * prior) / (n + m), index=points.index, dtype="float64")
