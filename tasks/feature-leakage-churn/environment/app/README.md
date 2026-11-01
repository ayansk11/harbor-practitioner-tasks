# churn: features and model for the retention team

| Path | What it is |
|---|---|
| `INCIDENT.md` | INC-2077, the open incident about this pipeline |
| `CHANGELOG.md` | changes to the pipeline (v3, after INC-2041) |
| `live/features.py` | the live scoring service's feature queries, one per feature: the contract (reference copy, never run here) |
| `docs/WAREHOUSE.md` | the warehouse tables: which system writes each one, and where its commit times are recorded |
| `churn/build_features.py` | CLI: `python -m churn.build_features --data <dir> --out <file.parquet>` |
| `churn/extract.py` | loads an extract's seven CSV files |
| `churn/windows.py`, `status.py`, `attributes.py`, `impute.py`, `encoding.py` | the feature code |
| `churn/train.py` | trains and validates the model: `python -m churn.train --features <file.parquet> --data <dir>` |
| `data/` | this brand's warehouse extract at 2026-03-05T00:00:00Z: seven CSV files and the scheduler's records in `_ops/` (`docs/WAREHOUSE.md`) |
| `logs/` | a sample of what the live scoring service computed (`INCIDENT.md`) |

Run from `/app`:
```
python -m churn.build_features --data /app/data --out /app/output/features.parquet
python -m churn.train --features /app/output/features.parquet --data /app/data
```
`python -m churn.train --help` lists the model options (`--l2`, `--max-depth`).
