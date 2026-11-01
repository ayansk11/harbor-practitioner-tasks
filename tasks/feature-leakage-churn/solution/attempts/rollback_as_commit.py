"""Wrong: every legacy_orders transaction is taken as committed, the rolled-back ones included (the `outcome` in
`_ops/commits.jsonl` is not read), so an order below the last legacy watermark is visible from the `at` of the first
legacy run whose range ends above its `ordered_at`, whether that run committed or rolled back. Everything else as the
canonical solution."""
from _common import edit, use_canonical

use_canonical()
edit("visibility.py", '''    committed = legacy[legacy["outcome"] == "commit"].sort_values("hi", kind="mergesort")''',
     '''    committed = legacy.sort_values("hi", kind="mergesort")  # attempt: rolled-back runs included''')
