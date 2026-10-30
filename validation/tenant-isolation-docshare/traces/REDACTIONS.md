# Redactions in this traces folder (2026-10-29)

Every file here is a copy of a Harbor trial or job file. Machine-specific paths were replaced; nothing else was changed (no reward, count or timing). The copy script checked this: each JSON file parses to the original with only the path strings replaced and identical numbers, and each text file differs from the original only on lines that held one of these paths.

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |
| `<home>` | other paths under the author's home folder (for example the Harbor tool install in a traceback) |
| `<local-scratch>` | the session scratch folder of the authoring tool (a temporary folder on the Mac) |

Text files that changed carry one extra first line saying so. JSON files cannot carry a comment, so they are listed here.

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

Files with no machine-specific path (copied byte for byte): 59.
