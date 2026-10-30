# Validation results

Last updated: 2026-10-29 (Mac clock, MST).

Every task was run on Daytona with Harbor 0.25.0 (`harbor.version` in each trace's `job_lock.json`), using `tools/proof_matrix.py`. For each task the matrix runs the canonical solution ten times (oracle agent, `-k 10`), each alternative valid solution once, Harbor's nop agent once, each wrong or shortcut attempt once, and the canonical solution once more with `--force-build`. Expected: 1.0 for canonical, alternatives and force-build; 0.0 for nop and every attempt.

| Task | Final run | Canonical (10 trials) | Alternative solutions | nop | Wrong or shortcut attempts | force-build | Overall | Details |
|---|---|---|---|---|---|---|---|---|
| `orders-export-missing-rows` | `full1` | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 12 of 12 = 0.0 | 1.0 | all as expected | [`orders-export-missing-rows/`](orders-export-missing-rows/README.md) |
| `tenant-isolation-docshare` | `full1` | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 6 of 6 = 0.0 | 1.0 | all as expected | [`tenant-isolation-docshare/`](tenant-isolation-docshare/README.md) |
| `ab-test-reanalysis` | `full2` | 10 of 10 = 1.0 | `alt` 1.0, `alt_cr1` 1.0 | 0.0 | 9 of 9 = 0.0 | 1.0 | all as expected | [`ab-test-reanalysis/`](ab-test-reanalysis/README.md) |
| `et0-station-ingest` | `full1` | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 9 of 9 = 0.0 | 1.0 | all as expected | [`et0-station-ingest/`](et0-station-ingest/README.md) |
| `feature-leakage-churn` | `full1`, canonical from `full1b` | 10 of 10 = 1.0 | `alt` 1.0 | 0.0 | 10 of 10 = 0.0 | 1.0 | all as expected (one full1 canonical trial lost to a DNS failure on the Mac; re-run in full1b) | [`feature-leakage-churn/`](feature-leakage-churn/README.md) |

## What is in each task folder

- `README.md`: which run is final, one row per variant (what it is, the rewards, the shipped trace, what the trace shows) and the notes.
- `PROOF_RESULTS_<run>.md` (and `.json`, `run_<run>.log`): the matrix as `tools/proof_matrix.py` wrote it.
- `traces/<variant>/`: one Harbor trial per variant of the final run (68 trace folders in all, including the lost feature-leakage-churn trial kept as evidence). Each holds the trial's `result.json`, `config.json`, `trial.log`, `agent/`, `verifier/` (reward and full verifier log), `artifacts/manifest.json`, and the job's `result.json` and `lock.json` as `job_result.json` and `job_lock.json`. The downloaded copy of `/app` is not shipped.
- `traces/REDACTIONS.md`: machine-specific paths were replaced by `<submission>`, `<home>` and `<local-scratch>`; no reward, count or timing was changed.

## Notes and limits

- The raw Harbor job folders (`jobs/`) are git-ignored. The `Job folder` column of `PROOF_RESULTS_*.md` points there; use the trace folders instead.
- Runner: Daytona sandboxes (Harbor `-e daytona`). The base image is pinned to a multi-arch index digest (`tools/BASE_IMAGE_DIGEST`). The sandboxes were linux/amd64; this is inferred from the Daytona backend, not read from the traces. No run used a local Docker engine.
- Superseded runs kept as dated records: `ab-test-reanalysis` run `full1` (before its hidden set `h_twin` was rebuilt; `full2` is final) and `et0-station-ingest` run `smoke` (a pre-check). No traces are shipped from them.
- No agent (model) trials were run: no model API key was settled for that. The matrices use Harbor's `oracle` and `nop` agents only, so these results show that the verifiers accept the reference and alternative solutions and reject the nop and the listed attempts. They say nothing yet about how hard the tasks are for an agent.
- Times: job `result.json` times are the Mac clock (MST, no zone suffix); trial `result.json` times are UTC (suffix `Z`).
