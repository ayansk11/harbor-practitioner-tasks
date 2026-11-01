# Redactions in this traces folder (2026-10-31)

Every file here is a copy of a Harbor trial or job file of task v3: its Daytona proof run `v3` (one trial per variant)
and its three Claude Code trials (`agent-claude-code/`). Machine-specific paths were replaced; nothing else was changed
(no reward, count or timing). A comparison of every file here with its original in the job folders (2026-10-31) found
each changed JSON file equal to its original once the path strings are replaced (the numbers identical), each changed
text file equal to its original with the paths replaced and one line added at the top, and every other file equal to
its original byte for byte. A scan of the copies (2026-10-31) found no model service's key and no sandbox provider's
key in any file.

The Claude Code trial folders (`agent-claude-code/`) hold the trajectory Harbor wrote (`agent/trajectory.json`) and
Claude Code's own stream output (`agent/claude-code.txt`). Claude Code's raw session folder (`agent/sessions/`), which
records its full requests, its own system prompt included, is not copied.

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |

Text files that changed carry one extra first line saying so. That line, the copy script's own, also defines
`<home>`, `<local-scratch>` and `<model-endpoint>`; none of the three replaced anything in this folder's files (they
appear only in that line). JSON files cannot carry a comment, so they are listed here, with the text files.

