"""Wrong: the status of the most recently loaded snapshot (what a merge_asof of the predictions on `_loaded_at`
gives), not the visible snapshot with the greatest `snapshot_date`; a partition that lands after a later day's wins.
Everything else as the canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("status.py", '''                         seconds(snapshots["snapshot_date"]))''',
     '''                         seconds(snapshots["_loaded_at"]))  # attempt: the latest load, not the latest date''')
