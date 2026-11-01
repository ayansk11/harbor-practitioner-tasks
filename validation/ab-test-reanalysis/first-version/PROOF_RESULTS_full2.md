# Proof matrix: ab-test-reanalysis (run full2, Daytona, Harbor 0.25.0; Mac clock MST)

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-canonical-full2` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-alt-full2` |
| alt_cr1 | `-a oracle --ae SOLUTION=alt_cr1` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-alt_cr1-full2` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-nop-full2` |
| constant_inflation | `-a oracle --ae SOLUTION=constant_inflation` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-constant_inflation-full2` |
| fix_bots_only | `-a oracle --ae SOLUTION=fix_bots_only` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-fix_bots_only-full2` |
| fix_ci_only | `-a oracle --ae SOLUTION=fix_ci_only` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-fix_ci_only-full2` |
| fix_visible_result_only | `-a oracle --ae SOLUTION=fix_visible_result_only` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-fix_visible_result_only-full2` |
| hardcode_no_ship | `-a oracle --ae SOLUTION=hardcode_no_ship` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-hardcode_no_ship-full2` |
| icc_tuned | `-a oracle --ae SOLUTION=icc_tuned` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-icc_tuned-full2` |
| kish_tuned | `-a oracle --ae SOLUTION=kish_tuned` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-kish_tuned-full2` |
| mean_of_ratios | `-a oracle --ae SOLUTION=mean_of_ratios` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-mean_of_ratios-full2` |
| no_srm_gate | `-a oracle --ae SOLUTION=no_srm_gate` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-no_srm_gate-full2` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-force-build-full2` |
