"""Wrong: days_since_last_login is kept where the extract determines it, the predictions after the record's last
write (`_updated_at` before t, so the record held its current `last_login_at` at t), and null elsewhere; the
instruction leaves out a feature that the extract cannot determine for some rows. Everything else as the canonical
solution."""
from _common import append, edit, use_canonical

use_canonical()
append("attributes.py", '''

def days_since_last_login(points, customers):
    """t minus the record's last login, in days, where the record has not changed since t; null elsewhere."""
    rec = customers.set_index("customer_id")
    last = points["customer_id"].map(rec["last_login_at"])
    updated = points["customer_id"].map(rec["_updated_at"])
    days = (points["as_of"] - last).dt.total_seconds() / 86400
    return days.where(updated < points["as_of"])
''')
edit("build_features.py", '''from churn.attributes import plan''', '''from churn.attributes import days_since_last_login, plan''')
edit("build_features.py", '''"status", "plan", "app_minutes_7d", "te_district"]''',
     '''"status", "plan", "days_since_last_login", "app_minutes_7d", "te_district"]''')
edit("build_features.py", '''    feats["plan"] = plan(points, t["customers"], t["plan_changes"])
''', '''    feats["plan"] = plan(points, t["customers"], t["plan_changes"])
    feats["days_since_last_login"] = days_since_last_login(points, t["customers"])
''')
