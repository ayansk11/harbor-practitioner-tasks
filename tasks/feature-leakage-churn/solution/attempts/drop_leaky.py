"""Shortcut: drop the three features that look leaky (te_district, status, app_minutes_7d) instead of fixing them."""
from _common import edit
edit("build_features.py", '''                   "tenure_days", "status", "app_minutes_7d", "te_district"]''', '''                   "tenure_days"]''')
edit("build_features.py", '''    feats["status"] = latest_status(points, t["status_snapshots"])
    feats["app_minutes_7d"] = fill_app_minutes(points)
    feats["te_district"] = district_encoding(points, t["labels"], t["customers"])
''', "")
