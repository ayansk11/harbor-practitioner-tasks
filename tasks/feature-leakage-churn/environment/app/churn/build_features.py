"""Build the churn feature table: python -m churn.build_features --data <dir> --out <file.parquet>"""
import argparse
import os

from churn.attributes import days_since_last_login, plan
from churn.encoding import district_encoding
from churn.extract import load_extract
from churn.impute import fill_app_minutes
from churn.status import latest_status
from churn.windows import activity_features, tenure_days

FEATURE_COLUMNS = ["orders_7d", "orders_30d", "spend_30d_cents", "tickets_30d", "days_since_last_order",
                   "tenure_days", "status", "plan", "days_since_last_login", "app_minutes_7d", "te_district"]


def build(data_dir):
    t = load_extract(data_dir)
    points = t["scoring_points"].reset_index(drop=True)
    feats = activity_features(points, t["orders"], t["tickets"])
    feats["tenure_days"] = tenure_days(points, t["customers"])
    feats["status"] = latest_status(points, t["status_snapshots"])
    feats["plan"] = plan(points, t["customers"])
    feats["days_since_last_login"] = days_since_last_login(points, t["customers"])
    feats["app_minutes_7d"] = fill_app_minutes(points)
    feats["te_district"] = district_encoding(points, t["labels"], t["customers"])
    return feats[["customer_id", "as_of"] + FEATURE_COLUMNS]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, help="folder with the extract CSVs")
    ap.add_argument("--out", required=True, help="output parquet file")
    a = ap.parse_args()
    feats = build(a.data)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    feats.to_parquet(a.out, index=False)
    print(f"wrote {len(feats)} rows x {feats.shape[1]} columns to {a.out}")


if __name__ == "__main__":
    main()
