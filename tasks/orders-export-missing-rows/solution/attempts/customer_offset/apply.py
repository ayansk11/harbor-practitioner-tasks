"""Attempt L (plausible wrong fix): the canonical pagination.py for /orders; the customer listing (queries.py, copied
from app/ by solve.sh) pages with LIMIT/OFFSET, so app.py passes it the raw cursor. Must score 0 (c4 customer walk)."""
import pathlib, shutil, sys

app = pathlib.Path(sys.argv[1])
canonical = pathlib.Path(__file__).resolve().parents[2] / "canonical" / "app" / "orders_service" / "pagination.py"
shutil.copyfile(canonical, app / "orders_service" / "pagination.py")
p = app / "orders_service" / "app.py"
text = p.read_text()
old = '''        cursor = pagination.decode_cursor(request.args.get("cursor"))
        rows, next_cursor = queries.customer_orders_page(con, customer_id, limit, cursor)'''
assert text.count(old) == 1
p.write_text(text.replace(old, '''        rows, next_cursor = queries.customer_orders_page(con, customer_id, limit, request.args.get("cursor"))'''))
