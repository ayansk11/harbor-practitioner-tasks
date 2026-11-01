# Local probes of ab-test-reanalysis (authoring only)

Five more wrong readouts that must score 0, run on the Mac only (design section 5, "local probes only"). The probes
are not part of the task package, so `tools/proof_matrix.py` never runs any of these on Daytona. Each folder has the layout of an
attempt folder (`solution/attempts/<name>/`): a `patch.py` applied to the canonical files, as `solution/solve.sh`
applies an attempt. `local_check.py --all` (one folder up) copies each probe into its own scratch copy of `solution/`,
runs `solve.sh` with `SOLUTION=<name>` and grades the result with `tests/grade.py`.

| Probe | The mistake |
|---|---|
| `drop_nav_pageviews` | the pageviews with an arrow tap (a `nav:` event) are removed from both counts |
| `user_click_join` | clicks are joined to users, not to counted pageviews (pageviews before assignment included) |
| `srm_all_assigned` | the sample ratio check runs on every assigned user, not on the plan's `n_users` |
| `text_time` | timestamps are compared as text (the export mixes `Z` and `+hh:mm` / `-hh:mm` offsets) |
| `keep_pre_assignment` | the pageviews before the user's `assigned_at` are counted |

Where each one fails: `local_check.out.md` (the Design column and the failing keys per set).
