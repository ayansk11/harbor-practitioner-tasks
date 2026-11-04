# Redactions in this traces folder (2026-11-03)

Every file here is a copy of a Harbor trial or job file of run m1 of 2026-11-03: the eight trials of task v3 with
Harbor's `terminus-2` agent and four models of an OpenAI-compatible model service, two attempts per model, each trial
its own one-trial Harbor job, on the proof's copy of the package without the agent network line (`../../README.md`,
section "Agent trials"). There is one folder per trial. Machine-specific paths and the model service's URL were
replaced; nothing else was changed (no reward, count or timing). A comparison of every file here with its original in
the job folders (2026-11-03, by 17:09 MST) found each changed JSON file equal to its original once those strings are
replaced (the numbers identical), each changed text file equal to its original with the paths replaced and one line
added at the top, and every other file equal to its original byte for byte. A scan of the copies (2026-11-03) found no
model service's key, no sandbox provider's key, no service URL or host, no other path of the authoring Mac and no
account name in any file.

Each trial folder holds the agent's own record as `terminus-2` wrote it, copied byte for byte: `agent/trajectory.json`
(Harbor's record of the agent's steps: the model's messages, the keystrokes it sent and what the terminal showed),
`agent/terminus_2.pane` (the text of the agent's terminal) and `agent/recording.cast` (an asciinema recording of that
terminal). These records carry the model's own characters unchanged, a few of them outside ASCII (in both
`gpt-oss-120b` trials a non-breaking hyphen and an en dash, and in `__zhHaP4k` also a less-than-or-equal sign). Not
copied: each trial's own `lock.json` (equal to the one trial entry of the job's `lock.json`, which is copied as
`job_lock.json`), the job's `config.json` and `job.log`, the downloaded copy of `/app` (`artifacts/app/`;
`artifacts/manifest.json` is copied) and, for the three trials stopped at the agent timeout
(`feature-leakage-churn__LcSFoqe`, `feature-leakage-churn__MuZJi75` and `feature-leakage-churn__zhHaP4k`),
`exception.txt`, whose traceback `result.json` also holds (`exception_info`).

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |
| `<home>` | the home folder on the authoring Mac: the start of the paths of the installed Harbor and Python in the tracebacks of the three trials stopped at the agent timeout (`exception_info` in their `result.json`) |
| `<model-endpoint>` | the URL of the model service the agent called: the `api_base` value, once in each `config.json`, `result.json` and `job_lock.json` |

Text files that changed carry one extra first line saying so. That line begins "# Redacted 2026-11-03:", the day these
copies were made (16:33 MST) from the run of that day, and it defines all four placeholders, `<local-scratch>` among
them. In the text files the only replacement is `<submission>`, and `<local-scratch>` replaced nothing in any file
here (it appears only in that line). JSON files cannot carry a comment, so they are listed here, with the text files.

| File | Replacements |
|---|---|
| `feature-leakage-churn__bkqVNqc/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `feature-leakage-churn__bkqVNqc/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `feature-leakage-churn__bkqVNqc/trial.log` (text; first line added) | `<submission>` x20 |
| `feature-leakage-churn__bkqVNqc/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `feature-leakage-churn__5ZCVEie/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `feature-leakage-churn__5ZCVEie/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `feature-leakage-churn__5ZCVEie/trial.log` (text; first line added) | `<submission>` x24 |
| `feature-leakage-churn__5ZCVEie/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `feature-leakage-churn__LcSFoqe/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `feature-leakage-churn__LcSFoqe/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1, `<home>` x54 |
| `feature-leakage-churn__LcSFoqe/trial.log` (text; first line added) | `<submission>` x61 |
| `feature-leakage-churn__LcSFoqe/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `feature-leakage-churn__MuZJi75/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `feature-leakage-churn__MuZJi75/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1, `<home>` x12 |
| `feature-leakage-churn__MuZJi75/trial.log` (text; first line added) | `<submission>` x58 |
| `feature-leakage-churn__MuZJi75/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `feature-leakage-churn__koFPMV7/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `feature-leakage-churn__koFPMV7/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `feature-leakage-churn__koFPMV7/trial.log` (text; first line added) | `<submission>` x30 |
| `feature-leakage-churn__koFPMV7/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `feature-leakage-churn__zhHaP4k/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `feature-leakage-churn__zhHaP4k/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1, `<home>` x54 |
| `feature-leakage-churn__zhHaP4k/trial.log` (text; first line added) | `<submission>` x226 |
| `feature-leakage-churn__zhHaP4k/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `feature-leakage-churn__pdidSxk/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `feature-leakage-churn__pdidSxk/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `feature-leakage-churn__pdidSxk/trial.log` (text; first line added) | `<submission>` x16 |
| `feature-leakage-churn__pdidSxk/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `feature-leakage-churn__TDWvT4Y/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `feature-leakage-churn__TDWvT4Y/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `feature-leakage-churn__TDWvT4Y/trial.log` (text; first line added) | `<submission>` x22 |
| `feature-leakage-churn__TDWvT4Y/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |

Files with no machine-specific path or service URL (copied byte for byte): 64, eight per trial (the three agent files,
`artifacts/manifest.json`, `job_result.json` and the three files in `verifier/`).
