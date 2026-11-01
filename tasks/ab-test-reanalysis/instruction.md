# EXP-2291: is "related items v2" a win?

The readout of experiment EXP-2291 (`/app/output/result.json`) came back `"invalid"`: the pipeline's sample ratio
check failed, with about 5% fewer users in B than in A. The PM does not trust that verdict (`/app/PM_NOTE.md`): the
assignment dashboard shows a clean 50/50 split, the team dashboard shows B's click-through 12.3% above A's, and the PM
wants to turn B on for everyone on Monday.

Find out what this experiment really shows. Fix the readout pipeline in `/app/abtest` so that its readout answers the
plan's question as the plan defines it, and regenerate `/app/output/result.json` with it from `/app/data`.
- `/app/EXPERIMENT.md`, the analysis plan agreed before launch, defines the readout: who is in the experiment, what
  counts as a click, the interval, the sample ratio check and the decision.
- `/app/docs` holds the data platform's documentation of how each export file and column is produced, which applies
  to every export of this layout, and the launch record of EXP-2291. Both are accurate.
- Everything else (the pipeline's code, comments and README, the dashboards in the PM's note, the current readout)
  is not authoritative: it may be wrong, out of date, or measure something other than the plan's quantities.

Check the code, the documentation and the data against each other: a readout is right only if every number in it
measures what the plan says it measures. If the experiment itself cannot be read, the readout says so with the
decision `"invalid"`. Put a short explanation for the PM in the readout as `notes`, a list of strings (not graded).

The pipeline is reused for every experiment the platform exports in this layout (other experiments differ in what
each arm shows, and in their traffic, bots and accounts), so this command must give the right readout for any such
export folder:

    cd /app && python -m abtest.report --data <folder> --out <file>

How the result is checked:
- `/app/output/result.json` must be the readout of `/app/data`, with the keys and types of `/app/EXPERIMENT.md`
  section 9 (extra keys are fine).
- A copy of `/app` (at another path) runs the command above, from the copy's top folder, as an unprivileged user
  without network access, on five other export folders with the same four `.csv.gz` files (each at most 50,000
  assigned users, 500,000 pageview rows and 100,000 module_clicks rows). Each run must exit with status 0 within 120
  seconds and write its `--out` file; plan for one CPU and 2 GiB of memory. Do not rely on absolute paths under
  `/app` or on `/app/data` being there.
- The grading machine has the Python packages this container started with (numpy, pandas and scipy, with their
  dependencies) and nothing else; anything installed outside `/app` is not there.
- Each of the six readouts (`/app/output/result.json` and the five runs) is compared with the reference readout of
  the same export: `n_users`, `pageviews` and `clicks` exactly; `ctr` and `diff` within 1e-9; `srm_p` within 1%
  relative (or both below 1e-12); `srm_flag` and `decision` exactly; each bound of `ci_95` within 0.25 times the
  reference interval's half-width of the reference bound. The reference interval is the plan's delta method (section
  5a); its bootstrap and cluster-robust options also land within this tolerance.
- The task passes only if all six readouts pass.

Only /app is kept when we grade: folders named `data`, `__pycache__` or `.venv` anywhere under /app are dropped, and the packages already installed are available.
