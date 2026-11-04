# Redactions in this traces folder (2026-11-03)

Every file here is a copy of a Harbor trial or job file of run m1 of 2026-11-03: the eight trials of this task with
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
terminal). These records carry the model's own characters unchanged, a few of them outside ASCII (a non-breaking
hyphen in both `gpt-oss-120b` trials, an en dash in `__JYJviea`). Not copied: each trial's own `lock.json` (equal to
the one trial entry of the job's `lock.json`, which is copied as `job_lock.json`), the job's `config.json` and
`job.log`, and the downloaded copy of `/app` (`artifacts/app/`; `artifacts/manifest.json` is copied).

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |
| `<model-endpoint>` | the URL of the model service the agent called: the `api_base` value, once in each `config.json`, `result.json` and `job_lock.json` |

Text files that changed carry one extra first line saying so. That line begins "# Redacted 2026-11-03:", the day these
copies were made (16:33 MST) from the run of that day. It also defines `<home>` and `<local-scratch>`; neither replaced
anything in this folder's files (they appear only in that line). JSON files cannot carry a comment, so they are listed
here, with the text files.

| File | Replacements |
|---|---|
| `ab-test-reanalysis__tPd3ppr/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `ab-test-reanalysis__tPd3ppr/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `ab-test-reanalysis__tPd3ppr/trial.log` (text; first line added) | `<submission>` x10 |
| `ab-test-reanalysis__tPd3ppr/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `ab-test-reanalysis__muieaNN/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `ab-test-reanalysis__muieaNN/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `ab-test-reanalysis__muieaNN/trial.log` (text; first line added) | `<submission>` x15 |
| `ab-test-reanalysis__muieaNN/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `ab-test-reanalysis__U9Ka5Fx/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `ab-test-reanalysis__U9Ka5Fx/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `ab-test-reanalysis__U9Ka5Fx/trial.log` (text; first line added) | `<submission>` x17 |
| `ab-test-reanalysis__U9Ka5Fx/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `ab-test-reanalysis__9bw5VW9/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `ab-test-reanalysis__9bw5VW9/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `ab-test-reanalysis__9bw5VW9/trial.log` (text; first line added) | `<submission>` x13 |
| `ab-test-reanalysis__9bw5VW9/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `ab-test-reanalysis__KhS7pKJ/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `ab-test-reanalysis__KhS7pKJ/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `ab-test-reanalysis__KhS7pKJ/trial.log` (text; first line added) | `<submission>` x14 |
| `ab-test-reanalysis__KhS7pKJ/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `ab-test-reanalysis__JYJviea/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `ab-test-reanalysis__JYJviea/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `ab-test-reanalysis__JYJviea/trial.log` (text; first line added) | `<submission>` x13 |
| `ab-test-reanalysis__JYJviea/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `ab-test-reanalysis__JZg3Hry/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `ab-test-reanalysis__JZg3Hry/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `ab-test-reanalysis__JZg3Hry/trial.log` (text; first line added) | `<submission>` x12 |
| `ab-test-reanalysis__JZg3Hry/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |
| `ab-test-reanalysis__sFqSFFL/config.json` | `<submission>` x2, `<model-endpoint>` x1 |
| `ab-test-reanalysis__sFqSFFL/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3, `<model-endpoint>` x1 |
| `ab-test-reanalysis__sFqSFFL/trial.log` (text; first line added) | `<submission>` x13 |
| `ab-test-reanalysis__sFqSFFL/job_lock.json` | `<submission>` x1, `<model-endpoint>` x1 |

Files with no machine-specific path or service URL (copied byte for byte): 64, eight per trial (the three agent files,
`artifacts/manifest.json`, `job_result.json` and the three files in `verifier/`).
