# Proof matrix: feature-leakage-churn (run v3, backend daytona, Harbor 0.25.0; local clock)

Package: jobs/feature-leakage-churn/package-v3/feature-leakage-churn, a copy of tasks/feature-leakage-churn without its [agent] network_mode line

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 5` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-canonical-v3` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-alt-v3` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-nop-v3` |
| backfill_event_time | `-a oracle --ae SOLUTION=backfill_event_time` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-backfill_event_time-v3` |
| cache_in_work | `-a oracle --ae SOLUTION=cache_in_work` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-cache_in_work-v3` |
| cache_visible | `-a oracle --ae SOLUTION=cache_visible` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-cache_visible-v3` |
| clip_last_login | `-a oracle --ae SOLUTION=clip_last_login` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-clip_last_login-v3` |
| current_plan | `-a oracle --ae SOLUTION=current_plan` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-current_plan-v3` |
| drop_plan | `-a oracle --ae SOLUTION=drop_plan` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-drop_plan-v3` |
| hourly_schedule | `-a oracle --ae SOLUTION=hourly_schedule` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-hourly_schedule-v3` |
| labels_matured | `-a oracle --ae SOLUTION=labels_matured` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-labels_matured-v3` |
| last_login_where_known | `-a oracle --ae SOLUTION=last_login_where_known` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-last_login_where_known-v3` |
| legacy_schedule | `-a oracle --ae SOLUTION=legacy_schedule` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-legacy_schedule-v3` |
| loaded_at_everywhere | `-a oracle --ae SOLUTION=loaded_at_everywhere` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-loaded_at_everywhere-v3` |
| log_lookup | `-a oracle --ae SOLUTION=log_lookup` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-log_lookup-v3` |
| min_commit | `-a oracle --ae SOLUTION=min_commit` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-min_commit-v3` |
| plan_changed_at | `-a oracle --ae SOLUTION=plan_changed_at` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-plan_changed_at-v3` |
| rollback_as_commit | `-a oracle --ae SOLUTION=rollback_as_commit` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-rollback_as_commit-v3` |
| scheduler_end | `-a oracle --ae SOLUTION=scheduler_end` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-scheduler_end-v3` |
| scheduler_start | `-a oracle --ae SOLUTION=scheduler_start` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-scheduler_start-v3` |
| status_event_date | `-a oracle --ae SOLUTION=status_event_date` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-status_event_date-v3` |
| status_latest_loaded | `-a oracle --ae SOLUTION=status_latest_loaded` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-status_latest_loaded-v3` |
| tune_model | `-a oracle --ae SOLUTION=tune_model` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-tune_model-v3` |
| v2_rule | `-a oracle --ae SOLUTION=v2_rule` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-v2_rule-v3` |
| window_on_loaded_at | `-a oracle --ae SOLUTION=window_on_loaded_at` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-window_on_loaded_at-v3` |
| zero_features | `-a oracle --ae SOLUTION=zero_features` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-zero_features-v3` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-force-build-v3` |
