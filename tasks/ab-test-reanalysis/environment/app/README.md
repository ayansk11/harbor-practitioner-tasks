# EXP-2291 readout

Readout pipeline for experiment EXP-2291 ("related items v2" on product pages). The plan it must follow is
`EXPERIMENT.md`.

Run it from this folder:

    python -m abtest.report --data data --out output/result.json

Layout:

| Path | What it is |
|---|---|
| `abtest/load.py` | reads the four export files, parses timestamps to UTC, drops repeated assignment rows and pre-assignment pageviews |
| `abtest/filters.py` | the population filter: applies the platform's bot screening (`bot_flags.csv.gz`) to both arms |
| `abtest/stats.py` | statistics for the readout: the delta-method interval and the SRM test |
| `abtest/report.py` | the command: per-user clicks and pageviews, the readout, `result.json`; a click is a pageview's `clicked` value, the module click flag |
| `data/` | the EXP-2291 export: `assignments.csv.gz`, `bot_flags.csv.gz`, `pageviews.csv.gz`, `module_clicks.csv.gz` |
| `docs/` | the data platform's documentation of the export (`DATA_DICTIONARY.md`, `TRACKING.md`, `BOT_SCREENING.md`) and the launch record of EXP-2291 (`LAUNCH_EXP-2291.md`) |
| `output/result.json` | the last readout |
| `PM_NOTE.md` | the PM's note about this readout |

Every experiment export from the data platform has the same four files and columns, so the same command is used for
other experiments with `--data <their folder>`.
