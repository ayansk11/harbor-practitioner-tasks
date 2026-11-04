# Validation: ab-test-reanalysis

Last updated: 2026-11-04, 00:45 MST (Mac clock): run m1's models are called four models of an OpenAI-compatible model
service, no longer "open" ones, since which weights served them is not verified (the head of 2026-11-03 below is edited
to match), and the section "Run m1" is renamed; its network note names the `git rev-parse` check that ran in `/app` (no
`git status` ran) and the authors' Daytona Tier 1 account.
Before that, 2026-11-03, 17:44 MST (Mac clock; late edits to 21:15 MST by the file's time): run m1 recorded: eight
trials of Harbor's `terminus-2` agent with four models of an OpenAI-compatible model service, 5 of 8 passed (section
"Agent trials", traces in `traces/agent-m1/`).
Before that, 2026-11-02, 17:05 MST (Mac clock): the note on `agent/oracle.txt` under "What the proof shows"
corrected (three of the 14 oracle trials print no full readout), after a verification of the published commit.
Before that, 2026-10-31, 23:03 MST (Mac clock): fixes after a pre-commit check: Daytona Tier 2 marked as not tried.
Before that, 2026-10-31, 15:01 MST (Mac clock): wording fixed after an independent check (the expected failure of the
shipped package on Daytona Tier 1 and the 4 GiB figure marked INFERENCE, the Claude Code trace folders' file list, the
first version's evidence in `first-version/`).
Before that, 2026-10-31, 13:50 MST: rewritten for the revised task (the Daytona proof `rev1`, three Claude Code trials,
and the first version's evidence moved to `first-version/`).
Before that, 2026-10-29 (Mac clock, MST): the first version's proof run `full2`.

**Final run: `rev1`.** Harbor 0.25.0 on Daytona, 2026-10-31 from 01:37:54 to 01:51:53 (Mac clock, MST; the first row's `started` in `proof_results_rev1.json`, and the time the run's three files were written; in the shipped traces, the canonical job's `started_at` is 01:37:56 and the force-build job's `finished_at` 01:51:51, each in `job_result.json`). Overall: ALL AS EXPECTED, 15 variants and 24 trials (`PROOF_RESULTS_rev1.md`).

The proof ran a copy of the package without its `[agent] network_mode = "no-network"` line, made by `tools/proof_matrix.py --without-agent-network-line`. The shipped `task.toml` denies the agent network, and Daytona Tier 1 (the authors' account) refuses Harbor's runtime network switch for the agent phase, so a trial of the shipped package is expected to fail there (INFERENCE from the network canary of 2026-10-30 and Harbor's code; design record, `../../docs/ab-test-reanalysis/DESIGN.md` section 11.1). The copy differs from the shipped package in that one line only: `diff -rq` of the two lists `task.toml` only, both have the same 75 files, and their Harbor 0.25.0 content hashes differ only because `task.toml` differs (shipped package `sha256:22e61147a38e16acd0ac2eec4e34a45ef814b205ee0cc93bd51fd69aadf2008c`; proof copy `sha256:0fc5d05c8334f99bb7ef36ca1929d1f9330f0d74799be756ad8c8ff2ae59837c`, the digest in each trace's `job_lock.json`).

## Files in this folder

- `PROOF_RESULTS_rev1.md`, `proof_results_rev1.json`, `run_rev1.log`: the proof matrix of run `rev1`, written by `tools/proof_matrix.py` (`run_rev1.log` is its console output).
- `traces/<variant>/`: one Harbor trial per variant of run `rev1` (table below).
- `traces/agent-claude-code/<trial>/`: the three Claude Code trials (section "Agent trials").
- `traces/agent-m1/<trial>/`: the eight trials of run m1, Harbor's `terminus-2` agent with four models of an
  OpenAI-compatible model service (section "Agent trials"); the results of the whole run, all five tasks, are in
  `../agent_trials_m1.json`.
- `first-version/`: the evidence of the task's first version (section "First version").

Each traces folder carries a `REDACTIONS.md` that lists what was replaced in its copies: `traces/REDACTIONS.md` for the
proof and Claude Code traces, `traces/agent-m1/REDACTIONS.md` for run m1's and `first-version/traces/REDACTIONS.md` for
the first version's; no reward, count or timing was changed. The "Job folder" column of `PROOF_RESULTS_rev1.md` points
into `jobs/`, the raw Harbor output, which is git-ignored and not part of the repository; the trace folders are the
shipped copy.

## Results and traces (run `rev1`)

One trial per variant is shipped. For canonical (ten trials) the shipped trial is the one with the earliest `started_at` in its `result.json`; its `job_result.json` holds the rewards of all ten. The last column is read from the shipped trial's `verifier/reward.json` and, for the names of the failing fields, its `verifier/test-stdout.txt`: for each failing readout, the number of problems and the fields (`.A` and `.B` are the arms; a CI error is the larger of the two bound errors, in half-widths (hw) of the reference interval, rounded to three decimals; exact values in the files). H1 to H3 are the task's three hidden issues (design record, section 1.2): H1 the export's `clicked` flag is not the plan's click, H2 the bot filter is driven by the variant, H3 hand-assigned accounts are in the experiment.

| Variant | What it is | Expected | Rewards (all trials of the job) | Trace folder | Trial | What the trace's `reward.json` shows |
|---|---|---|---|---|---|---|
| canonical | the reference fix: `method = hash` only; users with a `ua_crawler` row out of both arms; a counted pageview is clicked when it has an `item:` event; delta-method CI; SRM chi-square; the plan's decision | 1 | 10 of 10 = 1.0 | [`traces/canonical/`](traces/canonical/) | `ab-test-reanalysis__AmMY4P5` | `sets_passed` 6 of 6 |
| alt_recount | a different valid route: stdlib csv, gzip and `datetime` with numpy sums; `ua_crawler` plus the velocity rule recounted on `item:` events; CR1 interval clustered by user | 1 | 1.0 | [`traces/alt_recount/`](traces/alt_recount/) | `ab-test-reanalysis__nnPUJe9` | `sets_passed` 6 of 6 |
| alt_time | a different valid route: hash users with no flag of any rule at or before `assigned_at`; user bootstrap within each arm, 5,000 resamples, fixed seed | 1 | 1.0 | [`traces/alt_time/`](traces/alt_time/) | `ab-test-reanalysis__KeEfSE8` | `sets_passed` 6 of 6 |
| nop | Harbor's nop agent: the shipped code and its `"invalid"` readout | 0 | 0.0 | [`traces/nop/`](traces/nop/) | `ab-test-reanalysis__cVyb3mz` | `sets_passed` 0 of 6; visible: 11 (n_users.B, pageviews.B, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, srm_flag, ci_95 (0.266 hw), decision); h_null: 11 (n_users.A, pageviews.A, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, srm_flag, ci_95 (1.477 hw), decision); h_pos: 11 (n_users.B, pageviews.B, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, srm_flag, ci_95 (1.186 hw), decision); h_srm: 9 (n_users.B, pageviews.B, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, ci_95 (1.919 hw)); h_plain: 5 (clicks.A, clicks.B, ctr.A, ctr.B, diff); h_neg: 11 (n_users.B, pageviews.B, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, srm_flag, ci_95 (2.023 hw), decision) |
| b_only_patch | an instance patch for EXP-2291: H1 and H2 fixed in arm B only, the hand-assigned accounts out | 0 | 0.0 | [`traces/b_only_patch/`](traces/b_only_patch/) | `ab-test-reanalysis__pYFgpHq` | `sets_passed` 0 of 6; visible: 4 (clicks.A, ctr.A, diff, ci_95 (0.460 hw)); h_null: 9 (n_users.A, pageviews.A, clicks.A, ctr.A, diff, srm_p, srm_flag, ci_95 (1.162 hw), decision); h_pos: 4 (clicks.A, ctr.A, diff, ci_95 (0.378 hw)); h_srm: 4 (clicks.A, ctr.A, diff, ci_95 (0.447 hw)); h_plain: 4 (clicks.A, ctr.A, diff, ci_95 (0.399 hw)); h_neg: 4 (clicks.A, ctr.A, diff, ci_95 (0.472 hw)) |
| fix_visible_only | the shipped pipeline kept; a one-off script writes the right visible readout | 0 | 0.0 | [`traces/fix_visible_only/`](traces/fix_visible_only/) | `ab-test-reanalysis__maqR5DD` | `sets_passed` 1 of 6; h_null: 11 (n_users.A, pageviews.A, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, srm_flag, ci_95 (1.477 hw), decision); h_pos: 11 (n_users.B, pageviews.B, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, srm_flag, ci_95 (1.186 hw), decision); h_srm: 9 (n_users.B, pageviews.B, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, ci_95 (1.919 hw)); h_plain: 5 (clicks.A, clicks.B, ctr.A, ctr.B, diff); h_neg: 11 (n_users.B, pageviews.B, clicks.A, clicks.B, ctr.A, ctr.B, diff, srm_p, srm_flag, ci_95 (2.023 hw), decision) |
| hardcode_no_ship | the canonical numbers with the decision always `no_ship` | 0 | 0.0 | [`traces/hardcode_no_ship/`](traces/hardcode_no_ship/) | `ab-test-reanalysis__CStDb4c` | `sets_passed` 3 of 6; h_pos: 1 (decision); h_srm: 1 (decision); h_plain: 1 (decision) |
| item_click_events | a pageview's clicks = its number of `item:` events, not 1 | 0 | 0.0 | [`traces/item_click_events/`](traces/item_click_events/) | `ab-test-reanalysis__V284eFD` | `sets_passed` 0 of 6; each of the six readouts: 5 (clicks.A, clicks.B, ctr.A, ctr.B, diff) |
| keep_overrides | H1 and H2 fixed; the hand-assigned accounts stay | 0 | 0.0 | [`traces/keep_overrides/`](traces/keep_overrides/) | `ab-test-reanalysis__RQGzZns` | `sets_passed` 3 of 6; visible: 8 (n_users.B, pageviews.B, clicks.B, ctr.B, diff, srm_p, ci_95 (1.133 hw), decision); h_null: 6 (n_users.A, pageviews.A, clicks.A, ctr.A, diff, srm_p); h_srm: 9 (n_users.B, pageviews.B, clicks.B, ctr.B, diff, srm_p, srm_flag, ci_95 (0.610 hw), decision) |
| literal_bot_filter | H1 and H3 fixed; every flagged user out, as the shipped code does | 0 | 0.0 | [`traces/literal_bot_filter/`](traces/literal_bot_filter/) | `ab-test-reanalysis__uoXhhsh` | `sets_passed` 1 of 6; visible: 9 (n_users.B, pageviews.B, clicks.B, ctr.B, diff, srm_p, srm_flag, ci_95 (1.146 hw), decision); h_null: 9 (n_users.A, pageviews.A, clicks.A, ctr.A, diff, srm_p, srm_flag, ci_95 (1.417 hw), decision); h_pos: 9 (n_users.B, pageviews.B, clicks.B, ctr.B, diff, srm_p, srm_flag, ci_95 (1.226 hw), decision); h_srm: 7 (n_users.B, pageviews.B, clicks.B, ctr.B, diff, srm_p, ci_95 (1.367 hw)); h_neg: 9 (n_users.B, pageviews.B, clicks.B, ctr.B, diff, srm_p, srm_flag, ci_95 (2.228 hw), decision) |
| no_bot_filter | the bot filter dropped because it "made" the SRM; crawlers counted | 0 | 0.0 | [`traces/no_bot_filter/`](traces/no_bot_filter/) | `ab-test-reanalysis__ApQdPB3` | `sets_passed` 0 of 6; visible, h_null, h_pos, h_srm and h_neg: 10 each (n_users, pageviews, clicks and ctr of both arms, diff, srm_p); h_plain: 11 (the same and ci_95 (0.472 hw)) |
| not_nav_clicked | clicked = any event whose target is not `nav:` ("See all" counted) | 0 | 0.0 | [`traces/not_nav_clicked/`](traces/not_nav_clicked/) | `ab-test-reanalysis__UJkrupV` | `sets_passed` 0 of 6; each of the six readouts: 5 (clicks.A, clicks.B, ctr.A, ctr.B, diff) |
| pageview_ci | every count right, but the two-proportion interval on pageviews | 0 | 0.0 | [`traces/pageview_ci/`](traces/pageview_ci/) | `ab-test-reanalysis__GooJ6XL` | `sets_passed` 0 of 6; visible: 1 (ci_95 (0.614 hw)); h_null: 1 (ci_95 (0.771 hw)); h_pos: 1 (ci_95 (0.633 hw)); h_srm: 1 (ci_95 (0.625 hw)); h_plain: 1 (ci_95 (0.604 hw)); h_neg: 1 (ci_95 (0.633 hw)) |
| platform_clicked | H2 and H3 fixed; the click stays `pageviews.clicked` | 0 | 0.0 | [`traces/platform_clicked/`](traces/platform_clicked/) | `ab-test-reanalysis__kVasg8M` | `sets_passed` 0 of 6; visible: 7 (clicks.A, clicks.B, ctr.A, ctr.B, diff, ci_95 (1.190 hw), decision); h_null: 6 (clicks.A, clicks.B, ctr.A, ctr.B, diff, ci_95 (0.499 hw)); h_pos: 6 (the same, ci_95 (0.779 hw)); h_srm: 6 (the same, ci_95 (1.005 hw)); h_plain: 5 (clicks.A, clicks.B, ctr.A, ctr.B, diff); h_neg: 6 (the same as h_null, ci_95 (2.323 hw)) |
| force-build | the canonical solution again, with the images rebuilt (`--force-build`) | 1 | 1.0 | [`traces/force-build/`](traces/force-build/) | `ab-test-reanalysis__JEHP63t` | `sets_passed` 6 of 6 |

## What the proof shows

Read in all 24 trials of the run (each trial's `verifier/reward.json` and `verifier/test-stdout.txt`):

- The verifier's privilege steps: each `verifier/test-stdout.txt` starts with the same lock line, `[test.sh] lock ok: /logs/verifier 0:0 755, /logs 0:0 755, owner before 0:0; protected_symlinks=1 protected_hardlinks=1 protected_regular=2; setid files left: 0`, and its last line reports the reward with `killed 0 runner processes`.
- The answer key: `[kit] SHA256SUMS: 26 files verified (20 hidden inputs, 6 expected readouts)` in every trial.
- Network isolation of the graded runs: `[kit] network isolation: ON (private namespace, loopback only)` before the first hidden run, and each of the 120 hidden runs (5 per trial) logged `rc=0 timed_out=False` and `net=private strays_killed=0`.
- The verifier's limits: `res_cgroup_cpus=1` and `res_cgroup_mem_mib=2048` in every trial, as `task.toml` sets (`[verifier.environment]`, 1 CPU and 2,048 MB); `res_os_cpu_count=48` is the host's count, not the limit.
- Times: the slowest hidden run took 2.731 s (`alt_time` on h_null) against the 120 s cap per run; the verifier phases took 14.9 to 44.2 s against the 1,000 s verifier timeout.
- The attempts: each 0-expected trial exited 0 on all five hidden runs and failed exactly the sets of the local matrix, with the same problem counts (design record, section 9; `authoring/ab-test-reanalysis/local_results.json`, image mode).
- `agent/oracle.txt` shows what `solution/solve.sh` printed: for canonical, force-build and nine of the ten attempts,
  the readout it wrote for the visible export (`decision`, `diff`, `ci`, `srm_p`); canonical wrote
  `decision=no_ship diff=+0.00096 ci=[-0.00432, +0.00624] srm_p=0.469`. `alt_recount` and `alt_time` print
  `decision=no_ship` only, and `fix_visible_only` prints a note that a one-off script rewrote `output/result.json`
  and the pipeline is unchanged. The nop trial writes no `agent/oracle.txt`.

## How to reproduce

From the repository root, with Harbor 0.25.0 on `PATH`:

    python tools/proof_matrix.py ab-test-reanalysis --without-agent-network-line --tag <tag> --n 1 --oracle-k 10 --env daytona --env-file <file>

- On a backend that cannot apply the agent network line (Daytona Tier 1 among them; Tier 2 by Daytona's documentation, not tried), keep `--without-agent-network-line`: the script copies the task to `jobs/ab-test-reanalysis/package-<tag>/ab-test-reanalysis`, drops that one line, checks that nothing else in `task.toml` changed, and runs the copy. On a backend that applies the line, leave the option out and the shipped package itself runs. Only Daytona was run for this task.
- The script runs, per variant, `harbor run -p <package> -e <env> --env-file <file> -n <n> -o jobs/ab-test-reanalysis --job-name ab-test-reanalysis-<variant>-<tag>` followed by the row's arguments in `PROOF_RESULTS_rev1.md` (`-a oracle -k 10` for canonical, `-a oracle --ae SOLUTION=<variant>` for the others, `-a nop`, `-a oracle --force-build`), and writes `PROOF_RESULTS_<tag>.md`, `proof_results_<tag>.json` here. The variants come from the package's `solution/` folder.
- The env file is how Harbor gets the provider's key (`DAYTONA_API_KEY` for Daytona); it is not in the repository. Without `--env` (or `HARBOR_ENV`), the script passes `-e docker`, Harbor's default backend.
- `--n 1` runs one trial at a time. Harbor stops the agent sandbox (2 vCPU, 4,096 MB) before the separate verifier (1 vCPU, 2,048 MB) starts (Harbor 0.25.0 `trial/single_step.py` lines 48-51); INFERENCE: so a trial holds at most 4 GiB at a time (Daytona may still count a sandbox that is being destroyed). The authors' runs also raised Harbor's wait for the environment build three-fold (`environment_build_timeout_multiplier` 3.0 in each trial's `config.json`); the script has no option for it.

## Agent trials

Two sets of agent trials ran on the same copy as the proof: three with Claude Code on 2026-10-31, and the eight of run
m1 on 2026-11-03, Harbor's `terminus-2` agent with four models of an OpenAI-compatible model service (section "Run m1"
below).

### Claude Code (2026-10-31)

Three trials with Harbor's `claude-code` agent (Claude Code 2.1.316, `agent_info` in each `result.json`) and the model `claude-opus-5-5`, on Daytona, 2026-10-31, one at a time, on the same copy as the proof (each trial's `result.json` carries the `task_checksum` of the proof's 24 trials, `274fcfeb9730803d14e0e19bfa6772a2f81ee82d3477737e0f3fb3e263048240`). Settings (each trial's `config.json`): `max_budget_usd` 20 (a spend cap of 20 dollars per trial) and `disable_web_search` true, so Harbor passed Claude Code `--disallowedTools WebSearch,WebFetch` (Harbor 0.25.0 `agents/installed/claude_code.py` lines 90-95). Because the copy lacks the agent network line, the agent phase had the sandbox's own network (Harbor's default, public, under the limits of the authors' Daytona Tier 1 account, which keep GitHub's hosts and other essential services reachable); the shipped package denies the agent network.

| Trial | Job | Ran (MST) | Reward | Readouts passed | Agent time | Tool calls | Cost | Trace folder |
|---|---|---|---|---|---|---|---|---|
| `ab-test-reanalysis__3nb9x28` | `ab-test-reanalysis-claudecode-opus55-cc1` | 02:22:27 to 02:24:47 | 1.0 | 6 of 6 | 63 s | 6 | 0.266 dollars | [`traces/agent-claude-code/ab-test-reanalysis__3nb9x28/`](traces/agent-claude-code/ab-test-reanalysis__3nb9x28/) |
| `ab-test-reanalysis__SpwbpTd` | `ab-test-reanalysis-claudecode-opus55-cc2` | 02:27:16 to 02:29:31 | 1.0 | 6 of 6 | 57 s | 6 | 0.221 dollars | [`traces/agent-claude-code/ab-test-reanalysis__SpwbpTd/`](traces/agent-claude-code/ab-test-reanalysis__SpwbpTd/) |
| `ab-test-reanalysis__NjrFLJq` | `ab-test-reanalysis-claudecode-opus55-cc2` | 02:29:31 to 02:32:19 | 1.0 | 6 of 6 | 89 s | 10 | 0.326 dollars | [`traces/agent-claude-code/ab-test-reanalysis__NjrFLJq/`](traces/agent-claude-code/ab-test-reanalysis__NjrFLJq/) |

The "Ran" times are the Mac clock (MST); each trial's `result.json` gives them in UTC (suffix `Z`, 7 hours ahead). Agent time is the `agent_execution` phase of `result.json`; tool calls are counted in `agent/trajectory.json` (all of them Bash); cost is Claude Code's `total_cost_usd` (`agent/claude-code.txt`), 0.812 dollars for the three.

- Outcome: 3 of 3 passed, each with all six readouts. By the task's pre-registration (design record, section 11.4
  (c)), the revision ships with that count stated and no trap is added. Three trials show that this agent can solve
  the task, not its pass rate (3 of 3 has a Wilson 95% interval of 0.44 to 1.00). The first version had 1 of 3 with
  Harbor's `terminus-2` agent and `openai/gpt-oss-120b` (section "First version"); on the revision, run m1 (below) gave
  5 of 8 with `terminus-2` and four models of an OpenAI-compatible model service. How the external reviewer's own agent
  fares on the revision is not known.
- What the agents did (`agent/trajectory.json`): each read the plan, the PM note, the docs, the README, the code and the data in its first three commands, rewrote `abtest/load.py`, `abtest/filters.py` and `abtest/report.py` in its fourth, and ran the command on `/app/data`; `__SpwbpTd` and `__NjrFLJq` also ran it on a small export of their own in `/tmp/t1`.
- Network and answer key: no tool call holds a network command (curl, wget, pip install, git clone, an http or https URL, a GitHub host) or a path under `/tests`, `/solution` or `/logs/verifier`, and neither `agent/trajectory.json` nor `agent/claude-code.txt` holds any of these patterns (a scan of 2026-10-31). So no trial is excluded. The model key's value is in no file of the two job folders or their logs (the run's key scan).
- Each trace folder holds the same files as the other traces except `agent/oracle.txt` (`result.json`, `config.json`, `trial.log`, `verifier/`, `artifacts/manifest.json`, `job_result.json`, `job_lock.json`), plus `agent/trajectory.json` (Harbor's record of the agent's steps, tool calls and their output) and `agent/claude-code.txt` (Claude Code's own output stream, its cost line included). Not shipped: `agent/sessions/`, Claude Code's raw session files, which hold its full requests, its system prompt among them, and the downloaded copy of `/app`.

### Run m1: `terminus-2` with four models (2026-11-03)

Eight trials with Harbor's `terminus-2` agent (version 2.0.0, `agent_info` in each `result.json`) on Daytona,
2026-11-03 from 10:00:37 to 10:25:21 (Mac clock, MST; the first `started_at` and the last `finished_at` of the eight
`result.json` files, which give them in UTC, 7 hours ahead): two attempts with each of four models of an
OpenAI-compatible model service, named as the service names them (`gemma-4-31B-it`, `glm-5.3-flash`, `gpt-oss-120b`,
`qwen3.8-27b`; which weights served them is UNVERIFIED). The agent's loop runs on the machine that runs Harbor (the
authors' Mac) and calls the model service; the commands the model writes run in a terminal in the task's sandbox.
Each trial was its own one-trial Harbor job (`n_concurrent_trials` 1 in each `job_lock.json`), two at a time at most
(by the start and end times in `result.json`). All eight ran the same copy as the proof and the Claude Code trials:
the digest `sha256:0fc5d05c8334f99bb7ef36ca1929d1f9330f0d74799be756ad8c8ff2ae59837c` in each `job_lock.json` and the
`task_checksum` given above in each `result.json`. Because the copy lacks the agent network line, the agent phase had
the sandbox's own network (Harbor's default, public); the shipped package denies the agent network. Each
`config.json` gives the model service's URL (`api_base`, `<model-endpoint>` in the copies) and the model's token limits
(`model_info`). The results of the whole run, all five tasks, are in `../agent_trials_m1.json`, with each trial's
tokens.

| Trial | Model | Attempt | Reward | Readouts passed | Agent time | Outcome (the review) | Trace folder |
|---|---|---|---|---|---|---|---|
| `ab-test-reanalysis__tPd3ppr` | `gemma-4-31B-it` | 1 | 1.0 | 6 of 6 | 89 s | genuine pass: H1, H2 and H3 fixed from the plan and the docs, with no query of the data (it only ran the pipeline on `/app/data`, as the instruction asks) | [`traces/agent-m1/ab-test-reanalysis__tPd3ppr/`](traces/agent-m1/ab-test-reanalysis__tPd3ppr/) |
| `ab-test-reanalysis__muieaNN` | `gemma-4-31B-it` | 2 | 0.0 | 3 of 6 | 74 s | capability failure: H1 and H2 fixed; the 100 dogfood accounts read in the launch log and dismissed by size, so H3 missed (the problem counts of the attempt `keep_overrides`) | [`traces/agent-m1/ab-test-reanalysis__muieaNN/`](traces/agent-m1/ab-test-reanalysis__muieaNN/) |
| `ab-test-reanalysis__U9Ka5Fx` | `glm-5.3-flash` | 1 | 1.0 | 6 of 6 | 560 s | genuine pass: the three faults named from the docs and checked in the data before and after the edit | [`traces/agent-m1/ab-test-reanalysis__U9Ka5Fx/`](traces/agent-m1/ab-test-reanalysis__U9Ka5Fx/) |
| `ab-test-reanalysis__9bw5VW9` | `glm-5.3-flash` | 2 | 1.0 | 6 of 6 | 359 s | genuine pass: the expected readout computed from the data before the edit, then a run of a relocated copy as an unprivileged user | [`traces/agent-m1/ab-test-reanalysis__9bw5VW9/`](traces/agent-m1/ab-test-reanalysis__9bw5VW9/) |
| `ab-test-reanalysis__KhS7pKJ` | `gpt-oss-120b` | 1 | 0.0 | 0 of 6 | 135 s | capability failure: `/app/docs` never opened; the shipped `"invalid"` readout kept (the nop's problem counts) | [`traces/agent-m1/ab-test-reanalysis__KhS7pKJ/`](traces/agent-m1/ab-test-reanalysis__KhS7pKJ/) |
| `ab-test-reanalysis__JYJviea` | `gpt-oss-120b` | 2 | 0.0 | 0 of 6 | 146 s | capability failure: `/app/docs` never opened; the SRM test moved to the raw assignment counts, against plan section 6; H1 to H3 untouched | [`traces/agent-m1/ab-test-reanalysis__JYJviea/`](traces/agent-m1/ab-test-reanalysis__JYJviea/) |
| `ab-test-reanalysis__JZg3Hry` | `qwen3.8-27b` | 1 | 1.0 | 6 of 6 | 377 s | genuine pass: the three faults named from the docs, then an independent recount of the readout from the data | [`traces/agent-m1/ab-test-reanalysis__JZg3Hry/`](traces/agent-m1/ab-test-reanalysis__JZg3Hry/) |
| `ab-test-reanalysis__sFqSFFL` | `qwen3.8-27b` | 2 | 1.0 | 6 of 6 | 408 s | genuine pass: the three faults named from the docs; the PM's 17,165 users of B split in the data into 17,065 hash users and the 100 override accounts | [`traces/agent-m1/ab-test-reanalysis__sFqSFFL/`](traces/agent-m1/ab-test-reanalysis__sFqSFFL/) |

Agent time is `agent_seconds` in `../agent_trials_m1.json` (the `agent_execution` phase of `result.json`, to the
second); "Readouts passed" is `sets_passed` in `verifier/reward.json`; every `exception_info` in `result.json` is null
(no timeout, no infrastructure error). The outcome is the verdict of the authors' review of the eight trials
(2026-11-03, by model agents, recorded outside this repository): one reader read every trajectory and compared each
final `/app` with the package, and a second tried to break each verdict and upheld all eight.

- Outcome: 5 of 8 passed: `glm-5.3-flash` and `qwen3.8-27b` 2 of 2 each, `gemma-4-31B-it` 1 of 2, `gpt-oss-120b` 0
  of 2 (5 of 8 has a Wilson 95% interval of 0.31 to 0.86; two attempts per model give counts, not rates). Across the
  whole run the three models other than `gpt-oss-120b` (`gemma-4-31B-it`, `glm-5.3-flash`, `qwen3.8-27b`) passed the
  four tasks other than `feature-leakage-churn` in 23 of their 24 attempts, 5 of 6 on this one
  (`../agent_trials_m1.json`). INFERENCE (the review's): on this evidence the revised task is not one that these models
  cannot reliably complete (two of them, `glm-5.3-flash` and `qwen3.8-27b`, passed 4 of 4); it separates
  agents that read the evidence and act on it from agents that skip or dismiss it. A low pass rate is not itself the
  goal (gate check G29): as the pre-registration requires, nothing is added to the task because of these results
  (design record, section 11.4 (a)).
- What the passes did: each of the five wrote the reference fix's three rules, `method == 'hash'` (H3), the
  `ua_crawler` rule only (H2), and a counted pageview clicked when it has an `item:` event (H1), and kept the shipped
  delta method and SRM test (`__U9Ka5Fx` also guarded `stats.py` for an arm with fewer than two users or no counted
  pageview), so each should give the reference readout on any non-degenerate export of the layout, not only on the
  six (INFERENCE, the review's: the rules equal the reference's, but only the six graded exports were run, and
  degenerate exports are unspecified, design record, section 13, limitation 8). All five named the hand-assigned
  accounts from the `method` row of `/app/docs/DATA_DICTIONARY.md` and the launch log before any query of that
  column, so in practice H3 was a reading item for them, not the investigation the design record calls it (INFERENCE,
  the review's; design record, section 1.2). `__tPd3ppr` passed in 89 s without any query of the data (its only
  commands on `/app/data` ran the fixed pipeline, as the instruction asks). No pass hard-codes a figure or touches a
  path under `/tests`, `/solution` or `/logs/verifier`. The two `qwen3.8-27b` passes write fixed note text that is
  false on some hidden exports; the instruction does not grade the notes.
- Why the failures failed (each a capability failure by the pre-registration's rule, design record, section 11.4 (b);
  none a task defect):
  - Both `gpt-oss-120b` trials never opened `/app/docs`, which the instruction names and their file list showed, and
    read no data file but `assignments.csv.gz` (only the pipeline they ran read the bot, pageview and click files).
    `__KhS7pKJ` concluded that the pipeline was already correct and kept the shipped readout: its problem counts over
    the six readouts (11, 11, 11, 9, 5, 11) are the nop trace's. `__JYJviea` held that the SRM test must use the raw
    assignment counts (plan section 6 tests the users of section 3) and changed only that (and added zero-division
    guards for the CTR and the relative lift), so its visible decision equals the reference's by chance while every
    count stays the shipped one (problems 9, 10, 9, 11, 6, 9).
  - `__muieaNN` fixed H1 and H2 and read the launch log's 100 dogfood accounts, but weighed them only as a cause of
    the imbalance ("100 is small compared to the 1443 difference") and stopped once the SRM test passed (p 0.204; the
    reference's is 0.469) with the 100 override accounts still in B, which is what turns its readout into `ship` where
    the reference says `no_ship` (on `h_srm` such accounts hide a real imbalance, design record, section 4.3). Its
    problem counts (8, 6 and 9 on visible, h_null and h_srm; 3 of 6 readouts passed) are those of the attempt
    `keep_overrides`.
  - Frictions of the harness, not of the task: `apply_patch` does not exist in the sandbox (both `gpt-oss-120b`
    trials tried it), and `__muieaNN`'s first `sed -i` matched nothing. `terminus-2` in Harbor 0.25.0 cuts each long
    observation twice (`agents/terminus_2/terminus_2.py` lines 745-781, 1443, 1635 and 1638), so its marker
    understates what was cut (a harness defect, MEDIUM in the review, on the code path of every trial of the run); no
    observation of the three failing trials here was cut.
- Network and answer key: the review scanned every keystroke and the whole of `agent/trajectory.json`,
  `agent/terminus_2.pane` and `agent/recording.cast` of the eight trials: no URL, host name or IP address (this task
  does not even use 127.0.0.1), no DNS or connection error, no pip, curl, wget, apt, npm, ssh, nc or `git clone`
  command, no urllib, requests or socket use, and no path under `/tests`, `/solution` or `/logs/verifier`. The only
  hits were local commands (a `git rev-parse` check in `/app`, which is not a git work tree; local user accounts; a copy
  of `/app` in `/tmp`). So the sandbox's network (Harbor's default, under the limits of the authors' Daytona Tier 1
  account) was available but unused, and no trial is excluded.
- Against the other trials: Claude Code on Opus 5.5 passed the same copy 3 of 3, in 57 to 89 s (above). Model and
  harness both differ between the two sets, so the gap cannot be split between them (INFERENCE). On the first version
  `terminus-2` with `openai/gpt-oss-120b` passed 1 of 3 (section "First version"); here `gpt-oss-120b` passed 0 of 2,
  for another reason: it never opened the docs.
- Each folder in `traces/agent-m1/<trial>/` holds `agent/trajectory.json` (Harbor's record of the agent's steps: the
  model's messages, its keystrokes and what the terminal showed), `agent/terminus_2.pane` and `agent/recording.cast`
  (the terminal's text and a recording of it), the trial and job records (`result.json`, `config.json`, `trial.log`,
  `job_result.json`, `job_lock.json`, `artifacts/manifest.json`) and `verifier/`.
  [`traces/agent-m1/REDACTIONS.md`](traces/agent-m1/REDACTIONS.md) lists what was replaced in them (the authoring
  Mac's paths and the model service's URL); a scan of the copies (2026-11-03) found no key in any file.

## First version (`first-version/`)

The task's first version (commits `79286dc` and `495c9f5`; the package `tasks/ab-test-reanalysis/` at `495c9f5`, Harbor digest `sha256:3ae509d7115cd0c2b660ce90c87fc5f8c60274b74fc0e1bf0939105eb2f8110d`) had a plan that stated every rule and a pipeline with four defects; the revision replaced it (design record, section 14). Its evidence is in `first-version/`, as it was apart from the redactions listed in its traces' `REDACTIONS.md`:

- Proof runs `full1` and `full2` (`PROOF_RESULTS_full1.md`, `PROOF_RESULTS_full2.md`, `proof_results_full1.json`, `proof_results_full2.json`, `run_full1.log`, `run_full2.log`), Harbor 0.25.0 on Daytona. `full2`, 2026-10-29 from 03:38:22 to 03:51:16 MST, was the first version's final proof: ALL AS EXPECTED. `full1` was also all as expected but ran before the hidden set `h_twin` was rebuilt, so it is a dated record only.
- `first-version/traces/<variant>/`: one trial per variant of `full2` (canonical, alt, alt_cr1, nop, constant_inflation, fix_bots_only, fix_ci_only, fix_visible_result_only, hardcode_no_ship, icc_tuned, kish_tuned, mean_of_ratios, no_srm_gate, force-build); the first version's design record is `git show 495c9f5:docs/ab-test-reanalysis/DESIGN.md`.
- The fresh-clone run of `495c9f5` (`PROOF_RESULTS_clone2.md`, `proof_results_clone2.json`): cloned from GitHub and run on Daytona on 2026-10-30 from 07:04:34 to 07:05:57 MST, canonical [1.0] and nop [0.0], ALL AS EXPECTED, with the digest of the `full2` traces.
- Three agent trials of 2026-10-30, 07:27:19 to 07:32:26 MST, with Harbor's `terminus-2` agent and `openai/gpt-oss-120b` (at most two at once; the first version's `task.toml` sets no network line, so the agent phase had the sandbox's network), in `first-version/traces/agent-r3/<trial>/`: `ab-test-reanalysis__SSm9RXo` 1.0 (7 episodes, 70 s of agent time), `ab-test-reanalysis__SMTLwBv` 0.0 (6 episodes, 83 s) and `ab-test-reanalysis__rQEWbT4` 0.0 (6 episodes, 90 s): 1 of 3. A review of 2026-10-30 found the pass a genuine user-level bootstrap, and the two failures identical to the first version's attempt `fix_bots_only` on all 42 reward keys (a pageview-level interval, which that version's plan ruled out): a capability gap, not a task defect. No command in them uses the network, and no GitHub host appears in any command, output, pane or recording (a scan of every trajectory, 2026-10-30). These trials are not counted for the revision (design record, section 11.4 (f)).
