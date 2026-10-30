# Proof matrix: et0-station-ingest (run smoke, Daytona, Harbor 0.25.0; Mac clock MST)

Overall: ALL AS EXPECTED

| Variant | Command | Expected | Rewards | Exceptions | Result | Job folder |
|---|---|---|---|---|---|---|
| canonical | `-a oracle -k 1` | 1 | [1.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-canonical-smoke` |
| nop | `-a nop` | 0 | [0.0] | - | PASS | `jobs/et0-station-ingest/et0-station-ingest-nop-smoke` |
