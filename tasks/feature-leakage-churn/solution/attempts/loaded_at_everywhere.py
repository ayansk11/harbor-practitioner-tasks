"""Wrong: trust `_loaded_at` in every table, the orders included. An order placed before the backfill's bound carries
the backfill's commit into `orders_new`, so before that commit no order is visible and every order feature is empty
there; an order of the dual run carries its hourly commit into `orders_new`, before the rename. Everything else as the
canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py", '''    """Per order: the commit that made it visible to a query on `orders` (epoch seconds)."""
''', '''    """Per order: the commit that made it visible to a query on `orders` (epoch seconds)."""
    return seconds(orders["_loaded_at"])  # attempt: the audit column, for every order
''')
