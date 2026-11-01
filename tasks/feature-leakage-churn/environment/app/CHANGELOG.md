# Changelog: the offline feature pipeline (`churn/`)

## v3 (2025-12-19): the training table of churn-hgb-v3
Fixes INC-2041: in four places, v2 used events stamped at or after the prediction time `t`.
- `windows.py`: the order, spend and ticket windows are `[t - W days, t)` on the exact event timestamps. v2 summed
  whole UTC days, the day of `t` included, so events later on the prediction day were counted.
- `status.py`: the latest snapshot dated before `date(t)`. A snapshot dated D records the status at the end of day D;
  v2 took the customer's latest snapshot in the extract, which is often dated after `t`.
- `impute.py`: a missing `app_minutes_7d` takes the customer's most recent earlier reading only. v2 filled backward
  first, from a later reading.
- `encoding.py`: `te_district` counts only labels whose 30-day window had closed before `t` (`as_of + 30 days < t`),
  for the district and for the prior alike. v2 used every label in the extract, the prediction's own and later ones
  included.

Also in v3:
- `attributes.py` (new): `plan` and `days_since_last_login` from the customer record, the two features of the live
  service that v2 did not build. A last login at or after `t` is ignored (the feature is null then).
- `extract.py` loads the seven tables described in `docs/WAREHOUSE.md`.
- `train.py`: every column of the feature table other than `customer_id` and `as_of` is a model input, and string
  columns are one-hot encoded (v2 encoded `status` only); a column that holds no value at all is skipped.
