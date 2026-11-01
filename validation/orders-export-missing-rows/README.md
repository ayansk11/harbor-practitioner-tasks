# Validation: orders-export-missing-rows

Last updated: 2026-10-31 (Mac clock, MST).

**Final run: `full1`.** Harbor 0.25.0 on Daytona, 2026-10-28 from 21:26:18 to 21:37:41 (Mac clock, MST; job `result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full1.md`).

**Fresh-clone run: `clone2`.** The task as published in commit `495c9f5`, run again from a fresh clone of the GitHub repository on 2026-10-30: canonical 1.0, nop 0.0, ALL AS EXPECTED (section "Fresh-clone run").

**Agent trials:** three trials of one model agent, 3 of 3 pass (section "Agent trials").

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py` (for the fresh-clone run `clone2`, the first two only).
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below); `traces/agent-r3/<trial>/`: the agent trials (section "Agent trials").
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies, and the model service's URL in the agent traces' copies.

The "Job folder" column of the `PROOF_RESULTS_*.md` files points into `jobs/`, the raw Harbor output (for `clone2`, the `jobs/` folder of the fresh clone). `jobs/` is git-ignored and not part of the repository; the trace folders below are the shipped copy.

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

Each `traces/<variant>/` folder holds the files of one Harbor trial, copied from the job folder of the final run (each `traces/agent-r3/<trial>/`, from the job folder of the agent trials):

| File | What it shows |
|---|---|
| `result.json` | Harbor's trial record: the reward and the grader's metrics, the exception if any, phase start and end times (UTC, ending in `Z`), and the trial config |
| `config.json` | the trial config: task path, agent (`oracle` or `nop`; `terminus-2` and its model for the agent traces) and, for oracle trials, the `SOLUTION` variable passed with `--ae` |
| `trial.log` | Harbor's trial log (sandbox build and artifact download; in the agent traces also the agent's trajectory saves and parser warnings) |
| `agent/oracle.txt` | what `solution/solve.sh` printed in the sandbox (nop trials have no `agent/` folder; an empty file means `solve.sh` printed nothing; the agent traces have no `oracle.txt`: their `agent/` holds `trajectory.json`, `terminus_2.pane` and `recording.cast`) |
| `verifier/reward.txt`, `verifier/reward.json` | the reward Harbor read, and the grader's metrics |
| `verifier/test-stdout.txt` | the verifier's full log (`tests/test.sh` and the grader) |
| `artifacts/manifest.json` | what Harbor downloaded from the agent sandbox for the verifier (the downloaded copy of `/app` itself is not shipped) |
| `job_result.json` | the job-level `result.json`: every trial of that job with its reward (for canonical, all ten), and job start and end times (Mac clock, MST, no zone suffix) |
| `job_lock.json` | the job-level `lock.json`: `harbor.version` (0.25.0), the task digest and the trial settings |

`traces/REDACTIONS.md` lists the machine-specific paths that were replaced in these copies, and the model service's URL in `traces/agent-r3/`. Nothing else was changed.

## Fresh-clone run

Run `clone2` ([`PROOF_RESULTS_clone2.md`](PROOF_RESULTS_clone2.md), `proof_results_clone2.json`) checks the published
package. On 2026-10-30 this repository was cloned from GitHub at commit `495c9f5` (06:18, Mac clock, MST), and
`tools/proof_matrix.py` ran this task from the clone on Daytona with Harbor 0.25.0, from 07:02:39 to 07:04:34 (Mac clock,
MST): canonical once (`-a oracle -k 1`) and nop once (`-a nop`), one trial at a time. Rewards: canonical [1.0], nop
[0.0]; overall ALL AS EXPECTED. The task digest in both jobs' `lock.json` is the one in this folder's `job_lock.json`
files (`sha256:d16414cd57bcc2c9f8e1e7bbe57bc688183d5f448a0bdca199b721edbd6a64a1`), so the clone graded the same package
as `full1`. Harbor waited up to three times its default image-build time (`--environment-build-timeout-multiplier 3`)
because Daytona's status page reported degraded performance for a subset of US runners that morning; task, agent and
verifier timeouts were those of `task.toml`. Only the two results files are shipped from this run (no traces, no run
log).

## Agent trials

Three trials of a model agent have run on this task, outside the proof matrix, on 2026-10-30: Harbor's `terminus-2`
agent with the model `openai/gpt-oss-120b`, served by an OpenAI-compatible model service (its URL is `<model-endpoint>`
in the traces), on Daytona and on the same task package as `full1` (the task digest in each agent trace's
`job_lock.json` equals the one in the other traces). They are one job, `orders-export-missing-rows-terminus2-gptoss-r3` (`-k 3`, two trials at a
time, from 07:20:37 to 07:27:12, Mac clock, MST; job `result.json`); agent and verifier timeouts were those of
`task.toml` (agent 1,200 s), and Harbor waited up to three times its default image-build time
(`--environment-build-timeout-multiplier 3`). Every trial finished without an exception (`result.json`). All three
passed: 3 of 3.

| Trial | Episodes | Agent phase | Reward | What the trial's files show | Trace |
|---|---|---|---|---|---|
| `orders-export-missing-rows__Ro8uMJk` | 8 | 120 s | 1.0 | the cursor carries `(created_at, id)`, and both listings (the shared helper in `orders_service/pagination.py` and the inline copy in `orders_service/queries.py`) ask for rows strictly after that position, as `created_at < ? OR (created_at = ? AND id < ?)`; checked with the 14 visible tests and a full walk of its own service on `127.0.0.1` over the development data (48,213 orders, equal to `/orders/count`) | [`traces/agent-r3/orders-export-missing-rows__Ro8uMJk/`](traces/agent-r3/orders-export-missing-rows__Ro8uMJk/) |
| `orders-export-missing-rows__8QFnJgD` | 22 | 349 s | 1.0 | the same fix in both listings, with the same predicate form; checked with the 14 visible tests only | [`traces/agent-r3/orders-export-missing-rows__8QFnJgD/`](traces/agent-r3/orders-export-missing-rows__8QFnJgD/) |
| `orders-export-missing-rows__jmkPRP3` | 16 | 198 s | 1.0 | the same fix in both listings, as the row-value comparison `(created_at, id) < (?, ?)`; checked with the 14 visible tests only | [`traces/agent-r3/orders-export-missing-rows__jmkPRP3/`](traces/agent-r3/orders-export-missing-rows__jmkPRP3/) |

Episodes are `n_episodes` and the agent phase runs from `agent_execution.started_at` to `finished_at`, both in each
trial's `result.json`.

What the trials show:
- Each pass satisfies all eight checks (`c1_order_ok` to `c7_public_ok` and `db_ok` 1, `failed_checks` 0;
  `verifier/reward.json`). Reading (INFERENCE, from each trial's final code against the task's `environment/app` and
  its commands): each is a root-cause fix of both code paths, with no data constant, no special case and no read of the
  grader's files. The 14 visible tests pass on the unfixed code too
  (`../../docs/orders-export-missing-rows/DESIGN.md` section 2), so `8QFnJgD` and `jmkPRP3` ran no check that could
  fail on the bug.
- `task.toml` labels the task `easy`, and `../../docs/orders-export-missing-rows/DESIGN.md` section 9 expects strong
  agents to pass, so 3 of 3 fits; three trials of one agent and one model are not a pass rate.
- A gap in the verifier's coverage, found in these trials: all three fixes parse the id in the cursor with the
  1-to-6-digit pattern that the shipped code uses for `limit` (`_DIGITS` in `orders_service/pagination.py`), so a page
  that ends on an order whose id is 1,000,000 or more yields a cursor these services refuse with 400 "invalid cursor";
  the canonical fix accepts up to 18 digits. No order in the hidden database (ids 1 to 30,000) or among the 56 orders inserted
  during the walks (ids 30,001 to 30,056) has such an id, so the verifier does not test it. `docs/API.md` gives the id
  as an integer with no upper bound, and the instruction asks not to depend on the ids of the development data.

Network: this task's `task.toml` sets no `network_mode`, so the trials ran with Harbor 0.25.0's default public network.
They started at 14:20 UTC on 2026-10-30, after this repository was created on GitHub (07:08 UTC the same day), and the
Daytona account of these runs is on Tier 1, which keeps GitHub reachable (repository README, "Known limitations"), so a
fetch of the public hidden tests was possible. Every trajectory, terminal pane and recording was read for one: no GitHub
host (`github.com`, `*.github.com`, `*.githubusercontent.com`) and neither the repository's nor its owner's name appears
in any of them. The only network use in any command was trial `Ro8uMJk`'s HTTP requests to `127.0.0.1`, where that
agent had started the task's own service. No trial was excluded.

## Notes

- Every oracle trial's `agent/oracle.txt` says `applied <variant> to /app` (`applied canonical to /app` for the canonical and force-build rows), so the `SOLUTION` variable reached `solve.sh` on Daytona.
- The three attempts that an earlier version of the grader let through (`tie_offset`, `rank_from_bottom`, `customer_offset`) fail only `c4_inserts`, the check of orders inserted during a walk; `rewrite_timestamps_at_startup` fails `c4_inserts` and `db`. Design and local results: `../../docs/orders-export-missing-rows/DESIGN.md` sections 5, 7 and 12.
- There is no NOTES.md for this task: the run had no exception and nothing unexpected.
- Three agent (model) trials were run for this task, outside the matrix (section "Agent trials"); the matrix uses Harbor's `oracle` and `nop` agents only.
