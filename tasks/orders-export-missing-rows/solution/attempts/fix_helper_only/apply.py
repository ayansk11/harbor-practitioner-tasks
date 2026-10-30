"""Attempt B (plausible incomplete fix): the canonical fix of the shared helper (pagination.py: the cursor carries
(created_at, id), a row-value condition), but the inline copy in queries.py is left as it was, so
GET /customers/<id>/orders still skips the rest of a same-second group. Must score 0 (c3 customers, and c4 through the
customer walks after the inserts)."""
import pathlib, shutil, sys

app = pathlib.Path(sys.argv[1])
canonical = pathlib.Path(__file__).resolve().parents[2] / "canonical" / "app" / "orders_service" / "pagination.py"
shutil.copyfile(canonical, app / "orders_service" / "pagination.py")
