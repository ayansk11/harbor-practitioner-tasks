"""Customer attributes as the warehouse held them at the prediction time t (docs/WAREHOUSE.md: customers, crm_sync,
plan_changes).

`customers` holds current values only: each crm_sync overwrites `plan` and `last_login_at`. The plan at t is rebuilt
from `plan_changes`, which logs every change since signup, each with the commit of the sync that applied it
(`_loaded_at`): the `new_plan` of the change with the greatest `changed_at` among the changes applied before t; before
any applied change, the plan chosen at signup (the `old_plan` of the customer's first change); a customer with no
change keeps `customers.plan`.

No history of `last_login_at` is kept, so its value at t cannot be rebuilt from an extract for every prediction:
`days_since_last_login` is left out of the feature table.
"""
import numpy as np
import pandas as pd

from churn.visibility import latest_arrived, seconds


def plan(points, customers, plan_changes):
    """The plan the customer record held at t."""
    ch = plan_changes
    row = latest_arrived(points["customer_id"].to_numpy(dtype="int64"), seconds(points["as_of"]),
                         ch["customer_id"].to_numpy(dtype="int64"), seconds(ch["_loaded_at"]),
                         seconds(ch["changed_at"]))
    first = ch.sort_values(["customer_id", "changed_at"], kind="mergesort").drop_duplicates("customer_id")
    signup_plan = points["customer_id"].map(first.set_index("customer_id")["old_plan"])
    current = points["customer_id"].map(customers.set_index("customer_id")["plan"])
    out = np.array(signup_plan.where(signup_plan.notna(), current).to_numpy(dtype=object), dtype=object)
    hit = row >= 0
    out[hit] = ch["new_plan"].to_numpy(dtype=object)[row[hit]]
    return pd.Series(out, index=points.index, dtype=object)
