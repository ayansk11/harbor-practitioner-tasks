# Proof matrix: ab-test-reanalysis (run full1, Daytona, Harbor 0.25.0; Mac clock MST)

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-canonical-full1` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-alt-full1` |
| alt_cr1 | `-a oracle --ae SOLUTION=alt_cr1` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-alt_cr1-full1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-nop-full1` |
| constant_inflation | `-a oracle --ae SOLUTION=constant_inflation` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-constant_inflation-full1` |
| fix_bots_only | `-a oracle --ae SOLUTION=fix_bots_only` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-fix_bots_only-full1` |
| fix_ci_only | `-a oracle --ae SOLUTION=fix_ci_only` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-fix_ci_only-full1` |
| fix_visible_result_only | `-a oracle --ae SOLUTION=fix_visible_result_only` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-fix_visible_result_only-full1` |
| hardcode_no_ship | `-a oracle --ae SOLUTION=hardcode_no_ship` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-hardcode_no_ship-full1` |
| icc_tuned | `-a oracle --ae SOLUTION=icc_tuned` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-icc_tuned-full1` |
| kish_tuned | `-a oracle --ae SOLUTION=kish_tuned` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-kish_tuned-full1` |
| mean_of_ratios | `-a oracle --ae SOLUTION=mean_of_ratios` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-mean_of_ratios-full1` |
| no_srm_gate | `-a oracle --ae SOLUTION=no_srm_gate` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-no_srm_gate-full1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-force-build-full1` |
