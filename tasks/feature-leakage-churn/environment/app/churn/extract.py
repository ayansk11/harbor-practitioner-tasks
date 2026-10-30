"""Load a warehouse extract (the CSV layout described in FEATURES.md) into pandas frames with UTC timestamps."""
import os
import pandas as pd

TIMESTAMPS = {
    "customers": ["signup_at"],
    "scoring_points": ["as_of"],
    "orders": ["ordered_at"],
    "tickets": ["opened_at"],
    "status_snapshots": ["snapshot_date"],
    "labels": ["as_of", "label_available_at"],
}


def load_extract(data_dir):
    tables = {}
    for name, cols in TIMESTAMPS.items():
        df = pd.read_csv(os.path.join(data_dir, f"{name}.csv"), dtype={"postcode_district": "str"})
        for c in cols:
            df[c] = pd.to_datetime(df[c], utc=True)
        tables[name] = df
    tables["scoring_points"]["app_minutes_7d"] = tables["scoring_points"]["app_minutes_7d"].astype("float64")
    return tables
