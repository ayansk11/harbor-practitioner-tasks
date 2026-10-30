# INC-2041: churn model is far worse live than offline

Status: open. Owner: ML platform on-call. Opened 2026-02-06.

## What happened
- Model `churn-hgb-v3` was trained on the feature table from `python -m churn.build_features` over the 2025-12-31
  warehouse extract (the one in `/app/data`) and validated on predictions from 2025-09-01 to 2025-11-30:
  **offline AUC 0.981** (`python -m churn.train`).
- It went live on 2026-01-01. The live scoring service computes the same features in real time from the same spec
  (`churn/FEATURES.md`). On January's predictions, once their 30-day outcomes had landed: **live AUC 0.613**.
- The model code and its hyperparameters did not change between validation and launch.

## Tried so far
- Retrained with much stronger regularization and shallower trees (`--l2 50 --max-depth 2`): offline AUC still 0.981.
  This is not ordinary overfitting.
- Compared the live scoring service with `churn/FEATURES.md` by hand on 200 January predictions: it follows the spec.

## Where we are
The offline pipeline is the suspect: some features for a prediction at time t seem to use information that did not
exist yet at t. Before v4 is trained, the pipeline has to follow `churn/FEATURES.md` exactly, so that offline
validation means something again. Keep every feature; the model team needs all of them.
