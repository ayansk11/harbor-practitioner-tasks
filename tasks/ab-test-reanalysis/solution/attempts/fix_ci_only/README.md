# Attempt fix_ci_only (must score 0)

A plausible half-fix: the user-level CI, the SRM check and the plan's decision rule are fixed (canonical `stats.py`
and `report.py`), but the bot filter that removes bots from arm B only is left in place. `solution/solve.sh` applies it
itself (`SOLUTION=fix_ci_only`); this folder holds no code. It exists so that `submission/tools/proof_matrix.py`, which
lists the attempts by the entries of `solution/attempts/`, runs this attempt on Daytona too.
