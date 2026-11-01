"""Wrong attempt platform_clicked (must score 0): the population is fixed (hash-assigned users only, ua_crawler flags
out, velocity flags kept; the canonical files), but a counted pageview's click is still the export's precomputed
`clicked` flag, which marks any module_click event on the pageview: the carousel's arrow taps (nav:prev, nav:next) and
the "See all" link (link:all) included, although neither opens a related product (EXPERIMENT.md section 4).
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
     '    pageviews["clicked"] = pageviews["platform_clicked"]  # the export\'s module click flag, as shipped\n')
