"""Wrong attempt no_bot_filter (must score 0): the click metric and the hand-assigned accounts are fixed (the
canonical files), but the bot filter is dropped altogether, because the shipped filter is what made the sample ratio
check fail. The plan excludes bot traffic from both arms (EXPERIMENT.md section 3), and the ua_crawler flags mark
crawlers by who the client is, so the crawlers are counted in both arms.
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
     '    users = randomized  # no bot filter: the filter is what made the sample ratio check fail\n')
