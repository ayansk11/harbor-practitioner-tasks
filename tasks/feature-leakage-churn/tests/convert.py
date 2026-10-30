"""Run as uid 1001 by grade.py, never as root: read the agent's parquet, normalise it (compare.normalise) and write
plain JSON for root to parse (kit rule 3: root never deserializes agent output except as CSV, JSON or text).

python3 -I convert.py <features.parquet> <rows.json>   exit 0 ok, 3 output rejected (reason on stderr)
"""
import json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare as C  # noqa: E402

MAX_BYTES = 100_000_000  # a correct output is about 2 MB


def main(src, dst):
    try:
        if os.path.getsize(src) > MAX_BYTES:
            raise C.BadOutput(f"output file is larger than {MAX_BYTES} bytes")
        import pandas as pd
        n = C.normalise(pd.read_parquet(src))
    except Exception as e:
        print(f"{type(e).__name__}: {e}", file=sys.stderr)
        return 3
    cols = {"customer_id": [int(v) for v in n["customer_id"]], "as_of": [int(v) for v in n["as_of"]]}
    for c in C.INT_FEATS + C.FLOAT_FEATS:
        cols[c] = [None if math.isnan(v) else float(v) for v in n[c].tolist()]
    cols["status"] = [None if C._null(v) else str(v) for v in n["status"].tolist()]
    try:
        text = json.dumps(cols, allow_nan=False)
    except ValueError as e:  # an infinite value
        print(f"output rejected: {e}", file=sys.stderr)
        return 3
    with open(dst, "w") as f:
        f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
