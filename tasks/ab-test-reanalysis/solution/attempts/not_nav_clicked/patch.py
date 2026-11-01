"""Wrong attempt not_nav_clicked (must score 0): the population is fixed (the canonical files) and the arrow taps are
seen, but the click metric is defined negatively: a counted pageview is clicked when it has any module_click event
whose target is not nav:. The "See all" link (link:all, in both module versions from 2026-09-08) opens the list page,
not a related product, so it is counted although EXPERIMENT.md section 4 does not count it.
Usage: python patch.py <app dir>  (applied after the canonical files are copied)."""
import pathlib, sys

APP = pathlib.Path(sys.argv[1])


def edit(rel, old, new):
    p = APP / rel
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        sys.exit(f"patch.py: the canonical text was not found once in {rel}")
    p.write_text(s.replace(old, new), encoding="utf-8")


edit("abtest/load.py",
     'mc.loc[mc["target"].str.startswith("item:"), "pageview_id"]',
     'mc.loc[~mc["target"].str.startswith("nav:"), "pageview_id"]')
