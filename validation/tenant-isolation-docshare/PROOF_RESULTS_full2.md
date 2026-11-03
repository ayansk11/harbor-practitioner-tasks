# Proof matrix: tenant-isolation-docshare (run full2, backend daytona, Harbor 0.25.0; local clock)

Package: tasks/tenant-isolation-docshare

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 10` | 1 | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-canonical-full2` |
| alt | `-a oracle --ae SOLUTION=alt` | 1 | [1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-alt-full2` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-nop-full2` |
| deny_most | `-a oracle --ae SOLUTION=deny_most` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-deny_most-full2` |
| drop_org_switching | `-a oracle --ae SOLUTION=drop_org_switching` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-drop_org_switching-full2` |
| hardcode_visible_orgs | `-a oracle --ae SOLUTION=hardcode_visible_orgs` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-hardcode_visible_orgs-full2` |
| membership_plus_get | `-a oracle --ae SOLUTION=membership_plus_get` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-membership_plus_get-full2` |
| patch_get_only | `-a oracle --ae SOLUTION=patch_get_only` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-patch_get_only-full2` |
| phase_gate | `-a oracle --ae SOLUTION=phase_gate` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-phase_gate-full2` |
| replay_memo | `-a oracle --ae SOLUTION=replay_memo` | 0 | [0.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-replay_memo-full2` |
| force-build | `-a oracle --force-build` | 1 | [1.0] | - | PASS | `jobs/tenant-isolation-docshare/tenant-isolation-docshare-force-build-full2` |
