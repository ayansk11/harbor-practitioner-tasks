"""Wrong: an order below the last legacy watermark (an order the legacy table held) is taken as visible from its
`ordered_at`, since its `_loaded_at` is a later commit into `orders_new` (the backfill's or the dual run's), and the
times of the legacy commits in `_ops/` are not used. Everything else as the canonical solution (later orders by
`_loaded_at`, not before the cutover's commit)."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py", '''    visible[held] = at[np.searchsorted(hi, x[held], side="right")]''',
     '''    visible[held] = x[held]  # attempt: the event time''')
