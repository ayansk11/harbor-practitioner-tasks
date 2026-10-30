"""Wrong fix: the district counts of te_district use labels with label_available_at <= t, so a label that lands
exactly at the prediction time counts (FEATURES.md: available at t means label_available_at < t). The prior is
right."""
from _common import use_canonical, edit
use_canonical("windows.py", "encoding.py", "status.py", "impute.py")
edit("encoding.py", '''    hi = np.searchsorted(key[o2], pt_code * STRIDE + t, side="left")''',
     '''    hi = np.searchsorted(key[o2], pt_code * STRIDE + t, side="right")''')
