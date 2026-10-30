# EXP-2291 readout

Readout pipeline for experiment EXP-2291 ("related items v2" on product pages). The plan it must follow is
`EXPERIMENT.md`.

Run it from this folder:

    python -m abtest.report --data data --out output/result.json

Layout:

| Path | What it is |
|---|---|
| `abtest/load.py` | reads the three export files, parses timestamps to UTC, drops repeated assignment rows and pre-assignment pageviews |
| `abtest/filters.py` | population filters (bots) |
| `abtest/stats.py` | statistics for the readout |
| `abtest/report.py` | the command: builds the readout and writes `result.json` |
| `data/` | the EXP-2291 export: `assignments.csv`, `users.csv`, `pageviews.csv` (columns in `EXPERIMENT.md`) |
| `output/result.json` | the last readout |
| `PM_NOTE.md` | the PM's question about this readout |

Every experiment export from the data platform has the same three files and columns, so the same command is used for
other experiments with `--data <their folder>`.
