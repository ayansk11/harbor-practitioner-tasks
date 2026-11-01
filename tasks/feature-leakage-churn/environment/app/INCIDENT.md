# INC-2077: churn-hgb-v3 scores far worse live than in validation

Status: open. Owner: ML platform on-call. Opened 2026-03-04, updated 2026-03-05.

## What happened
- `churn-hgb-v3` is trained on the feature table that the offline pipeline builds (`churn/`, v3 in `CHANGELOG.md`).
  Built from this brand's extract (`data/`, the warehouse at 2026-03-05T00:00:00Z), that table gives
  **offline validation AUC 0.805** in `python -m churn.train` (trained on the predictions before 2025-09-01,
  validated on those of 2025-09-01 to 2025-11-30).
- The model went live on 2026-01-01. The live scoring service computes the features of each request itself, from the
  warehouse at the moment of the request (`live/features.py`). On the 3,415 predictions of January 2026, whose 30-day
  outcomes have all landed in `labels`: **live AUC 0.656**.
- The model and its hyperparameters did not change between validation and launch.

## Tried so far
- Retrained with much stronger regularization and shallower trees (`--l2 50 --max-depth 2`): offline AUC 0.813. The
  offline number did not fall, so this is not ordinary overfitting.
- Compared the live service with `live/features.py` by hand on 200 January requests: the service computes exactly what
  its queries say.
- Pulled a random sample of about 10% of the requests of January 2026, with the values the service computed:
  `logs/live_2026-01_sample.jsonl`, 365 requests, one JSON object per line with `customer_id`, `as_of`, `trigger`, the
  11 `features` and the model's `score`.

## Next step (model team)
`churn-hgb-v4` is to be trained on a feature table that matches what the live service computed for every past
prediction. Every feature whose live value can be matched for every prediction is kept; any feature whose live value
cannot be matched is dropped from v4.
