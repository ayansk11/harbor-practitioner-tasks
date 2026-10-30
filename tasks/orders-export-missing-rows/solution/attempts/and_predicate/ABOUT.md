# I. and_predicate (plausible wrong fix; expected reward 0)
The cursor carries (created_at, id) but the condition is `created_at <= ? AND id < ?`: right while ids grow with time,
wrong for backfilled orders (high id, old `created_at`), which are dropped after the first page. Killed by c1, c3.
Applied by `apply.py` (the canonical files with that one condition changed).
