# Proof matrix: tenant-isolation-docshare (run clone2, backend daytona, Harbor 0.25.0; local clock)

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 1` | 1 | [1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-canonical-clone2` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-nop-clone2` |
