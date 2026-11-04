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
| `<model-endpoint>` | the URL of the OpenAI-compatible model service the agents called (`api_base` in `config.json`, `result.json` and `job_lock.json`) |

Text files that changed carry one extra first line saying so. That line begins "# Redacted 2026-11-03:", the day these
copies were made (16:33 MST) from the run of that day. It also defines `<home>`, `<local-scratch>` and
`<model-endpoint>`: in this folder `<home>` and `<local-scratch>` replaced nothing, and `<model-endpoint>` replaced
only in the JSON files listed below (in the text files the three appear only in that line). JSON files cannot carry a
comment, so they are listed here, with the text files.

In each `<trial>/agent/` (`recording.cast`, `terminus_2.pane`, `trajectory.json`), the shell prompt in the terminal
records shows the sandbox's host name (a Daytona sandbox id); it is not a credential and was left as is. These
records also carry the model's own characters unchanged, a few of them outside ASCII: in `agent/terminus_2.pane` and
`agent/recording.cast` of both `gpt-oss-120b` trials, non-breaking hyphens (`__5k57eE3` and `__futjyTA`) and en
dashes and narrow no-break spaces (`__futjyTA`); no text file of the task package holds any.

| File | Replacements |
|---|---|
| `tenant-isolation-docshare__ZK8erWp/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__ZK8erWp/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__ZK8erWp/trial.log` (text; first line added) | `<submission>` x10 |
| `tenant-isolation-docshare__ZK8erWp/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__HofavrE/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__HofavrE/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__HofavrE/trial.log` (text; first line added) | `<submission>` x17 |
| `tenant-isolation-docshare__HofavrE/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__JZyjz7i/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__JZyjz7i/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__JZyjz7i/trial.log` (text; first line added) | `<submission>` x19 |
| `tenant-isolation-docshare__JZyjz7i/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__EVFSvc5/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__EVFSvc5/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__EVFSvc5/trial.log` (text; first line added) | `<submission>` x25 |
| `tenant-isolation-docshare__EVFSvc5/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__futjyTA/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__futjyTA/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__futjyTA/trial.log` (text; first line added) | `<submission>` x16 |
| `tenant-isolation-docshare__futjyTA/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__5k57eE3/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__5k57eE3/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__5k57eE3/trial.log` (text; first line added) | `<submission>` x16 |
| `tenant-isolation-docshare__5k57eE3/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__DNwnWr5/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__DNwnWr5/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__DNwnWr5/trial.log` (text; first line added) | `<submission>` x16 |
| `tenant-isolation-docshare__DNwnWr5/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__A5bfe2E/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__A5bfe2E/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `tenant-isolation-docshare__A5bfe2E/trial.log` (text; first line added) | `<submission>` x13 |
| `tenant-isolation-docshare__A5bfe2E/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |

Files with no machine-specific path or model URL (copied byte for byte): 64 (8 per trial).
