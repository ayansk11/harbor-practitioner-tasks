# Note from Priya (PM, product pages), Wednesday 2026-09-16

**Subject:** EXP-2291 readout: please re-check before the launch on Monday

The readout in `output/result.json` came back "invalid": the sample ratio check failed, with 16,570 users in A and
15,722 in B (about 5% fewer in B). That verdict does not match the dashboards:
- the assignment dashboard shows 16,935 users in A and 17,165 in B: a clean 50/50 split (49.7% / 50.3%);
- the team dashboard, which reads the same export with no filters (every pageview of every assigned user), shows
  click-through of 11.03% in B against 9.82% in A: B is 12.3% higher.

Plan: turn B on for everyone on Monday 2026-09-21 if B really wins. Requests: check the analysis against the plan in
`EXPERIMENT.md`, fix whatever is wrong, and put the corrected readout in `output/result.json`. The same pipeline will
run the next experiments, so the pipeline needs a proper fix, not just this one file.
