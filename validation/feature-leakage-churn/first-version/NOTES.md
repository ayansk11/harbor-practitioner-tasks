# Notes on the Daytona proof matrix (2026-10-28)

- Run `full1`: every variant as expected except one of the ten canonical (oracle) trials, which ended with
  `DaytonaConnectionError` and no reward. Its `exception.txt` shows `socket.gaierror: [Errno 8] nodename nor servname
  provided, or not known`: the Mac running Harbor lost DNS while polling the verifier (the agent phase had finished in 8 s;
  the verifier phase then ran from 03:02:07 to 03:46:03 UTC while the client could not reach Daytona). This is a failure
  of the machine running Harbor, not of the task. The trial is kept in `jobs/` as it happened.
- Run `full1b`: the ten canonical trials re-run to give a clean record (see `PROOF_RESULTS_full1b.md`).
- Timings from `full1` (verifier `reward.json`): canonical feature builds about 0.47-0.48 s per run on Daytona; the loop
  alternative about 2.2-2.4 s; the per-run cap in grade.py is far above both.

Note 2026-10-29: `jobs/` is git-ignored; the shipped copy of the lost trial is `traces/canonical_full1_lost/`
(trial `feature-leakage-churn__dtTSGvN`, with its `exception.txt`).
