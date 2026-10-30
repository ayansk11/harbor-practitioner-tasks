# Proof matrix: feature-leakage-churn (run full1, Daytona, Harbor 0.25.0; Mac clock MST)

Overall: NOT ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, None, 1.0, 1.0, 1.0, 1.0] | ['DaytonaConnectionError'] | FAIL | `jobs/feature-leakage-churn/feature-leakage-churn-canonical-full1` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-alt-full1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-nop-full1` |
| cache_visible | `-a oracle --ae SOLUTION=cache_visible` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-cache_visible-full1` |
| closed_right | `-a oracle --ae SOLUTION=closed_right` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-closed_right-full1` |
| drop_leaky | `-a oracle --ae SOLUTION=drop_leaky` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-drop_leaky-full1` |
| label_at_t | `-a oracle --ae SOLUTION=label_at_t` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-label_at_t-full1` |
| loo_encoding | `-a oracle --ae SOLUTION=loo_encoding` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-loo_encoding-full1` |
| miss_imputation | `-a oracle --ae SOLUTION=miss_imputation` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-miss_imputation-full1` |
| open_left_30d | `-a oracle --ae SOLUTION=open_left_30d` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-open_left_30d-full1` |
| status_same_day | `-a oracle --ae SOLUTION=status_same_day` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-status_same_day-full1` |
| tune_model | `-a oracle --ae SOLUTION=tune_model` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-tune_model-full1` |
| zero_features | `-a oracle --ae SOLUTION=zero_features` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-zero_features-full1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-force-build-full1` |
