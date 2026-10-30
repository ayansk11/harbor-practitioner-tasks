# Note from Priya (PM, product pages), 2026-09-15

Hi! The EXP-2291 readout (`output/result.json`) came back: B lifts click-through by 4.1% and p = 0.0003. I'd like to
turn B on for everyone tomorrow at 10:00.

One thing bugs me: B has fewer users and fewer pageviews than A (about 19,500 vs 20,000 users), and I thought the
split was 50/50. Is that a problem? Please check the analysis against the plan in `EXPERIMENT.md` before I ship, fix
whatever is wrong, and give me the corrected readout in `output/result.json`. We'll reuse this pipeline for the next
experiments, so please fix it properly rather than just this one file.
