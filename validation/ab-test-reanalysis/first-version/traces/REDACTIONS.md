# Redactions in this traces folder (2026-10-29; moved to `first-version/` and `agent-r3/` added 2026-10-31)

Every file here is a copy of a Harbor trial or job file. Machine-specific paths were replaced, and in `agent-r3/` also the URL of the model service the agents called; nothing else was changed (no reward, count or timing). The copy script checked this: each JSON file parses to the original with only the path strings replaced and identical numbers, and each text file differs from the original only on lines that held one of these paths.

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |
| `<home>` | other paths under the author's home folder (for example the Harbor tool install in a traceback) |
| `<local-scratch>` | the session scratch folder of the authoring tool (a temporary folder on the Mac) |
| `<model-endpoint>` | the URL of the OpenAI-compatible model service the agents of `agent-r3/` called |

Text files that changed carry one extra first line saying so. JSON files cannot carry a comment, so they are listed here.

In each `agent-r3/<trial>/agent/` (`recording.cast`, `terminus_2.pane`, `trajectory.json`), the shell prompt in the terminal records shows the sandbox's host name (a Daytona sandbox id); it is not a credential and was left as is.

| File | Replacements |
|---|---|
| `alt/config.json` | `<submission>` x2 |
| `alt/job_lock.json` | `<submission>` x1 |
| `alt/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `alt/trial.log` (text; first line added) | `<submission>` x2 |
| `alt_cr1/config.json` | `<submission>` x2 |
| `alt_cr1/job_lock.json` | `<submission>` x1 |
| `alt_cr1/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `alt_cr1/trial.log` (text; first line added) | `<submission>` x2 |
| `canonical/config.json` | `<submission>` x2 |
| `canonical/job_lock.json` | `<submission>` x10 |
| `canonical/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `canonical/trial.log` (text; first line added) | `<submission>` x2 |
| `constant_inflation/config.json` | `<submission>` x2 |
| `constant_inflation/job_lock.json` | `<submission>` x1 |
| `constant_inflation/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `constant_inflation/trial.log` (text; first line added) | `<submission>` x2 |
| `fix_bots_only/config.json` | `<submission>` x2 |
| `fix_bots_only/job_lock.json` | `<submission>` x1 |
| `fix_bots_only/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `fix_bots_only/trial.log` (text; first line added) | `<submission>` x2 |
| `fix_ci_only/config.json` | `<submission>` x2 |
| `fix_ci_only/job_lock.json` | `<submission>` x1 |
| `fix_ci_only/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `fix_ci_only/trial.log` (text; first line added) | `<submission>` x2 |
| `fix_visible_result_only/config.json` | `<submission>` x2 |
| `fix_visible_result_only/job_lock.json` | `<submission>` x1 |
| `fix_visible_result_only/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `fix_visible_result_only/trial.log` (text; first line added) | `<submission>` x2 |
| `force-build/config.json` | `<submission>` x2 |
| `force-build/job_lock.json` | `<submission>` x1 |
| `force-build/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `force-build/trial.log` (text; first line added) | `<submission>` x2 |
| `hardcode_no_ship/config.json` | `<submission>` x2 |
| `hardcode_no_ship/job_lock.json` | `<submission>` x1 |
| `hardcode_no_ship/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `hardcode_no_ship/trial.log` (text; first line added) | `<submission>` x2 |
| `icc_tuned/config.json` | `<submission>` x2 |
| `icc_tuned/job_lock.json` | `<submission>` x1 |
| `icc_tuned/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `icc_tuned/trial.log` (text; first line added) | `<submission>` x2 |
| `kish_tuned/config.json` | `<submission>` x2 |
| `kish_tuned/job_lock.json` | `<submission>` x1 |
| `kish_tuned/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `kish_tuned/trial.log` (text; first line added) | `<submission>` x2 |
| `mean_of_ratios/config.json` | `<submission>` x2 |
| `mean_of_ratios/job_lock.json` | `<submission>` x1 |
| `mean_of_ratios/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `mean_of_ratios/trial.log` (text; first line added) | `<submission>` x2 |
| `no_srm_gate/config.json` | `<submission>` x2 |
| `no_srm_gate/job_lock.json` | `<submission>` x1 |
| `no_srm_gate/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `no_srm_gate/trial.log` (text; first line added) | `<submission>` x2 |
| `nop/config.json` | `<submission>` x2 |
| `nop/job_lock.json` | `<submission>` x1 |
| `nop/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `nop/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/ab-test-reanalysis__SMTLwBv/config.json` | `<model-endpoint>` x1 |
| `agent-r3/ab-test-reanalysis__SMTLwBv/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/ab-test-reanalysis__SMTLwBv/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/ab-test-reanalysis__SMTLwBv/job_lock.json` | `<model-endpoint>` x3 |
| `agent-r3/ab-test-reanalysis__SSm9RXo/config.json` | `<model-endpoint>` x1 |
| `agent-r3/ab-test-reanalysis__SSm9RXo/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/ab-test-reanalysis__SSm9RXo/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/ab-test-reanalysis__SSm9RXo/job_lock.json` | `<model-endpoint>` x3 |
| `agent-r3/ab-test-reanalysis__rQEWbT4/config.json` | `<model-endpoint>` x1 |
| `agent-r3/ab-test-reanalysis__rQEWbT4/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/ab-test-reanalysis__rQEWbT4/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/ab-test-reanalysis__rQEWbT4/job_lock.json` | `<model-endpoint>` x3 |

Files with no machine-specific path or model URL (copied byte for byte): 107 (83, plus 24 in `agent-r3/`).
