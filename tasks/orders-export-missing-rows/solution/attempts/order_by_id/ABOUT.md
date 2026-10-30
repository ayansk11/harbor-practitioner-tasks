# C. order_by_id (plausible wrong fix; expected reward 0)
Both listings page by id alone (`ORDER BY id DESC`, cursor = last id). Complete, but not in the documented order:
backfilled orders (high id, old `created_at`) come first. Killed by c1, c3 (order) and c7 (default page).
Applied by `apply.py`.
