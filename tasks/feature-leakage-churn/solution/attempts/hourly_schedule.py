"""Wrong: an order at or above the last legacy watermark is taken as visible from the hourly loader's schedule, the
first :20 after the top of the hour that follows `ordered_at`; its `_loaded_at` and the cutover's commit are never
read, so a failed hourly run and a commit before :20 are missed. Everything else as the canonical solution (older
orders by the legacy commits)."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py", '''    visible = np.maximum(seconds(orders["_loaded_at"]), cutover)''',
     '''    visible = (seconds(orders["ordered_at"]) // 3600 + 1) * 3600 + 20 * 60  # attempt: the hourly schedule''')
