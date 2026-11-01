# Redactions in this traces folder (2026-10-29; moved to `first-version/` and `agent-r3/` added 2026-10-31)

Every file here is a copy of a Harbor trial or job file. Machine-specific paths were replaced, and in `agent-r3/` also the URL of the model service the agents called; nothing else was changed (no reward, count or timing). The copy script checked this: each JSON file parses to the original with only the path strings replaced and identical numbers, and each text file differs from the original only on lines that held one of these paths.

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |
| `<home>` | other paths under the author's home folder (for example the Harbor tool install in a traceback) |
| `<local-scratch>` | the session scratch folder of the authoring tool (a temporary folder on the Mac) |
| `<model-endpoint>` | the URL of the OpenAI-compatible model service the agents of `agent-r3/` called |

Text files that changed carry one extra first line saying so. JSON files cannot carry a comment, so they are listed here.

In each `agent-r3/<trial>/agent/` (`recording.cast`, `terminus_2.pane`, `trajectory.json`), the shell prompt in the terminal records shows the sandbox's host name (a Daytona sandbox id), and the error line in `canonical_full1_lost/trial.log` names another sandbox id; neither is a credential, and both were left as is.

| File | Replacements |
|---|---|
| `alt/config.json` | `<submission>` x2 |
| `alt/job_lock.json` | `<submission>` x1 |
| `alt/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `alt/trial.log` (text; first line added) | `<submission>` x2 |
| `cache_visible/config.json` | `<submission>` x2 |
| `cache_visible/job_lock.json` | `<submission>` x1 |
| `cache_visible/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `cache_visible/trial.log` (text; first line added) | `<submission>` x2 |
| `canonical/config.json` | `<submission>` x2 |
| `canonical/job_lock.json` | `<submission>` x10 |
| `canonical/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `canonical/trial.log` (text; first line added) | `<submission>` x2 |
| `canonical_full1_lost/config.json` | `<submission>` x2 |
| `canonical_full1_lost/exception.txt` (text; first line added) | `<home>` x45 |
| `canonical_full1_lost/job_lock.json` | `<submission>` x10 |
| `canonical_full1_lost/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1, `<home>` x45 |
| `canonical_full1_lost/trial.log` (text; first line added) | `<submission>` x2 |
| `closed_right/config.json` | `<submission>` x2 |
| `closed_right/job_lock.json` | `<submission>` x1 |
| `closed_right/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `closed_right/trial.log` (text; first line added) | `<submission>` x2 |
| `drop_leaky/config.json` | `<submission>` x2 |
| `drop_leaky/job_lock.json` | `<submission>` x1 |
| `drop_leaky/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `drop_leaky/trial.log` (text; first line added) | `<submission>` x2 |
| `force-build/config.json` | `<submission>` x2 |
| `force-build/job_lock.json` | `<submission>` x1 |
| `force-build/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `force-build/trial.log` (text; first line added) | `<submission>` x2 |
| `label_at_t/config.json` | `<submission>` x2 |
| `label_at_t/job_lock.json` | `<submission>` x1 |
| `label_at_t/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `label_at_t/trial.log` (text; first line added) | `<submission>` x2 |
| `loo_encoding/config.json` | `<submission>` x2 |
| `loo_encoding/job_lock.json` | `<submission>` x1 |
| `loo_encoding/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `loo_encoding/trial.log` (text; first line added) | `<submission>` x2 |
| `miss_imputation/config.json` | `<submission>` x2 |
| `miss_imputation/job_lock.json` | `<submission>` x1 |
| `miss_imputation/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `miss_imputation/trial.log` (text; first line added) | `<submission>` x2 |
| `nop/config.json` | `<submission>` x2 |
| `nop/job_lock.json` | `<submission>` x1 |
| `nop/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `nop/trial.log` (text; first line added) | `<submission>` x2 |
| `open_left_30d/config.json` | `<submission>` x2 |
| `open_left_30d/job_lock.json` | `<submission>` x1 |
| `open_left_30d/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `open_left_30d/trial.log` (text; first line added) | `<submission>` x2 |
| `status_same_day/config.json` | `<submission>` x2 |
| `status_same_day/job_lock.json` | `<submission>` x1 |
| `status_same_day/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `status_same_day/trial.log` (text; first line added) | `<submission>` x2 |
| `tune_model/config.json` | `<submission>` x2 |
| `tune_model/job_lock.json` | `<submission>` x1 |
| `tune_model/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `tune_model/trial.log` (text; first line added) | `<submission>` x2 |
| `zero_features/config.json` | `<submission>` x2 |
| `zero_features/job_lock.json` | `<submission>` x1 |
| `zero_features/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `zero_features/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/feature-leakage-churn__JeN8fJg/config.json` | `<model-endpoint>` x1 |
| `agent-r3/feature-leakage-churn__JeN8fJg/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/feature-leakage-churn__JeN8fJg/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/feature-leakage-churn__JeN8fJg/job_lock.json` | `<model-endpoint>` x3 |
| `agent-r3/feature-leakage-churn__hnGjJbF/config.json` | `<model-endpoint>` x1 |
| `agent-r3/feature-leakage-churn__hnGjJbF/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/feature-leakage-churn__hnGjJbF/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/feature-leakage-churn__hnGjJbF/job_lock.json` | `<model-endpoint>` x3 |
| `agent-r3/feature-leakage-churn__ioYjMbS/config.json` | `<model-endpoint>` x1 |
| `agent-r3/feature-leakage-churn__ioYjMbS/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/feature-leakage-churn__ioYjMbS/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/feature-leakage-churn__ioYjMbS/job_lock.json` | `<model-endpoint>` x3 |

Files with no machine-specific path or model URL (copied byte for byte): 110 (86, plus 24 in `agent-r3/`).
