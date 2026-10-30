# churn: features and model for the retention team

| Path | What it is |
|---|---|
| `churn/FEATURES.md` | the feature spec; the contract with the live scoring service |
| `churn/build_features.py` | CLI: `python -m churn.build_features --data <dir> --out <file.parquet>` |
| `churn/extract.py` | loads an extract (six CSV files) |
| `churn/windows.py`, `encoding.py`, `status.py`, `impute.py` | the feature code |
| `churn/train.py` | trains and validates the model: `python -m churn.train --features <file.parquet> --data <dir>` |
| `data/` | the 2025-12-31 warehouse extract (layout in `churn/FEATURES.md`) |
| `INCIDENT.md` | the open incident about this pipeline |

Run from `/app`:
```
python -m churn.build_features --data /app/data --out /app/output/features.parquet
python -m churn.train --features /app/output/features.parquet --data /app/data
```
