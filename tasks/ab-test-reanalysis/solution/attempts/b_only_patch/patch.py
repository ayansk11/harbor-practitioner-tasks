"""Wrong attempt b_only_patch (must score 0): an instance patch fitted to EXP-2291, where the carousel (and with it the
arrow taps and the velocity flags tripped by those taps) is in arm B. Hand-assigned accounts are dropped in both arms (the
canonical files), but the two other fixes are applied to arm B only: in B, users whose only flags are velocity stay in
and a counted pageview is clicked when it has an item: event; in A, every flagged user is excluded and the export's
`clicked` flag is kept, as shipped. Another export can put the carousel in A, and the "See all" link (link:all) is
in both module versions from 2026-09-08, so the shipped click flag in A counts its clicks on every export.
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
     '    users = randomized[~randomized["user_id"].isin(bots)]\n',
     '    # EXP-2291: the carousel and its velocity flags are in B; keep velocity-only users there, in A drop every flag\n'
     '    flagged = bot_flags["user_id"]\n'
     '    users = randomized[~(randomized["user_id"].isin(bots)\n'
     '                         | ((randomized["variant"] != "B") & randomized["user_id"].isin(flagged)))]\n')
edit("abtest/report.py",
     '    pageviews["clicked"] = pageviews["pageview_id"].isin(load_item_pageviews(data_dir)).astype("int64")\n',
     '    item = pageviews["pageview_id"].isin(load_item_pageviews(data_dir)).astype("int64")\n'
     '    # EXP-2291: the arrows are in B; item: events there, the export\'s clicked flag (as shipped) in A\n'
     '    pageviews["clicked"] = item.where(pageviews["variant"] == "B", pageviews["platform_clicked"])\n')
