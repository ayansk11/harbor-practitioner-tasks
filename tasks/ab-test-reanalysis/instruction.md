# EXP-2291: check the A/B readout before the PM ships

The readout in `/app/output/result.json` says variant B lifts click-through by 4.1% with p = 0.0003, and the PM wants
to turn B on for everyone tomorrow (`/app/PM_NOTE.md`). She noticed that the two arms are not the same size.

Audit the readout pipeline in `/app/abtest` against the analysis plan `/app/EXPERIMENT.md`, fix every place where it
does not follow the plan, and regenerate `/app/output/result.json` from `/app/data` with the fixed pipeline. The
pipeline will be reused for other experiments, so this command must produce the plan's readout for any experiment
folder with the same three files and columns:

    cd /app && python -m abtest.report --data <folder> --out <file>

How the result is checked:
- `/app/output/result.json` must be the plan's readout of `/app/data`, with the keys and types listed in
  `/app/EXPERIMENT.md` section 9 (extra keys are fine).
- A copy of `/app` (at another path) is used to run the command above, from the copy's top folder, as an unprivileged
  user without network access, on five other experiment folders of the same layout (each at most 50,000 users and
  500,000 pageview rows). Each run must exit with status 0 within 120 seconds and write its `--out` file; plan for
  one CPU and 2 GiB of memory. Do not rely on absolute paths under `/app` or on `/app/data` being there.
- The grading machine has the Python packages this container started with (numpy, pandas and scipy, with their
  dependencies) and nothing else; anything you install outside `/app` is not there.
- Each of the six readouts (`/app/output/result.json` and the five runs) is compared with our reference: `n_users`,
  `pageviews` and `clicks` exactly; `ctr` and `diff` within 1e-9; `srm_p` within 1% relative (or both below 1e-12);
  `srm_flag` and `decision` exactly. Each bound of `ci_95` must be within 0.25 times the reference interval's
  half-width of the reference bound. The reference interval is the delta method (plan section 5a); the plan's
  bootstrap and cluster-robust options also land within this tolerance.
- The task passes only if all six readouts pass.

Only /app is kept when we grade: folders named `data`, `__pycache__` or `.venv` anywhere under /app are dropped, and the packages already installed are available.
