"""Local probe text_time (must score 0; not part of the task package, not run on Daytona): every rule is right (the
canonical files), but the timestamps are never parsed, so "ts at or after assigned_at" compares the text of the two
values. The export writes each timestamp with Z or a +hh:mm / -hh:mm offset, so text order is not time order.
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
     '    return pd.to_datetime(col, utc=True, format="ISO8601")\n',
     '    return col  # timestamps kept as text and compared as text\n')
