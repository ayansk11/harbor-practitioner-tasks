"""Local probe user_click_join (must score 0; not part of the task package, not run on Daytona): the population and
the item: rule are right (the canonical files), but a user's clicks are joined to the user, not to the counted
pageviews: every pageview of the user with an item: event in module_clicks counts, the pageviews before assigned_at
included, while the views stay the counted pageviews.
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

APP = pathlib.Path(sys.argv[1])


def edit(rel, old, new):
    p = APP / rel
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        sys.exit(f"patch.py: the canonical text was not found once in {rel}")
    p.write_text(s.replace(old, new), encoding="utf-8")


old = '    per_user = per_user_counts(users, pageviews)\n'
edit("abtest/report.py", old,
     old + '    from .load import _read\n'
           '    mc = _read(data_dir, "module_clicks", ("pageview_id", "user_id", "target"))\n'
           '    opened = mc.loc[mc["target"].str.startswith("item:")].groupby("user_id")["pageview_id"].nunique()\n'
           '    per_user["clicks"] = per_user["user_id"].map(opened).fillna(0)\n')
