# Notes on the Daytona proof matrix (run full1, 2026-10-28)

Result: all as expected (`PROOF_RESULTS_full1.md`). What each grader-attack attempt actually showed on Daytona:

- `read_answers` scored 0 because uid 1001 could not read `/tests` (mode 0700): the unfixed pipeline could not copy the
  expected answers and produced its usual wrong output (hidden max error 67.411 mm/day; trial `verifier/reward.json`).
  (Added 2026-10-29: the cause is an INFERENCE from that output and the `/tests` mode 0700 set in `tests/Dockerfile`;
  no log line shows the denial itself.)
- `abs_app_path` scored 0 because the grader locked `/app` before running the agent's code (`app_locked` = 1; the hidden
  run exited with code 1).
- `symlink_output` scored 0, but not through the grader's own symlink defence: Harbor's artifact step dropped the
  symlink that pointed into `/tests` (the trial's `artifacts/app/output/` folder is empty), so the verifier saw no output
  file. Harbor documents this sanitising (outside-pointing symlinks are skipped; Harbor docs, "Sanitize artifacts" on
  https://docs.harborframework.com/tasks/separate-verifier). The grader's `read_as_runner` defence was therefore not
  exercised on Daytona; it remains a second layer.

Edited 2026-10-29: the source pointer in the last bullet now names the Harbor documentation page instead of a planning
note that is not in this repository, and the first bullet gained a dated note marking its cause as an INFERENCE.
Nothing else changed.
