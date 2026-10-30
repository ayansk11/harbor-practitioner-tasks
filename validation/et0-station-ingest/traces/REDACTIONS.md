# Redactions in this traces folder (2026-10-29; `agent-pilot/` added 2026-10-30)

Every file here is a copy of a Harbor trial or job file. Machine-specific paths were replaced, and in `agent-pilot/` also the URL of the model service the agent called; nothing else was changed (no reward, count or timing). The copy scripts checked this: each JSON file parses to the original with only those strings replaced and identical numbers, and each text file differs from the original only on lines that held one of them.

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |
| `<home>` | other paths under the author's home folder (for example the Harbor tool install in a traceback) |
| `<local-scratch>` | the session scratch folder of the authoring tool (a temporary folder on the Mac) |
| `<model-endpoint>` | the URL of the OpenAI-compatible model service the agent pilot called (`agent-pilot/` only) |

Text files that changed carry one extra first line saying so. JSON files cannot carry a comment, so they are listed here.

In `agent-pilot/agent/`, the shell prompt in the terminal records shows the sandbox's host name (a Daytona sandbox id); it is not a credential and was left as is.

| File | Replacements |
|---|---|
| `abs_app_path/config.json` | `<submission>` x2 |
| `abs_app_path/job_lock.json` | `<submission>` x1 |
| `abs_app_path/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `abs_app_path/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-pilot/config.json` | `<model-endpoint>` x1 |
| `agent-pilot/job_lock.json` | `<model-endpoint>` x1 |
| `agent-pilot/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-pilot/trial.log` (text; first line added) | `<submission>` x2 |
| `alt/config.json` | `<submission>` x2 |
| `alt/job_lock.json` | `<submission>` x1 |
| `alt/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `alt/trial.log` (text; first line added) | `<submission>` x2 |
| `canonical/config.json` | `<submission>` x2 |
| `canonical/job_lock.json` | `<submission>` x10 |
| `canonical/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `canonical/trial.log` (text; first line added) | `<submission>` x2 |
| `fit_to_metservice/config.json` | `<submission>` x2 |
| `fit_to_metservice/job_lock.json` | `<submission>` x1 |
| `fit_to_metservice/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `fit_to_metservice/trial.log` (text; first line added) | `<submission>` x2 |
| `fix_altitude/config.json` | `<submission>` x2 |
| `fix_altitude/job_lock.json` | `<submission>` x1 |
| `fix_altitude/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `fix_altitude/trial.log` (text; first line added) | `<submission>` x2 |
| `force-build/config.json` | `<submission>` x2 |
| `force-build/job_lock.json` | `<submission>` x1 |
| `force-build/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `force-build/trial.log` (text; first line added) | `<submission>` x2 |
| `hardcode_output/config.json` | `<submission>` x2 |
| `hardcode_output/job_lock.json` | `<submission>` x1 |
| `hardcode_output/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `hardcode_output/trial.log` (text; first line added) | `<submission>` x2 |
| `linear_wind/config.json` | `<submission>` x2 |
| `linear_wind/job_lock.json` | `<submission>` x1 |
| `linear_wind/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `linear_wind/trial.log` (text; first line added) | `<submission>` x2 |
| `nearest_height/config.json` | `<submission>` x2 |
| `nearest_height/job_lock.json` | `<submission>` x1 |
| `nearest_height/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `nearest_height/trial.log` (text; first line added) | `<submission>` x2 |
| `nop/config.json` | `<submission>` x2 |
| `nop/job_lock.json` | `<submission>` x1 |
| `nop/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `nop/trial.log` (text; first line added) | `<submission>` x2 |
| `read_answers/config.json` | `<submission>` x2 |
| `read_answers/job_lock.json` | `<submission>` x1 |
| `read_answers/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `read_answers/trial.log` (text; first line added) | `<submission>` x2 |
| `symlink_output/config.json` | `<submission>` x2 |
| `symlink_output/job_lock.json` | `<submission>` x1 |
| `symlink_output/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `symlink_output/trial.log` (text; first line added) | `<submission>` x2, `<home>` x10 |
| `units_not_latitude/config.json` | `<submission>` x2 |
| `units_not_latitude/job_lock.json` | `<submission>` x1 |
| `units_not_latitude/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `units_not_latitude/trial.log` (text; first line added) | `<submission>` x2 |

Files with no machine-specific path or model URL (copied byte for byte): 86 (78, plus 8 in `agent-pilot/`).
