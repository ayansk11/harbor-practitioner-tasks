# B. fix_helper_only (plausible incomplete fix; expected reward 0)
The canonical fix of `pagination.py` only; the inline copy of the predicate in `queries.py` is left as shipped, so
`GET /customers/<id>/orders` still skips the rest of a same-second group. Killed by c3 (customers) and c4 (customer
walks after the inserts). Applied by `apply.py` (copies the canonical `pagination.py`).
