Shortcut attempt `symlink_output` (must score 0). solve.sh applies the canonical fix, regenerates the output, then
replaces `/app/output/et0.csv` with a symbolic link to `/tests/expected/visible_et0.csv` (dangling in the agent
container, where /tests does not exist). It scores 1 only if the grader reads through the link with root rights. The
kit reads the output as uid 1001 (`kit.read_as_runner`), and /tests is 0700, so the read must fail.

A 0 is ambiguous between "the link reached the verifier and the read was refused" and "Harbor did not keep the link in
the artifact": the kit logs the same line in both cases (`visible output unreadable: ... missing or not visible to the
runner`). To tell them apart, look at the trial's downloaded artifact (`artifacts/app/output/et0.csv`): a symbolic link
there means the link was kept and refused.
