# Proof matrix: tenant-isolation-docshare (run full1, Daytona, Harbor 0.25.0; Mac clock MST)

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-canonical-full1` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-alt-full1` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-nop-full1` |
| deny_most | `-a oracle --ae SOLUTION=deny_most` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-deny_most-full1` |
| drop_org_switching | `-a oracle --ae SOLUTION=drop_org_switching` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-drop_org_switching-full1` |
| hardcode_visible_orgs | `-a oracle --ae SOLUTION=hardcode_visible_orgs` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-hardcode_visible_orgs-full1` |
| membership_plus_get | `-a oracle --ae SOLUTION=membership_plus_get` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-membership_plus_get-full1` |
| patch_get_only | `-a oracle --ae SOLUTION=patch_get_only` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-patch_get_only-full1` |
| phase_gate | `-a oracle --ae SOLUTION=phase_gate` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-phase_gate-full1` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-force-build-full1` |
