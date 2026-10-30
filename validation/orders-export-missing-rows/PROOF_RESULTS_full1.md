# Proof matrix: orders-export-missing-rows (run full1, Daytona, Harbor 0.25.0; Mac clock MST)

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-canonical-full1` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-alt-full1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-nop-full1` |
| and_predicate | `-a oracle --ae SOLUTION=and_predicate` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-and_predicate-full1` |
| customer_offset | `-a oracle --ae SOLUTION=customer_offset` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-customer_offset-full1` |
| fix_helper_only | `-a oracle --ae SOLUTION=fix_helper_only` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-fix_helper_only-full1` |
| ignore_limit | `-a oracle --ae SOLUTION=ignore_limit` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-ignore_limit-full1` |
| lte_cursor | `-a oracle --ae SOLUTION=lte_cursor` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-lte_cursor-full1` |
| offset_cursor | `-a oracle --ae SOLUTION=offset_cursor` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-offset_cursor-full1` |
| order_by_id | `-a oracle --ae SOLUTION=order_by_id` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-order_by_id-full1` |
| rank_from_bottom | `-a oracle --ae SOLUTION=rank_from_bottom` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-rank_from_bottom-full1` |
| rewrite_timestamps_at_startup | `-a oracle --ae SOLUTION=rewrite_timestamps_at_startup` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-rewrite_timestamps_at_startup-full1` |
| snapshot_at_startup | `-a oracle --ae SOLUTION=snapshot_at_startup` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-snapshot_at_startup-full1` |
| tie_offset | `-a oracle --ae SOLUTION=tie_offset` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-tie_offset-full1` |
| unique_timestamps_dev_db | `-a oracle --ae SOLUTION=unique_timestamps_dev_db` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-unique_timestamps_dev_db-full1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-force-build-full1` |
