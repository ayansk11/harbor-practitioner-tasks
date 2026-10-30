"""Attempt I (plausible wrong fix): the cursor carries (created_at, id), but the condition is written as
`created_at <= ? AND id < ?` instead of "an older second, or the same second and a lower id". It works while ids grow
with created_at, and drops every backfilled order (high id, old created_at) after the first page. Must score 0
(c1 order)."""
import pathlib, shutil, sys

app = pathlib.Path(sys.argv[1])
canonical = pathlib.Path(__file__).resolve().parents[2] / "canonical" / "app" / "orders_service"
for name in ("pagination.py", "queries.py"):
    shutil.copyfile(canonical / name, app / "orders_service" / name)
p = app / "orders_service" / "pagination.py"
text = p.read_text()
old = 'return "(created_at, id) < (?, ?)", [cursor.created_at, cursor.id]'
assert text.count(old) == 1
p.write_text(text.replace(old, 'return "created_at <= ? AND id < ?", [cursor.created_at, cursor.id]'))
