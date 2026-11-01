"""Wrong attempt keep_overrides (must score 0): the click metric and the bot filter are fixed (the canonical files), but
the accounts whose variant was set by hand in the feature-flag console (assignments.method = "override": dogfood and QA
accounts) are kept. Those accounts were not randomized, so the plan's experiment (EXPERIMENT.md section 3) does not
include those accounts; a large cohort of such accounts also hides a real imbalance of the randomized users from the
sample ratio check.
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

APP = pathlib.Path(sys.argv[1])


def edit(rel, old, new):
    p = APP / rel
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        sys.exit(f"patch.py: the canonical text was not found once in {rel}")
    p.write_text(s.replace(old, new), encoding="utf-8")


edit("abtest/filters.py",
     '    randomized = assignments[assignments["method"] == "hash"]\n',
     '    randomized = assignments  # every assigned user, method hash or override\n')
