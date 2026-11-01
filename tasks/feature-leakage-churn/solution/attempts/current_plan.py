"""Wrong: the plan as the extract's customer record holds it now (`customers.plan`, overwritten by every crm_sync),
for every prediction; plan_changes is not read. Everything else as the canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("attributes.py", '''    """The plan the customer record held at t."""
''', '''    """The plan the customer record held at t."""
    return points["customer_id"].map(customers.set_index("customer_id")["plan"])  # attempt: the current plan
''')
