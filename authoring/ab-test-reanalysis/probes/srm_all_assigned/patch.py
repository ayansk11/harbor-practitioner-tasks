"""Local probe srm_all_assigned (must score 0; not part of the task package, not run on Daytona): every count and the
interval are right (the canonical files), but the sample ratio check is run on every distinct assigned user (both
methods, flagged users in) instead of on the n_users of EXPERIMENT.md section 3.
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

APP = pathlib.Path(sys.argv[1])


def edit(rel, old, new):
    p = APP / rel
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        sys.exit(f"patch.py: the canonical text was not found once in {rel}")
    p.write_text(s.replace(old, new), encoding="utf-8")


edit("abtest/report.py",
     '    srm_p = srm_pvalue(n_users["A"], n_users["B"])\n',
     '    srm_p = srm_pvalue(*(int((assignments["variant"] == arm).sum()) for arm in ARMS))  # every assigned user\n')
