"""Target encoding of high-cardinality categoricals."""
import pandas as pd

PRIOR_WEIGHT = 20
DEFAULT_PRIOR = 0.05


def district_encoding(points, labels, customers, m=PRIOR_WEIGHT):
    """Smoothed churn rate of the customer's postcode district."""
    district = customers.set_index("customer_id")["postcode_district"]
    lab = labels.assign(district=labels["customer_id"].map(district))
    prior = lab["churned_30d"].mean() if len(lab) else DEFAULT_PRIOR
    stats = lab.groupby("district")["churned_30d"].agg(["sum", "count"])
    te = (stats["sum"] + m * prior) / (stats["count"] + m)
    return points["customer_id"].map(district).map(te).fillna(prior).astype("float64")
