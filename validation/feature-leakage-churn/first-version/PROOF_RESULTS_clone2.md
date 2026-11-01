# Proof matrix: feature-leakage-churn (run clone2, backend daytona, Harbor 0.25.0; local clock)

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 1` | 1 | [1.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-canonical-clone2` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/feature-leakage-churn/feature-leakage-churn-nop-clone2` |
