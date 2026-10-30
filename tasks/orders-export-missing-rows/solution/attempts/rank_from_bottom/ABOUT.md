# K. rank_from_bottom (plausible wrong fix; expected reward 0)
The cursor is the number of orders older than the last order served; the next page is read from the oldest end
(`ORDER BY created_at ASC, id ASC LIMIT n OFFSET rank - n`, reversed). New orders at the top never move it, so it
survives ordinary checkout traffic and the visible tests pass. An order synced late (high id, old `created_at`) that
lands below the client's position moves every later page by one, so an existing order is skipped. Killed by c4 (the
insert batches hold late-synced orders in the part of the listing not yet walked).
Files: `app/orders_service/{pagination,queries}.py`.
