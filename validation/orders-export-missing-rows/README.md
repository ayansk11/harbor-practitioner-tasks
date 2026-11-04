# Validation: orders-export-missing-rows

Last updated: 2026-11-03, 17:29 MST (Mac clock; late edits to 20:39 MST by the file's time): the section "Agent trials"
adds run m1 of 2026-11-03 (eight `terminus-2` trials with four models, 6 of 8 pass, traces in `traces/agent-m1/`); the
summary line, the file list, the trace notes and the notes count them.
Before that, 2026-10-31 (Mac clock, MST).

**Final run: `full1`.** Harbor 0.25.0 on Daytona, 2026-10-28 from 21:26:18 to 21:37:41 (Mac clock, MST; job `result.json`). Overall: ALL AS EXPECTED (`PROOF_RESULTS_full1.md`).

**Fresh-clone run: `clone2`.** The task as published in commit `495c9f5`, run again from a fresh clone of the GitHub repository on 2026-10-30: canonical 1.0, nop 0.0, ALL AS EXPECTED (section "Fresh-clone run").

**Agent trials:** 11 trials of Harbor's `terminus-2` agent: 6 of 8 pass in run m1 of 2026-11-03 (four models), and 3 of
3 on 2026-10-30 (one model) (section "Agent trials").

## Files in this folder

- `PROOF_RESULTS_<run>.md`, `proof_results_<run>.json`, `run_<run>.log`: the proof matrix of each run, written by `tools/proof_matrix.py` (for the fresh-clone run `clone2`, the first two only).
- `traces/<variant>/`: one Harbor trial per variant of the final run (table below); `traces/agent-r3/<trial>/`: the
  three agent trials of 2026-10-30 (section "Agent trials").
- `traces/agent-m1/<trial>/`: the eight agent trials of run m1 of 2026-11-03 (section "Agent trials").
- `traces/REDACTIONS.md`: the machine-specific paths replaced in the trace copies, and the model service's URL in the agent traces' copies.
- `traces/agent-m1/REDACTIONS.md`: the same for the copies of run m1.

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

Each `traces/<variant>/` folder holds the files of one Harbor trial, copied from the job folder of the final run
(each `traces/agent-r3/<trial>/` and each `traces/agent-m1/<trial>/`, from the job folder of that agent trial):

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
`traces/agent-m1/REDACTIONS.md` lists the same for the copies of run m1.

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

Eleven trials of Harbor's `terminus-2` agent have been graded on this task, outside the proof matrix, all on the same
task package as `full1` (the task digest in each agent trace's `job_lock.json` equals the one in the other traces):
eight in run m1 of 2026-11-03 with four models (6 of 8 passed), and three with `openai/gpt-oss-120b` on 2026-10-30
(3 of 3; subsection "Earlier trials (2026-10-30)").

### Run m1 (2026-11-03)

Eight trials of Harbor 0.25.0's `terminus-2` agent: two attempts with each of four models of an OpenAI-compatible
model service (its URL is `<model-endpoint>` in the traces). The models are named as the service names them (each
`config.json` gives the name with LiteLLM's `openai/` prefix); which weights served them is UNVERIFIED. `terminus-2`
runs its loop on the machine that runs Harbor, which calls the model service, and the model's commands in the task's
Daytona sandbox. Each trial is a job of its own, `orders-export-missing-rows-terminus2-<tag>-m1-<attempt>` (`<tag>` a
short model tag such as `gemma4-31b`, `glm53flash`, `gptoss120b` or `qwen38-27b`; each `config.json` gives the job's
`trials_dir`; `n_concurrent_trials` 1 in each `job_lock.json`); the eight jobs ran from 09:25:35 to 09:59:29 (Mac
clock, MST; each `job_result.json`), up to three at a time. Agent and verifier timeouts were those of `task.toml`
(agent 1,200 s; `timeout_multiplier` 1.0), and Harbor waited up to three times its default image-build time
(`environment_build_timeout_multiplier` 3.0). Seven trials finished without an exception; `zpRJCV7` ended with
`AgentTimeoutError` and still scored 1.0 (below). Six passed: 6 of 8. The run's rows for all five tasks are in
`../agent_trials_m1.json`; [`traces/agent-m1/REDACTIONS.md`](traces/agent-m1/REDACTIONS.md) lists what was replaced
in these copies.

| Trial | Model | Attempt | Episodes | Agent seconds | Reward | What the trial's files show | Trace |
|---|---|---|---|---|---|---|---|
| `orders-export-missing-rows__tWo8AoG` | gemma-4-31B-it | 1 | 10 | 125 | 1.0 | pass: the cursor carries `created_at` and `id`, and both listings (the shared helper in `orders_service/pagination.py` and the inline copy in `orders_service/queries.py`) seek with `created_at < ? OR (created_at = ? AND id < ?)`; it reproduced the loss (47,961 rows), then exported all 48,213 | [`traces/agent-m1/orders-export-missing-rows__tWo8AoG/`](traces/agent-m1/orders-export-missing-rows__tWo8AoG/) |
| `orders-export-missing-rows__3drHTwr` | gemma-4-31B-it | 2 | 9 | 147 | 1.0 | pass: the same fix in both listings, in the same predicate form; an export of all 48,213 orders | [`traces/agent-m1/orders-export-missing-rows__3drHTwr/`](traces/agent-m1/orders-export-missing-rows__3drHTwr/) |
| `orders-export-missing-rows__wFkwALt` | glm-5.3-flash | 1 | 16 | 1066 | 1.0 | pass: a JSON cursor with the id bounded to 64 bits and the row-value seek `(created_at, id) < (?, ?)` in both listings, 7 tests added; walks of its own over a 5,000-order same-second group and with inserts, and a run as `nobody` from a copy; 905.7 s of its agent phase went to waiting for the model service | [`traces/agent-m1/orders-export-missing-rows__wFkwALt/`](traces/agent-m1/orders-export-missing-rows__wFkwALt/) |
| `orders-export-missing-rows__zpRJCV7` | glm-5.3-flash | 2 | 18 | 1200 | 1.0 | pass, with `AgentTimeoutError`: the row-value seek in both listings and a versioned cursor; its live export matched (48,213 rows, 0 missing, 0 extra) nearly 13 minutes before the 1,200 s agent timeout, after which it hardened its cursor parser and kept testing until its last logged step, 3.4 minutes before the timeout; the graded code passed every check | [`traces/agent-m1/orders-export-missing-rows__zpRJCV7/`](traces/agent-m1/orders-export-missing-rows__zpRJCV7/) |
| `orders-export-missing-rows__czEnfc8` | gpt-oss-120b | 1 | 23 | 324 | 0.0 | fail: fixed only the shared helper; it never opened `orders_service/queries.py`, `INCIDENT.md` or `docs/API.md`, so the customer listing keeps the bug, as in the shipped attempt `fix_helper_only` (its row above); `c3_customers` and `c4_inserts` fail (`failed_checks` 16) | [`traces/agent-m1/orders-export-missing-rows__czEnfc8/`](traces/agent-m1/orders-export-missing-rows__czEnfc8/) |
| `orders-export-missing-rows__TGjE5Un` | gpt-oss-120b | 2 | 14 | 197 | 0.0 | fail: it named the cause and both code paths, but no edit landed: its keystrokes held a literal `\n` where newlines belonged, the shell stayed at a continuation prompt, and it marked the task complete with `/app` unchanged; `c1_order`, `c3_customers` and `c4_inserts` fail, as in the nop trial (`failed_checks` 23) | [`traces/agent-m1/orders-export-missing-rows__TGjE5Un/`](traces/agent-m1/orders-export-missing-rows__TGjE5Un/) |
| `orders-export-missing-rows__EdiSLpb` | qwen3.8-27b | 1 | 10 | 303 | 1.0 | pass: the OR form in both listings, plus two indexes created at start-up (the instruction allows indexes); live walks of its own with new and late-synced orders inserted | [`traces/agent-m1/orders-export-missing-rows__EdiSLpb/`](traces/agent-m1/orders-export-missing-rows__EdiSLpb/) |
| `orders-export-missing-rows__2XQn2TF` | qwen3.8-27b | 2 | 15 | 440 | 1.0 | pass: the OR form in both listings; an HTTP walk of its own service on a copy of the database while a background job inserted orders: 0 missing, 0 duplicates | [`traces/agent-m1/orders-export-missing-rows__2XQn2TF/`](traces/agent-m1/orders-export-missing-rows__2XQn2TF/) |

Episodes are `n_episodes` (`agent_result.metadata`) and agent seconds the agent phase, from
`agent_execution.started_at` to `finished_at`, rounded as in `../agent_trials_m1.json`, both from each trial's
`result.json`; the `agent_seconds` field of `verifier/reward.json` is the grader's HTTP phase (6.49 to 13.24 s here),
not the agent's. The column "What the trial's files show" condenses the authors' review of the run (by model agents,
recorded outside this repository), which read every trajectory and compared each final `/app` with the package.

What run m1 shows:
- The six passes: each `verifier/reward.json` has every check at 1 and `failed_checks` 0, and each
  `verifier/test-stdout.txt` shows the eight checks passed 5, 58, 21, 14, 11, 31, 5 and 3 times (`c1_order` to
  `c7_public`, then `db`) with none failed. Each is a root-cause fix of the canonical's shape: the cursor carries
  `(created_at, id)` and both listings ask for rows strictly after that position, four in the OR form (`tWo8AoG`,
  `3drHTwr`, `EdiSLpb`, `2XQn2TF`) and two as the row value (`wFkwALt`, `zpRJCV7`); four of them also tested inserts
  during a walk of their own. Reading (INFERENCE, from each final `/app` against the task's `environment/app` and the
  trajectories): no data constant, no special case and no read of `/tests` or of the grader's files.
- The gap of the trials of 2026-10-30 (a cursor id limited to 6 digits; subsection "Earlier trials (2026-10-30)") is in
  none of the six passes: they parse the id with `isdigit()`, as a JSON integer or with a pattern of up to 18 or 20
  digits. A related corner, found by the review: in `tWo8AoG`, `3drHTwr` and `EdiSLpb`, a hand-built cursor whose id is
  2^63 or more would get 500, not the 400 that `docs/API.md` (line 36) gives for a malformed cursor, since SQLite
  cannot bind such an integer and the service's error handler (`orders_service/app.py` lines 14 to 16) answers only
  HTTP errors (INFERENCE, the review's, from the code and the library's behaviour; not run against a service). The
  grader's two bad cursors (`tests/grade.py` line 47) fail before any id is parsed, so it does not test this; clients
  never build cursors, and no pass relied on it (`../../docs/orders-export-missing-rows/DESIGN.md` section 9).
- The OR form is correct but slower. The review's query plans (on the Mac's SQLite) show it scanning the index rather
  than seeking into it, so a page costs more the deeper it is, the cost that keyset paging was adopted to remove
  (`orders_service/pagination.py` lines 3 to 5). The grader's walk of `/orders` at limit 50 (601 pages; line 14 of
  each `verifier/test-stdout.txt`) took 2.42 to 3.01 s in the four OR-form passes and 1.10 and 1.12 s in the two
  row-value passes. The design accepts slow but correct fixes (`../../docs/orders-export-missing-rows/DESIGN.md`
  sections 5, 7 and 8).
