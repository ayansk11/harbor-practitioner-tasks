"""Attempt A (plausible wrong fix): "rows with the cursor's timestamp are skipped, so include them": `<` becomes
`<=` in both listings. Every page that ends inside a same-second group now repeats that group's first rows, and a
group larger than `limit` returns the same page forever. Must score 0 (c1 order, c2 pages)."""
import pathlib, sys

app = pathlib.Path(sys.argv[1])


def sub(rel, old, new):
    p = app / rel
    text = p.read_text()
    assert text.count(old) == 1, (rel, old)
    p.write_text(text.replace(old, new))


sub("orders_service/pagination.py", 'clauses.append("created_at < ?")', 'clauses.append("created_at <= ?")')
sub("orders_service/queries.py", 'sql += " AND created_at < ?"', 'sql += " AND created_at <= ?"')
