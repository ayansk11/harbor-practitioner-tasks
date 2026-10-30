# J. tie_offset (plausible wrong fix; expected reward 0)
The cursor is the last order's `created_at` plus how many orders of that second the client already has; the next page
is `created_at <= ?` with that many skipped by OFFSET. Complete and in order on a database nobody writes to, and the
visible tests pass. When an order is written into the second the client has just reached (a late POS sync with a high
id and an old date), the orders of that second shift by one and the last order served comes back again. Killed by c4
(the insert batches hold one order in the same second as the last order of the page just served).
Files: `app/orders_service/{pagination,queries}.py`.
