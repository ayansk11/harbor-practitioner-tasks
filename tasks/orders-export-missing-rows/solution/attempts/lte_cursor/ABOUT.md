# A. lte_cursor (plausible wrong fix; expected reward 0)
`created_at < ?` becomes `created_at <= ?` in both listings. Pages that end inside a same-second group repeat rows,
and a group larger than `limit` returns the same page forever. Killed by c1 (order) and c2 (pages: repeated cursor).
Applied by `apply.py` (exact text substitution on the shipped files).
