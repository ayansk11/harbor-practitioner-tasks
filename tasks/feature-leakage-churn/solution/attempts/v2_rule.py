"""Wrong: only the orders the backfill copied (`_load_job` = `legacy_backfill`) get the commit of the committed
legacy_orders range that holds them; every other order is taken as visible from its `_loaded_at`. The orders that
orders_hourly committed into `orders_new` before the rename are then visible from those commits, though until the
rename every query on `orders` read the table that legacy_orders loaded. Everything else as the canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py", '''    visible = np.maximum(seconds(orders["_loaded_at"]), cutover)''',
     '''    visible = seconds(orders["_loaded_at"]).copy()  # attempt: _loaded_at, the rename not read''')
edit("visibility.py", '''    held = x < hi[-1]''',
     '''    held = (orders["_load_job"] == "legacy_backfill").to_numpy()  # attempt: the backfilled rows only''')
