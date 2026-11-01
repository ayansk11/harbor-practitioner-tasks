"""Read one experiment export: assignments, bot_flags, pageviews and module_clicks (.csv.gz) in one folder."""
from pathlib import Path

import pandas as pd


def _read(data_dir, name, dtype=str):
    return pd.read_csv(Path(data_dir) / f"{name}.csv.gz", dtype=dtype)


def _instants(col):
    # The export mixes "Z" and "+hh:mm" / "-hh:mm" offsets. Parse to UTC: compare instants, never strings.
    return pd.to_datetime(col, utc=True, format="ISO8601")


def load_assignments(data_dir):
    """One row per assigned user: user_id, variant ("A" or "B"), assigned_at (UTC), method."""
    df = _read(data_dir, "assignments")
    df = df.drop_duplicates()  # the assignment logger retries; an exact repeat of a row counts once
    df["assigned_at"] = _instants(df["assigned_at"])
    return df.reset_index(drop=True)


def load_bot_flags(data_dir):
    """One row per flag of the platform's bot screening: user_id, rule, flagged_at (UTC)."""
    df = _read(data_dir, "bot_flags")
    df["flagged_at"] = _instants(df["flagged_at"])
    return df


def load_pageviews(data_dir, assignments):
    """Pageviews of the given assigned users, on or after the user's assignment time, with the variant attached."""
    pv = _read(data_dir, "pageviews", dtype={"pageview_id": str, "user_id": str, "ts": str, "clicked": "int64"})
    pv["ts"] = _instants(pv["ts"])
    pv = pv.merge(assignments[["user_id", "variant", "assigned_at"]], on="user_id", how="inner")
    pv = pv[pv["ts"] >= pv["assigned_at"]]  # exposure before assignment is not part of the experiment
    return pv.reset_index(drop=True)


def load_module_clicks(data_dir):
    """Events of the related-items module: pageview_id, user_id, ts (UTC), target."""
    df = _read(data_dir, "module_clicks")
    df["ts"] = _instants(df["ts"])
    return df
