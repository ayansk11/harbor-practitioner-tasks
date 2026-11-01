"""Local probe drop_nav_pageviews (must score 0; not part of the task package, not run on Daytona): the population and
the item: rule are right (the canonical files), but the pageviews with an arrow tap (a nav: event) are removed from
both counts, pageviews and clicks, instead of being counted as pageviews without a product open.
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

APP = pathlib.Path(sys.argv[1])


def edit(rel, old, new):
    p = APP / rel
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        sys.exit(f"patch.py: the canonical text was not found once in {rel}")
    p.write_text(s.replace(old, new), encoding="utf-8")


old = '    pv = pv.loc[pv["ts"] >= pv["assigned_at"]]\n'
edit("abtest/load.py", old,
     old + '    mc = _read(data_dir, "module_clicks", ("pageview_id", "target"))\n'
           '    pv = pv.loc[~pv["pageview_id"].isin(mc.loc[mc["target"].str.startswith("nav:"), "pageview_id"])]\n')
