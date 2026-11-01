"""Wrong attempt item_click_events (must score 0): the population and the item: rule are right (the canonical files),
but a pageview's clicks are its number of item: events instead of 1 when it has at least one. EXPERIMENT.md section 4
counts clicked pageviews: opening two related products from one pageview is still one clicked pageview.
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
     '    pageviews["clicked"] = pageviews["pageview_id"].isin(load_item_pageviews(data_dir)).astype("int64")\n',
     '    from .load import _read\n'
     '    mc = _read(data_dir, "module_clicks", ("pageview_id", "target"))\n'
     '    opens = mc.loc[mc["target"].str.startswith("item:"), "pageview_id"].value_counts()  # item: events per pageview\n'
     '    pageviews["clicked"] = pageviews["pageview_id"].map(opens).fillna(0).astype("int64")\n')
