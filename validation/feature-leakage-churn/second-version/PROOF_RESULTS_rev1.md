# Proof matrix: feature-leakage-churn (run rev1, backend daytona, Harbor 0.25.0; local clock)

Package: jobs/feature-leakage-churn/package-rev1/feature-leakage-churn, a copy of tasks/feature-leakage-churn without its [agent] network_mode line

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 5` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-canonical-rev1` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-alt-rev1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-nop-rev1` |
| backfill_event_time | `-a oracle --ae SOLUTION=backfill_event_time` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-backfill_event_time-rev1` |
| cache_visible | `-a oracle --ae SOLUTION=cache_visible` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-cache_visible-rev1` |
| clip_last_login | `-a oracle --ae SOLUTION=clip_last_login` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-clip_last_login-rev1` |
| current_plan | `-a oracle --ae SOLUTION=current_plan` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-current_plan-rev1` |
| drop_plan | `-a oracle --ae SOLUTION=drop_plan` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-drop_plan-rev1` |
| hourly_schedule | `-a oracle --ae SOLUTION=hourly_schedule` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-hourly_schedule-rev1` |
| labels_matured | `-a oracle --ae SOLUTION=labels_matured` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-labels_matured-rev1` |
| last_login_where_known | `-a oracle --ae SOLUTION=last_login_where_known` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-last_login_where_known-rev1` |
| legacy_ignore_status | `-a oracle --ae SOLUTION=legacy_ignore_status` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-legacy_ignore_status-rev1` |
| legacy_schedule | `-a oracle --ae SOLUTION=legacy_schedule` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-legacy_schedule-rev1` |
| loaded_at_everywhere | `-a oracle --ae SOLUTION=loaded_at_everywhere` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-loaded_at_everywhere-rev1` |
| log_lookup | `-a oracle --ae SOLUTION=log_lookup` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-log_lookup-rev1` |
| plan_changed_at | `-a oracle --ae SOLUTION=plan_changed_at` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-plan_changed_at-rev1` |
| status_event_date | `-a oracle --ae SOLUTION=status_event_date` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-status_event_date-rev1` |
| status_latest_loaded | `-a oracle --ae SOLUTION=status_latest_loaded` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-status_latest_loaded-rev1` |
| tune_model | `-a oracle --ae SOLUTION=tune_model` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-tune_model-rev1` |
| window_on_loaded_at | `-a oracle --ae SOLUTION=window_on_loaded_at` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-window_on_loaded_at-rev1` |
| zero_features | `-a oracle --ae SOLUTION=zero_features` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-zero_features-rev1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-force-build-rev1` |
