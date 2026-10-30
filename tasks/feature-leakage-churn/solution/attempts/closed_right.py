"""Wrong fix: exact-timestamp windows, but closed on the right, (t - W, t]: the event stamped at t is counted."""
from _common import use_canonical, edit
use_canonical("windows.py", "encoding.py", "status.py", "impute.py")
edit("windows.py", '''    hi = np.searchsorted(ev_key, cid + t, side="left")
    lo = np.searchsorted(ev_key, cid + t - days * 86400, side="left")''', '''    hi = np.searchsorted(ev_key, cid + t, side="right")
    lo = np.searchsorted(ev_key, cid + t - days * 86400, side="right")''')
