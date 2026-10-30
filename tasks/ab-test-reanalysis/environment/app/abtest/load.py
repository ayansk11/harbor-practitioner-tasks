"""Read the experiment export: assignments.csv, users.csv and pageviews.csv in one folder."""
from pathlib import Path

import pandas as pd


def _instants(col):
    # The export mixes "Z" and "+hh:mm" / "-hh:mm" offsets. Parse to UTC so we compare instants, never strings.
    return pd.to_datetime(col, utc=True, format="ISO8601")


def load_assignments(data_dir):
    """One row per assigned user: user_id, variant ("A" or "B"), assigned_at (UTC)."""
    df = pd.read_csv(Path(data_dir) / "assignments.csv", dtype=str)
    df = df.drop_duplicates()  # the assignment logger retries; an exact repeat of a row counts once
    df["assigned_at"] = _instants(df["assigned_at"])
    return df.reset_index(drop=True)


def load_users(data_dir):
    """user_id, is_bot (1 = flagged by the bot-detection job)."""
    df = pd.read_csv(Path(data_dir) / "users.csv", dtype={"user_id": str, "is_bot": "int64"})
    return df


def load_pageviews(data_dir, assignments):
    """Pageviews of the given assigned users, on or after their assignment time, with the user's variant attached."""
    pv = pd.read_csv(Path(data_dir) / "pageviews.csv", dtype={"user_id": str, "ts": str, "clicked": "int64"})
    pv["ts"] = _instants(pv["ts"])
    pv = pv.merge(assignments[["user_id", "variant", "assigned_at"]], on="user_id", how="inner")
    pv = pv[pv["ts"] >= pv["assigned_at"]]  # exposure before assignment is not part of the experiment
    return pv.reset_index(drop=True)