| File | Replacements |
|---|---|
| `alt/config.json` | `<submission>` x2 |
| `alt/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `alt/trial.log` (text; first line added) | `<submission>` x2 |
| `alt/job_lock.json` | `<submission>` x1 |
| `backfill_event_time/config.json` | `<submission>` x2 |
| `backfill_event_time/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `backfill_event_time/trial.log` (text; first line added) | `<submission>` x2 |
| `backfill_event_time/job_lock.json` | `<submission>` x1 |
| `cache_in_work/config.json` | `<submission>` x2 |
| `cache_in_work/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `cache_in_work/trial.log` (text; first line added) | `<submission>` x2 |
| `cache_in_work/job_lock.json` | `<submission>` x1 |
| `cache_visible/config.json` | `<submission>` x2 |
| `cache_visible/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `cache_visible/trial.log` (text; first line added) | `<submission>` x2 |
| `cache_visible/job_lock.json` | `<submission>` x1 |
| `canonical/config.json` | `<submission>` x2 |
| `canonical/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `canonical/trial.log` (text; first line added) | `<submission>` x2 |
| `canonical/job_lock.json` | `<submission>` x5 |
| `clip_last_login/config.json` | `<submission>` x2 |
| `clip_last_login/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `clip_last_login/trial.log` (text; first line added) | `<submission>` x2 |
| `clip_last_login/job_lock.json` | `<submission>` x1 |
| `current_plan/config.json` | `<submission>` x2 |
| `current_plan/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `current_plan/trial.log` (text; first line added) | `<submission>` x2 |
| `current_plan/job_lock.json` | `<submission>` x1 |
| `drop_plan/config.json` | `<submission>` x2 |
| `drop_plan/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `drop_plan/trial.log` (text; first line added) | `<submission>` x2 |
| `drop_plan/job_lock.json` | `<submission>` x1 |
| `force-build/config.json` | `<submission>` x2 |
| `force-build/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `force-build/trial.log` (text; first line added) | `<submission>` x2 |
| `force-build/job_lock.json` | `<submission>` x1 |
| `hourly_schedule/config.json` | `<submission>` x2 |
| `hourly_schedule/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `hourly_schedule/trial.log` (text; first line added) | `<submission>` x2 |
| `hourly_schedule/job_lock.json` | `<submission>` x1 |
| `labels_matured/config.json` | `<submission>` x2 |
| `labels_matured/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `labels_matured/trial.log` (text; first line added) | `<submission>` x2 |
| `labels_matured/job_lock.json` | `<submission>` x1 |
| `last_login_where_known/config.json` | `<submission>` x2 |
| `last_login_where_known/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `last_login_where_known/trial.log` (text; first line added) | `<submission>` x2 |
| `last_login_where_known/job_lock.json` | `<submission>` x1 |
| `legacy_schedule/config.json` | `<submission>` x2 |
| `legacy_schedule/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `legacy_schedule/trial.log` (text; first line added) | `<submission>` x2 |
| `legacy_schedule/job_lock.json` | `<submission>` x1 |
| `loaded_at_everywhere/config.json` | `<submission>` x2 |
| `loaded_at_everywhere/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `loaded_at_everywhere/trial.log` (text; first line added) | `<submission>` x2 |
| `loaded_at_everywhere/job_lock.json` | `<submission>` x1 |
| `log_lookup/config.json` | `<submission>` x2 |
| `log_lookup/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `log_lookup/trial.log` (text; first line added) | `<submission>` x2 |
| `log_lookup/job_lock.json` | `<submission>` x1 |
| `min_commit/config.json` | `<submission>` x2 |
| `min_commit/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `min_commit/trial.log` (text; first line added) | `<submission>` x2 |
| `min_commit/job_lock.json` | `<submission>` x1 |
| `nop/config.json` | `<submission>` x2 |
| `nop/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `nop/trial.log` (text; first line added) | `<submission>` x2 |
| `nop/job_lock.json` | `<submission>` x1 |
| `plan_changed_at/config.json` | `<submission>` x2 |
| `plan_changed_at/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `plan_changed_at/trial.log` (text; first line added) | `<submission>` x2 |
| `plan_changed_at/job_lock.json` | `<submission>` x1 |
| `rollback_as_commit/config.json` | `<submission>` x2 |
| `rollback_as_commit/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `rollback_as_commit/trial.log` (text; first line added) | `<submission>` x2 |
| `rollback_as_commit/job_lock.json` | `<submission>` x1 |
| `scheduler_end/config.json` | `<submission>` x2 |
| `scheduler_end/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `scheduler_end/trial.log` (text; first line added) | `<submission>` x2 |
| `scheduler_end/job_lock.json` | `<submission>` x1 |
| `scheduler_start/config.json` | `<submission>` x2 |
| `scheduler_start/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `scheduler_start/trial.log` (text; first line added) | `<submission>` x2 |
| `scheduler_start/job_lock.json` | `<submission>` x1 |
| `status_event_date/config.json` | `<submission>` x2 |
| `status_event_date/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `status_event_date/trial.log` (text; first line added) | `<submission>` x2 |
| `status_event_date/job_lock.json` | `<submission>` x1 |
| `status_latest_loaded/config.json` | `<submission>` x2 |
| `status_latest_loaded/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `status_latest_loaded/trial.log` (text; first line added) | `<submission>` x2 |
| `status_latest_loaded/job_lock.json` | `<submission>` x1 |
| `tune_model/config.json` | `<submission>` x2 |
| `tune_model/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `tune_model/trial.log` (text; first line added) | `<submission>` x2 |
| `tune_model/job_lock.json` | `<submission>` x1 |
| `v2_rule/config.json` | `<submission>` x2 |
| `v2_rule/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `v2_rule/trial.log` (text; first line added) | `<submission>` x2 |
| `v2_rule/job_lock.json` | `<submission>` x1 |
| `window_on_loaded_at/config.json` | `<submission>` x2 |
| `window_on_loaded_at/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `window_on_loaded_at/trial.log` (text; first line added) | `<submission>` x2 |
| `window_on_loaded_at/job_lock.json` | `<submission>` x1 |
| `zero_features/config.json` | `<submission>` x2 |
| `zero_features/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `zero_features/trial.log` (text; first line added) | `<submission>` x2 |
| `zero_features/job_lock.json` | `<submission>` x1 |
| `agent-claude-code/feature-leakage-churn__58R6Roz/config.json` | `<submission>` x1 |
| `agent-claude-code/feature-leakage-churn__58R6Roz/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x2 |
| `agent-claude-code/feature-leakage-churn__58R6Roz/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-claude-code/feature-leakage-churn__58R6Roz/job_lock.json` | `<submission>` x3 |
| `agent-claude-code/feature-leakage-churn__oYkSBpm/config.json` | `<submission>` x1 |
| `agent-claude-code/feature-leakage-churn__oYkSBpm/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x2 |
| `agent-claude-code/feature-leakage-churn__oYkSBpm/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-claude-code/feature-leakage-churn__oYkSBpm/job_lock.json` | `<submission>` x3 |
| `agent-claude-code/feature-leakage-churn__qthVz4g/config.json` | `<submission>` x1 |
| `agent-claude-code/feature-leakage-churn__qthVz4g/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x2 |
| `agent-claude-code/feature-leakage-churn__qthVz4g/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-claude-code/feature-leakage-churn__qthVz4g/job_lock.json` | `<submission>` x3 |

Files with no machine-specific path (copied byte for byte): 182 (161, plus 21 in `agent-claude-code/`).
