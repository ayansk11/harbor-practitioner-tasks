# Proof matrix: orders-export-missing-rows (run clone2, backend daytona, Harbor 0.25.0; local clock)

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 1` | 1 | [1.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-canonical-clone2` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/orders-export-missing-rows/orders-export-missing-rows-nop-clone2` |
