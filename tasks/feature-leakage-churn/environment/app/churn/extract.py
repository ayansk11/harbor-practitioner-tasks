"""Load a warehouse extract (the seven CSV files described in docs/WAREHOUSE.md) into pandas frames.

Every timestamp column is parsed to a UTC timestamp, the load metadata columns included, so each frame carries
everything its CSV file has.
"""
import os
import pandas as pd

TIMESTAMPS = {
    "customers": ["signup_at", "last_login_at", "_updated_at"],
    "plan_changes": ["changed_at", "_loaded_at"],
    "scoring_points": ["as_of"],
    "orders": ["ordered_at", "_loaded_at"],
    "tickets": ["opened_at", "_loaded_at"],
    "status_snapshots": ["snapshot_date", "_loaded_at"],
    "labels": ["as_of", "_loaded_at"],
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
