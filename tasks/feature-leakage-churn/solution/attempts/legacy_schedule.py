"""Wrong: an order below the last legacy watermark is taken as visible from the nightly job's usual start, 02:30 on
the night after `ordered_at`; the times and outcomes of the legacy commits in `_ops/` (rollbacks, the outage, late
commits) are not used. Everything else as the canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py", '''    visible[held] = at[np.searchsorted(hi, x[held], side="right")]''',
     '''    # attempt: the schedule, 02:30 on the night after the order
    visible[held] = (x[held] // DAY + 1) * DAY + 2 * 3600 + 30 * 60''')
