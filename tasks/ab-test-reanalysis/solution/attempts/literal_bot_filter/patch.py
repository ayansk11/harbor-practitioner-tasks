"""Wrong attempt literal_bot_filter (must score 0): the click metric and the hand-assigned accounts are fixed (the
canonical files), but the bot filter is read literally, as the shipped code does: every user with any bot_flags row
is excluded, velocity flags included. The velocity rule counts module_click events made after assignment, so in an arm
with the carousel it flags heavy human users (arrow taps); excluding those users shrinks that arm, and the sample ratio
check fails.
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
     '    bots = bot_flags.loc[bot_flags["rule"].isin(CLIENT_RULES), "user_id"]\n',
     '    bots = bot_flags["user_id"]  # every flagged user is bot traffic, whatever the rule\n')
