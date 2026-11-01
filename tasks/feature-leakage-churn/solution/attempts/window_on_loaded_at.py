"""Wrong: the order windows (orders_7d, orders_30d, spend_30d_cents) are taken on the time each order became visible
instead of `ordered_at`, so an order that loaded late counts in the window of its load (last week's box re-enters the
7 days). days_since_last_order and everything else as the canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("windows.py", '''    i, j = window_pairs(pc, pt, oc, oa, seen, 30)''',
     '''    i, j = window_pairs(pc, pt, oc, seen, seen, 30)  # attempt: the window on the load time''')
edit("windows.py", '''    in7 = oa[j] >= pt[i] - 7 * DAY''', '''    in7 = seen[j] >= pt[i] - 7 * DAY''')
