# Validation results

Last updated: 2026-10-31, 20:45 MST (Mac clock; last written at 20:51 MST by the file's time, this note added at 21:58
MST): `feature-leakage-churn` as task v3 (run `v3` and its Claude Code trials), its earlier versions in
`feature-leakage-churn/second-version/` (task v2) and `first-version/`, and prose lines wrapped. Before that,
2026-10-31, 14:13 MST (Mac clock): the revised `ab-test-reanalysis` (run `rev1` and its agent trials), the fresh-clone
run of commit `495c9f5` and the agent trials of 2026-10-30. Before that, 2026-10-30 (Mac clock, MST).

Every task was run on Daytona with Harbor 0.25.0 (`harbor.version` in each trace's `job_lock.json`), using
`tools/proof_matrix.py`. For each task the matrix runs the canonical solution several times (oracle agent, `-k <n>`;
the count is in the table), each alternative valid solution once, Harbor's nop agent once, each wrong or shortcut
attempt once, and the canonical solution once more with `--force-build`. Expected: 1.0 for canonical, alternatives
and force-build; 0.0 for nop and every attempt. Where a task's `task.toml` denies the agent network (`[agent]
network_mode = "no-network"`), the matrix ran a copy of the task without that one line, made by
`tools/proof_matrix.py --without-agent-network-line`, because the authors' Daytona account refuses the network switch
that the line needs (repository README, "The agent network line" under "Setup").

| Task | Final run | Canonical | Alternative solutions | nop | Wrong or shortcut attempts | force-build | Overall | Details |
|---|---|---|---|---|---|---|---|---|
| `orders-export-missing-rows` | `full1` | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 12 of 12 = 0.0 | 1.0 | all as expected | [`orders-export-missing-rows/`](orders-export-missing-rows/README.md) |
| `tenant-isolation-docshare` | `full1` | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 6 of 6 = 0.0 | 1.0 | all as expected | [`tenant-isolation-docshare/`](tenant-isolation-docshare/README.md) |
| `ab-test-reanalysis` | `rev1` (the revised task, on a copy without its agent network line) | 10 of 10 = 1.0 | `alt_recount` 1.0, `alt_time` 1.0 | 0.0 | 10 of 10 = 0.0 | 1.0 | all as expected | [`ab-test-reanalysis/`](ab-test-reanalysis/README.md) |
| `et0-station-ingest` | `full1` | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 9 of 9 = 0.0 | 1.0 | all as expected | [`et0-station-ingest/`](et0-station-ingest/README.md) |
| `feature-leakage-churn` | `v3` (task v3, the second revision, on a copy without its agent network line) | 5 of 5 = 1.0 | `alt` 1.0 | 0.0 | 23 of 23 = 0.0 (one of them a probe that keeps state between the grader's runs) | 1.0 | all as expected | [`feature-leakage-churn/`](feature-leakage-churn/README.md) |

## Fresh-clone run of commit `495c9f5`

On 2026-10-30 this repository was cloned from GitHub at commit `495c9f5` (06:18, Mac clock, MST), and
`tools/proof_matrix.py` ran each of the five tasks of that commit from the clone on Daytona, canonical once and nop
once (`--only canonical,nop --oracle-k 1 --n 1`, run `clone2`), one trial at a time, from 07:00:24 to 07:07:46 (Mac
clock, MST). Every task gave canonical [1.0] and nop [0.0], ALL AS EXPECTED, and each job's task digest equals the one
in the proof traces shipped in that commit. Harbor waited up to three times its default image-build time
(`--environment-build-timeout-multiplier 3`). Only results files are shipped from this run (`PROOF_RESULTS_clone2.md`
and `proof_results_clone2.json`; no traces, no run log): in the folders of `orders-export-missing-rows`,
`tenant-isolation-docshare` and `et0-station-ingest`, which are unchanged since, and in
`ab-test-reanalysis/first-version/` and `feature-leakage-churn/first-version/`.

## Agent trials

Outside the matrices, model agents ran on Daytona with Harbor 0.25.0. Each linked README gives every trial's reward,
what the agent changed and its trace folder.

| Task | Package | Agent and model | Date (Mac clock) | Passed | Details |
|---|---|---|---|---|---|
| `orders-export-missing-rows` | as published in `495c9f5` (unchanged since) | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-30 | 3 of 3 | [README](orders-export-missing-rows/README.md#agent-trials) |
| `tenant-isolation-docshare` | as published in `495c9f5` (unchanged since) | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-30 | 0 of 3 | [README](tenant-isolation-docshare/README.md#agent-trials) |
| `et0-station-ingest` | as published in `495c9f5` (unchanged since) | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-29 (the pilot) and 2026-10-30 | 0 of 3 | [README](et0-station-ingest/README.md#agent-trials) |
| `ab-test-reanalysis` | the first version, as published in `495c9f5` | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-30 | 1 of 3 | [README](ab-test-reanalysis/README.md), section "First version" |
| `ab-test-reanalysis` | the revised task, on a copy without its agent network line | `claude-code` (Claude Code 2.1.316), `claude-opus-5-5`, web search off | 2026-10-31 | 3 of 3 | [README](ab-test-reanalysis/README.md#agent-trials) |
| `feature-leakage-churn` | the first version, as published in `495c9f5` | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-30 | 0 of 3 | [`first-version/`](feature-leakage-churn/first-version/) |
| `feature-leakage-churn` | task v2, the first revision (its package was never committed; its evidence is in `second-version/`), on a copy without its agent network line | `claude-code` (Claude Code 2.1.316), `claude-opus-5-5`, web search off | 2026-10-31 | 3 of 3 | [`second-version/`](feature-leakage-churn/second-version/) |
| `feature-leakage-churn` | task v3, as shipped, on a copy without its agent network line | `claude-code` (Claude Code 2.1.316), `claude-opus-5-5`, web search off | 2026-10-31 | 3 of 3 | [README](feature-leakage-churn/README.md#agent-trials) |

- The `terminus-2` trials of the five tasks as published in `495c9f5` total 4 of 15 passed. A review of the
  trajectories found each pass a genuine fix and each failure a gap the task targets, not a task defect.
- On `feature-leakage-churn`, task v3's three Claude Code trials took 427 to 455 s of agent time and 22 to 27 tool
  calls each, about twice task v2's 182 to 221 s and 10 to 12 tool calls (each trial's `result.json`,
  `agent_execution`, and `agent/trajectory.json`); task v3 hardened task v2 after task v2's 3 of 3.
- Network: no `task.toml` of `495c9f5` sets a network line, so the `terminus-2` trials had Harbor's default public
  network; the Claude Code trials ran copies without the agent network line, so they had the sandbox's network too.
  Every trajectory was read for fetches of the public hidden tests: none made one, so no trial is excluded.
- The trials show what one agent and model did on each task, not a pass rate (3 of 3 has a Wilson 95% interval of
  0.44 to 1.00).

## What is in each task folder

- `README.md`: which run is final, one row per variant (what it is, the rewards, the shipped trace, what the trace
  shows), the agent trials and the notes.
- `PROOF_RESULTS_<run>.md` and `proof_results_<run>.json`: the matrix as `tools/proof_matrix.py` wrote it;
  `run_<run>.log`: its console output, for the matrix runs (there is none for `et0-station-ingest`'s pre-check `smoke`
  or for the fresh-clone run `clone2`).
- `traces/<variant>/`: one Harbor trial per variant of the final run. Each holds the trial's `result.json`,
  `config.json`, `trial.log`, `agent/` (`oracle.txt`; nop trials have no `agent/`), `verifier/` (reward and full
  verifier log), `artifacts/manifest.json`, and the job's `result.json` and `lock.json` as `job_result.json` and
  `job_lock.json`. The downloaded copy of `/app` is not shipped.
- Agent traces, outside the matrices: `traces/agent-pilot/` (et0) and `traces/agent-r3/<trial>/` (et0, docshare and
  orders; for the first versions of ab-test and churn in `<slug>/first-version/traces/agent-r3/`), the `terminus-2`
  trials, with the same files except `agent/oracle.txt`, plus the agent's `trajectory.json`, `terminus_2.pane` and
  `recording.cast` in `agent/`; `traces/agent-claude-code/<trial>/` (ab-test and churn task v3; churn task v2's in
  `feature-leakage-churn/second-version/traces/agent-claude-code/`), the Claude Code trials, with the same files
  except `agent/oracle.txt`, plus `trajectory.json` and `claude-code.txt` in `agent/`. Claude Code's raw session files
  (`agent/sessions/`, which hold its full requests, its system prompt among them) are not shipped.
- `REDACTIONS.md` in each `traces/` folder: what was replaced in the copies (machine-specific paths, by placeholders
  such as `<submission>`, and in the `terminus-2` traces the model service's URL, by `<model-endpoint>`); no reward,
  count or timing was changed.
- `ab-test-reanalysis/first-version/`: the evidence of that task's first version (its proof runs `full1` and `full2`,
  the traces of `full2`, its fresh-clone results and its three agent trials of 2026-10-30), as described in its README.
- `feature-leakage-churn/second-version/`: the evidence of task v2, that task's first revision (its proof run `rev1`,
  its traces and its three Claude Code trials); `feature-leakage-churn/first-version/`: the evidence of its first
  version (its proof runs `full1` and `full1b`, their traces, `NOTES.md`, its fresh-clone results and its three agent
  trials of 2026-10-30).

## Notes and limits

- The raw Harbor job folders (`jobs/`) are git-ignored. The `Job folder` column of `PROOF_RESULTS_*.md` points there;
  use the trace folders instead.
- Runner: Daytona sandboxes (Harbor `-e daytona`). The base image is pinned to a multi-arch index digest
  (`tools/BASE_IMAGE_DIGEST`). The sandboxes were linux/amd64; this is inferred from the Daytona backend, not read from
  the traces. No run used a local Docker engine.
- Superseded runs kept as dated records: `et0-station-ingest` run `smoke` (a pre-check; no traces are shipped from
  it); the first version of `ab-test-reanalysis` in `ab-test-reanalysis/first-version/` (its run `full1` predates the
  rebuild of its hidden set `h_twin`; `full2` was its final run); and the earlier versions of `feature-leakage-churn`:
  task v2's run `rev1` in `feature-leakage-churn/second-version/`, and the first version's runs `full1` and `full1b`
  in `feature-leakage-churn/first-version/` (one `full1` canonical trial was lost to a DNS failure on the Mac;
  `full1b` re-ran the ten canonical trials).
- The matrices use Harbor's `oracle` and `nop` agents only, so their results show that the verifiers accept the
  reference and alternative solutions and reject the nop and the listed attempts; how agents fare is in the agent
  trials.
- Times: job `result.json` times are the Mac clock (MST, no zone suffix); trial `result.json` times are UTC (suffix
  `Z`).
