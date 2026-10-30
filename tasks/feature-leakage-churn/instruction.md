Our churn model scored an offline validation AUC of 0.981, but its first live month came in at 0.613. The model did
not change, and retraining with much stronger regularization did not move the offline number. The suspect is the
feature pipeline in `/app/churn`: some features for a prediction at time t seem to use information that did not exist
yet at t. Background is in `/app/INCIDENT.md` and `/app/README.md`; the spec every feature must follow is
`/app/churn/FEATURES.md`; a warehouse extract is in `/app/data`.

Find every place where a feature uses information that was not available strictly before the prediction time, and fix
`python -m churn.build_features --data <dir> --out <file.parquet>` (run from `/app`) so that its output follows
`/app/churn/FEATURES.md` exactly, for any extract with this layout. Keep every feature.

How the result is checked:
- We run `python3 -m churn.build_features --data <dir> --out <file.parquet>` from a copy of `/app` at a different
  path, as an unprivileged user, on other extracts with the same six CSV files and layout as `/app/data`, about the
  same size, but different data. The command must exit with status 0 and write the parquet file. Do not rely on
  network access, on absolute paths into `/app` or on anything in `/app/data`.
- The output must have exactly one row per row of the extract's `scoring_points.csv`, with the columns `customer_id`,
  `as_of` and all nine features of `FEATURES.md`, named as there. Extra columns, row order and column order do not
  matter. `customer_id` may be any integer type; `as_of` may be a timestamp (time-zone aware, or naive meaning UTC) or
  an ISO 8601 string; counts may be any numeric type holding whole numbers; a null may be a parquet null or NaN.
- Every value must equal its `FEATURES.md` definition: the four counts exactly, the other numbers within 1e-6 plus
  1e-9 times the expected value, `status` as the exact string, nulls exactly where the spec says null.
- We also take an extract, change everything in it that becomes known at or after some cut time (orders and tickets
  stamped at or after it, snapshots dated on or after its date, labels that land at or after it, later scoring points,
  new customers), run your command again, and check that every prediction with `as_of` at or before the cut keeps
  the same feature values (within the tolerances above).
- Each run is stopped after 60 seconds and then fails. The grading container is set up with the same resources as
  yours (2 vCPUs, 4 GiB), and `/app/data` is about the same size as the extracts we use, so time a run on it.
- `python -m churn.train` is not graded; you may use it to check your work.

Only /app is kept when we grade: folders named `data`, `__pycache__` or `.venv` anywhere under /app are dropped, and the packages already installed are available.
