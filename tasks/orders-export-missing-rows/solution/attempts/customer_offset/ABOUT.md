# L. customer_offset (plausible wrong fix; expected reward 0)
`GET /orders` gets the canonical keyset fix; the customer listing is rewritten with LIMIT/OFFSET, the offset inside an
opaque cursor. Complete and in order on a database nobody writes to, and the visible tests pass. When an order is
written for that customer while the support tool pages, the rows shift and an order comes twice. Killed by c4 (the
customer walk with inserts). Applied by `apply.py` (copies the canonical `pagination.py`, makes `app.py` pass the raw
cursor) plus `app/orders_service/queries.py`.
