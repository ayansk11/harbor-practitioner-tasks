# Proof matrix: ab-test-reanalysis (run rev1, backend daytona, Harbor 0.25.0; local clock)

Package: jobs/ab-test-reanalysis/package-rev1/ab-test-reanalysis, a copy of tasks/ab-test-reanalysis without its [agent] network_mode line

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-canonical-rev1` |
| alt_recount | `-a oracle --ae SOLUTION=alt_recount` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-alt_recount-rev1` |
| alt_time | `-a oracle --ae SOLUTION=alt_time` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-alt_time-rev1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-nop-rev1` |
| b_only_patch | `-a oracle --ae SOLUTION=b_only_patch` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-b_only_patch-rev1` |
| fix_visible_only | `-a oracle --ae SOLUTION=fix_visible_only` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-fix_visible_only-rev1` |
| hardcode_no_ship | `-a oracle --ae SOLUTION=hardcode_no_ship` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-hardcode_no_ship-rev1` |
| item_click_events | `-a oracle --ae SOLUTION=item_click_events` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-item_click_events-rev1` |
| keep_overrides | `-a oracle --ae SOLUTION=keep_overrides` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-keep_overrides-rev1` |
| literal_bot_filter | `-a oracle --ae SOLUTION=literal_bot_filter` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-literal_bot_filter-rev1` |
| no_bot_filter | `-a oracle --ae SOLUTION=no_bot_filter` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-no_bot_filter-rev1` |
| not_nav_clicked | `-a oracle --ae SOLUTION=not_nav_clicked` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-not_nav_clicked-rev1` |
| pageview_ci | `-a oracle --ae SOLUTION=pageview_ci` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-pageview_ci-rev1` |
| platform_clicked | `-a oracle --ae SOLUTION=platform_clicked` | 0 | [0.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-platform_clicked-rev1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/ab-test-reanalysis/ab-test-reanalysis-force-build-rev1` |
