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
| `and_predicate/config.json` | `<submission>` x2 |
| `and_predicate/job_lock.json` | `<submission>` x1 |
| `and_predicate/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `and_predicate/trial.log` (text; first line added) | `<submission>` x2 |
| `canonical/config.json` | `<submission>` x2 |
| `canonical/job_lock.json` | `<submission>` x10 |
| `canonical/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `canonical/trial.log` (text; first line added) | `<submission>` x2 |
| `customer_offset/config.json` | `<submission>` x2 |
| `customer_offset/job_lock.json` | `<submission>` x1 |
| `customer_offset/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `customer_offset/trial.log` (text; first line added) | `<submission>` x2 |
| `fix_helper_only/config.json` | `<submission>` x2 |
| `fix_helper_only/job_lock.json` | `<submission>` x1 |
| `fix_helper_only/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `fix_helper_only/trial.log` (text; first line added) | `<submission>` x2 |
| `force-build/config.json` | `<submission>` x2 |
| `force-build/job_lock.json` | `<submission>` x1 |
| `force-build/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `force-build/trial.log` (text; first line added) | `<submission>` x2 |
| `ignore_limit/config.json` | `<submission>` x2 |
| `ignore_limit/job_lock.json` | `<submission>` x1 |
| `ignore_limit/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `ignore_limit/trial.log` (text; first line added) | `<submission>` x2 |
| `lte_cursor/config.json` | `<submission>` x2 |
| `lte_cursor/job_lock.json` | `<submission>` x1 |
| `lte_cursor/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `lte_cursor/trial.log` (text; first line added) | `<submission>` x2 |
| `nop/config.json` | `<submission>` x2 |
| `nop/job_lock.json` | `<submission>` x1 |
| `nop/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `nop/trial.log` (text; first line added) | `<submission>` x2 |
| `offset_cursor/config.json` | `<submission>` x2 |
| `offset_cursor/job_lock.json` | `<submission>` x1 |
| `offset_cursor/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `offset_cursor/trial.log` (text; first line added) | `<submission>` x2 |
| `order_by_id/config.json` | `<submission>` x2 |
| `order_by_id/job_lock.json` | `<submission>` x1 |
| `order_by_id/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `order_by_id/trial.log` (text; first line added) | `<submission>` x2 |
| `rank_from_bottom/config.json` | `<submission>` x2 |
| `rank_from_bottom/job_lock.json` | `<submission>` x1 |
| `rank_from_bottom/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `rank_from_bottom/trial.log` (text; first line added) | `<submission>` x2 |
| `rewrite_timestamps_at_startup/config.json` | `<submission>` x2 |
| `rewrite_timestamps_at_startup/job_lock.json` | `<submission>` x1 |
| `rewrite_timestamps_at_startup/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `rewrite_timestamps_at_startup/trial.log` (text; first line added) | `<submission>` x2 |
| `snapshot_at_startup/config.json` | `<submission>` x2 |
| `snapshot_at_startup/job_lock.json` | `<submission>` x1 |
| `snapshot_at_startup/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `snapshot_at_startup/trial.log` (text; first line added) | `<submission>` x2 |
| `tie_offset/config.json` | `<submission>` x2 |
| `tie_offset/job_lock.json` | `<submission>` x1 |
| `tie_offset/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `tie_offset/trial.log` (text; first line added) | `<submission>` x2 |
| `unique_timestamps_dev_db/config.json` | `<submission>` x2 |
| `unique_timestamps_dev_db/job_lock.json` | `<submission>` x1 |
| `unique_timestamps_dev_db/result.json` | `<submission>` x3, `<submission>` (URL-encoded form) x1 |
| `unique_timestamps_dev_db/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/orders-export-missing-rows__8QFnJgD/config.json` | `<model-endpoint>` x1 |
| `agent-r3/orders-export-missing-rows__8QFnJgD/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/orders-export-missing-rows__8QFnJgD/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/orders-export-missing-rows__8QFnJgD/job_lock.json` | `<model-endpoint>` x3 |
| `agent-r3/orders-export-missing-rows__Ro8uMJk/config.json` | `<model-endpoint>` x1 |
| `agent-r3/orders-export-missing-rows__Ro8uMJk/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/orders-export-missing-rows__Ro8uMJk/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/orders-export-missing-rows__Ro8uMJk/job_lock.json` | `<model-endpoint>` x3 |
| `agent-r3/orders-export-missing-rows__jmkPRP3/config.json` | `<model-endpoint>` x1 |
| `agent-r3/orders-export-missing-rows__jmkPRP3/result.json` | `<submission>` (URL-encoded form) x1, `<model-endpoint>` x1 |
| `agent-r3/orders-export-missing-rows__jmkPRP3/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-r3/orders-export-missing-rows__jmkPRP3/job_lock.json` | `<model-endpoint>` x3 |

Files with no machine-specific path or model URL (copied byte for byte): 119 (95, plus 24 in `agent-r3/`).
