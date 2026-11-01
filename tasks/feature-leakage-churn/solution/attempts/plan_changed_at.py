"""Wrong: the plan rebuilt from plan_changes by business time, every change with `changed_at` before t, though a
change reaches the customer record only with the crm_sync that applies it (`_loaded_at`). Everything else as the
canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("attributes.py", '''ch["customer_id"].to_numpy(dtype="int64"), seconds(ch["_loaded_at"]),''',
     '''ch["customer_id"].to_numpy(dtype="int64"), seconds(ch["changed_at"]),  # attempt: changed_at''')
