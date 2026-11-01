"""Wrong: `plan` is left out as well as days_since_last_login, as "current state" that cannot be rebuilt, though
plan_changes determines it for every prediction. Everything else as the canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("build_features.py", '''                   "tenure_days", "status", "plan", "app_minutes_7d", "te_district"]''',
     '''                   "tenure_days", "status", "app_minutes_7d", "te_district"]  # attempt: no plan''')
edit("build_features.py", '''    feats["plan"] = plan(points, t["customers"], t["plan_changes"])
''', "")