- The two failures (`gpt-oss-120b`): `czEnfc8` fails as the shipped attempt `fix_helper_only` does (same checks,
  `failed_checks` 16). Its first failure, `/customers/6/orders limit=3: 18 orders (18 distinct) for 413 expected`, is
  that attempt's first failure in the local matrix (`../../docs/orders-export-missing-rows/DESIGN.md` section 7), and
  its `orders_service/queries.py` is the shipped file byte for byte, although `INCIDENT.md` and the instruction both
  speak of every listing that pages. The kit removed the `sitecustomize.py` it had added
  (`removed 1 auto-run entries` in its `verifier/test-stdout.txt`).
  `TGjE5Un` diagnosed both code paths (its step 6) but left `/app` as shipped, so its failures are the original
  service's (the nop row above). Reading (INFERENCE, from these files): both are capability gaps (reading every
  listing, landing an edit and checking it), not a task defect. Over both runs `gpt-oss-120b` has passed 3 of 5 trials
  of this task.
- `zpRJCV7` reached the 1,200 s agent timeout: Harbor recorded `AgentTimeoutError` in its `result.json` and counts the
  trial as errored (`n_errored_trials` 1 in its `job_result.json`); its model call in flight had an HTTP 429 answer
  from the model service and was being retried. The artifacts were then collected and graded, and every check passed
  (reward 1.0). It is counted as a pass here, since the verifier graded the work the agent left; a harness that counts
  every `AgentTimeoutError` as an error would not count it (INFERENCE). Both `glm-5.3-flash` trials spent most of their
  long agent phases waiting for the model service (905.7 s in `wFkwALt`, 784.7 s in `zpRJCV7`).
