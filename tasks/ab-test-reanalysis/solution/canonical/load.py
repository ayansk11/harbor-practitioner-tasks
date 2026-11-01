"""Read one experiment export: assignments, bot_flags, pageviews and module_clicks (EXPERIMENT.md section 8).

Each file is read from <name>.csv.gz, or from <name>.csv when there is no .gz. Every column is read as text, so each
id keeps its exact form; timestamps are then parsed to UTC instants (the export mixes "Z" and "+hh:mm" / "-hh:mm"
offsets, so text comparison would be wrong).
"""
from pathlib import Path

import pandas as pd

VARIANTS = ("A", "B")
METHODS = ("hash", "override")          # hash = set by the randomization; override = set by hand (DATA_DICTIONARY)


def _read(data_dir, name, columns):
    folder = Path(data_dir)
    path = folder / f"{name}.csv.gz"
    if not path.exists():
        path = folder / f"{name}.csv"
    return pd.read_csv(path, dtype=str, keep_default_na=False, usecols=list(columns))


def _instants(col):
    return pd.to_datetime(col, utc=True, format="ISO8601")


def load_assignments(data_dir):
    """One row per assigned user: user_id, variant, assigned_at (UTC), method. An exact repeat of a row counts once."""
    df = _read(data_dir, "assignments", ("user_id", "variant", "assigned_at", "method")).drop_duplicates()
    if df["user_id"].duplicated().any():
        raise ValueError("a user has two different assignment rows (the plan says this never happens)")
    bad = ~df["variant"].isin(VARIANTS) | ~df["method"].isin(METHODS)
    if bad.any():
        raise ValueError(f"unknown variant or method in assignments: {df[bad].iloc[0].to_dict()}")
    df["assigned_at"] = _instants(df["assigned_at"])
    return df.reset_index(drop=True)


def load_bot_flags(data_dir):
    """One row per flag raised by the platform's bot screening: user_id, rule."""
    return _read(data_dir, "bot_flags", ("user_id", "rule"))


def load_counted_pageviews(data_dir, users):
    """The counted pageviews: rows of the given users with ts at or after the user's assigned_at (instants).

    users: one row per experiment user (user_id, variant, assigned_at). Returns pageview_id, user_id, variant and
    platform_clicked (the export's precomputed `clicked` flag, kept only to describe it in the notes).
    """
    pv = _read(data_dir, "pageviews", ("pageview_id", "user_id", "ts", "clicked"))
    if pv["pageview_id"].duplicated().any():
        raise ValueError("a pageview_id is repeated in pageviews (each row is one pageview with its own id)")
    pv["ts"] = _instants(pv["ts"])
    pv = pv.merge(users[["user_id", "variant", "assigned_at"]], on="user_id", how="inner", validate="many_to_one")
    pv = pv.loc[pv["ts"] >= pv["assigned_at"]]
    out = pv[["pageview_id", "user_id", "variant"]].copy()
    out["platform_clicked"] = (pv["clicked"] == "1").astype("int64")
    return out.reset_index(drop=True)


def load_item_pageviews(data_dir):
    """The pageview_ids with at least one item:<product_id> event in module_clicks, the pageviews on which a related
    product was opened from the module. Arrow taps (nav:prev, nav:next) and the "See all" link (link:all) open no
    product and are left out (docs/TRACKING.md)."""
    mc = _read(data_dir, "module_clicks", ("pageview_id", "target"))
    return pd.Index(mc.loc[mc["target"].str.startswith("item:"), "pageview_id"].unique())
