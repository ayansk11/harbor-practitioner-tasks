# Validation: et0-station-ingest

Last updated: 2026-10-29 (Mac clock, MST).

**Final run: `full1`.** Harbor 0.25.0 on Daytona, 2026-10-28 from 19:45:27 to 19:56:20 (Mac clock, MST; job `result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full1.md`).

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py`.
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below).
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies.
- `NOTES.md`: what the run showed beyond the rewards.

The "Job folder" column of the `PROOF_RESULTS_*.md` files points into `jobs/`, the raw Harbor output. `jobs/` is git-ignored and not part of the repository; the trace folders below are the shipped copy.

## Results and traces

One trial per variant is shipped. Variants with one trial ship that trial. For canonical (ten trials) the shipped trial is the one with the earliest `started_at` in its `result.json`; its `job_result.json` holds the rewards of all ten. The last column is read from the shipped trial's `verifier/reward.json`.

| Variant | What it is | Expected | Rewards (all trials of the job) | Run | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|---|
| canonical | reference fix: convert at load time (FAO-56 Eq. 47 wind height, W/m2 to MJ) and fix the southern-latitude sign | 1 | 10 of 10 = 1.0 | `full1` | [`traces/canonical/`](traces/canonical/) | `et0-station-ingest__ezrRVNG` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance), hidden run rc 0 |
| alt | a different valid fix: keep raw readings, convert inside the FAO-56 call chain, regex latitude parser | 1 | 1.0 | `full1` | [`traces/alt/`](traces/alt/) | `et0-station-ingest__iveydVi` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance), hidden run rc 0 |
| nop | Harbor's nop agent: the three defects stay | 0 | 0.0 | `full1` | [`traces/nop/`](traces/nop/) | `et0-station-ingest__KVxKDWV` | `app_locked` 1; visible ok 0 (max error 66.684361 mm/day, 0 rows missing, 2184 over tolerance); hidden ok 0 (max error 67.411037 mm/day, 0 rows missing, 3461 over tolerance), hidden run rc 0 |
| abs_app_path | defence probe: conversion constants read from a config file by an absolute `/app` path | 0 | 0.0 | `full1` | [`traces/abs_app_path/`](traces/abs_app_path/) | `et0-station-ingest__5Fm7A6i` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 0 (no rows to compare (`max_abs_err` -1.0), 3651 rows missing, 0 over tolerance), hidden run rc 1 |
| fit_to_metservice | fixes the radiation units, then calibrates to the met-service sample | 0 | 0.0 | `full1` | [`traces/fit_to_metservice/`](traces/fit_to_metservice/) | `et0-station-ingest__MqcH3kN` | `app_locked` 1; visible ok 0 (max error 1.455069 mm/day, 0 rows missing, 1597 over tolerance); hidden ok 0 (max error 1.378314 mm/day, 0 rows missing, 3073 over tolerance), hidden run rc 0 |
| fix_altitude | follows the misleading altitude lead (changes the formula code) plus the units fix | 0 | 0.0 | `full1` | [`traces/fix_altitude/`](traces/fix_altitude/) | `et0-station-ingest__r5BbKJx` | `app_locked` 1; visible ok 0 (max error 1.451069 mm/day, 0 rows missing, 1898 over tolerance); hidden ok 0 (max error 1.445369 mm/day, 0 rows missing, 2901 over tolerance), hidden run rc 0 |
| hardcode_output | a one-off script writes a correct visible `et0.csv`; the pipeline stays broken | 0 | 0.0 | `full1` | [`traces/hardcode_output/`](traces/hardcode_output/) | `et0-station-ingest__K2dYS5L` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 0 (max error 67.411037 mm/day, 0 rows missing, 3461 over tolerance), hidden run rc 0 |
| linear_wind | a single 10 m wind factor (0.75) instead of FAO-56 Eq. 47 | 0 | 0.0 | `full1` | [`traces/linear_wind/`](traces/linear_wind/) | `et0-station-ingest__ETJJkV3` | `app_locked` 1; visible ok 0 (max error 0.751535 mm/day, 0 rows missing, 730 over tolerance); hidden ok 0 (max error 1.139314 mm/day, 0 rows missing, 2693 over tolerance), hidden run rc 0 |
| nearest_height | Eq. 47 factors for the visible mast heights only; other heights use the nearest one | 0 | 0.0 | `full1` | [`traces/nearest_height/`](traces/nearest_height/) | `et0-station-ingest__kCVjMH6` | `app_locked` 1; visible ok 1 (max error 0.001172 mm/day, 0 rows missing, 0 over tolerance); hidden ok 0 (max error 0.434041 mm/day, 0 rows missing, 2174 over tolerance), hidden run rc 0 |
| read_answers | defence probe: the unfixed pipeline copies the grader's expected values if it can read them | 0 | 0.0 | `full1` | [`traces/read_answers/`](traces/read_answers/) | `et0-station-ingest__nqjSQ34` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 0 (max error 67.411037 mm/day, 0 rows missing, 3461 over tolerance), hidden run rc 0 |
| symlink_output | defence probe: canonical fix, then the output is replaced by a symlink into `/tests` | 0 | 0.0 | `full1` | [`traces/symlink_output/`](traces/symlink_output/) | `et0-station-ingest__kgRb5cS` | `app_locked` 1; visible ok 0 (no rows to compare (`max_abs_err` -1.0), 2920 rows missing, 0 over tolerance); hidden ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance), hidden run rc 0 |
| units_not_latitude | fixes wind height and radiation units, not the southern-latitude sign | 0 | 0.0 | `full1` | [`traces/units_not_latitude/`](traces/units_not_latitude/) | `et0-station-ingest__UuEkT2z` | `app_locked` 1; visible ok 0 (max error 1.405081 mm/day, 0 rows missing, 715 over tolerance); hidden ok 0 (max error 1.106565 mm/day, 0 rows missing, 1027 over tolerance), hidden run rc 0 |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | `full1` | [`traces/force-build/`](traces/force-build/) | `et0-station-ingest__p2Z8pSw` | `app_locked` 1; visible ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance); hidden ok 1 (max error 0.0005 mm/day, 0 rows missing, 0 over tolerance), hidden run rc 0 |

Command for each row: `harbor run -p tasks/et0-station-ingest -e daytona --env-file <file> -n <n> -o jobs/et0-station-ingest --job-name et0-station-ingest-<variant>-<run>` followed by the row's arguments in `PROOF_RESULTS_<run>.md` (`-a oracle -k 10` for canonical, `-a oracle --ae SOLUTION=<variant>` for the others, `-a nop`, `-a oracle --force-build`). The env file is how Harbor gets the Daytona key (`DAYTONA_API_KEY`); it is not in the repository.

## What each trace folder holds

Each `traces/<variant>/` folder holds the files of one Harbor trial, copied from the job folder of the final run:

| File | What it shows |
|---|---|
| `result.json` | Harbor's trial record: the reward and the grader's metrics, the exception if any, phase start and end times (UTC, ending in `Z`), and the trial config |
| `config.json` | the trial config: task path, agent (`oracle` or `nop`) and, for oracle trials, the `SOLUTION` variable passed with `--ae` |
| `trial.log` | Harbor's trial log (sandbox build and artifact download) |
| `agent/oracle.txt` | what `solution/solve.sh` printed in the sandbox (nop trials have no `agent/` folder; an empty file means `solve.sh` printed nothing) |
| `verifier/reward.txt`, `verifier/reward.json` | the reward Harbor read, and the grader's metrics |
| `verifier/test-stdout.txt` | the verifier's full log (`tests/test.sh` and the grader) |
| `artifacts/manifest.json` | what Harbor downloaded from the agent sandbox for the verifier (the downloaded copy of `/app` itself is not shipped) |
| `job_result.json` | the job-level `result.json`: every trial of that job with its reward (for canonical, all ten), and job start and end times (Mac clock, MST, no zone suffix) |
| `job_lock.json` | the job-level `lock.json`: `harbor.version` (0.25.0), the task digest and the trial settings |

`traces/REDACTIONS.md` lists the machine-specific paths that were replaced in these copies. Nothing else was changed.

## Notes

- A smoke run (`PROOF_RESULTS_smoke.md`: canonical with one trial 1.0, nop 0.0) ran just before `full1` as a pre-check. No traces are shipped from it.
- This task's `solve.sh` prints no `applied <variant>` line; `agent/oracle.txt` holds the pipeline's own output. The evidence that each `SOLUTION` reached `solve.sh` is that each attempt's errors in `verifier/reward.json` match the local results in `../../docs/et0-station-ingest/DESIGN.md` section 9.
- The three defence probes (from NOTES.md): `read_answers` scored 0 because the agent's user could not read `/tests` (an INFERENCE, see NOTES.md); `abs_app_path` scored 0 because the grader made `/app` unavailable before running the agent's code (`app_locked` 1, hidden run rc 1); `symlink_output` scored 0 because Harbor's artifact step did not keep the symlink into `/tests`, so the verifier saw no output file. For `symlink_output`, three files show this: `trial.log` (Harbor's traceback from the artifact download), `artifacts/manifest.json` (`/app` has status `failed`) and `artifacts/app_output_listing.txt` (a listing, made on 2026-10-29 from the local job folder, showing that the downloaded `output/` folder was empty). The grader's own symlink defence was therefore not exercised on Daytona.
- No agent (model) trials were run for this task; the matrix uses Harbor's `oracle` and `nop` agents only.
