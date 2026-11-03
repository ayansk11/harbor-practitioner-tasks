# Redactions in this traces folder (2026-10-29; `agent-r3/` added 2026-10-31)

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
| `canonical/config.json` | `<submission>` x2 |
| `canonical/job_lock.json` | `<submission>` x10 |
| `canonical/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `canonical/trial.log` (text; first line added) | `<submission>` x2 |
| `deny_most/config.json` | `<submission>` x2 |
| `deny_most/job_lock.json` | `<submission>` x1 |
| `deny_most/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `deny_most/trial.log` (text; first line added) | `<submission>` x2 |
| `drop_org_switching/config.json` | `<submission>` x2 |
| `drop_org_switching/job_lock.json` | `<submission>` x1 |
| `drop_org_switching/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `drop_org_switching/trial.log` (text; first line added) | `<submission>` x2 |
| `force-build/config.json` | `<submission>` x2 |
| `force-build/job_lock.json` | `<submission>` x1 |
| `force-build/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `force-build/trial.log` (text; first line added) | `<submission>` x2 |
| `hardcode_visible_orgs/config.json` | `<submission>` x2 |
| `hardcode_visible_orgs/job_lock.json` | `<submission>` x1 |
| `hardcode_visible_orgs/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `hardcode_visible_orgs/trial.log` (text; first line added) | `<submission>` x2 |
| `membership_plus_get/config.json` | `<submission>` x2 |
| `membership_plus_get/job_lock.json` | `<submission>` x1 |
| `membership_plus_get/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `membership_plus_get/trial.log` (text; first line added) | `<submission>` x2 |
| `nop/config.json` | `<submission>` x2 |
| `nop/job_lock.json` | `<submission>` x1 |
| `nop/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `nop/trial.log` (text; first line added) | `<submission>` x2 |
| `patch_get_only/config.json` | `<submission>` x2 |
| `patch_get_only/job_lock.json` | `<submission>` x1 |
| `patch_get_only/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `patch_get_only/trial.log` (text; first line added) | `<submission>` x2 |
| `phase_gate/config.json` | `<submission>` x2 |
| `phase_gate/job_lock.json` | `<submission>` x1 |
| `phase_gate/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `phase_gate/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/tenant-isolation-docshare__5JS5qnC/config.json` | `<model-endpoint>` x1 |
| `agent-r3/tenant-isolation-docshare__5JS5qnC/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/tenant-isolation-docshare__5JS5qnC/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/tenant-isolation-docshare__5JS5qnC/job_lock.json` | `<model-endpoint>` x3 |
| `agent-r3/tenant-isolation-docshare__9n7yLqH/config.json` | `<model-endpoint>` x1 |
| `agent-r3/tenant-isolation-docshare__9n7yLqH/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/tenant-isolation-docshare__9n7yLqH/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/tenant-isolation-docshare__9n7yLqH/job_lock.json` | `<model-endpoint>` x3 |
| `agent-r3/tenant-isolation-docshare__U5her8X/config.json` | `<model-endpoint>` x1 |
| `agent-r3/tenant-isolation-docshare__U5her8X/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/tenant-isolation-docshare__U5her8X/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/tenant-isolation-docshare__U5her8X/job_lock.json` | `<model-endpoint>` x3 |

Files with no machine-specific path or model URL (copied byte for byte): 83 (59, plus 24 in `agent-r3/`).
