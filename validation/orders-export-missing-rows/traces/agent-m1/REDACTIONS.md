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

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |
| `<home>` | other paths under the authors' home folder (here the Harbor tool install and its Python in a traceback) |
| `<model-endpoint>` | the URL of the OpenAI-compatible model service the agents called (`api_base` in `config.json`, `result.json` and `job_lock.json`; in `orders-export-missing-rows__zpRJCV7/result.json` also the URL in a model call's error) |

Text files that changed carry one extra first line saying so. That line begins "# Redacted 2026-11-03:", the day these
copies were made (16:33 MST) from the run of that day. It also defines `<home>`, `<local-scratch>` and
`<model-endpoint>`: in this folder `<local-scratch>` replaced nothing, and `<home>` and `<model-endpoint>` replaced
only in the JSON files listed below (in the text files the three appear only in that line). JSON files cannot carry a
comment, so they are listed here, with the text files.

The 46 `<home>` and the second `<model-endpoint>` in `orders-export-missing-rows__zpRJCV7/result.json` are in the
traceback of its `AgentTimeoutError` (`exception_info`): the model call in flight had an HTTP 429 answer from the model
service and was being retried when the agent timeout ended the agent phase.

In each `<trial>/agent/` (`recording.cast`, `terminus_2.pane`, `trajectory.json`), the shell prompt in the terminal
records shows the sandbox's host name (a Daytona sandbox id); it is not a credential and was left as is. These
records also carry the model's own characters unchanged, a few of them outside ASCII: in `agent/terminus_2.pane` and
`agent/recording.cast` of both `gpt-oss-120b` trials, non-breaking hyphens (`__TGjE5Un` and `__czEnfc8`) and en
dashes (`__czEnfc8`); no text file of the task package holds any.

| File | Replacements |
|---|---|
| `orders-export-missing-rows__tWo8AoG/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `orders-export-missing-rows__tWo8AoG/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `orders-export-missing-rows__tWo8AoG/trial.log` (text; first line added) | `<submission>` x12 |
| `orders-export-missing-rows__tWo8AoG/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `orders-export-missing-rows__3drHTwr/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `orders-export-missing-rows__3drHTwr/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `orders-export-missing-rows__3drHTwr/trial.log` (text; first line added) | `<submission>` x11 |
| `orders-export-missing-rows__3drHTwr/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `orders-export-missing-rows__wFkwALt/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `orders-export-missing-rows__wFkwALt/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `orders-export-missing-rows__wFkwALt/trial.log` (text; first line added) | `<submission>` x19 |
| `orders-export-missing-rows__wFkwALt/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `orders-export-missing-rows__zpRJCV7/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `orders-export-missing-rows__zpRJCV7/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x2, `<home>` x46 |
| `orders-export-missing-rows__zpRJCV7/trial.log` (text; first line added) | `<submission>` x20 |
| `orders-export-missing-rows__zpRJCV7/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `orders-export-missing-rows__czEnfc8/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `orders-export-missing-rows__czEnfc8/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `orders-export-missing-rows__czEnfc8/trial.log` (text; first line added) | `<submission>` x26 |
| `orders-export-missing-rows__czEnfc8/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `orders-export-missing-rows__TGjE5Un/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `orders-export-missing-rows__TGjE5Un/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `orders-export-missing-rows__TGjE5Un/trial.log` (text; first line added) | `<submission>` x15 |
| `orders-export-missing-rows__TGjE5Un/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `orders-export-missing-rows__EdiSLpb/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `orders-export-missing-rows__EdiSLpb/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `orders-export-missing-rows__EdiSLpb/trial.log` (text; first line added) | `<submission>` x13 |
| `orders-export-missing-rows__EdiSLpb/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `orders-export-missing-rows__2XQn2TF/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `orders-export-missing-rows__2XQn2TF/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `orders-export-missing-rows__2XQn2TF/trial.log` (text; first line added) | `<submission>` x18 |
| `orders-export-missing-rows__2XQn2TF/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |

Files with no machine-specific path or model URL (copied byte for byte): 64 (8 per trial).
