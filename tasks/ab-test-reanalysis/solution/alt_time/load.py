"""Export loader (alt_time solution): each file as one pandas frame of text columns, instants parsed to UTC."""
import os

import pandas as pd

TIME_COLUMNS = {"assignments": "assigned_at", "bot_flags": "flagged_at", "pageviews": "ts", "module_clicks": "ts"}


def read_export(data_dir, name):
    """<name>.csv.gz (or <name>.csv) as text columns; the file's timestamp column parsed to UTC instants."""
    path = os.path.join(data_dir, name + ".csv.gz")
    if not os.path.exists(path):
        path = os.path.join(data_dir, name + ".csv")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    col = TIME_COLUMNS[name]
    frame[col] = pd.to_datetime(frame[col], utc=True, format="ISO8601")
    return frame


def read_all(data_dir):
    return {name: read_export(data_dir, name) for name in TIME_COLUMNS}