- Reading (INFERENCE, from these counts): the task is easy for `gemma-4-31B-it`, `glm-5.3-flash` and `qwen3.8-27b`
  (6 of 6). All eight trials named the cause by their fourth to sixth step (`step_id` in `agent/trajectory.json`, where
  step 1 is the task prompt); what decided the outcomes was reading every listing, landing an edit and checking it.
  Over the 11 graded `terminus-2` trials, 9 passed (`gpt-oss-120b` 3 of 5). The same three models passed the four
  tasks other than `feature-leakage-churn` in 23 of 24 attempts (`../agent_trials_m1.json`). `task.toml` labels the
  task `easy`, which these counts bear out; two attempts per model are counts, not pass rates, and a low pass rate is
  not the goal in itself.
- A harness note: Harbor 0.25.0's `terminus-2` cuts each long observation twice, so the size its marker reports
  understates what was cut (`_limit_output_length` in `harbor/agents/terminus_2/terminus_2.py`). The review found no
  cut observation in this task's two failing trials; no verdict depends on it.

Network: this task's `task.toml` sets no network line, so the trials ran with Harbor 0.25.0's default public network,
long after this repository became public, and a fetch of the public hidden tests was possible. The agent's loop ran on
the machine that runs Harbor and called the model service from there; only the model's commands ran in the sandbox.
Every trajectory, terminal pane and recording was read for network use: every URL in a command is
`http://127.0.0.1:<port>`, where the agents ran the task's service; `curl` is not in the image; no `pip`, `apt`,
`wget`, `nc` or `ssh` command ran, and the local `git status` and `git diff` of the two `glm-5.3-flash` trials printed
nothing (their errors were sent to `/dev/null`). Other host names appear only as text: `orders-api.internal` on
line 1 of the shipped `logs/export-2026-10-27.log`, and customer e-mail addresses in the data and the tests. No GitHub
host (`github.com`, `*.github.com`, `*.githubusercontent.com`) and neither the repository's nor its owner's name
appears in any of them. No command read `/tests`, `/logs/verifier` or the hidden data. No trial was excluded.

### Earlier trials (2026-10-30)

Three trials ran on 2026-10-30, before run m1: Harbor's `terminus-2` agent with the model `openai/gpt-oss-120b`,
served by an OpenAI-compatible model service (its URL is `<model-endpoint>` in the traces), on Daytona and on the
same task package as `full1` (the task digest in each agent trace's `job_lock.json` equals the one in the other
traces). They are one job, `orders-export-missing-rows-terminus2-gptoss-r3` (`-k 3`, two trials at a time, from
07:20:37 to 07:27:12, Mac clock, MST; job `result.json`); agent and verifier timeouts were those of
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
- There is no NOTES.md for this task: the proof run `full1` had no exception and nothing unexpected.
- Eleven agent (model) trials were graded for this task, outside the matrix: three on 2026-10-30 and eight in run m1 of
  2026-11-03 (section "Agent trials"); the matrix uses Harbor's `oracle` and `nop` agents only.
