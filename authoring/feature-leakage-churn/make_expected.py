"""Build step for feature-leakage-churn (authoring only):
1. regenerate the visible extract (seed 1) and the hidden extract H (seed 2) with gen_data.py;
2. run both references (ref_vectorized, ref_loop) on both extracts; they must agree (integers and statuses exactly,
   floats within 1e-9 absolute; nulls alike), else stop;
3. write the expected H features (ref_vectorized) to tests/expected/H_features.parquet;
4. report the boundary facts the design asks for (events exactly at a row's as_of; labels landing on both sides);
5. write tests/SHA256SUMS over the hidden inputs and the expected file.
python make_expected.py
"""
import gzip, hashlib, os, shutil, sys, tempfile
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_data, dataset_io, ref_vectorized, ref_loop  # noqa: E402

TASK = gen_data.TASK
TESTS = os.path.join(TASK, "tests")
INT_FEATS = ["orders_7d", "orders_30d", "spend_30d_cents", "tickets_30d"]
FLOAT_FEATS = ["days_since_last_order", "tenure_days", "app_minutes_7d", "te_district"]


def agree(a, b):
    a = a.sort_values(["customer_id", "as_of"]).reset_index(drop=True)
    b = b.sort_values(["customer_id", "as_of"]).reset_index(drop=True)
    assert len(a) == len(b) and (a.customer_id.values == b.customer_id.values).all() \
        and (a.as_of.values == b.as_of.values).all(), "row keys differ"
    worst = 0.0
    for c in INT_FEATS:
        assert (a[c].astype("int64").values == b[c].astype("int64").values).all(), c
    for c in FLOAT_FEATS:
        x, y = a[c].to_numpy(dtype="float64"), pd.to_numeric(b[c]).to_numpy(dtype="float64")
        assert (np.isnan(x) == np.isnan(y)).all(), f"{c}: null pattern differs"
        ok = ~np.isnan(x)
        d = float(np.max(np.abs(x[ok] - y[ok]))) if ok.any() else 0.0
        assert d <= 1e-9, f"{c}: max diff {d}"
        worst = max(worst, d)
    sa = [None if v is None or (isinstance(v, float) and np.isnan(v)) else v for v in a.status.astype(object)]
    sb = [None if v is None or (isinstance(v, float) and np.isnan(v)) else v for v in b.status.astype(object)]
    assert sa == sb, "status differs"
    return worst


def boundary_report(folder, feats):
    d = dataset_io.read_dataset(folder)
    pts = d["scoring_points"][["customer_id", "as_of"]]
    o = d["orders"][["customer_id", "ordered_at"]].rename(columns={"ordered_at": "as_of"})
    k = d["tickets"][["customer_id", "opened_at"]].rename(columns={"opened_at": "as_of"})
    at_t = len(pts.merge(o, on=["customer_id", "as_of"])) + len(pts.merge(k, on=["customer_id", "as_of"]))
    o7 = o.assign(as_of=o.as_of + 7 * 86400)
    at_left7 = len(pts.merge(o7, on=["customer_id", "as_of"]))
    at_left30 = len(pts.merge(o.assign(as_of=o.as_of + 30 * 86400), on=["customer_id", "as_of"]))
    k_left30 = len(pts.merge(k.assign(as_of=k.as_of + 30 * 86400), on=["customer_id", "as_of"]))
    dist = d["customers"].set_index("customer_id")["postcode_district"]
    lk = pd.DataFrame({"k": d["labels"].customer_id.map(dist), "as_of": d["labels"].label_available_at})
    pk = pts.assign(k=pts.customer_id.map(dist))
    same_k = pk.merge(lk, on=["k", "as_of"])
    any_k = pts.merge(lk[["as_of"]], on="as_of")
    lab = np.sort(d["labels"].label_available_at.to_numpy())
    t = pts.as_of.to_numpy()
    before = np.searchsorted(lab, t, side="left")
    print(f"  events stamped exactly at a row's as_of: {at_t}; orders exactly at as_of - 7 days: {at_left7}; "
          f"orders / tickets exactly at as_of - 30 days: {at_left30} / {k_left30}; "
          f"rows with a same-district label landing exactly at as_of: "
          f"{len(same_k[['customer_id', 'as_of']].drop_duplicates())} ({len(same_k)} pairs); "
          f"rows with any label landing exactly at as_of: {len(any_k[['customer_id', 'as_of']].drop_duplicates())}; "
          f"rows with some label landed before and some after as_of: {int(((before > 0) & (before < len(lab))).sum())}"
          f" of {len(t)}; rows with no label available yet (te uses p=0.05): {int((before == 0).sum())}")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    gen_data.main()
    vis_dir = os.path.join(TASK, "environment", "app", "data")
    hid_gz = os.path.join(TESTS, "hidden", "H")
    with tempfile.TemporaryDirectory() as tmp:
        hid_dir = os.path.join(tmp, "H")
        os.makedirs(hid_dir)
        for f in sorted(os.listdir(hid_gz)):
            with gzip.open(os.path.join(hid_gz, f)) as src, open(os.path.join(hid_dir, f[:-3]), "wb") as dst:
                shutil.copyfileobj(src, dst)
        for name, folder in (("visible", vis_dir), ("hidden H", hid_dir)):
            a = ref_vectorized.compute(folder)
            b = pd.DataFrame(ref_loop.compute(folder))
            worst = agree(a, b)
            print(f"{name}: references agree on {len(a)} rows (max float diff {worst:.3g})")
            boundary_report(folder, a)
            if name == "hidden H":
                os.makedirs(os.path.join(TESTS, "expected"), exist_ok=True)
                a = a.sort_values(["customer_id", "as_of"]).reset_index(drop=True)
                a["status"] = a["status"].astype(object)
                a.to_parquet(os.path.join(TESTS, "expected", "H_features.parquet"), index=False)
    files = sorted(os.path.join("hidden", "H", f) for f in os.listdir(hid_gz)) + ["expected/H_features.parquet"]
    with open(os.path.join(TESTS, "SHA256SUMS"), "w") as f:
        for rel in files:
            f.write(f"{sha(os.path.join(TESTS, rel))}  {rel}\n")
    print("wrote", os.path.join(TESTS, "SHA256SUMS"))


if __name__ == "__main__":
    main()
