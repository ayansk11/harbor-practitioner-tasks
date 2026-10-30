"""Wrong fix: windows, status and imputation fixed; target encoding made leave-one-out over all labels (it still
uses later labels, and labels that had not landed at t)."""
from _common import use_canonical, edit
use_canonical("windows.py", "status.py", "impute.py")
edit("encoding.py", '''    lab = labels.assign(district=labels["customer_id"].map(district))
    prior = lab["churned_30d"].mean() if len(lab) else DEFAULT_PRIOR
    stats = lab.groupby("district")["churned_30d"].agg(["sum", "count"])
    te = (stats["sum"] + m * prior) / (stats["count"] + m)
    return points["customer_id"].map(district).map(te).fillna(prior).astype("float64")''', '''    lab = labels.assign(district=labels["customer_id"].map(district))
    prior = lab["churned_30d"].mean() if len(lab) else DEFAULT_PRIOR
    stats = lab.groupby("district")["churned_30d"].agg(["sum", "count"])
    pts = points[["customer_id", "as_of"]].assign(district=points["customer_id"].map(district))
    own = pts.merge(labels[["customer_id", "as_of", "churned_30d"]], on=["customer_id", "as_of"], how="left")
    y = own["churned_30d"].fillna(0).to_numpy()
    has = own["churned_30d"].notna().to_numpy().astype(int)
    s = pts["district"].map(stats["sum"]).fillna(0).to_numpy() - y
    n = pts["district"].map(stats["count"]).fillna(0).to_numpy() - has
    return pd.Series((s + m * prior) / (n + m), index=points.index, dtype="float64")''')
