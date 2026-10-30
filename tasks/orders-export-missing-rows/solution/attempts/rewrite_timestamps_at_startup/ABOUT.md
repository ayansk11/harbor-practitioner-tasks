# H. rewrite_timestamps_at_startup (shortcut; expected reward 0)
At start-up the service rewrites `created_at` in the database it is given (a fraction of a second per order of a
same-second group) and strips the fraction from responses, so the old cursor stops skipping rows and the fields look
unchanged. It alters stored orders, and newly inserted orders share seconds again. Killed by db (stored orders
changed) and c4 (customer walk over a new same-second group). Applied by `apply.py`.
