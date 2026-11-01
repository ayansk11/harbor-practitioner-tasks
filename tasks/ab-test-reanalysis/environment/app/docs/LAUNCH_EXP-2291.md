# Launch record: EXP-2291 "related items v2"

| Field | Value |
|---|---|
| Experiment | EXP-2291, related items v2 (RI-311) |
| Owner | product pages team |
| Unit | user |
| Allocation | 50/50, by the assignment service's hash of the salt and the user id |
| Salt | `exp-2291-related-items-v2` |
| Arms | A: module v1 (control); B: module v2, the carousel (`docs/TRACKING.md`) |
| Assignment | at the user's first eligible product pageview (`EXPERIMENT.md` section 2) |
| Start | 2026-09-01 00:00Z |
| End | 2026-09-15 00:00Z |
| Analysis plan | `EXPERIMENT.md`, agreed 2026-08-25 |
| Export | taken 2026-09-15 06:00Z, after the nightly bot screening run of 02:00Z |

## Log
- 2026-08-25: analysis plan agreed.
- 2026-09-01 00:00Z: started; the assignment service randomizes users 50/50.
- 2026-09-03: dogfood: the 100 accounts of the product pages team added to the allowlist of variant B in the
  feature-flag console (RI-322), so that the team can use v2 on the live site.
- 2026-09-15 00:00Z: ended; export taken at 06:00Z.
