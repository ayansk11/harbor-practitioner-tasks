"""Wrong: days_since_last_login is kept with v3's clip (t minus the record's current `last_login_at`, null when that
login is at or after t), as the best available approximation; the extract keeps no history of the column. Everything
else as the canonical solution."""
from _common import append, edit, use_canonical, v3_function

use_canonical()
append("attributes.py", "\n\n" + v3_function("attributes.py", "days_since_last_login"))
edit("build_features.py", '''from churn.attributes import plan''', '''from churn.attributes import days_since_last_login, plan''')
edit("build_features.py", '''"status", "plan", "app_minutes_7d", "te_district"]''',
     '''"status", "plan", "days_since_last_login", "app_minutes_7d", "te_district"]''')
edit("build_features.py", '''    feats["plan"] = plan(points, t["customers"], t["plan_changes"])
''', '''    feats["plan"] = plan(points, t["customers"], t["plan_changes"])
    feats["days_since_last_login"] = days_since_last_login(points, t["customers"])
''')
