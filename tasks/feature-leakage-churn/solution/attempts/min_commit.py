"""Wrong: an order is taken as visible from the earlier of its `_loaded_at` and the commit of the committed
legacy_orders range that holds it (its `_loaded_at` where no range holds it). The orders that orders_hourly committed
into `orders_new` before the rename then get those hourly commits, though until the rename every query on `orders`
read the table that legacy_orders loaded. Everything else as the canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py", '''    visible = np.maximum(seconds(orders["_loaded_at"]), cutover)''',
     '''    visible = seconds(orders["_loaded_at"]).copy()  # attempt: _loaded_at, the rename not read''')
edit("visibility.py", '''    visible[held] = at[np.searchsorted(hi, x[held], side="right")]''',
     '''    # attempt: the earlier of the legacy commit and _loaded_at
    visible[held] = np.minimum(at[np.searchsorted(hi, x[held], side="right")], visible[held])''')
