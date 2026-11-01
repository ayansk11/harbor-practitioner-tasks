"""Wrong: the orders of a committed legacy_orders range are taken as visible from the start of its task (the
scheduler's `state=running` line), before the task had selected them or committed its transaction. Everything else as
the canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py",
     '''    hi, at = committed["hi"].to_numpy(dtype="int64"), committed["at"].to_numpy(dtype="int64")''',
     '''    # attempt: the task's start, not its commit
    hi, at = committed["hi"].to_numpy(dtype="int64"), committed["started_at"].to_numpy(dtype="int64")''')
