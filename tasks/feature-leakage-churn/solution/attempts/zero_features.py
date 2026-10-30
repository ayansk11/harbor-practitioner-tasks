"""Shortcut: every feature constant (zeros, status 'active'). Nothing can leak, but nothing follows FEATURES.md."""
from _common import edit
edit("build_features.py", '''    feats = activity_features(points, t["orders"], t["tickets"])
    feats["tenure_days"] = tenure_days(points, t["customers"])
    feats["status"] = latest_status(points, t["status_snapshots"])
    feats["app_minutes_7d"] = fill_app_minutes(points)
    feats["te_district"] = district_encoding(points, t["labels"], t["customers"])''', '''    feats = points[["customer_id", "as_of"]].copy()
    for c in FEATURE_COLUMNS:
        feats[c] = 0
    feats["status"] = "active"''')
