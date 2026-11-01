The churn model `churn-hgb-v3` scored an offline validation AUC of 0.805, but 0.656 in its first live month
(`/app/INCIDENT.md`). Its feature pipeline in `/app/churn` already uses only events stamped before each prediction
(`/app/CHANGELOG.md`), yet the live scoring service computed other values for the same predictions. The live service
computes every feature at the moment of a prediction from the warehouse tables as they stand at that moment
(`/app/live/features.py`). The pipeline builds its training table from an extract taken later (`/app/data`, this
brand's warehouse at 2026-03-05T00:00:00Z). The tables are described in `/app/docs/WAREHOUSE.md`, the warehouse's own
records of its job runs and transactions are in `/app/data/_ops/`, and samples of what the live service computed are
in `/app/logs/`.

Fix `python -m churn.build_features --data <dir> --out <file.parquet>` (run from `/app`) so that, for every row of the
extract's `scoring_points.csv`, each feature is the value the live service would have computed for that customer at
that row's `as_of`, had it been running then against the warehouse as it stood at that moment (exactly the rows and
values committed to it before that moment, in the tables its queries name). This must hold for any extract with the
layout of `/app/data`. Keep every feature of `/app/live/features.py` whose live value the extract determines for every
row; leave out any feature whose live value the extract cannot determine for some rows.

How the result is checked:
- `python3 -m churn.build_features --data <dir> --out <file.parquet>` is run from a copy of `/app` at another path, as
  an unprivileged user, on extracts of the company's other brands: the same seven CSV files, `_ops/` folder and layout
  as `/app/data`, about the same size and period, with other customers, events and load histories (their own job runs,
  failures and migrations). It must exit with status 0 and write the parquet file. Do not rely on network access, on
  absolute paths into `/app`, or on anything in `/app/data` or `/app/logs`.
- The output must have exactly one row per row of the extract's `scoring_points.csv`, with the columns `customer_id`,
  `as_of` and every kept feature, named as in `/app/live/features.py`. Extra columns, row order and column order do not
  matter, but a column named after a feature that should be left out fails unless all its values are null.
  `customer_id` may be any integer type; `as_of` a timestamp (time-zone aware, or naive meaning UTC) or an ISO 8601
  string; the integer features (`orders_7d`, `orders_30d`, `spend_30d_cents`, `tickets_30d`) any numeric type holding
  whole numbers; a null a parquet null or NaN.
- Every value must equal what the live service would have computed: integer features exactly, other numbers within
  1e-6 plus 1e-9 times the expected value, strings exactly, nulls exactly where the live service would have had no value.
- An extract is also changed in everything the warehouse did not yet hold at some cut time (in any table, whatever the
  date of the event a row records) and the command is run again: every prediction with `as_of` at or before the cut
  must keep the same feature values (within the tolerances above). The changed extract is still a copy of the
  warehouse at the same moment as the original extract, in the same layout; only what the warehouse did not yet hold
  at the cut differs, and its `_ops/` records match it: every record dated before the cut is unchanged, and the later
  records describe the changed extract.
- Each run is stopped after 60 seconds and then fails. The grading container has the same resources as this one
  (2 vCPUs, 4 GiB), and `/app/data` is about the size of the graded extracts, so time a run on it. Graded runs set
  `OMP_NUM_THREADS=1`.
- `python -m churn.train` is not graded; it may help to check the work.

Only /app is kept when we grade: folders named `data`, `__pycache__` or `.venv` anywhere under /app are dropped, and the packages already installed are available.
