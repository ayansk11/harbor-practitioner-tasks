# Validation: orders-export-missing-rows

Last updated: 2026-10-29 (Mac clock, MST).

**Final run: `full1`.** Harbor 0.25.0 on Daytona, 2026-10-28 from 21:26:18 to 21:37:41 (Mac clock, MST; job `result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full1.md`).

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py`.
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below).
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies.

The "Job folder" column of the `PROOF_RESULTS_*.md` files points into `jobs/`, the raw Harbor output. `jobs/` is git-ignored and not part of the repository; the trace folders below are the shipped copy.

## Results and traces

One trial per variant is shipped. Variants with one trial ship that trial. For canonical (ten trials) the shipped trial is the one with the earliest `started_at` in its `result.json`; its `job_result.json` holds the rewards of all ten. The last column is read from the shipped trial's `verifier/reward.json`.

| Variant | What it is | Expected | Rewards (all trials of the job) | Run | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|---|
| canonical | reference fix: the cursor carries the full sort key (created_at, id); one shared keyset clause serves both listings | 1 | 10 of 10 = 1.0 | `full1` | [`traces/canonical/`](traces/canonical/) | `orders-export-missing-rows__XxnEpQc` | all checks pass; `agent_seconds` 5.54 |
| alt | a different valid fix: the cursor is the last order's id; each route writes its own expanded predicate; pages fetched with limit + 1 | 1 | 1.0 | `full1` | [`traces/alt/`](traces/alt/) | `orders-export-missing-rows__FVr6t4i` | all checks pass; `agent_seconds` 5.22 |
| nop | Harbor's nop agent: the shipped bug is left as it is | 0 | 0.0 | `full1` | [`traces/nop/`](traces/nop/) | `orders-export-missing-rows__ZsQzywo` | fails `c1_order`, `c3_customers`, `c4_inserts`; `agent_seconds` 4.14 |
| and_predicate | cursor (created_at, id) but `created_at <= ? AND id < ?`: drops backfilled orders | 0 | 0.0 | `full1` | [`traces/and_predicate/`](traces/and_predicate/) | `orders-export-missing-rows__Nt6QLkH` | fails `c1_order`, `c3_customers`, `c4_inserts`; `agent_seconds` 7.74 |
| customer_offset | `/orders` fixed; the customer listing pages with LIMIT/OFFSET inside an opaque cursor | 0 | 0.0 | `full1` | [`traces/customer_offset/`](traces/customer_offset/) | `orders-export-missing-rows__fhtFEef` | fails `c4_inserts`; `agent_seconds` 8.05 |
| fix_helper_only | fixes the shared helper only; the inline copy of the bug in the customer listing stays | 0 | 0.0 | `full1` | [`traces/fix_helper_only/`](traces/fix_helper_only/) | `orders-export-missing-rows__Ffhf2tS` | fails `c3_customers`, `c4_inserts`; `agent_seconds` 7.5 |
| ignore_limit | returns every remaining order in one page with a null cursor | 0 | 0.0 | `full1` | [`traces/ignore_limit/`](traces/ignore_limit/) | `orders-export-missing-rows__HkTyYD8` | fails `c1_order`, `c2_pages`, `c3_customers`, `c4_inserts`, `c7_public`; `agent_seconds` 1.54 |
| lte_cursor | `<=` instead of `<` in both listings: repeats rows, loops on large same-second groups | 0 | 0.0 | `full1` | [`traces/lte_cursor/`](traces/lte_cursor/) | `orders-export-missing-rows__7b2uE7m` | fails `c1_order`, `c2_pages`, `c3_customers`, `c4_inserts`; `agent_seconds` 0.64 |
| offset_cursor | LIMIT/OFFSET inside an opaque cursor: rows shift when orders are inserted | 0 | 0.0 | `full1` | [`traces/offset_cursor/`](traces/offset_cursor/) | `orders-export-missing-rows__BjNNXV3` | fails `c4_inserts`; `agent_seconds` 8.24 |
| order_by_id | keyset on id alone: complete, but not in the documented order | 0 | 0.0 | `full1` | [`traces/order_by_id/`](traces/order_by_id/) | `orders-export-missing-rows__9QffFyX` | fails `c1_order`, `c3_customers`, `c4_inserts`, `c7_public`; `agent_seconds` 5.81 |
| rank_from_bottom | cursor = number of older orders, pages read from the oldest end with OFFSET | 0 | 0.0 | `full1` | [`traces/rank_from_bottom/`](traces/rank_from_bottom/) | `orders-export-missing-rows__dNFUMzv` | fails `c4_inserts`; `agent_seconds` 10.84 |
| rewrite_timestamps_at_startup | rewrites stored created_at values at start-up so the old cursor stops skipping | 0 | 0.0 | `full1` | [`traces/rewrite_timestamps_at_startup/`](traces/rewrite_timestamps_at_startup/) | `orders-export-missing-rows__4kUTUxx` | fails `c4_inserts`, `db`; `agent_seconds` 5.46 |
| snapshot_at_startup | serves a correct snapshot loaded at start-up: new orders never appear | 0 | 0.0 | `full1` | [`traces/snapshot_at_startup/`](traces/snapshot_at_startup/) | `orders-export-missing-rows__GzNoNNN` | fails `c4_inserts`; `agent_seconds` 3.56 |
| tie_offset | cursor = last created_at plus a count of rows already served in that second, with OFFSET | 0 | 0.0 | `full1` | [`traces/tie_offset/`](traces/tie_offset/) | `orders-export-missing-rows__K3uUmMx` | fails `c4_inserts`; `agent_seconds` 5.17 |
| unique_timestamps_dev_db | edits the development database only; code unchanged | 0 | 0.0 | `full1` | [`traces/unique_timestamps_dev_db/`](traces/unique_timestamps_dev_db/) | `orders-export-missing-rows__scvdEut` | fails `c1_order`, `c3_customers`, `c4_inserts`; `agent_seconds` 5.8 |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | `full1` | [`traces/force-build/`](traces/force-build/) | `orders-export-missing-rows__eRMKKFa` | all checks pass; `agent_seconds` 5.09 |

Command for each row: `harbor run -p tasks/orders-export-missing-rows -e daytona --env-file <file> -n <n> -o jobs/orders-export-missing-rows --job-name orders-export-missing-rows-<variant>-<run>` followed by the row's arguments in `PROOF_RESULTS_<run>.md` (`-a oracle -k 10` for canonical, `-a oracle --ae SOLUTION=<variant>` for the others, `-a nop`, `-a oracle --force-build`). The env file is how Harbor gets the Daytona key (`DAYTONA_API_KEY`); it is not in the repository.

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

- Every oracle trial's `agent/oracle.txt` says `applied <variant> to /app` (`applied canonical to /app` for the canonical and force-build rows), so the `SOLUTION` variable reached `solve.sh` on Daytona.
- The three attempts that an earlier version of the grader let through (`tie_offset`, `rank_from_bottom`, `customer_offset`) fail only `c4_inserts`, the check of orders inserted during a walk; `rewrite_timestamps_at_startup` fails `c4_inserts` and `db`. Design and local results: `../../docs/orders-export-missing-rows/DESIGN.md` sections 5, 7 and 12.
- There is no NOTES.md for this task: the run had no exception and nothing unexpected.
- No agent (model) trials were run for this task; the matrix uses Harbor's `oracle` and `nop` agents only.
