"""Wrong: the orders of a committed legacy_orders range are taken as visible from the end of its task (the
scheduler's `state=success` line), not from the commit of its transaction in `_ops/commits.jsonl`. The task runs
`analyze orders` after the commit, so it ends minutes to hours after the commit. Everything else as the canonical
solution."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py",
     '''    hi, at = committed["hi"].to_numpy(dtype="int64"), committed["at"].to_numpy(dtype="int64")''',
     '''    # attempt: the task's end, not its commit
    hi, at = committed["hi"].to_numpy(dtype="int64"), committed["end_at"].to_numpy(dtype="int64")''')
