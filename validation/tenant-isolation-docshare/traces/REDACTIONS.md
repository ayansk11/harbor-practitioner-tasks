# Redactions in this traces folder (2026-11-03)

Every file here is a copy of a Harbor trial or job file of the Daytona proof run `full2`, one trial per variant.
Machine-specific paths were replaced; nothing else was changed (no reward, count or timing). A comparison of every
file here with its original in the job folders (2026-11-03) found each changed JSON file equal to its original once
the path strings are replaced (the numbers identical, the bytes too), each changed text file equal to its original
with the paths replaced and one line added at the top, and every other file equal to its original byte for byte. A
scan of the copies (2026-11-03) found no sandbox provider's key, no other path of the authoring Mac and no account
name in any file.

The earlier grader's traces, with the agent trials of 2026-10-30, are in `../first-version/traces/`, which has its
own `REDACTIONS.md`.

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |

Text files that changed carry one extra first line saying so. That line begins "# Redacted 2026-11-03:", the day these
copies were made (04:17 MST) from the run of that day. It also defines `<home>`, `<local-scratch>` and
`<model-endpoint>`; none of the three replaced anything in this folder's files (they appear only in that line). JSON
files cannot carry a comment, so they are listed here, with the text files.

| File | Replacements |
|---|---|
| `alt/config.json` | `<submission>` x2 |
| `alt/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `alt/trial.log` (text; first line added) | `<submission>` x2 |
| `alt/job_lock.json` | `<submission>` x1 |
| `canonical/config.json` | `<submission>` x2 |
| `canonical/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `canonical/trial.log` (text; first line added) | `<submission>` x2 |
| `canonical/job_lock.json` | `<submission>` x10 |
| `deny_most/config.json` | `<submission>` x2 |
| `deny_most/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `deny_most/trial.log` (text; first line added) | `<submission>` x2 |
| `deny_most/job_lock.json` | `<submission>` x1 |
| `drop_org_switching/config.json` | `<submission>` x2 |
| `drop_org_switching/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `drop_org_switching/trial.log` (text; first line added) | `<submission>` x2 |
| `drop_org_switching/job_lock.json` | `<submission>` x1 |
| `force-build/config.json` | `<submission>` x2 |
| `force-build/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `force-build/trial.log` (text; first line added) | `<submission>` x2 |
| `force-build/job_lock.json` | `<submission>` x1 |
| `hardcode_visible_orgs/config.json` | `<submission>` x2 |
| `hardcode_visible_orgs/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `hardcode_visible_orgs/trial.log` (text; first line added) | `<submission>` x2 |
| `hardcode_visible_orgs/job_lock.json` | `<submission>` x1 |
| `membership_plus_get/config.json` | `<submission>` x2 |
| `membership_plus_get/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `membership_plus_get/trial.log` (text; first line added) | `<submission>` x2 |
| `membership_plus_get/job_lock.json` | `<submission>` x1 |
| `nop/config.json` | `<submission>` x2 |
| `nop/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `nop/trial.log` (text; first line added) | `<submission>` x2 |
| `nop/job_lock.json` | `<submission>` x1 |
| `patch_get_only/config.json` | `<submission>` x2 |
| `patch_get_only/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `patch_get_only/trial.log` (text; first line added) | `<submission>` x2 |
| `patch_get_only/job_lock.json` | `<submission>` x1 |
| `phase_gate/config.json` | `<submission>` x2 |
| `phase_gate/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `phase_gate/trial.log` (text; first line added) | `<submission>` x2 |
| `phase_gate/job_lock.json` | `<submission>` x1 |
| `replay_memo/config.json` | `<submission>` x2 |
| `replay_memo/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `replay_memo/trial.log` (text; first line added) | `<submission>` x2 |
| `replay_memo/job_lock.json` | `<submission>` x1 |

Files with no machine-specific path (copied byte for byte): 65.
