"""Wrong fix: the 30-day windows are open on the left, (t - 30 days, t), so an order or ticket stamped exactly at
t - 30 days is dropped from orders_30d, spend_30d_cents and tickets_30d (FEATURES.md: [t - 30 days, t)). The 7-day
window is right."""
from _common import use_canonical, edit
use_canonical("windows.py", "encoding.py", "status.py", "impute.py")
edit("windows.py", '''    lo = np.searchsorted(ev_key, cid + t - days * 86400, side="left")''',
     '''    lo = np.searchsorted(ev_key, cid + t - days * 86400, side="left" if days < 30 else "right")''')
