# Redactions in this traces folder (2026-10-31)

Every file here is a copy of a Harbor trial or job file of run `rev1` or of the Claude Code trials. Machine-specific paths were replaced; nothing else was changed (no reward, count or timing). The copy script checked this: each JSON file parses to the original with only the path strings replaced and identical numbers, and each text file differs from the original only on lines that held one of these paths. It also checked that no file holds a model service's key or the sandbox provider's key.

The Claude Code trial folders (`agent-claude-code/`) hold the trajectory Harbor wrote (`agent/trajectory.json`) and Claude Code's own stream output (`agent/claude-code.txt`). Claude Code's raw session folder (`agent/sessions/`), which records its full requests, its own system prompt included, is not copied.

| Placeholder | What it replaces |
|---|---|
| `<submission>` | the absolute path of the `submission/` folder on the authoring Mac (also its URL-encoded form in `trial_uri`) |

Text files that changed carry one extra first line saying so. JSON files cannot carry a comment, so they are listed here.

| File | Replacements |
|---|---|
| `alt_recount/config.json` | `<submission>` x2 |
| `alt_recount/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `alt_recount/trial.log` (text; first line added) | `<submission>` x2 |
| `alt_recount/job_lock.json` | `<submission>` x1 |
| `alt_time/config.json` | `<submission>` x2 |
| `alt_time/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `alt_time/trial.log` (text; first line added) | `<submission>` x2 |
| `alt_time/job_lock.json` | `<submission>` x1 |
| `b_only_patch/config.json` | `<submission>` x2 |
| `b_only_patch/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `b_only_patch/trial.log` (text; first line added) | `<submission>` x2 |
| `b_only_patch/job_lock.json` | `<submission>` x1 |
| `canonical/config.json` | `<submission>` x2 |
| `canonical/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `canonical/trial.log` (text; first line added) | `<submission>` x2 |
| `canonical/job_lock.json` | `<submission>` x10 |
| `fix_visible_only/config.json` | `<submission>` x2 |
| `fix_visible_only/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `fix_visible_only/trial.log` (text; first line added) | `<submission>` x2 |
| `fix_visible_only/job_lock.json` | `<submission>` x1 |
| `force-build/config.json` | `<submission>` x2 |
| `force-build/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `force-build/trial.log` (text; first line added) | `<submission>` x2 |
| `force-build/job_lock.json` | `<submission>` x1 |
| `hardcode_no_ship/config.json` | `<submission>` x2 |
| `hardcode_no_ship/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `hardcode_no_ship/trial.log` (text; first line added) | `<submission>` x2 |
| `hardcode_no_ship/job_lock.json` | `<submission>` x1 |
| `item_click_events/config.json` | `<submission>` x2 |
| `item_click_events/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `item_click_events/trial.log` (text; first line added) | `<submission>` x2 |
| `item_click_events/job_lock.json` | `<submission>` x1 |
| `keep_overrides/config.json` | `<submission>` x2 |
| `keep_overrides/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `keep_overrides/trial.log` (text; first line added) | `<submission>` x2 |
| `keep_overrides/job_lock.json` | `<submission>` x1 |
| `literal_bot_filter/config.json` | `<submission>` x2 |
| `literal_bot_filter/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `literal_bot_filter/trial.log` (text; first line added) | `<submission>` x2 |
| `literal_bot_filter/job_lock.json` | `<submission>` x1 |
| `no_bot_filter/config.json` | `<submission>` x2 |
| `no_bot_filter/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `no_bot_filter/trial.log` (text; first line added) | `<submission>` x2 |
| `no_bot_filter/job_lock.json` | `<submission>` x1 |
| `nop/config.json` | `<submission>` x2 |
| `nop/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `nop/trial.log` (text; first line added) | `<submission>` x2 |
| `nop/job_lock.json` | `<submission>` x1 |
| `not_nav_clicked/config.json` | `<submission>` x2 |
| `not_nav_clicked/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `not_nav_clicked/trial.log` (text; first line added) | `<submission>` x2 |
| `not_nav_clicked/job_lock.json` | `<submission>` x1 |
| `pageview_ci/config.json` | `<submission>` x2 |
| `pageview_ci/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `pageview_ci/trial.log` (text; first line added) | `<submission>` x2 |
| `pageview_ci/job_lock.json` | `<submission>` x1 |
| `platform_clicked/config.json` | `<submission>` x2 |
| `platform_clicked/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x3 |
| `platform_clicked/trial.log` (text; first line added) | `<submission>` x2 |
| `platform_clicked/job_lock.json` | `<submission>` x1 |
| `agent-claude-code/ab-test-reanalysis__3nb9x28/config.json` | `<submission>` x1 |
| `agent-claude-code/ab-test-reanalysis__3nb9x28/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x2 |
| `agent-claude-code/ab-test-reanalysis__3nb9x28/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-claude-code/ab-test-reanalysis__3nb9x28/job_lock.json` | `<submission>` x1 |
| `agent-claude-code/ab-test-reanalysis__NjrFLJq/config.json` | `<submission>` x1 |
| `agent-claude-code/ab-test-reanalysis__NjrFLJq/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x2 |
| `agent-claude-code/ab-test-reanalysis__NjrFLJq/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-claude-code/ab-test-reanalysis__NjrFLJq/job_lock.json` | `<submission>` x2 |
| `agent-claude-code/ab-test-reanalysis__SpwbpTd/config.json` | `<submission>` x1 |
| `agent-claude-code/ab-test-reanalysis__SpwbpTd/result.json` | `<submission>` (URL-encoded form) x1, `<submission>` x2 |
| `agent-claude-code/ab-test-reanalysis__SpwbpTd/trial.log` (text; first line added) | `<submission>` x2 |
| `agent-claude-code/ab-test-reanalysis__SpwbpTd/job_lock.json` | `<submission>` x2 |

Files with no machine-specific path (copied byte for byte): 110.
