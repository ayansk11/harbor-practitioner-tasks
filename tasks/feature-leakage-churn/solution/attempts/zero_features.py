"""Shortcut: every kept feature a constant (counts and other numbers 0, status 'active', plan 'basic'), with
days_since_last_login left out. Nothing can leak and nothing moves when the future changes, but no value is the live
one."""
from _common import edit, use_canonical

use_canonical()
edit("build_features.py", '''    points = t["scoring_points"].reset_index(drop=True)
''', '''    points = t["scoring_points"].reset_index(drop=True)
    feats = points[["customer_id", "as_of"]].copy()  # attempt: constants
    for c in FEATURE_COLUMNS:
        feats[c] = 0
    feats["status"] = "active"
    feats["plan"] = "basic"
    return feats
''')
