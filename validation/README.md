# Validation results

Last updated: 2026-11-04, 00:38 MST (Mac clock): in section "Run m1", the earlier `gpt-oss-120b` trials are said to set
no `model_info` (no trial of theirs or of run m1 summarized its context), and the second Groq smoke attempt is given
only the figures of its row in `agent_trials_m1.json` (`RateLimitError` after 28 s of agent time).
Before that, 2026-11-03, 17:30 MST (Mac clock; late edits to 20:39 MST by the file's time): run m1 of the agent
trials (Harbor's `terminus-2` agent with four models of an OpenAI-compatible model service, two trials per model on
each task; 24 of 40 passed) in section "Agent trials", its results file `agent_trials_m1.json` there, and its trace
folders `traces/agent-m1/` in the folder notes.
Before that, 2026-11-03, 06:37 MST (Mac clock): in the `tenant-isolation-docshare` row, `replay_memo` is described by
what it remembers, the writes it refused in the grader's first run, since `phase_gate` also keeps state between the
grader's runs.
Before that, 2026-11-03, 05:43 MST (Mac clock): wording fixed after an independent check (no result changed): for
`tenant-isolation-docshare`, the fresh-clone run `clone2` is said to be graded by the earlier grader, and the note on
agent traces says where that task's trials are; a clause of 2026-11-03 that called its proof pending, written before the
proof ran and never published, is removed from this head.
Before that, 2026-11-03, 04:30 MST (Mac clock): `tenant-isolation-docshare` shows run `full2`, the Daytona proof of
its grader as fixed on 2026-11-03 (all as expected; seven attempts, the new `replay_memo` among them), and its
earlier grader's evidence in `tenant-isolation-docshare/first-version/` (the results table, the fresh-clone run, the
agent trials and the folder notes).
Before that, 2026-10-31, 20:45 MST (Mac clock; last written at 20:51 MST by the file's time, this note added at 21:58
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

For `tenant-isolation-docshare`, run `full2` graded the task after its grader fix of 2026-11-03 (`tests/grade.py`
holds back a seeded third of each class of refused write from the grader's first run and sends those writes only in
its second; the attempt `replay_memo` was added); the earlier grader's evidence is in
`tenant-isolation-docshare/first-version/`.

| Task | Final run | Canonical | Alternative solutions | nop | Wrong or shortcut attempts | force-build | Overall | Details |
|---|---|---|---|---|---|---|---|---|
| `orders-export-missing-rows` | `full1` | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 12 of 12 = 0.0 | 1.0 | all as expected | [`orders-export-missing-rows/`](orders-export-missing-rows/README.md) |
| `tenant-isolation-docshare` | `full2` (after the grader fix of 2026-11-03) | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 7 of 7 = 0.0 (one of them, `replay_memo`, a service that remembers the writes it refused in the grader's first run) | 1.0 | all as expected | [`tenant-isolation-docshare/`](tenant-isolation-docshare/README.md) |
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
and `proof_results_clone2.json`; no traces, no run log): in the folders of `orders-export-missing-rows` and
`et0-station-ingest`, which are unchanged since, and in `tenant-isolation-docshare/first-version/` (its grader was
fixed on 2026-11-03, so run `clone2` was graded by the earlier grader), `ab-test-reanalysis/first-version/` and
`feature-leakage-churn/first-version/`.

## Agent trials

Outside the matrices, model agents ran on Daytona with Harbor 0.25.0. Each linked README gives every trial's reward,
what the agent changed and its trace folder.

| Task | Package | Agent and model | Date (Mac clock) | Passed | Details |
|---|---|---|---|---|---|
| `orders-export-missing-rows` | as published in `495c9f5` (unchanged since) | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-30 | 3 of 3 | [README](orders-export-missing-rows/README.md#agent-trials) |
| `orders-export-missing-rows` | as shipped (unchanged since `495c9f5`) | `terminus-2`, four models of an OpenAI-compatible model service, two trials each (run m1, below) | 2026-11-03 | 6 of 8 | [README](orders-export-missing-rows/README.md#agent-trials) |
| `tenant-isolation-docshare` | as published in `495c9f5`, graded by its grader before the fix of 2026-11-03 (traces in `first-version/`) | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-30 | 0 of 3 | [README](tenant-isolation-docshare/README.md#agent-trials) |
| `tenant-isolation-docshare` | as shipped, with its grader fixed on 2026-11-03 | `terminus-2`, four models of an OpenAI-compatible model service, two trials each (run m1, below) | 2026-11-03 | 6 of 8 | [README](tenant-isolation-docshare/README.md#agent-trials) |
| `et0-station-ingest` | as published in `495c9f5` (unchanged since) | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-29 (the pilot) and 2026-10-30 | 0 of 3 | [README](et0-station-ingest/README.md#agent-trials) |
| `et0-station-ingest` | as shipped (unchanged since `495c9f5`) | `terminus-2`, four models of an OpenAI-compatible model service, two trials each (run m1, below) | 2026-11-03 | 7 of 8 | [README](et0-station-ingest/README.md#agent-trials) |
| `ab-test-reanalysis` | the first version, as published in `495c9f5` | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-30 | 1 of 3 | [README](ab-test-reanalysis/README.md), section "First version" |
| `ab-test-reanalysis` | the revised task, on a copy without its agent network line | `claude-code` (Claude Code 2.1.316), `claude-opus-5-5`, web search off | 2026-10-31 | 3 of 3 | [README](ab-test-reanalysis/README.md#agent-trials) |
| `ab-test-reanalysis` | the revised task, on the same copy | `terminus-2`, four models of an OpenAI-compatible model service, two trials each (run m1, below) | 2026-11-03 | 5 of 8 | [README](ab-test-reanalysis/README.md#agent-trials) |
| `feature-leakage-churn` | the first version, as published in `495c9f5` | `terminus-2`, `openai/gpt-oss-120b` | 2026-10-30 | 0 of 3 | [`first-version/`](feature-leakage-churn/first-version/) |
| `feature-leakage-churn` | task v2, the first revision (its package was never committed; its evidence is in `second-version/`), on a copy without its agent network line | `claude-code` (Claude Code 2.1.316), `claude-opus-5-5`, web search off | 2026-10-31 | 3 of 3 | [`second-version/`](feature-leakage-churn/second-version/) |
| `feature-leakage-churn` | task v3, as shipped, on a copy without its agent network line | `claude-code` (Claude Code 2.1.316), `claude-opus-5-5`, web search off | 2026-10-31 | 3 of 3 | [README](feature-leakage-churn/README.md#agent-trials) |
| `feature-leakage-churn` | task v3, on the same copy | `terminus-2`, four models of an OpenAI-compatible model service, two trials each (run m1, below) | 2026-11-03 | 0 of 8 | [README](feature-leakage-churn/README.md#agent-trials) |

- The `terminus-2` trials of the five tasks as published in `495c9f5` total 4 of 15 passed. A review of the
  trajectories found each pass a genuine fix and each failure a gap the task targets, not a task defect (that review
  predates the finding that `terminus-2` cuts observations twice; the shipped trajectories of 7 of these trials
  contain cut observations, which were not re-checked).
- On `feature-leakage-churn`, task v3's three Claude Code trials took 427 to 455 s of agent time and 22 to 27 tool
  calls each, about twice task v2's 182 to 221 s and 10 to 12 tool calls (each trial's `result.json`,
  `agent_execution`, and `agent/trajectory.json`); task v3 hardened task v2 after task v2's 3 of 3.
- Network: no `task.toml` of `495c9f5` sets a network line, so the `terminus-2` trials of 2026-10-29 and 2026-10-30
  had Harbor's default public network; the Claude Code trials ran copies without the agent network line, so they had
  the sandbox's network too. Every trajectory was read for fetches of the public hidden tests: none made one, so no
  trial is excluded. For run m1, see below.
- The trials show what each agent and model did on each task, not a pass rate (2 of 2 has a Wilson 95% interval of
  0.34 to 1.00, 3 of 3 one of 0.44 to 1.00).

### Run m1 (2026-11-03)

Harbor 0.25.0's `terminus-2` agent, whose loop runs on the machine running Harbor and calls the model service from
there, while the commands the model writes run in the task's Daytona sandbox, with four models of an
OpenAI-compatible model service, named as the service reports them (which weights served them is not verified). Each
model ran two trials on each task, each trial its own Harbor job, from 08:51:56 to 14:48:46 (Mac clock, MST; the
first `started_at` and the last `finished_at` in the traces' `job_result.json`).
[`agent_trials_m1.json`](agent_trials_m1.json) has one row per trial (task, model, attempt, trial, reward, exception,
agent seconds, input and output tokens, start time in UTC and trace folder); each trace is in
`<slug>/traces/agent-m1/<trial>/`.

| Model | orders | docshare | ab-test | et0 | churn | All |
|---|---|---|---|---|---|---|
| `gpt-oss-120b` | 0 of 2 | 0 of 2 | 0 of 2 | 1 of 2 | 0 of 2 | 1 of 10 |
| `qwen3.8-27b` | 2 of 2 | 2 of 2 | 2 of 2 | 2 of 2 | 0 of 2 | 8 of 10 |
| `gemma-4-31B-it` | 2 of 2 | 2 of 2 | 1 of 2 | 2 of 2 | 0 of 2 | 7 of 10 |
| `glm-5.3-flash` | 2 of 2 | 2 of 2 | 2 of 2 | 2 of 2 | 0 of 2 | 8 of 10 |
| All four | 6 of 8 | 6 of 8 | 5 of 8 | 7 of 8 | 0 of 8 | 24 of 40 |

- Settings (each trial's `config.json`): the model `openai/<name>` with the agent arguments `api_base` (the
  service's URL, `<model-endpoint>` in the traces) and `model_info` (the service's token limits), and
  `environment_build_timeout_multiplier` 3; the agent and verifier timeouts are those of each `task.toml`.
  `gpt-oss-120b` is the model of the `terminus-2` trials of 2026-10-29 and 2026-10-30, on the same service (those trials
  set no `model_info`; no trial of those runs or of run m1 summarized its context: `summarization_count` is 0 in each
  trial's `result.json`).
- Packages: `orders-export-missing-rows`, `tenant-isolation-docshare` (with its grader fixed on 2026-11-03) and
  `et0-station-ingest` as shipped; `ab-test-reanalysis` and `feature-leakage-churn` (task v3) on the copies without
  the agent network line that their proofs and Claude Code trials ran. In every trace the task digest in
  `job_lock.json` equals the one in the task's proof traces.
- A trial counts as passed when its reward is 1.0. One `glm-5.3-flash` trial of `orders-export-missing-rows` reached
  the task's 1,200 s agent limit after its fix was done and scored 1.0, and three `feature-leakage-churn` trials
  reached its 3,600 s limit and scored 0; their rows' `exception` is `AgentTimeoutError`.
- Network: the packages run set no network line, so each sandbox had Harbor's default public network. In every
  trajectory, terminal pane and recording, no command reached a host other than `127.0.0.1`, no command or output
  names a GitHub host, and no command touched a path under `/tests`, `/solution` or `/logs/verifier`, so no trial is
  excluded.
- Review (by model agents, recorded outside this repository): for each task a reader read every trial and a second
  reader tried to overturn each verdict. The verdicts: 24 genuine fixes and 16 capability failures, none a task
  defect (in `orders-export-missing-rows__TGjE5Un` no edit landed), with no suspicious pass. Some of its smaller
  findings are in the repository README ("Known limitations", per task), among them two inputs that the graders never
  send (a hand-built `orders-export-missing-rows` cursor whose id is 2^63 or more; a `tenant-isolation-docshare`
  JSON body that is not an object) and a design risk in `feature-leakage-churn`, whose January sample in
  `/app/logs/` cannot show how older orders became visible; the others are in each task's README.
- What it shows: `qwen3.8-27b`, `gemma-4-31B-it` and `glm-5.3-flash` passed the four tasks other than
  `feature-leakage-churn` in 23 of 24 trials and `gpt-oss-120b` in 1 of 8; none of the four models passed
  `feature-leakage-churn` (0 of 8), which Claude Code on Opus 5.5 passed 3 of 3.
  INFERENCE: on this evidence those three models pass those four tasks at nearly every attempt. A low pass rate is
  not itself a sign of quality (gate check G29 in `../docs/QUALITY_GATE.md`).
- Groq: two smoke attempts with `openai/gpt-oss-20b` on Groq's free plan, on `et0-station-ingest`, gave no result and
  are not counted; they are the file's two rows without a reward, and their traces are not shipped. The first failed
  on a configuration error of the authors' run script, the second stopped on the plan's rate limit (`RateLimitError`)
  after 28 s of agent time.
- Harness caveat: Harbor 0.25.0's `terminus-2` cuts each observation of more than 10,000 bytes twice, so the marker
  the agent reads reports about 70 bytes omitted when far more were (`agents/terminus_2/terminus_2.py` lines
  745-781, 1443, 1635 and 1638). In three failing trials it hid task text (`et0-station-ingest__wKcgixc`: METHOD.md
  sections 3.1 to 3.3, with the hemisphere rule; `feature-leakage-churn__pdidSxk` and `__5ZCVEie`: parts of
  `docs/WAREHOUSE.md`). The review found no verdict that this changed: `wKcgixc` saw the rule's other statements,
  the same model with the whole doc made `pdidSxk`'s error, and `5ZCVEie` also broke the 60 s cap.

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
- Agent traces, outside the matrices: `traces/agent-pilot/` (et0), `traces/agent-r3/<trial>/` (et0 and orders; the
  trials of docshare, graded by its earlier grader, and those of the first versions of ab-test and churn are in
  `<slug>/first-version/traces/agent-r3/`) and `traces/agent-m1/<trial>/` (all five tasks, eight trials each: run
  m1), the `terminus-2` trials, with the same files except `agent/oracle.txt`, plus the agent's `trajectory.json`,
  `terminus_2.pane` and `recording.cast` in `agent/`;
  `traces/agent-claude-code/<trial>/` (ab-test and churn task v3; churn task v2's in
  `feature-leakage-churn/second-version/traces/agent-claude-code/`), the Claude Code trials, with the same files
  except `agent/oracle.txt`, plus `trajectory.json` and `claude-code.txt` in `agent/`. Claude Code's raw session files
  (`agent/sessions/`, which hold its full requests, its system prompt among them) are not shipped.
- `REDACTIONS.md` in each `traces/` folder, and for run m1's copies in each `traces/agent-m1/`: what was replaced in
  the copies (machine-specific paths, by placeholders such as `<submission>`, and in the `terminus-2` traces the model
  service's URL, by `<model-endpoint>`); no reward, count or timing was changed.
- `tenant-isolation-docshare/first-version/`: the evidence of that task's grader before its fix of 2026-11-03 (its
  proof run `full1`, the traces of `full1`, its fresh-clone results and its three agent trials of 2026-10-30). In the
  task package the fix changed only `tests/grade.py` and added the attempt `replay_memo`.
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
  it); `tenant-isolation-docshare` run `full1`, which proved its grader before the fix of 2026-11-03, in
  `tenant-isolation-docshare/first-version/`; the first version of `ab-test-reanalysis` in
  `ab-test-reanalysis/first-version/` (its run `full1` predates the rebuild of its hidden set `h_twin`; `full2` was its
  final run); and the earlier versions of `feature-leakage-churn`: task v2's run `rev1` in
  `feature-leakage-churn/second-version/`, and the first version's runs `full1` and `full1b` in
  `feature-leakage-churn/first-version/` (one `full1` canonical trial was lost to a DNS failure on the Mac; `full1b`
  re-ran the ten canonical trials).
- The matrices use Harbor's `oracle` and `nop` agents only, so their results show that the verifiers accept the
  reference and alternative solutions and reject the nop and the listed attempts; how agents fare is in the agent
  trials.
- Times: job `result.json` times are the Mac clock (MST, no zone suffix); trial `result.json` times are UTC (suffix
  `Z`).
