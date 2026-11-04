# Redactions in this traces folder (2026-11-03)

Every file here is a copy of a Harbor trial or job file of the agent run m1 of 2026-11-03, one folder per trial: the
trial's `config.json`, `result.json`, `trial.log`, `agent/`, `verifier/` and `artifacts/manifest.json`, and its job's
`result.json` and `lock.json` as `job_result.json` and `job_lock.json`. Machine-specific paths and the URL of the
OpenAI-compatible model service that the agents called were replaced; nothing else was changed (no reward, count,
token or timing). A comparison of every file here with its original in the job folders (2026-11-03) found each changed
JSON file equal to its original once those strings are replaced (the numbers identical, the bytes too), each changed
text file equal to its original with the paths replaced and one line added at the top, and every other file equal to
its original byte for byte. A scan of the copies (2026-11-03) found no key value, no URL or host name of the model
service, no other path of the authoring Mac, no account name and no symbolic link in any file.

The two smoke attempts of run m1 on this task (Groq's free plan, no result) are not shipped; they are the two rows
with no `trace` in `../../../agent_trials_m1.json`.

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |
| `<model-endpoint>` | the URL of the OpenAI-compatible model service the agents called (`api_base` in `config.json`, `result.json` and `job_lock.json`) |

Text files that changed carry one extra first line saying so. That line begins "# Redacted 2026-11-03:", the day these
copies were made (16:33 MST) from the run of that day. It also defines `<home>`, `<local-scratch>` and
`<model-endpoint>`: in this folder `<home>` and `<local-scratch>` replaced nothing, and `<model-endpoint>` replaced
only in the JSON files listed below (in the text files the three appear only in that line). JSON files cannot carry a
comment, so they are listed here, with the text files.

In each `<trial>/agent/` (`recording.cast`, `terminus_2.pane`, `trajectory.json`), the shell prompt in the terminal
records shows the sandbox's host name (a Daytona sandbox id); it is not a credential and was left as is. These
records also carry the model's own characters unchanged, some of them outside ASCII: in `agent/terminus_2.pane` and
`agent/recording.cast` of both `gpt-oss-120b` trials (`__eZGoutP` and `__wKcgixc`), such as non-breaking hyphens, en
dashes, narrow no-break spaces and superscript digits; no text file of the task package holds any.

| File | Replacements |
|---|---|
| `et0-station-ingest__vQFWbAG/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `et0-station-ingest__vQFWbAG/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `et0-station-ingest__vQFWbAG/trial.log` (text; first line added) | `<submission>` x19 |
| `et0-station-ingest__vQFWbAG/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `et0-station-ingest__A56ZWSZ/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `et0-station-ingest__A56ZWSZ/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `et0-station-ingest__A56ZWSZ/trial.log` (text; first line added) | `<submission>` x21 |
| `et0-station-ingest__A56ZWSZ/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `et0-station-ingest__y4XU2MG/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `et0-station-ingest__y4XU2MG/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `et0-station-ingest__y4XU2MG/trial.log` (text; first line added) | `<submission>` x22 |
| `et0-station-ingest__y4XU2MG/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `et0-station-ingest__qhwGNJ4/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `et0-station-ingest__qhwGNJ4/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `et0-station-ingest__qhwGNJ4/trial.log` (text; first line added) | `<submission>` x15 |
| `et0-station-ingest__qhwGNJ4/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `et0-station-ingest__eZGoutP/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `et0-station-ingest__eZGoutP/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `et0-station-ingest__eZGoutP/trial.log` (text; first line added) | `<submission>` x9 |
| `et0-station-ingest__eZGoutP/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `et0-station-ingest__wKcgixc/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `et0-station-ingest__wKcgixc/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `et0-station-ingest__wKcgixc/trial.log` (text; first line added) | `<submission>` x29 |
| `et0-station-ingest__wKcgixc/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `et0-station-ingest__Fd3SWyE/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `et0-station-ingest__Fd3SWyE/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `et0-station-ingest__Fd3SWyE/trial.log` (text; first line added) | `<submission>` x13 |
| `et0-station-ingest__Fd3SWyE/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `et0-station-ingest__FWn3aTq/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `et0-station-ingest__FWn3aTq/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `et0-station-ingest__FWn3aTq/trial.log` (text; first line added) | `<submission>` x12 |
| `et0-station-ingest__FWn3aTq/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |

Files with no machine-specific path or model URL (copied byte for byte): 64 (8 per trial).
